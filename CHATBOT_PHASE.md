# B+ Plus ERP — Chatbot Phase Design

> **Phase:** หลังจาก ETL Centralize พร้อมแล้ว  
> **Approach:** Template-based SQL + Claude Tool Use  
> **Target:** ถามข้อมูล ERP ด้วยภาษาไทย → ได้ผลลัพธ์ทันที

---

## 1. Architecture Overview

```
User: "ยอดขายลูกค้าเม้ง เดือนมิถุนายนนี้ สาขาตากสิน"
           │
           ▼
    ┌─────────────────────────────────────┐
    │  Claude API (Tool Use)              │
    │  - System Prompt (context)          │
    │  - Tool Definitions (15 templates)  │
    └─────────────────────────────────────┘
           │
           ▼ เลือก tool + แทน params อัตโนมัติ
    {
      tool: "query_sales_by_customer",
      params: {
        customer:  "เม้ง",
        date_from: "2026-06-01",
        date_to:   "2026-06-30",
        branch_id: 1
      }
    }
           │
           ▼
    ┌─────────────────────────────────────┐
    │  SQL Template Runner                │
    │  แทนค่า params → รัน PostgreSQL     │
    └─────────────────────────────────────┘
           │
           ▼ SQL results (rows)
    ┌─────────────────────────────────────┐
    │  Claude API (Round 2)               │
    │  สรุปผลลัพธ์เป็นภาษาไทย            │
    └─────────────────────────────────────┘
           │
           ▼
    "ยอดขายลูกค้าเม้ง เดือนมิถุนายน 2026
     รวม 3 รายการ ยอดรวม 45,800 บาท ..."
```

---

## 2. ทำไมถึงเลือก Template-based (ไม่ใช่ Text-to-SQL)

| | Template-based ✅ | Text-to-SQL |
|---|---|---|
| SQL ผิดพลาด | ต่ำมาก (เขียนไว้แล้ว) | สูง (generate เอง) |
| Join ซับซ้อน | รับประกันถูกต้อง | อาจ join ผิด |
| Performance | มี index ตาม template | ไม่รับประกัน |
| Flexibility | จำกัดแค่ที่เขียนไว้ | ถามได้ทุกอย่าง |
| ต้นทุน token | ต่ำกว่า | สูงกว่า (ต้องโหลด schema) |
| Schema KB | ไม่จำเป็น | จำเป็นมาก |

**สรุป:** ERP reports 90% เป็น structured queries (SUM, GROUP BY, date range)  
Template-based เหมาะกว่า — ขยายได้ทีหลังถ้าต้องการ ad-hoc queries

---

## 3. Query Templates

### 3.1 รายการ Templates (15 หลัก)

| # | Template Name | ใช้เมื่อถามเรื่อง | Params หลัก |
|---|---|---|---|
| 1 | `query_sales_by_customer` | ยอดขายตามลูกค้า | customer, date_from, date_to, branch_id? |
| 2 | `query_sales_by_branch` | ยอดขายตามสาขา | date_from, date_to, branch_id? |
| 3 | `query_sales_by_sku` | ยอดขายตามสินค้า | sku?, brand?, date_from, date_to, branch_id? |
| 4 | `query_sales_summary` | สรุปยอดขายรวม | date_from, date_to, branch_id? |
| 5 | `query_ar_outstanding` | ลูกหนี้ค้างชำระ | customer?, as_of_date, branch_id? |
| 6 | `query_ar_payment` | รับชำระลูกหนี้ | customer?, date_from, date_to, branch_id? |
| 7 | `query_stock_balance` | สต็อกคงเหลือ | sku?, brand?, branch_id? |
| 8 | `query_stock_movement` | การเคลื่อนไหวสินค้า | sku?, date_from, date_to, branch_id? |
| 9 | `query_documents_today` | เอกสารวันนี้/ล่าสุด | branch_id?, doc_type?, limit? |
| 10 | `query_payment_received` | เงินรับวันนี้/เดือนนี้ | date_from, date_to, branch_id? |
| 11 | `query_ap_outstanding` | เจ้าหนี้ค้างจ่าย | supplier?, as_of_date |
| 12 | `query_sales_by_doctype` | ยอดขายแยกประเภท (รถ/อะไหล่/ซ่อม) | date_from, date_to, branch_id? |
| 13 | `query_bank_statement` | รายการธนาคาร | bank?, date_from, date_to, branch_id? |
| 14 | `query_top_customers` | ลูกค้าสูงสุด | date_from, date_to, branch_id?, limit? |
| 15 | `query_top_skus` | สินค้าขายดี | date_from, date_to, branch_id?, limit? |

