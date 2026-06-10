"""
Main Chat Function
Handle conversation with DeepSeek using OpenAI-compatible function calling.
"""
import json
from openai import OpenAI
from typing import Dict, List, Any, Tuple, Optional
from .settings import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from .tools import build_tools
from .system_prompt import build_system_prompt, inject_context
from .runner import run_sql_template, format_rows_for_claude


# Initialize OpenAI client pointed at DeepSeek
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

# Cache tools (they don't change between requests)
_cached_tools: Optional[List[Dict]] = None


def _get_tools() -> List[Dict]:
    global _cached_tools
    if _cached_tools is None:
        _cached_tools = build_tools()
    return _cached_tools


def chat(user_input: str, history: Optional[List[Dict]] = None) -> Tuple[str, List[Dict]]:
    """
    Main chat function with multi-turn support.

    Args:
        user_input: User's question in Thai
        history: Optional conversation history (last 5 turns)

    Returns:
        (response_text, updated_history)
    """
    tools = _get_tools()
    system_prompt = build_system_prompt()

    # Dynamic context (date, branches) injected into the user message
    user_with_ctx = inject_context(user_input)

    # Initialize or limit history
    if history is None:
        history = []
    else:
        history = history[-10:]  # keep last 5 turns

    # Build messages: system + history + current user
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_with_ctx})

    try:
        # Debug logging
        _tools_count = len(tools) if tools else 0
        _msgs_preview = json.dumps(
            [{"role": m["role"], "content": str(m.get("content", ""))[:100]} for m in messages],
            ensure_ascii=False
        )
        print(f"\n{'='*60}")
        print(f"[REQUEST] model={DEEPSEEK_MODEL} base_url={DEEPSEEK_BASE_URL}")
        print(f"[REQUEST] tools: {_tools_count} definitions")
        print(f"[REQUEST] messages ({len(messages)} msgs): {_msgs_preview}")
        print(f"{'='*60}\n")

        # Round 1: DeepSeek selects function + extracts params
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=4096,
        )

        msg = response.choices[0].message
        usage = response.usage
        print(f"[USAGE] input={usage.prompt_tokens} output={usage.completion_tokens} total={usage.total_tokens}")

        # If no tool calls, model responded directly (clarification, greeting, etc.)
        if not msg.tool_calls:
            assistant_text = msg.content or ""
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": assistant_text})
            return assistant_text, history[-10:]

        # Run all tool calls and collect results
        all_errors = []
        tool_results = []

        # Add assistant message with tool_calls to history
        messages.append({
            "role": "assistant",
            "content": msg.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in msg.tool_calls
            ]
        })

        for tc in msg.tool_calls:
            template_name = tc.function.name
            try:
                params = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                all_errors.append(f"{template_name}: invalid JSON arguments")
                continue

            result = run_sql_template(template_name, params)

            if result["success"]:
                result_text = format_rows_for_claude(result["rows"], result["row_count"])
            else:
                result_text = f"❌ Error: {result['error']}"
                all_errors.append(f"{template_name}: {result['error']}")

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result_text
            })

        # If ALL tools failed, return error directly
        if all_errors and len(all_errors) == len(msg.tool_calls):
            error_msg = f"❌ เกิดข้อผิดพลาดในการค้นหาข้อมูล: {'; '.join(all_errors)}"
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": error_msg})
            return error_msg, history[-10:]

        # Round 2: DeepSeek summarizes results
        print(f"\n{'='*60}")
        print(f"[REQUEST R2] messages: {len(messages)} total")
        print(f"{'='*60}\n")

        final_response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
            max_tokens=4096,
        )

        usage2 = final_response.usage
        print(f"[USAGE R2] input={usage2.prompt_tokens} output={usage2.completion_tokens} total={usage2.total_tokens}")

        final_text = final_response.choices[0].message.content or ""

        # Return cleaned history (user + assistant only, no tool messages)
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": final_text})

        return final_text, history[-10:]

    except Exception as e:
        error_msg = f"❌ เกิดข้อผิดพลาด: {str(e)}"
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": error_msg})
        return error_msg, history[-10:]


def chat_simple(user_input: str) -> str:
    """Simple chat without history (for testing). Returns text only."""
    response, _ = chat(user_input, history=None)
    return response
