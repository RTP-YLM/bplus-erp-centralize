# Task: B+ Plus ERP Chatbot + LINE Bot Integration

## Overview
Build the chatbot module for B+ Plus ERP that integrates with LINE Official Account. The chatbot uses **Template-based SQL + Claude Tool Use** pattern (NOT Text-to-SQL).

## Architecture
```
User (LINE OA) → LINE Webhook → FastAPI → Claude Tool Use → SQL Template → PostgreSQL (Supabase) → Claude summarize → LINE reply
```

## What to Build

### 1. SQL Templates (`schema/002_query_templates.sql`)
Create a Supabase migration that creates a `query_templates` table and inserts 15 templates. The table structure:

```sql
CREATE TABLE IF NOT EXISTS query_templates (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    sql_template TEXT NOT NULL,
    params      JSONB NOT NULL DEFAULT '[]',  -- [{name, type, required, description}]
    created_at  TIMESTAMPTZ DEFAULT now()
);
```

The 15 templates (from CHATBOT_PHASE.md):
1. `query_sales_by_customer` — ยอดขายตามลูกค้า (customer, date_from, date_to, branch_id?)
2. `query_sales_by_branch` — ยอดขายตามสาขา (date_from, date_to, branch_id?)
3. `query_sales_by_sku` — ยอดขายตามสินค้า (sku?, brand?, date_from, date_to, branch_id?)
4. `query_sales_summary` — สรุปยอดขายรวม (date_from, date_to, branch_id?)
5. `query_ar_outstanding` — ลูกหนี้ค้างชำระ (customer?, as_of_date, branch_id?)
6. `query_ar_payment` — รับชำระลูกหนี้ (customer?, date_from, date_to, branch_id?)
7. `query_stock_balance` — สต็อกคงเหลือ (sku?, brand?, branch_id?)
8. `query_stock_movement` — การเคลื่อนไหวสินค้า (sku?, date_from, date_to, branch_id?)
9. `query_documents_today` — เอกสารวันนี้/ล่าสุด (branch_id?, doc_type?, limit?)
10. `query_payment_received` — เงินรับวันนี้/เดือนนี้ (date_from, date_to, branch_id?)
11. `query_ap_outstanding` — เจ้าหนี้ค้างจ่าย (supplier?, as_of_date)
12. `query_sales_by_doctype` — ยอดขายแยกประเภท (date_from, date_to, branch_id?)
13. `query_bank_statement` — รายการธนาคาร (bank?, date_from, date_to, branch_id?)
14. `query_top_customers` — ลูกค้าสูงสุด (date_from, date_to, branch_id?, limit?)
15. `query_top_skus` — สินค้าขายดี (date_from, date_to, branch_id?, limit?)

**IMPORTANT:** All SQL templates must use parameterized queries with `:param` placeholders. All templates must have `LIMIT 50`. Use `(:branch_id IS NULL OR ...)` pattern for optional branch filtering.

### 2. Chatbot Module (`chatbot/`)

Create these files:

#### `chatbot/__init__.py`
Empty init.

#### `chatbot/settings.py`
Load env vars: PG_DSN, ANTHROPIC_API_KEY, LINE_CHANNEL_ACCESS_TOKEN, LINE_DESTINATION_USER_ID, CLAUDE_MODEL (default: claude-haiku-4-5)

#### `chatbot/templates.py`
- Load templates from `query_templates` table on startup
- Cache in memory
- Provide `get_template(name)` and `list_templates()` functions

#### `chatbot/tools.py`
- Generate Claude Tool Use definitions from templates
- Each template → one tool with `name`, `description`, `input_schema`
- `build_tools()` function returns list of tool dicts

#### `chatbot/system_prompt.py`
- `build_system_prompt()` function
- Inject: current date, date context (month_start, month_end, prev_month, year_start), branches from `batch_branch` table
- Include rules for Thai date parsing, branch mapping, fallback behavior
- Include response format guidelines (markdown tables, totals, date range)

#### `chatbot/runner.py`
- `run_sql_template(template_name, params)` function
- Load template SQL, replace `:param` with parameterized values
- Execute against PostgreSQL (Supabase)
- Return rows as list of dicts
- Handle errors gracefully

#### `chatbot/chat.py`
- Main chat function: `chat(user_input, history=None) -> (response, updated_history)`
- Round 1: Claude selects template + params
- Round 2: Run SQL, Claude summarizes results
- Multi-turn: inherit branch_id, date_from, date_to from previous turn
- History window: keep last 5 turns

#### `chatbot/webhook.py`
- FastAPI app with `/webhook` POST endpoint for LINE
- Verify LINE webhook signature
- Parse incoming text messages
- Call `chat()` function
- Reply via LINE Messaging API (use requests library, not LINE SDK)
- `/health` GET endpoint
- `/templates` GET endpoint to list available templates

