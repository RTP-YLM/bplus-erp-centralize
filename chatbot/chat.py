"""
Main Chat Function
Handle conversation with Claude using Tool Use pattern
With prompt caching for cost optimization
"""
from anthropic import Anthropic
from typing import Dict, List, Any, Tuple, Optional
from .settings import ANTHROPIC_API_KEY, CLAUDE_MODEL
from .tools import build_tools
from .system_prompt import build_system_prompt, inject_context
from .runner import run_sql_template, format_rows_for_claude


# Initialize Anthropic client
client = Anthropic(api_key=ANTHROPIC_API_KEY)

# Cache tools (they don't change between requests)
_cached_tools: Optional[List[Dict]] = None



def _serialize_content(content) -> Any:
    """Convert Anthropic SDK ContentBlock objects to plain dicts for storage."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        result = []
        for block in content:
            if hasattr(block, 'model_dump'):
                result.append(block.model_dump())
            elif hasattr(block, '__dict__'):
                result.append({k: v for k, v in block.__dict__.items() if not k.startswith('_')})
            elif isinstance(block, dict):
                result.append(block)
            else:
                result.append(str(block))
        return result
    return content

def _get_tools() -> List[Dict]:
    global _cached_tools
    if _cached_tools is None:
        _cached_tools = build_tools()
    return _cached_tools



def _extract_text_from_content(content) -> str:
    """Extract plain text from any content type (string, list of blocks, SDK objects)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                # skip tool_use, tool_result, image, etc.
            elif hasattr(block, "type"):
                if block.type == "text":
                    parts.append(getattr(block, "text", ""))
        return " ".join(p for p in parts if p).strip()
    return ""


def _clean_history_for_next_turn(history: List[Dict]) -> List[Dict]:
    """
    Strip tool_use/tool_result blocks, keep only text content.
    Ensures proper user/assistant alternation to prevent Anthropic API 400 errors:
    - 'tool_use ids found without tool_result'
    - 'roles must alternate between user and assistant'
    """
    # Step 1: extract text-only, drop messages with no text (tool_use, tool_result, etc.)
    text_only = []
    for msg in history:
        text = _extract_text_from_content(msg.get("content", ""))
        if text:
            text_only.append({"role": msg["role"], "content": text})

    # Step 2: merge consecutive same-role messages
    # (happens when a tool_use-only assistant message is dropped between two user messages)
    merged = []
    for msg in text_only:
        if merged and merged[-1]["role"] == msg["role"]:
            merged[-1]["content"] += "\n" + msg["content"]
        else:
            merged.append(dict(msg))

    # Step 3: must start with "user" role (Claude API requirement)
    while merged and merged[0]["role"] != "user":
        merged.pop(0)

    return merged

def _build_cached_system(system_prompt: str) -> List[Dict]:
    """
    Wrap system prompt with cache_control for prompt caching.
    Anthropic caches the prefix, so placing cache_control on the
    system prompt means subsequent requests skip re-processing it.
    """
    return [
        {
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"}
        }
    ]


