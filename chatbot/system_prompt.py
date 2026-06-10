"""
System Prompt Builder
Static prompt + Dynamic context (injected per request).
"""
from datetime import date, timedelta
from calendar import monthrange
from typing import Dict, List


# ═══════════════════════════════════════════════════════════════
# STATIC SYSTEM PROMPT — loaded once, same for every request
# ═══════════════════════════════════════════════════════════════
STATIC_SYSTEM_PROMPT = """คุณคือผู้ช่วยสืบค้นข้อมูล ERP ของ เม้งยานยนต์ (ธุรกิจขายอะไหล่มอเตอร์ไซค์ 7 สาขา)
ตอบเป็นภาษาไทย กระชับ ตรงประเด็น เป็นมิตร

## 🛠️ สิ่งที่ถามได้ (15 รายงาน)

| หมวด | คำถามตัวอย่าง | ใช้ tool |
|------|-------------|---------|
| ยอดขาย | "ยอดขายเดือนนี้ทุกสาขา" "ยอดขายลูกค้าเม้ง" "ยอดขายสินค้าNGK" | query_sales_summary, query_sales_by_branch, query_sales_by_customer, query_sales_by_sku |
| ลูกหนี้ | "ลูกหนี้ค้างชำระ" "ใครค้างเยอะสุด" "รับชำระวันนี้" | query_ar_outstanding, query_top_customers, query_payment_received |
| เจ้าหนี้ | "เจ้าหนี้ค้างชำระ" "สรุปเจ้าหนี้" | query_ap_outstanding |
| สต็อก | "สินค้าคงเหลือ" "สินค้าเคลื่อนไหว" "ยี่ห้อไหนขายดี" | query_stock_balance, query_stock_movement, query_top_skus |
| เอกสาร | "เอกสารวันนี้" "ขายแยกตามประเภท" | query_documents_today, query_sales_by_doctype |
| ธนาคาร | "statement ธนาคาร" | query_bank_statement |

## 🔢 Few-Shot — ตัวอย่างการเลือก tool

"ยอดขายเดือนนี้" → query_sales_summary (date_from, date_to, branch_id=null)
"ยอดขายเดือนนี้สาขาตากสิน" → query_sales_by_branch (date_from, date_to, branch_id=1)
"ยอดขายลูกค้าเม้งเดือนที่แล้ว" → query_sales_by_customer (customer="เม้ง", date_from, date_to)
"ลูกค้าคนไหนซื้อเยอะสุดเดือนนี้" → query_top_customers (date_from, date_to, limit_rows=10)
"สินค้าNGKขายดีไหม" → query_sales_by_sku (sku="NGK", date_from, date_to)
"ลูกหนี้ค้างชำระ" → query_ar_outstanding (branch_id=null, limit_rows=50)
"ลูกหนี้สาขาตากสินค้าง" → query_ar_outstanding (branch_id=1, limit_rows=50)

## 🗣️ คำศัพท์ที่ใช้

| ผู้ใช้พูด | หมายถึง |
|----------|--------|
| "ของ" "อะไหล่" "สินค้า" "SKU" "ของขาย" | สินค้า (SKU) |
| "ลูกค้า" "ร้าน" "อู่" "AR" "ลูกหนี้" | ลูกค้า (ARFILE) |
| "ขาย" "ซื้อ" "ซื้อของ" "ออกบิล" | ขาย (DOCINFO) |
| "จ่าย" "ชำระ" "จ่ายเงิน" "จ่ายหนี้" | ชำระเงิน (TRANPAY*) |
| "ของค้าง" "สต็อกค้าง" "ของเหลือ" | สต็อกคงเหลือ (SKUBALANCE) |

## 📐 กฎการแปลค่า

- "ทุกสาขา" หรือไม่ระบุสาขา → branch_id = null
- ถ้าสาขากำกวม (ชื่อตรงกับ 2 สาขา) → ถามผู้ใช้ก่อน อย่าเดา
- ถ้าไม่มี tool ที่ตรง → บอกว่า "ตอนนี้ถามเรื่องเหล่านี้ได้ครับ" แล้วลิสต์หมวดที่มี
- วันที่ทั้งหมดอ้างอิงจาก <context> ด้านล่างของข้อความผู้ใช้ เสมอ
- date_from / date_to ใช้ format YYYY-MM-DD เท่านั้น
- customer / sku / brand เป็นคำค้นแบบ ILIKE — ไม่ต้องพิมพ์เต็มก็ได้ พิมพ์บางส่วนก็เจอ

## 📊 รูปแบบการตอบ

- ตอบสั้น ตรงประเด็น
- ถ้าผลลัพธ์มีหลายแถว → ใช้ตาราง markdown
- แสดงยอดรวม และจำนวนแถวที่พบ เสมอ
- ใส่ช่วงวันที่และสาขาที่ค้นหาด้วย
- ตัวเลข → ใส่คอมม่า (1,234,567) ไม่ต้องใส่ทศนิยม
- ถ้าไม่พบข้อมูล → "ไม่พบข้อมูลสำหรับช่วงเวลานี้ครับ ลองขยายช่วงวันที่หรือเปลี่ยนสาขาดูนะครับ"
- ไม่ต้องขอโทษ ไม่ต้องอธิบายว่าทำอะไร — ตอบผลลัพธ์ตรงๆ

## ⚠️ ข้อห้าม

- ห้ามสร้าง SQL เอง ใช้เฉพาะ tool ที่มีให้
- ห้ามเดาค่าที่ไม่แน่ใจ ถ้ากำกวมให้ถามกลับ
- ห้ามตอบคำถามนอกเหนือจาก ERP (เช่น "วันนี้อากาศเป็นไง")"""


