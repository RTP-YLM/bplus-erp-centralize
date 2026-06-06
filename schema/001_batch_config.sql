-- =============================================================
-- B+ Plus ERP Centralize — Batch Config Schema
-- =============================================================

-- 1. Source branches (each MSSQL database = 1 branch)
CREATE TABLE IF NOT EXISTS batch_branch (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,          -- e.g. "ตากสิน 18"
    branch_code  VARCHAR(10),                    -- e.g. MY00, MY03
    mssql_host   VARCHAR(255) NOT NULL DEFAULT 'localhost',
    mssql_port   INT          NOT NULL DEFAULT 1433,
    mssql_db     VARCHAR(100) NOT NULL,
    mssql_user   VARCHAR(100) NOT NULL,
    mssql_pass   VARCHAR(255) NOT NULL,
    enabled      BOOLEAN      NOT NULL DEFAULT true,
    created_at   TIMESTAMPTZ  DEFAULT now(),
    updated_at   TIMESTAMPTZ  DEFAULT now()
);

-- 2. Table sync configuration (LOV)
CREATE TABLE IF NOT EXISTS batch_table_config (
    id              SERIAL       PRIMARY KEY,
    table_name      VARCHAR(100) NOT NULL UNIQUE,
    priority        SMALLINT     NOT NULL DEFAULT 2,           -- 1=transaction, 2=master, 3=config
    frequency       VARCHAR(20)  NOT NULL DEFAULT 'daily',     -- daily, weekly, monthly, once
    sync_type       VARCHAR(20)  NOT NULL DEFAULT 'incremental', -- fullload, incremental
    pk_columns      TEXT[]       NOT NULL DEFAULT '{}',        -- composite PK in target
    watermark_col   VARCHAR(100),                              -- column used for incremental
    watermark_type  VARCHAR(20)  DEFAULT 'lastupd',            -- lastupd (bigint nvarchar), integer, datetime
    batch_size      INT          NOT NULL DEFAULT 1000,
    enabled         BOOLEAN      NOT NULL DEFAULT true,
    notes           TEXT,
    created_at      TIMESTAMPTZ  DEFAULT now(),
    updated_at      TIMESTAMPTZ  DEFAULT now()
);