def chat(user_input: str, history: Optional[List[Dict]] = None) -> Tuple[str, List[Dict]]:
    """
    Main chat function with multi-turn support and prompt caching.

    Args:
        user_input: User's question in Thai
        history: Optional conversation history (last 5 turns)

    Returns:
        (response_text, updated_history)
    """
    # Static system prompt — CACHED by Anthropic (never changes between requests)
    tools = _get_tools()
    system_prompt = build_system_prompt()         # static only
    system_cached = _build_cached_system(system_prompt)

    # Dynamic context (date, branches) injected into the user message — NOT cached
    # Keeps cache valid all day; only ~50 tokens per request
    user_with_ctx = inject_context(user_input)

    # Initialize or limit history
    if history is None:
        history = []
    else:
        # Clean tool blocks and keep last 10 messages (5 turns)
        history = _clean_history_for_next_turn(history)[-10:]

    # Add current user message WITH context prepended
    messages = history + [{"role": "user", "content": user_with_ctx}]

    try:
        # Debug: log full request payload
        import json as _json
        def _serialize(obj):
            if hasattr(obj, '__dict__'):
                return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
            return str(obj)

        _sys_preview = _json.dumps(system_cached, ensure_ascii=False, default=_serialize)[:500]
        _msgs_preview = _json.dumps(messages, ensure_ascii=False, default=_serialize)[:2000]
        _tools_count = len(tools) if tools else 0
        print(f"\n{'='*60}")
        print(f"[REQUEST] model={CLAUDE_MODEL}")
        print(f"[REQUEST] system ({len(system_cached)} blocks): {_sys_preview}")
        print(f"[REQUEST] tools: {_tools_count} definitions")
        print(f"[REQUEST] messages ({len(messages)} msgs): {_msgs_preview}")
        print(f"{'='*60}\n")

        # Round 1: Claude selects template + params
        # System prompt is cached — subsequent requests reuse it
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=system_cached,
            tools=tools,
            messages=messages
        )

        # Log cache performance
        usage = response.usage
        cache_creation = getattr(usage, 'cache_creation_input_tokens', 0) or 0
        cache_read = getattr(usage, 'cache_read_input_tokens', 0) or 0
        print(f"[CACHE] input={usage.input_tokens} cache_create={cache_creation} cache_read={cache_read} output={usage.output_tokens}")

        # Collect ALL tool_use blocks (Claude may return parallel tool calls)
        tool_uses = [b for b in response.content if b.type == "tool_use"]

        # If no tool use, Claude responded directly (e.g., clarification question)
        if not tool_uses:
            assistant_text = ""
            for block in response.content:
                if block.type == "text":
                    assistant_text += block.text

            clean_history = _clean_history_for_next_turn(
                messages + [{"role": "assistant", "content": _serialize_content(response.content)}]
            )
            return assistant_text, clean_history

        # Run ALL tool calls and collect results
        tool_results = []
        all_errors = []

        for tool_use in tool_uses:
            template_name = tool_use.name
            params = tool_use.input
            tool_use_id = tool_use.id

            result = run_sql_template(template_name, params)

            if result["success"]:
                result_text = format_rows_for_claude(result["rows"], result["row_count"])
            else:
                result_text = f"❌ Error: {result['error']}"
                all_errors.append(f"{template_name}: {result['error']}")

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": result_text
            })

        # If ALL tools failed, return error directly (no tool blocks in history)
        if len(all_errors) == len(tool_uses):
            error_msg = f"❌ เกิดข้อผิดพลาดในการค้นหาข้อมูล: {'; '.join(all_errors)}"
            clean_history = _clean_history_for_next_turn(
                messages + [{"role": "assistant", "content": error_msg}]
            )
            return error_msg, clean_history

        # Round 2: Claude summarizes results
        messages_round2 = messages + [
            {
                "role": "assistant",
                "content": _serialize_content(response.content)
            },
            {
                "role": "user",
                "content": tool_results
            }
        ]

        _msgs2_preview = _json.dumps(messages_round2, ensure_ascii=False, default=_serialize)[:3000]
        print(f"\n{'='*60}")
        print(f"[REQUEST R2] messages ({len(messages_round2)} msgs): {_msgs2_preview}")
        print(f"{'='*60}\n")

        final_response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=system_cached,
            tools=tools,
            messages=messages_round2
        )

        # Log round 2 cache performance
        usage2 = final_response.usage
        cache_creation2 = getattr(usage2, 'cache_creation_input_tokens', 0) or 0
        cache_read2 = getattr(usage2, 'cache_read_input_tokens', 0) or 0
        print(f"[CACHE R2] input={usage2.input_tokens} cache_create={cache_creation2} cache_read={cache_read2} output={usage2.output_tokens}")

        # Extract final text response
        final_text = ""
        for block in final_response.content:
            if block.type == "text":
                final_text += block.text

        # Return cleaned history
        raw_history = messages_round2 + [{
            "role": "assistant",
            "content": _serialize_content(final_response.content)
        }]
        clean_history = _clean_history_for_next_turn(raw_history)

        return final_text, clean_history

    except Exception as e:
        error_msg = f"❌ เกิดข้อผิดพลาด: {str(e)}"
        clean_history = _clean_history_for_next_turn(messages)
        return error_msg, clean_history


def chat_simple(user_input: str) -> str:
    """Simple chat without history (for testing). Returns text only."""
    response, _ = chat(user_input, history=None)
    return response