---

### 3.2 ตัวอย่าง SQL Template จริง

```sql
-- Template: query_sales_by_customer
-- Description: ดึงยอดขายตามลูกค้า ใช้เมื่อถามยอดขาย รายการซื้อ ของลูกค้าคนใดคนหนึ่ง

SELECT
    d.di_ref                            AS เลขเอกสาร,
    d.di_date                           AS วันที่,
    a.ar_name                           AS ลูกค้า,
    dt.dt_thaidesc                      AS ประเภท,
    COALESCE(SUM(t.trd_n_amt), 0)      AS ยอดสุทธิ
FROM docinfo d
JOIN dtype dt       ON dt.dt_key     = d.di_dt       AND dt.branch_id = d.branch_id
JOIN transtkh h     ON h.trh_di      = d.di_key       AND h.branch_id  = d.branch_id
JOIN transtkd t     ON t.trd_trh     = h.trh_key      AND t.branch_id  = h.branch_id
JOIN tranpayh p     ON p.tph_di      = d.di_key       AND p.branch_id  = d.branch_id
JOIN arfile a       ON a.ar_key      = p.tph_ar       AND a.branch_id  = p.branch_id
WHERE d.di_date BETWEEN :date_from AND :date_to
  AND a.ar_name ILIKE '%' || :customer || '%'
  AND (:branch_id IS NULL OR d.branch_id = :branch_id)
GROUP BY d.di_ref, d.di_date, a.ar_name, dt.dt_thaidesc
ORDER BY d.di_date DESC
LIMIT 50
```

**หลักการเขียน template:**
- `:param` = placeholder ที่ระบบแทนค่า — Claude ไม่แตะ SQL เลย
- `(:branch_id IS NULL OR ...)` = optional param, NULL = ทุกสาขา
- `LIMIT 50` ทุก template — ป้องกัน token พัง + ควบคุมต้นทุน
- `ILIKE '%...'` สำหรับชื่อ — รองรับพิมพ์บางส่วน

---

## 4. Tool Use Mechanism

### 4.1 Claude ไม่สร้าง SQL — แค่เลือก template + แทน params

```
Claude หน้าที่:   ประโยค → { tool_name, params }
System หน้าที่:  params → รัน SQL template → return rows
Claude หน้าที่:  rows → สรุปเป็นภาษาไทย
```

Claude ไม่รู้ว่า:
- มี table อะไรบ้าง
- join ยังไง
- branch_id เป็น column ไหน

### 4.2 Tool Definition (ที่ส่งใน API call)

```python
tools = [
    {
        "name": "query_sales_by_customer",
        "description": """
            ดึงยอดขายตามลูกค้า ใช้เมื่อถามเกี่ยวกับ
            ยอดขาย, รายการซื้อ, เอกสารขาย ของลูกค้าคนใดคนหนึ่ง
            ในช่วงวันที่หรือเดือนที่ระบุ
        """,
        "input_schema": {
            "type": "object",
            "properties": {
                "customer":  {"type": "string",  "description": "ชื่อลูกค้า (ค้นแบบ LIKE)"},
                "date_from": {"type": "string",  "description": "วันเริ่ม YYYY-MM-DD"},
                "date_to":   {"type": "string",  "description": "วันสิ้นสุด YYYY-MM-DD"},
                "branch_id": {"type": "integer", "description": "รหัสสาขา null = ทุกสาขา"},
            },
            "required": ["customer", "date_from", "date_to"]
        }
    },
    # ... อีก 14 tools
]
```

### 4.3 Flow จริง 2 Round Trips

```python
# Round 1: เลือก template + แทน params
res = claude.messages.create(
    model="claude-haiku-4-5",
    system=build_system_prompt(),    # inject วันที่ + สาขา
    tools=tools,                      # tools ทั้ง 15 ตัว
    messages=[{"role": "user", "content": user_input}]
)
# res.content[0].type == "tool_use"
# res.content[0].input == {"customer": "เม้ง", "date_from": "...", ...}

# รัน SQL
rows = run_sql_template(res.content[0].name, res.content[0].input)

# Round 2: สรุปผลลัพธ์
final = claude.messages.create(
    model="claude-haiku-4-5",
    system=build_system_prompt(),
    tools=tools,
    messages=[
        {"role": "user",      "content": user_input},
        {"role": "assistant", "content": res.content},
        {"role": "user",      "content": [{"type": "tool_result",
                                           "tool_use_id": res.content[0].id,
                                           "content": format_rows(rows)}]}
    ]
)
```