-- 3. Sync execution log (state + history)
CREATE TABLE IF NOT EXISTS batch_sync_log (
    id              BIGSERIAL    PRIMARY KEY,
    branch_id       INT          REFERENCES batch_branch(id),
    table_name      VARCHAR(100) NOT NULL,
    sync_type       VARCHAR(20)  NOT NULL,
    status          VARCHAR(20)  NOT NULL DEFAULT 'running',   -- running, success, failed, skipped
    rows_extracted  INT          DEFAULT 0,
    rows_upserted   INT          DEFAULT 0,
    watermark_from  TEXT,        -- value at start of this run
    watermark_to    TEXT,        -- value at end (saved for next run)
    error_msg       TEXT,
    started_at      TIMESTAMPTZ  DEFAULT now(),
    finished_at     TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_sync_log_lookup
    ON batch_sync_log (branch_id, table_name, status, finished_at DESC);

-- =============================================================
-- Pre-populate table config LOV
-- =============================================================
INSERT INTO batch_table_config
    (table_name, priority, frequency, sync_type, pk_columns, watermark_col, watermark_type, notes)
VALUES
-- ── Priority 1: Transaction (daily incremental) ──────────────
('DOCINFO',        1,'daily',   'incremental', ARRAY['branch_id','di_key'],    'DI_CRE_DATE',  'datetime', 'จุดศูนย์กลางทุก transaction'),
('TRANSTKH',       1,'daily',   'incremental', ARRAY['branch_id','trh_key'],   'TRH_LASTUPD',  'lastupd',  'Header สต็อก'),
('TRANSTKD',       1,'daily',   'incremental', ARRAY['branch_id','trd_key'],   'TRD_LASTUPD',  'lastupd',  'Detail สต็อก'),
('TRANPAYH',       1,'daily',   'incremental', ARRAY['branch_id','tph_key'],   'TPH_LASTUPD',  'lastupd',  'Header ชำระเงิน'),
('TRANPAYD',       1,'daily',   'incremental', ARRAY['branch_id','tpd_key'],   'TPD_LASTUPD',  'lastupd',  'Detail ชำระเงิน'),
('TRANPAYA',       1,'daily',   'incremental', ARRAY['branch_id','tpa_key'],   'TPA_LASTUPD',  'lastupd',  'Apportion'),
('ACCOUNTVOUCHER', 1,'daily',   'incremental', ARRAY['branch_id','vc_key'],    'VC_LASTUPD',   'lastupd',  'ใบสำคัญบัญชี'),
('ACCOUNTJOURNAL', 1,'daily',   'incremental', ARRAY['branch_id','jr_key'],    'JR_LASTUPD',   'lastupd',  'บัญชีรายวัน'),
('VATTABLE',       1,'daily',   'incremental', ARRAY['branch_id','vat_key'],   'VAT_LASTUPD',  'lastupd',  'ภาษีมูลค่าเพิ่ม'),
('ARPAYMENT',      1,'daily',   'incremental', ARRAY['branch_id','arp_key'],   'ARP_LASTUPD',  'lastupd',  'รับชำระลูกหนี้'),
('APPAYMENT',      1,'daily',   'incremental', ARRAY['branch_id','app_key'],   'APP_LASTUPD',  'lastupd',  'ชำระเจ้าหนี้'),
('BANKSTATEMENT',  1,'daily',   'incremental', ARRAY['branch_id','bstm_key'],  'BSTM_LASTUPD', 'lastupd',  'Statement ธนาคาร (date ผ่าน BSTM_DI→DOCINFO)'),
('CASHBOOK',       1,'daily',   'incremental', ARRAY['branch_id','cashb_key'], 'CASHB_LASTUPD','lastupd',  'สมุดเงินสด'),
('SLDETAIL',       1,'daily',   'incremental', ARRAY['branch_id','sld_key'],   'SLD_LASTUPD',  'lastupd',  'รายละเอียดขาย'),
('ARDETAIL',       1,'daily',   'incremental', ARRAY['branch_id','ard_key'],   'ARD_LASTUPD',  'lastupd',  'ลูกหนี้ subledger'),
('APDETAIL',       1,'daily',   'incremental', ARRAY['branch_id','apd_key'],   'APD_LASTUPD',  'lastupd',  'เจ้าหนี้ subledger'),
('SKUMOVE',        1,'daily',   'incremental', ARRAY['branch_id','skm_key'],   'SKM_KEY',      'integer',  'เคลื่อนไหวสินค้า (ไม่มี LASTUPD → ใช้ PK watermark)'),
-- ── Priority 2: Master (weekly incremental) ──────────────────
('SKUMASTER',      2,'weekly',  'incremental', ARRAY['branch_id','sku_key'],   'SKU_LASTUPD',  'lastupd',  'สินค้า — 44,964 rows'),
('GOODSMASTER',    2,'weekly',  'incremental', ARRAY['branch_id','goods_key'], 'GOODS_LASTUPD','lastupd',  'สินค้า (Goods) — 44,968 rows'),
('SKUAP',          2,'weekly',  'incremental', ARRAY['branch_id','skp_key'],   'SKP_LASTUPD',  'lastupd',  'SKU↔ผู้ขาย mapping — 45,366 rows'),
('ARPLU',          2,'weekly',  'incremental', ARRAY['branch_id','arplu_key'], 'ARPLU_LASTUPD','lastupd',  'รายการราคาลูกค้า — 41,233 rows'),
('ARFILE',         2,'weekly',  'incremental', ARRAY['branch_id','ar_key'],    'AR_LASTUPD',   'lastupd',  'ลูกหนี้ master — 8,032 rows'),
('APFILE',         2,'weekly',  'incremental', ARRAY['branch_id','ap_key'],    'AP_LASTUPD',   'lastupd',  'เจ้าหนี้ master — 267 rows'),
('ACCOUNTCHART',   2,'weekly',  'incremental', ARRAY['branch_id','ac_key'],    'AC_LASTUPD',   'lastupd',  'ผังบัญชี — 277 rows'),
('SALESMAN',       2,'weekly',  'incremental', ARRAY['branch_id','sl_key'],    'SL_LASTUPD',   'lastupd',  'พนักงานขาย'),
('BRAND',          2,'weekly',  'incremental', ARRAY['branch_id','brn_key'],   'BRN_LASTUPD',  'lastupd',  'ยี่ห้อ — 125 rows'),
('PAYMENTTYPE',    2,'weekly',  'incremental', ARRAY['branch_id','pmt_key'],   'PMT_LASTUPD',  'lastupd',  'วิธีชำระ'),
('BANKFILE',       2,'weekly',  'incremental', ARRAY['branch_id','bnk_key'],   'BNK_LASTUPD',  'lastupd',  'ธนาคาร'),
('BRANCH',         2,'weekly',  'incremental', ARRAY['branch_id','br_key'],    'BR_LASTUPD',   'lastupd',  'สาขา — 6 rows'),
-- ── Priority 3: Config (once / fullload) ─────────────────────
('DOCTYPE',        3,'once',    'fullload',    ARRAY['branch_id','dt_key'],    NULL,           NULL,       'ประเภทเอกสาร — 134 rows'),
('COMPANYINFO',    3,'once',    'fullload',    ARRAY['branch_id','ci_key'],    NULL,           NULL,       'ข้อมูลบริษัท'),
('GLPERIOD',       3,'once',    'fullload',    ARRAY['branch_id','glp_key'],   NULL,           NULL,       'งวดบัญชี')
ON CONFLICT (table_name) DO NOTHING;
