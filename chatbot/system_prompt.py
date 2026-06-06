"""
System Prompt Builder
Static prompt (cached) + Dynamic context (injected per request)
"""
from datetime import date, timedelta
from calendar import monthrange
from typing import Dict, List


# ─────────────────────────────────────────────
# STATIC SYSTEM PROMPT  (cached by Anthropic — never changes)
# ─────────────────────────────────────────────
STATIC_SYSTEM_PROMPT = """คุณคือผู้ช่วยสืบค้นข้อมูล ERP ของเม้งยานยนต์ ตอบเป็นภาษาไทย กระชับ ตรงประเด็น

## กฎการแปลค่า
- "ทุกสาขา" หรือไม่ระบุสาขา → branch_id = null
- ถ้าสาขากำกวม (เช่น "ตากสิน" ตรงกับ 2 สาขา) → ถามผู้ใช้ก่อน อย่าเดา
- ถ้าไม่มี template ที่ตรง → แจ้งว่าสืบค้นไม่ได้ อย่าสร้าง SQL เอง
- วันที่ทั้งหมดอ้างอิงจาก context ที่ส่งมาใน <context> ด้านล่างของแต่ละ message เสมอ

## รูปแบบการตอบ
- ตอบสั้น ชัดเจน ตรงประเด็น
- ถ้าผลลัพธ์มีหลายแถว ให้ใช้ตาราง markdown
- แสดงยอดรวมเสมอ
- ระบุช่วงวันที่และสาขาที่ค้นหาด้วย
- ถ้าไม่มีข้อมูล ให้บอกว่า "ไม่พบข้อมูล" พร้อมเสนอแนะให้ตรวจสอบเงื่อนไข

## ข้อควรระวัง
- ห้ามสร้าง SQL เอง ต้องใช้ tool ที่มีเท่านั้น
- ห้ามเดาค่าที่ไม่แน่ใจ ถ้ากำกวมให้ถามกลับ
- ถ้าไม่มี tool ที่เหมาะสม ให้บอกตรงๆ ว่าทำไม่ได้และแนะนำว่าถามอะไรได้บ้าง"""


# ─────────────────────────────────────────────
# DYNAMIC CONTEXT  (injected per request, prepended to user message)
# ─────────────────────────────────────────────

def get_date_context(today: date = None) -> Dict[str, str]:
    if today is None:
        today = date.today()
    y, m = today.year, today.month
    prev_m, prev_y = (m - 1, y) if m > 1 else (12, y - 1)
    return {
        "today":            today.isoformat(),
        "yesterday":        (today - timedelta(days=1)).isoformat(),
        "month_start":      date(y, m, 1).isoformat(),
        "month_end":        date(y, m, monthrange(y, m)[1]).isoformat(),
        "prev_month_start": date(prev_y, prev_m, 1).isoformat(),
        "prev_month_end":   date(prev_y, prev_m, monthrange(prev_y, prev_m)[1]).isoformat(),
        "year_start":       date(y, 1, 1).isoformat(),
    }


def get_branches() -> List[Dict]:
    from .supabase_client import get_supabase_client
    supabase = get_supabase_client()
    response = supabase.table('batch_branch') \
        .select('id, name, branch_code, enabled') \
        .eq('enabled', True) \
        .order('id') \
        .execute()
    return response.data


def build_dynamic_context(today: date = None) -> str:
    """
    Build the dynamic context block injected at the top of each user message.
    Contains: today's date shortcuts + branch list.
    Small and cheap — NOT cached.
    """
    d = get_date_context(today)
    branches = get_branches()

    branch_lines = "\n".join(
        f"  - {b['name']} = branch_id {b['id']} ({b['branch_code']})"
        for b in branches
    )

    return f"""<context>
วันที่: วันนี้={d['today']} | เมื่อวาน={d['yesterday']}
เดือนนี้: {d['month_start']} ถึง {d['month_end']}
เดือนที่แล้ว: {d['prev_month_start']} ถึง {d['prev_month_end']}
ปีนี้: {d['year_start']} ถึง {d['today']}
สาขา:
{branch_lines}
</context>"""


def inject_context(user_message: str, today: date = None) -> str:
    """Prepend dynamic context to user message."""
    ctx = build_dynamic_context(today)
    return f"{ctx}\n\n{user_message}"


# ─────────────────────────────────────────────
# Backwards-compatible wrapper (used by chat.py)
# ─────────────────────────────────────────────
def build_system_prompt(today: date = None) -> str:
    """Returns STATIC prompt only — dynamic context goes into user message."""
    return STATIC_SYSTEM_PROMPT