---

## 5. System Prompt Design

### 5.1 สิ่งที่ต้อง Inject ทุก Request (Runtime)

```python
def build_system_prompt():
    today      = date.today()
    branches   = fetch_from_db("SELECT id, name, branch_code FROM batch_branch WHERE enabled=true")
    doc_types  = fetch_from_db("SELECT dt_key, dt_doccode, dt_thaidesc FROM doctype LIMIT 50")

    return f"""
คุณคือผู้ช่วยสืบค้นข้อมูล ERP ของเม้งยานยนต์ ตอบเป็นภาษาไทย กระชับ ตรงประเด็น

## วันที่ปัจจุบัน
วันนี้: {today}
เดือนนี้: {today.replace(day=1)} ถึง {last_day_of_month(today)}
ปีนี้: {today.year}-01-01 ถึง {today}

## สาขา
{format_branches(branches)}

## กฎการแปลค่า
- "ทุกสาขา" หรือไม่ระบุสาขา → branch_id = null
- "เดือนที่แล้ว" → {prev_month_start} ถึง {prev_month_end}
- "ไตรมาสนี้" → {quarter_start} ถึง {today}
- ถ้าสาขากำกวม (เช่น "ตากสิน" ตรงกับ 2 สาขา) → ถามผู้ใช้ก่อน อย่าเดา
- ถ้าไม่มี template ที่ตรง → แจ้งว่าสืบค้นไม่ได้ อย่าสร้าง SQL เอง

## รูปแบบตอบ
- ตอบสั้น ใช้ตาราง markdown ถ้าผลหลายแถว
- แสดงยอดรวมเสมอ
- ระบุช่วงวันที่และสาขาที่ค้นหาด้วย
"""
```

### 5.2 สาขา → branch_id Mapping (ดึงจาก DB จริง)

```
ตากสิน 18        = branch_id 1   (MY00)
เอกชัย 118       = branch_id 2   (MY03)
เวสป้าสุขสวัสดิ์   = branch_id 3   (MY04)
เวสป้าตากสิน     = branch_id 4   (MY06)
เวสป้าบางโพ      = branch_id 5   (MY07)
```

**ไม่ hard-code ใน code** — ดึงจาก `batch_branch` table ทุก request

---

## 6. Parameter Extraction — Claude ทำอัตโนมัติ

| User พูด | Claude แปลเป็น params |
|---|---|
| "ยอดเม้งเดือนนี้" | customer="เม้ง", date=มิ.ย. 2026 |
| "สต็อก Honda สาขาเอกชัย" | brand="Honda", branch_id=2 |
| "ลูกหนี้ค้างทุกสาขา" | as_of=วันนี้, branch_id=null |
| "ขายรถไปกี่คันปีนี้" | doc_type=รถ, date=ม.ค.-มิ.ย. 2026 |
| "วันนี้มีเอกสารอะไรบ้าง" | date=วันนี้ |
| "3 เดือนที่แล้ว" | date_from=มี.ค., date_to=มี.ค. |
| "เมื่อวาน" | date_from=date_to=2026-06-04 |

**Claude รู้ได้เพราะ:** system prompt inject วันที่ปัจจุบัน + สาขา mapping ไว้แล้ว  
**Claude ไม่ต้องรู้:** โครงสร้าง DB, join, column names

---

## 7. ต้นทุน (Cost Estimation)

### 7.1 Token ต่อ 1 คำถาม

```
Round 1 Input:
  System prompt (วันที่ + สาขา + กฎ)    ≈    600 tokens
  Tool definitions (15 templates)         ≈  3,000 tokens
  User message                            ≈     50 tokens
  ─────────────────────────────────────────────────────
  รวม Round 1 Input                       ≈  3,650 tokens
  Output (tool call JSON)                 ≈    150 tokens

Round 2 Input:
  ซ้ำ Round 1 input                       ≈  3,650 tokens
  SQL results (LIMIT 50 rows)             ≈    750 tokens
  ─────────────────────────────────────────────────────
  รวม Round 2 Input                       ≈  4,400 tokens
  Output (คำตอบภาษาไทย)                  ≈    300 tokens

รวมทั้งหมด: ~8,050 input + ~450 output ต่อ 1 คำถาม
```