#### `chatbot/line_client.py`
- LINE Messaging API client (plain requests, no SDK dependency)
- `push_text_message(user_id, text)` — push text to user
- `reply_text_message(reply_token, text)` — reply to message
- `push_flex_message(user_id, alt_text, contents)` — push flex message
- Uses LINE_CHANNEL_ACCESS_TOKEN from env

### 3. Dependencies
Update `requirements.txt` to add:
- `anthropic>=0.40.0`
- `fastapi>=0.115.0`
- `uvicorn>=0.34.0`
- `requests>=2.32.0`

### 4. Docker Support
Create `chatbot/Dockerfile` and update/create `docker-compose.yml` with chatbot service.

## Database Info
- **Supabase Project:** xbgfiengqwcsdxrnvbbk.supabase.co
- **PG_DSN:** `postgresql://postgres:PASSWORD@db.xbgfiengqwcsdxrnvbbk.supabase.co:5432/postgres`
- **Existing tables:** batch_branch, batch_table_config, batch_sync_log, docinfo, transtkh, transtkd, tranpayh, tranpayd, tranpaya, skumove, vattable, arpayment, appayment, bankstatement, accountjournal, accountvoucher, sldetail, ardetail, apdetail, cashbook, skumaster, goodsmaster, arfile, apfile, accountchart, doctype, brand, salesman, branch, paymenttype, bankfile
- **Branches:** branch_id 1=ตากสิน18, 2=เอกชัย118, 3=เวสป้าสุขสวัสดิ์, 4=เวสป้าตากสิน, 5=เวสป้าบางโพ

## Key Column Names (from BPLUS_ERP_DB_STRUCTURE.md)
- DOCINFO: DI_KEY, DI_DATE, DI_REF, DI_DT (→ DOCTYPE.DT_KEY), DI_CRE_DATE, branch_id
- TRANSTKH: TRH_KEY, TRH_DI (→ DOCINFO.DI_KEY), branch_id
- TRANSTKD: TRD_KEY, TRD_TRH (→ TRANSTKH.TRH_KEY), TRD_SKU, TRD_N_AMT, branch_id
- TRANPAYH: TPH_KEY, TPH_DI, TPH_AR (→ ARFILE.AR_KEY), branch_id
- TRANPAYD: TPD_KEY, TPD_TPH, branch_id
- ARFILE: AR_KEY, AR_NAME, branch_id
- APFILE: AP_KEY, AP_NAME, branch_id
- SKUMASTER: SKU_KEY, SKU_NAME, SKU_BRN (→ BRAND.BRN_KEY), branch_id
- BRAND: BRN_KEY, BRN_NAME, branch_id
- DOCTYPE: DT_KEY, DT_DOCCODE, DT_THAIDESC, DT_PROPERTIES, branch_id
- SKUBALANCE: SKB_SKU, SKB_QTY, branch_id
- ARDETAIL: ARD_KEY, ARD_DI, ARD_AR, branch_id
- SLDETAIL: SLD_KEY, SLD_DI, branch_id
- BANKSTATEMENT: BSTM_KEY, BSTM_DI, BSTM_BANK, branch_id

## LINE Bot Info
- **Channel Access Token:** (in .env as LINE_CHANNEL_ACCESS_TOKEN)
- **Default User ID:** Ub5928af25c0550217c9ec9d828f51f98
- **Webhook URL:** Will be configured after deployment

## Constraints
- Python 3.9+ compatible
- Use `psycopg2` for PostgreSQL (already in requirements)
- Use `anthropic` SDK for Claude API
- Use plain `requests` for LINE API (no LINE SDK)
- All SQL templates must be parameterized (no string formatting)
- All queries must have LIMIT 50
- Respond in Thai
- Error messages in Thai (from CHATBOT_PHASE.md section 11)

## File Structure
```
bplus-erp-centralize/
├── etl/                    (existing)
├── schema/
│   ├── 001_batch_config.sql  (existing)
│   └── 002_query_templates.sql  (NEW — create this)
├── chatbot/                (NEW — create all)
│   ├── __init__.py
│   ├── settings.py
│   ├── templates.py
│   ├── tools.py
│   ├── system_prompt.py
│   ├── runner.py
│   ├── chat.py
│   ├── webhook.py
│   └── line_client.py
├── Dockerfile              (NEW)
├── docker-compose.yml      (NEW)
├── requirements.txt        (UPDATE)
├── .env.example            (UPDATE with LINE vars)
└── CHATBOT_PHASE.md        (existing — reference)
```

## Testing
After building, create `chatbot/test_chat.py` that:
1. Tests template loading
2. Tests SQL runner with a simple query
3. Tests chat function with sample questions