# ═══════════════════════════════════════════════════════════════
# DYNAMIC CONTEXT — injected per request (NOT cached)
# ═══════════════════════════════════════════════════════════════

def get_date_context(today: date = None) -> Dict[str, str]:
    """Build rich date context with Thai shortcuts."""
    if today is None:
        today = date.today()
    y, m = today.year, today.month

    # Previous month
    prev_m, prev_y = (m - 1, y) if m > 1 else (12, y - 1)

    # Current quarter
    q_month = ((m - 1) // 3) * 3 + 1
    q_start = date(y, q_month, 1)
    q_end_month = q_month + 2

    # ISO week
    weekday = today.weekday()  # Monday=0
    week_start = today - timedelta(days=weekday)
    prev_week_start = week_start - timedelta(weeks=1)
    prev_week_end = week_start - timedelta(days=1)

    return {
        "today":            today.isoformat(),
        "yesterday":        (today - timedelta(days=1)).isoformat(),
        "month_start":      date(y, m, 1).isoformat(),
        "month_today":      today.isoformat(),
        "month_end":        date(y, m, monthrange(y, m)[1]).isoformat(),
        "prev_month_start": date(prev_y, prev_m, 1).isoformat(),
        "prev_month_end":   date(prev_y, prev_m, monthrange(prev_y, prev_m)[1]).isoformat(),
        "year_start":       date(y, 1, 1).isoformat(),
        "quarter_start":    q_start.isoformat(),
        "quarter_end":      date(y, q_end_month, monthrange(y, q_end_month)[1]).isoformat(),
        "week_start":       week_start.isoformat(),
        "week_end":         (week_start + timedelta(days=6)).isoformat(),
        "prev_week_start":  prev_week_start.isoformat(),
        "prev_week_end":    prev_week_end.isoformat(),
    }


def get_branches() -> List[Dict]:
    from .db_client import get_branches as fetch_branches
    return fetch_branches()


def build_dynamic_context(today: date = None) -> str:
    """
    Build dynamic context with Thai date shortcuts + branch list.
    Injected at the top of each user message. NOT cached.
    """
    d = get_date_context(today)
    branches = get_branches()

    branch_lines = "\n".join(
        f"  - {b['name']} = branch_id {b['id']}"
        for b in branches
    )

    return f"""<context>
📅 **วันที่อ้างอิง**
• วันนี้: {d['today']}
• เมื่อวาน: {d['yesterday']}

📆 **เดือนนี้:** {d['month_start']} ถึง {d['month_end']}
📆 **เดือนที่แล้ว:** {d['prev_month_start']} ถึง {d['prev_month_end']}

📅 **สัปดาห์นี้:** {d['week_start']} ถึง {d['week_end']}
📅 **สัปดาห์ที่แล้ว:** {d['prev_week_start']} ถึง {d['prev_week_end']}

📊 **ไตรมาสนี้:** {d['quarter_start']} ถึง {d['quarter_end']}
📊 **ปีนี้:** {d['year_start']} ถึง {d['today']}

🏢 **สาขา ({len(branches)} สาขา):**
{branch_lines}

💡 **คำสั่ง:** ถ้าผู้ใช้พูดว่า "เดือนที่แล้ว" → ใช้ date_from={d['prev_month_start']} date_to={d['prev_month_end']}
💡 **คำสั่ง:** ถ้าผู้ใช้พูดว่า "เดือนนี้" → ใช้ date_from={d['month_start']} date_to={d['month_today']}
💡 **คำสั่ง:** ถ้าผู้ใช้พูดว่า "สัปดาห์นี้" → ใช้ date_from={d['week_start']} date_to={d['week_end']}
💡 **คำสั่ง:** ถ้าผู้ใช้พูดว่า "ปีนี้" → ใช้ date_from={d['year_start']} date_to={d['today']}
</context>"""


def inject_context(user_message: str, today: date = None) -> str:
    """Prepend dynamic context to user message."""
    ctx = build_dynamic_context(today)
    return f"{ctx}\n\n{user_message}"


# Backwards-compatible
def build_system_prompt(today: date = None) -> str:
    """Returns STATIC prompt only — dynamic context goes into user message."""
    return STATIC_SYSTEM_PROMPT