### 7.2 ราคาต่อ 1 คำถาม

| Model | ไม่มี Cache | มี Prompt Cache | ราคา (cache) |
|---|---|---|---|
| **Claude Sonnet** | $0.032 | $0.012 | **~฿0.43** |
| **Claude Haiku**  | $0.007 | $0.002 | **~฿0.07** |

### 7.3 Prompt Caching ทำไมถึงช่วย

System prompt + tool definitions = 3,600 tokens **ซ้ำทุก request**

```
ไม่ cache:  3,600 tokens × $3.00/MTok  = $0.0108 ต่อ request
มี cache:   3,600 tokens × $0.30/MTok  = $0.0011 ต่อ request  (ถูกกว่า 10x)
```

### 7.4 ต้นทุนต่อเดือน

```
สมมติ 100 คำถาม/วัน × 30 วัน = 3,000 คำถาม/เดือน

Sonnet + cache:  3,000 × $0.012 = $36/เดือน  ≈ ฿1,300
Haiku  + cache:  3,000 × $0.002 = $6/เดือน   ≈ ฿220
```

### 7.5 สิ่งที่ทำให้ต้นทุนสูงขึ้น

| ปัจจัย | ผลกระทบ | วิธีควบคุม |
|---|---|---|
| SQL คืน rows เยอะ | token output พัง | `LIMIT 50` ทุก template |
| Multi-turn (ถามต่อ) | history สะสม | cache + ตัด history เก่า |
| Template เยอะขึ้น | tool definitions โต | cache รองรับได้ |
| ใช้ Sonnet แทน Haiku | ~6x แพงขึ้น | เริ่ม Haiku ก่อน |

**แนะนำ: เริ่มด้วย Haiku + Prompt Cache** — ถ้าคุณภาพคำตอบไม่พอค่อย upgrade Sonnet

---

## 8. Schema Knowledge Base — ไม่จำเป็นสำหรับ Phase นี้

```
Template-based:  schema อยู่ใน SQL template แล้ว
                 Claude ไม่ต้องรู้โครงสร้าง DB
                 → Schema KB = overhead ไม่จำเป็น

Text-to-SQL:     Claude ต้องรู้ table/column/join
                 → Schema KB จำเป็นมาก (future phase)
```

---

## 9. Implementation Steps

```
Step 1: เขียน SQL templates 15 ตัว + ทดสอบใน PostgreSQL
Step 2: สร้าง tool definitions จาก templates
Step 3: เขียน system prompt + inject runtime context
Step 4: build_system_prompt() ดึง branches จาก batch_branch table
Step 5: เชื่อม Claude API (Haiku + prompt cache)
Step 6: ทดสอบ edge cases (สาขากำกวม, params ไม่ครบ)
Step 7: deploy + monitor cost จาก API usage dashboard
```

---

## 10. Folder Structure (เพิ่มจาก ETL)

```
bplus-erp-centralize/
  ├── etl/                    ← ETL batch (พร้อมแล้ว)
  ├── schema/
  │   ├── 001_batch_config.sql
  │   └── 002_query_templates.sql   ← เก็บ SQL templates ใน DB
  └── chatbot/
      ├── templates.py              ← load templates จาก DB
      ├── tools.py                  ← Claude tool definitions
      ├── system_prompt.py          ← build system prompt + inject context
      ├── runner.py                 ← รัน SQL template ด้วย params
      └── chat.py                   ← main chat loop
```

---

---


## 11. Error Handling & Edge Cases

### 11.1 สถานการณ์ที่ต้องจัดการ

```python
ERROR_MESSAGES = {
    "no_template":  "❌ ไม่พบรายงานที่ตรงกับคำถาม กรุณาลองถามใหม่ เช่น:\n"
                    "- ยอดขายลูกค้าเม้งเดือนนี้\n"
                    "- สต็อก Honda สาขาเอกชัย\n"
                    "- ลูกหนี้ค้างชำระทุกสาขา",

    "ambiguous":    "⚠️ '{term}' ตรงกับหลายสาขา กรุณาระบุ:\n{choices}",

    "no_results":   "📭 ไม่พบข้อมูลตามเงื่อนไขที่ระบุ\n"
                    "ลองตรวจสอบ: ช่วงวันที่ / ชื่อลูกค้า / สาขา",

    "db_error":     "❌ เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง",

    "db_timeout":   "⏱️ Query ใช้เวลานาน ลองระบุช่วงวันที่สั้นลง",
}
```

