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
from .runner import run_sql_template, run_custom_sql, format_rows_for_claude


# Initialize OpenAI client pointed at DeepSeek
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

# Cache tools (they don't change between requests)
_cached_tools: Optional[List[Dict]] = None

# Max rounds of tool calls before forcing a text answer
# (allows chained queries + self-correcting failed SQL)
MAX_TOOL_ROUNDS = 3


def _get_tools() -> List[Dict]:
    global _cached_tools
    if _cached_tools is None:
        _cached_tools = build_tools()
    return _cached_tools


def _log_usage(prefix: str, usage) -> None:
    """Log token usage including cache hit/miss stats."""
    cache_hit = getattr(usage, 'prompt_cache_hit_tokens', None)
    cache_miss = getattr(usage, 'prompt_cache_miss_tokens', None)

    parts = [
        f"[USAGE {prefix}] input={usage.prompt_tokens} output={usage.completion_tokens} total={usage.total_tokens}"
    ]
    if cache_hit is not None:
        parts.append(f"cache_hit={cache_hit} cache_miss={cache_miss}")
        hit_pct = (cache_hit / usage.prompt_tokens * 100) if usage.prompt_tokens > 0 else 0
        parts.append(f"hit_rate={hit_pct:.0f}%")
    print(" ".join(parts))


def _run_tool(tc) -> Dict[str, Any]:
    """Run a single tool call (template or custom query). Returns result dict."""
    tool_name = tc.function.name
    try:
        params = json.loads(tc.function.arguments)
    except json.JSONDecodeError:
        return {"success": False, "error": f"{tool_name}: invalid JSON arguments"}

    if tool_name == "query_custom":
        sql = params.get("sql", "")
        if not sql:
            return {"success": False, "error": "query_custom: 'sql' parameter is required"}
        return run_custom_sql(sql, params)
    else:
        return run_sql_template(tool_name, params)


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
        print(f"[REQUEST] tools: {_tools_count} definitions (templates + query_custom)")
        print(f"[REQUEST] messages ({len(messages)} msgs): {_msgs_preview}")
        print(f"{'='*60}\n")

        # Tool loop: model can chain queries or retry a failed SQL.
        # IMPORTANT: `tools` + tool_choice="auto" in EVERY round — DeepSeek
        # serializes tool definitions into the prompt prefix; omitting tools
        # (or tool_choice="none", which drops them too) changes the prefix
        # and misses the entire cache. Verified: "none" cut hit rate 99%→48%.
        final_text = ""
        for round_no in range(1, MAX_TOOL_ROUNDS + 3):
            over_budget = round_no > MAX_TOOL_ROUNDS

            response = client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=4096,
            )

            msg = response.choices[0].message
            _log_usage(f"R{round_no}", response.usage)

            # No tool calls → model answered (or was forced to on last round)
            if not msg.tool_calls:
                final_text = msg.content or ""
                break

            chosen = [(tc.function.name, str(tc.function.arguments)[:80]) for tc in msg.tool_calls]
            print(f"[TOOL R{round_no}] DeepSeek chose: {chosen}")

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
                if over_budget:
                    # Budget exhausted — refuse execution, ask for a summary
                    result_text = (
                        "⚠️ ครบจำนวนรอบ query สูงสุดแล้ว — "
                        "กรุณาสรุปคำตอบจากข้อมูลที่ได้มาก่อนหน้านี้ "
                        "ถ้าข้อมูลไม่พอให้บอกผู้ใช้ตามตรง"
                    )
                else:
                    result = _run_tool(tc)
                    if result["success"]:
                        result_text = format_rows_for_claude(result["rows"], result["row_count"])
                    else:
                        # Feed the error back — model can fix the SQL and retry
                        result_text = f"❌ Error: {result['error']}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_text
                })

        if not final_text:
            final_text = "❌ ขออภัยครับ ค้นหาข้อมูลไม่สำเร็จในรอบที่กำหนด กรุณาลองถามใหม่อีกครั้ง"

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