### 11.2 Fallback เมื่อไม่มี template ตรง

```
ไม่มี template → Claude ถามกลับ:
  "ต้องการดูข้อมูลด้านไหนครับ?
   1. ยอดขาย / เอกสาร
   2. สต็อกสินค้า
   3. ลูกหนี้ / ชำระเงิน
   4. อื่นๆ (ระบุ)"

→ user เลือก → วนกลับเลือก template ใหม่
```

**กฎสำคัญ:** Claude ต้องไม่สร้าง SQL เอง ถ้าไม่มี template ตรง — บอกตรง ๆ ว่าทำไม่ได้

---

## 12. Multi-turn Conversation

### 12.1 Follow-up ที่พบบ่อย

```
Turn 1: "ยอดขายเดือนนี้สาขาตากสิน"
Turn 2: "แล้วลูกค้าไหนซื้อมากสุด?"       ← inherit branch + date
Turn 3: "เทียบกับเดือนที่แล้วเป็นยังไง?"  ← เปลี่ยนแค่ date
```

### 12.2 Context Inheritance

```python
# params ที่ inherit ได้จาก turn ก่อน
INHERIT = ["branch_id", "date_from", "date_to"]
CLEAR   = ["customer", "sku", "supplier"]   # ไม่ inherit — เฉพาะคำถามนั้น

# ใส่ context hint ท้าย user message
if last_params:
    ctx = {k: v for k, v in last_params.items() if k in INHERIT}
    user_input += f"\n(context เดิม: {ctx})"
```

### 12.3 ตัด History ป้องกัน Token บวม

```
เก็บแค่ 5 turns ล่าสุด — ตัดเก่าออกถ้าเกิน
Turn 1-5:  history ปกติ  ≈ 3,800–5,000 tokens
Turn 6+:   slide window  ≈ คงที่ ~5,000 tokens
```

---

## 13. Security (ขั้น Minimal)

### 13.1 SQL Injection — ปลอดภัยโดย Design

Template-based ไม่มีความเสี่ยง SQL injection เพราะ:
- SQL เขียนไว้คงที่ ไม่ generate ใหม่
- params แทนค่าผ่าน parameterized query เสมอ

```python
# ✅ ปลอดภัย — ไม่ string format SQL
cursor.execute("SELECT ... WHERE ar_name ILIKE %s", (f"%{customer}%",))

# ❌ อันตราย — ห้ามทำ
cursor.execute(f"SELECT ... WHERE ar_name LIKE '%{customer}%'")
```

### 13.2 API Key

```python
# .env
ANTHROPIC_API_KEY=sk-ant-...

# ไม่ commit .env — เพิ่มใน .gitignore
```

### 13.3 Branch Access (ถ้าต้องการในอนาคต)

```python
# ถ้า user ต่างคนดูได้ต่างสาขา — เพิ่ม later
# ตอนนี้ใช้ user เดียว / ทีมเดียว → ยังไม่จำเป็น
ALLOWED_BRANCHES = None   # None = ทุกสาขา
```

---

## 14. Monitoring (เก็บ Minimal)

### 14.1 Log ที่ต้องเก็บทุก Request

```python
# บันทึกลง PostgreSQL — ตาราง chatbot_log
CREATE TABLE chatbot_log (
    id           BIGSERIAL PRIMARY KEY,
    asked_at     TIMESTAMPTZ DEFAULT now(),
    question     TEXT,
    template     VARCHAR(100),
    params       JSONB,
    row_count    INT,
    tokens_in    INT,
    tokens_out   INT,
    cost_usd     NUMERIC(10,6),
    latency_ms   INT,
    error        TEXT
);
```

### 14.2 Metrics ที่ดูเป็นประจำ

```
no_template_match rate  → ถ้า > 10% แปลว่าต้องเพิ่ม template
avg cost/day            → monitor ค่าใช้จ่าย
avg latency             → ถ้า > 3 sec ให้ดู query plan
```

---

## 15. Business Rules & Fiscal Context

### 15.1 วันที่ที่ต้อง Inject ทุก Request

```python
from calendar import monthrange
from datetime import date

def date_context(today: date) -> dict:
    y, m = today.year, today.month
    prev_m = m - 1 if m > 1 else 12
    prev_y = y if m > 1 else y - 1

    return {
        "today":            today,
        "month_start":      date(y, m, 1),
        "month_end":        date(y, m, monthrange(y, m)[1]),
        "prev_month_start": date(prev_y, prev_m, 1),
        "prev_month_end":   date(prev_y, prev_m, monthrange(prev_y, prev_m)[1]),
        "year_start":       date(y, 1, 1),
    }
```

### 15.2 เตือนช่วง Closing Period

```python
# วันที่ 1-5 ของเดือน → อาจยังไม่ปิดยอดเดือนที่แล้ว
if today.day <= 5:
    warning = "⚠️ หมายเหตุ: ข้อมูลเดือนที่แล้วอาจยังไม่ปิดยอด"
```

---

## 16. Testing

### 16.1 Test Cases หลัก

| ID | คำถาม | Expected Template | Params สำคัญ |
|---|---|---|---|
| TC01 | "ยอดขายเดือนนี้สาขาตากสิน" | `query_sales_summary` | branch_id=1, date=มิ.ย. |
| TC02 | "ลูกค้าเม้งสั่งของเดือนนี้เท่าไหร่" | `query_sales_by_customer` | customer="เม้ง" |
| TC03 | "สต็อก Honda ทุกสาขา" | `query_stock_balance` | brand="Honda", branch=null |
| TC04 | "ลูกหนี้ค้างชำระ" | `query_ar_outstanding` | as_of=วันนี้ |
| TC05 | "วันนี้อากาศเป็นยังไง" | `None` (fallback) | — |
| TC06 | "ยอดสาขาตากสิน" (กำกวม) | ถามกลับ | — |
| TC07 | "แล้วสาขาอื่นล่ะ" (follow-up) | inherit branch | — |

### 16.2 รัน Manual ก่อน Deploy

```python
# tests/test_templates.py — รันด้วย python tests/test_templates.py
for tc in TEST_CASES:
    result = chat(tc["question"])
    status = "✓" if result.template == tc["expected"] else "✗"
    print(f"{status} {tc['id']}: {result.template}")
```

---

## 17. Deployment

### 17.1 Docker Compose (minimal)

```yaml
services:
  chatbot:
    build: ./chatbot
    ports:
      - "8000:8000"
    environment:
      - PG_DSN=postgresql://user:pass@postgres:5432/bplus_central
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - CLAUDE_MODEL=claude-haiku-4-5
    depends_on:
      - postgres
    restart: unless-stopped

  postgres:
    image: postgres:16
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=bplus_central
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass

volumes:
  pgdata:
```

### 17.2 Endpoints

```
POST /chat          ← รับคำถาม → ตอบ
GET  /health        ← health check
GET  /templates     ← ดู templates ที่ active อยู่
```

---

## 18. Implementation Checklist

```
Week 1 — Foundation
  ☐ เขียน SQL templates 13 ตัว + ทดสอบใน PostgreSQL
  ☐ สร้าง tool definitions
  ☐ build_system_prompt() + inject branches/date จาก DB

Week 2 — Core
  ☐ Claude API (Haiku + prompt cache)
  ☐ SQL runner + parameterized queries
  ☐ Error handling + fallback messages
  ☐ Multi-turn + context inheritance

Week 3 — Ship
  ☐ chatbot_log table + บันทึกทุก request
  ☐ Test cases 7 ตัว ผ่านหมด
  ☐ Docker + .env setup
  ☐ ทดสอบกับ user จริง 1 สัปดาห์

Ongoing
  ☐ Monitor no_template_match rate → เพิ่ม template ถ้าสูง
  ☐ Review cost รายสัปดาห์
  ☐ เพิ่ม template ตาม feedback
```

---

## 19. Future Enhancements

### Text-to-SQL Fallback
ถ้า template ไม่ตรง → ใช้ Text-to-SQL พร้อม Schema KB  
แสดง SQL ให้ user confirm ก่อน execute  
ถ้าใช้บ่อย → สร้างเป็น template ใหม่

### Template Auto-suggestion
```python
# คำถามที่ไม่มี template บ่อยๆ → แจ้ง admin
# "คำถาม 'สินค้าไม่เคลื่อนไหว' ถูกถาม 8 ครั้งสัปดาห์นี้"
```

### LINE OA Integration
User ถามใน LINE → LINE Bot → FastAPI → Claude → ตอบกลับ  
ข้อดี: ใช้งานได้ทุกที่บนมือถือ  
ข้อควรระวัง: ตารางยาวแสดงได้ไม่สวย → สรุปเป็นข้อความแทน

---

*Updated: 2026-06-05 | Approach: Template-based SQL + Claude Tool Use + Prompt Cache*
