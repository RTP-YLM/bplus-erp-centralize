-- B+ Plus ERP Query Templates
-- Created: 2026-06-06
-- Purpose: Template-based SQL queries for chatbot interface

-- Create query_templates table
CREATE TABLE IF NOT EXISTS query_templates (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    sql_template TEXT NOT NULL,
    params      JSONB NOT NULL DEFAULT '[]',
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- Insert 15 query templates

-- 1. Sales by Customer
INSERT INTO query_templates (name, description, sql_template, params) VALUES (
    'query_sales_by_customer',
    'ดึงยอดขายตามลูกค้า ใช้เมื่อถามเกี่ยวกับยอดขาย รายการซื้อ เอกสารขาย ของลูกค้าคนใดคนหนึ่งในช่วงวันที่หรือเดือนที่ระบุ',
    'SELECT
        d.di_ref AS เลขเอกสาร,
        d.di_date AS วันที่,
        a.ar_name AS ลูกค้า,
        dt.dt_thaidesc AS ประเภท,
        COALESCE(SUM(t.trd_n_amt), 0) AS ยอดสุทธิ
    FROM docinfo d
    JOIN doctype dt ON dt.dt_key = d.di_dt AND dt.branch_id = d.branch_id
    JOIN transtkh h ON h.trh_di = d.di_key AND h.branch_id = d.branch_id
    JOIN transtkd t ON t.trd_trh = h.trh_key AND t.branch_id = h.branch_id
    JOIN tranpayh p ON p.tph_di = d.di_key AND p.branch_id = d.branch_id
    JOIN arfile a ON a.ar_key = p.tph_ar AND a.branch_id = p.branch_id
    WHERE d.di_date BETWEEN :date_from AND :date_to
      AND a.ar_name ILIKE ''%'' || :customer || ''%''
      AND (:branch_id IS NULL OR d.branch_id = :branch_id)
    GROUP BY d.di_ref, d.di_date, a.ar_name, dt.dt_thaidesc
    ORDER BY d.di_date DESC
    LIMIT 50',
    '[{"name": "customer", "type": "string", "required": true, "description": "ชื่อลูกค้า (ค้นแบบ LIKE)"},
      {"name": "date_from", "type": "string", "required": true, "description": "วันเริ่ม YYYY-MM-DD"},
      {"name": "date_to", "type": "string", "required": true, "description": "วันสิ้นสุด YYYY-MM-DD"},
      {"name": "branch_id", "type": "integer", "required": false, "description": "รหัสสาขา null = ทุกสาขา"}]'::jsonb
);

-- 2. Sales by Branch
INSERT INTO query_templates (name, description, sql_template, params) VALUES (
    'query_sales_by_branch',
    'ดึงยอดขายตามสาขา สรุปยอดขายแต่ละสาขาในช่วงวันที่ระบุ',
    'SELECT
        b.name AS สาขา,
        COUNT(DISTINCT d.di_key) AS จำนวนเอกสาร,
        COALESCE(SUM(t.trd_n_amt), 0) AS ยอดสุทธิ
    FROM docinfo d
    JOIN batch_branch b ON b.id = d.branch_id
    JOIN transtkh h ON h.trh_di = d.di_key AND h.branch_id = d.branch_id
    JOIN transtkd t ON t.trd_trh = h.trh_key AND t.branch_id = h.branch_id
    WHERE d.di_date BETWEEN :date_from AND :date_to
      AND (:branch_id IS NULL OR d.branch_id = :branch_id)
    GROUP BY b.name, d.branch_id
    ORDER BY ยอดสุทธิ DESC
    LIMIT 50',
    '[{"name": "date_from", "type": "string", "required": true, "description": "วันเริ่ม YYYY-MM-DD"},
      {"name": "date_to", "type": "string", "required": true, "description": "วันสิ้นสุด YYYY-MM-DD"},
      {"name": "branch_id", "type": "integer", "required": false, "description": "รหัสสาขา null = ทุกสาขา"}]'::jsonb
);

-- 3. Sales by SKU
INSERT INTO query_templates (name, description, sql_template, params) VALUES (
    'query_sales_by_sku',
    'ดึงยอดขายตามสินค้า ใช้เมื่อถามเกี่ยวกับยอดขายของสินค้าหรือยี่ห้อใดยี่ห้อหนึ่ง',
    'SELECT
        s.sku_name AS สินค้า,
        br.brn_name AS ยี่ห้อ,
        SUM(t.trd_qty) AS จำนวน,
        COALESCE(SUM(t.trd_n_amt), 0) AS ยอดสุทธิ
    FROM transtkd t
    JOIN transtkh h ON h.trh_key = t.trd_trh AND h.branch_id = t.branch_id
    JOIN docinfo d ON d.di_key = h.trh_di AND d.branch_id = h.branch_id
    JOIN skumaster s ON s.sku_key = t.trd_sku AND s.branch_id = t.branch_id
    LEFT JOIN brand br ON br.brn_key = s.sku_brn AND br.branch_id = s.branch_id
    WHERE d.di_date BETWEEN :date_from AND :date_to
      AND (:sku IS NULL OR s.sku_name ILIKE ''%'' || :sku || ''%'')
      AND (:brand IS NULL OR br.brn_name ILIKE ''%'' || :brand || ''%'')
      AND (:branch_id IS NULL OR d.branch_id = :branch_id)
    GROUP BY s.sku_name, br.brn_name
    ORDER BY ยอดสุทธิ DESC
    LIMIT 50',
    '[{"name": "date_from", "type": "string", "required": true, "description": "วันเริ่ม YYYY-MM-DD"},
      {"name": "date_to", "type": "string", "required": true, "description": "วันสิ้นสุด YYYY-MM-DD"},
      {"name": "sku", "type": "string", "required": false, "description": "ชื่อสินค้า (ค้นแบบ LIKE)"},
      {"name": "brand", "type": "string", "required": false, "description": "ยี่ห้อ (ค้นแบบ LIKE)"},
      {"name": "branch_id", "type": "integer", "required": false, "description": "รหัสสาขา null = ทุกสาขา"}]'::jsonb
);

-- 4. Sales Summary
INSERT INTO query_templates (name, description, sql_template, params) VALUES (
    'query_sales_summary',
    'สรุปยอดขายรวมทั้งหมดในช่วงวันที่ระบุ',
    'SELECT
        COUNT(DISTINCT d.di_key) AS จำนวนเอกสาร,
        COUNT(DISTINCT p.tph_ar) AS จำนวนลูกค้า,
        COALESCE(SUM(t.trd_n_amt), 0) AS ยอดสุทธิ
    FROM docinfo d
    JOIN transtkh h ON h.trh_di = d.di_key AND h.branch_id = d.branch_id
    JOIN transtkd t ON t.trd_trh = h.trh_key AND t.branch_id = h.branch_id
    LEFT JOIN tranpayh p ON p.tph_di = d.di_key AND p.branch_id = d.branch_id
    WHERE d.di_date BETWEEN :date_from AND :date_to
      AND (:branch_id IS NULL OR d.branch_id = :branch_id)
    LIMIT 50',
    '[{"name": "date_from", "type": "string", "required": true, "description": "วันเริ่ม YYYY-MM-DD"},
      {"name": "date_to", "type": "string", "required": true, "description": "วันสิ้นสุด YYYY-MM-DD"},
      {"name": "branch_id", "type": "integer", "required": false, "description": "รหัสสาขา null = ทุกสาขา"}]'::jsonb
);

-- 5. AR Outstanding
INSERT INTO query_templates (name, description, sql_template, params) VALUES (
    'query_ar_outstanding',
    'ดึงยอดลูกหนี้ค้างชำระ ณ วันที่ระบุ',
    'SELECT
        a.ar_name AS ลูกค้า,
        COUNT(DISTINCT ar.ard_di) AS จำนวนเอกสาร,
        COALESCE(SUM(ar.ard_n_amt), 0) AS ยอดค้างชำระ
    FROM ardetail ar
    JOIN arfile a ON a.ar_key = ar.ard_ar AND a.branch_id = ar.branch_id
    JOIN docinfo d ON d.di_key = ar.ard_di AND d.branch_id = ar.branch_id
    WHERE d.di_date <= :as_of_date
      AND (:customer IS NULL OR a.ar_name ILIKE ''%'' || :customer || ''%'')
      AND (:branch_id IS NULL OR ar.branch_id = :branch_id)
      AND ar.ard_n_amt > 0
    GROUP BY a.ar_name
    ORDER BY ยอดค้างชำระ DESC
    LIMIT 50',
    '[{"name": "as_of_date", "type": "string", "required": true, "description": "วันที่ ณ วันนั้น YYYY-MM-DD"},
      {"name": "customer", "type": "string", "required": false, "description": "ชื่อลูกค้า (ค้นแบบ LIKE)"},
      {"name": "branch_id", "type": "integer", "required": false, "description": "รหัสสาขา null = ทุกสาขา"}]'::jsonb
);

-- 6. AR Payment
INSERT INTO query_templates (name, description, sql_template, params) VALUES (
    'query_ar_payment',
    'ดึงรายการรับชำระลูกหนี้ในช่วงวันที่ระบุ',
    'SELECT
        d.di_ref AS เลขเอกสาร,
        d.di_date AS วันที่,
        a.ar_name AS ลูกค้า,
        COALESCE(SUM(pd.tpd_baht), 0) AS ยอดรับชำระ
    FROM docinfo d
    JOIN tranpayh ph ON ph.tph_di = d.di_key AND ph.branch_id = d.branch_id
    JOIN tranpayd pd ON pd.tpd_tph = ph.tph_key AND pd.branch_id = ph.branch_id
    JOIN arfile a ON a.ar_key = ph.tph_ar AND a.branch_id = ph.branch_id
    WHERE d.di_date BETWEEN :date_from AND :date_to
      AND (:customer IS NULL OR a.ar_name ILIKE ''%'' || :customer || ''%'')
      AND (:branch_id IS NULL OR d.branch_id = :branch_id)
    GROUP BY d.di_ref, d.di_date, a.ar_name
    ORDER BY d.di_date DESC
    LIMIT 50',
    '[{"name": "date_from", "type": "string", "required": true, "description": "วันเริ่ม YYYY-MM-DD"},
      {"name": "date_to", "type": "string", "required": true, "description": "วันสิ้นสุด YYYY-MM-DD"},
      {"name": "customer", "type": "string", "required": false, "description": "ชื่อลูกค้า (ค้นแบบ LIKE)"},
      {"name": "branch_id", "type": "integer", "required": false, "description": "รหัสสาขา null = ทุกสาขา"}]'::jsonb
);

-- 7. Stock Balance
INSERT INTO query_templates (name, description, sql_template, params) VALUES (
    'query_stock_balance',
    'ดึงยอดสต็อกคงเหลือ ณ ปัจจุบัน',
    'SELECT
        s.sku_name AS สินค้า,
        br.brn_name AS ยี่ห้อ,
        COALESCE(sb.skb_qty, 0) AS คงเหลือ
    FROM skubalance sb
    JOIN skumaster s ON s.sku_key = sb.skb_sku AND s.branch_id = sb.branch_id
    LEFT JOIN brand br ON br.brn_key = s.sku_brn AND br.branch_id = s.branch_id
    WHERE (:sku IS NULL OR s.sku_name ILIKE ''%'' || :sku || ''%'')
      AND (:brand IS NULL OR br.brn_name ILIKE ''%'' || :brand || ''%'')
      AND (:branch_id IS NULL OR sb.branch_id = :branch_id)
      AND sb.skb_qty > 0
    ORDER BY sb.skb_qty DESC
    LIMIT 50',
    '[{"name": "sku", "type": "string", "required": false, "description": "ชื่อสินค้า (ค้นแบบ LIKE)"},
      {"name": "brand", "type": "string", "required": false, "description": "ยี่ห้อ (ค้นแบบ LIKE)"},
      {"name": "branch_id", "type": "integer", "required": false, "description": "รหัสสาขา null = ทุกสาขา"}]'::jsonb
);

-- 8. Stock Movement
INSERT INTO query_templates (name, description, sql_template, params) VALUES (
    'query_stock_movement',
    'ดึงการเคลื่อนไหวสินค้าในช่วงวันที่ระบุ',
    'SELECT
        d.di_date AS วันที่,
        d.di_ref AS เลขเอกสาร,
        s.sku_name AS สินค้า,
        sm.skm_qty AS จำนวน,
        dt.dt_thaidesc AS ประเภท
    FROM skumove sm
    JOIN docinfo d ON d.di_key = sm.skm_di AND d.branch_id = sm.branch_id
    JOIN skumaster s ON s.sku_key = sm.skm_sku AND s.branch_id = sm.branch_id
    JOIN doctype dt ON dt.dt_key = d.di_dt AND dt.branch_id = d.branch_id
    WHERE d.di_date BETWEEN :date_from AND :date_to
      AND (:sku IS NULL OR s.sku_name ILIKE ''%'' || :sku || ''%'')
      AND (:branch_id IS NULL OR d.branch_id = :branch_id)
    ORDER BY d.di_date DESC
    LIMIT 50',
    '[{"name": "date_from", "type": "string", "required": true, "description": "วันเริ่ม YYYY-MM-DD"},
      {"name": "date_to", "type": "string", "required": true, "description": "วันสิ้นสุด YYYY-MM-DD"},
      {"name": "sku", "type": "string", "required": false, "description": "ชื่อสินค้า (ค้นแบบ LIKE)"},
      {"name": "branch_id", "type": "integer", "required": false, "description": "รหัสสาขา null = ทุกสาขา"}]'::jsonb
);

-- 9. Documents Today
INSERT INTO query_templates (name, description, sql_template, params) VALUES (
    'query_documents_today',
    'ดึงเอกสารล่าสุดหรือเอกสารวันนี้',
    'SELECT
        d.di_ref AS เลขเอกสาร,
        d.di_date AS วันที่,
        dt.dt_thaidesc AS ประเภท,
        d.di_amount AS ยอดเงิน
    FROM docinfo d
    JOIN doctype dt ON dt.dt_key = d.di_dt AND dt.branch_id = d.branch_id
    WHERE d.di_date = COALESCE(:date, CURRENT_DATE)
      AND (:branch_id IS NULL OR d.branch_id = :branch_id)
      AND (:doc_type IS NULL OR dt.dt_doccode ILIKE ''%'' || :doc_type || ''%'')
    ORDER BY d.di_date DESC, d.di_cre_date DESC
    LIMIT :limit_rows',
    '[{"name": "date", "type": "string", "required": false, "description": "วันที่ (default CURRENT_DATE)"},
      {"name": "branch_id", "type": "integer", "required": false, "description": "รหัสสาขา null = ทุกสาขา"},
      {"name": "doc_type", "type": "string", "required": false, "description": "ประเภทเอกสาร (ค้นแบบ LIKE)"},
      {"name": "limit_rows", "type": "integer", "required": false, "description": "จำนวนแถวที่ต้องการ (default 50)"}]'::jsonb
);

-- 10. Payment Received
INSERT INTO query_templates (name, description, sql_template, params) VALUES (
    'query_payment_received',
    'ดึงยอดเงินรับในช่วงวันที่ระบุ (จากการรับชำระลูกหนี้)',
    'SELECT
        d.di_date AS วันที่,
        COUNT(DISTINCT d.di_key) AS จำนวนเอกสาร,
        COALESCE(SUM(pd.tpd_baht), 0) AS ยอดเงินรับ
    FROM docinfo d
    JOIN tranpayh ph ON ph.tph_di = d.di_key AND ph.branch_id = d.branch_id
    JOIN tranpayd pd ON pd.tpd_tph = ph.tph_key AND pd.branch_id = ph.branch_id
    WHERE d.di_date BETWEEN :date_from AND :date_to
      AND (:branch_id IS NULL OR d.branch_id = :branch_id)
    GROUP BY d.di_date
    ORDER BY d.di_date DESC
    LIMIT 50',
    '[{"name": "date_from", "type": "string", "required": true, "description": "วันเริ่ม YYYY-MM-DD"},
      {"name": "date_to", "type": "string", "required": true, "description": "วันสิ้นสุด YYYY-MM-DD"},
      {"name": "branch_id", "type": "integer", "required": false, "description": "รหัสสาขา null = ทุกสาขา"}]'::jsonb
);

-- 11. AP Outstanding
INSERT INTO query_templates (name, description, sql_template, params) VALUES (
    'query_ap_outstanding',
    'ดึงยอดเจ้าหนี้ค้างจ่าย ณ วันที่ระบุ',
    'SELECT
        ap.ap_name AS ผู้ขาย,
        COUNT(DISTINCT apd.apd_di) AS จำนวนเอกสาร,
        COALESCE(SUM(apd.apd_n_amt), 0) AS ยอดค้างจ่าย
    FROM apdetail apd
    JOIN apfile ap ON ap.ap_key = apd.apd_ap AND ap.branch_id = apd.branch_id
    JOIN docinfo d ON d.di_key = apd.apd_di AND d.branch_id = apd.branch_id
    WHERE d.di_date <= :as_of_date
      AND (:supplier IS NULL OR ap.ap_name ILIKE ''%'' || :supplier || ''%'')
      AND apd.apd_n_amt > 0
    GROUP BY ap.ap_name
    ORDER BY ยอดค้างจ่าย DESC
    LIMIT 50',
    '[{"name": "as_of_date", "type": "string", "required": true, "description": "วันที่ ณ วันนั้น YYYY-MM-DD"},
      {"name": "supplier", "type": "string", "required": false, "description": "ชื่อผู้ขาย (ค้นแบบ LIKE)"}]'::jsonb
);

-- 12. Sales by DocType
INSERT INTO query_templates (name, description, sql_template, params) VALUES (
    'query_sales_by_doctype',
    'ดึงยอดขายแยกตามประเภทเอกสาร (รถ/อะไหล่/ซ่อม)',
    'SELECT
        dt.dt_thaidesc AS ประเภท,
        COUNT(DISTINCT d.di_key) AS จำนวนเอกสาร,
        COALESCE(SUM(t.trd_n_amt), 0) AS ยอดสุทธิ
    FROM docinfo d
    JOIN doctype dt ON dt.dt_key = d.di_dt AND dt.branch_id = d.branch_id
    JOIN transtkh h ON h.trh_di = d.di_key AND h.branch_id = d.branch_id
    JOIN transtkd t ON t.trd_trh = h.trh_key AND t.branch_id = h.branch_id
    WHERE d.di_date BETWEEN :date_from AND :date_to
      AND (:branch_id IS NULL OR d.branch_id = :branch_id)
    GROUP BY dt.dt_thaidesc
    ORDER BY ยอดสุทธิ DESC
    LIMIT 50',
    '[{"name": "date_from", "type": "string", "required": true, "description": "วันเริ่ม YYYY-MM-DD"},
      {"name": "date_to", "type": "string", "required": true, "description": "วันสิ้นสุด YYYY-MM-DD"},
      {"name": "branch_id", "type": "integer", "required": false, "description": "รหัสสาขา null = ทุกสาขา"}]'::jsonb
);

-- 13. Bank Statement
INSERT INTO query_templates (name, description, sql_template, params) VALUES (
    'query_bank_statement',
    'ดึงรายการธนาคารในช่วงวันที่ระบุ',
    'SELECT
        d.di_date AS วันที่,
        d.di_ref AS เลขเอกสาร,
        bf.bf_name AS ธนาคาร,
        bs.bstm_debit AS เงินเข้า,
        bs.bstm_credit AS เงินออก
    FROM bankstatement bs
    JOIN docinfo d ON d.di_key = bs.bstm_di AND d.branch_id = bs.branch_id
    LEFT JOIN bankfile bf ON bf.bf_key = bs.bstm_bank AND bf.branch_id = bs.branch_id
    WHERE d.di_date BETWEEN :date_from AND :date_to
      AND (:bank IS NULL OR bf.bf_name ILIKE ''%'' || :bank || ''%'')
      AND (:branch_id IS NULL OR d.branch_id = :branch_id)
    ORDER BY d.di_date DESC
    LIMIT 50',
    '[{"name": "date_from", "type": "string", "required": true, "description": "วันเริ่ม YYYY-MM-DD"},
      {"name": "date_to", "type": "string", "required": true, "description": "วันสิ้นสุด YYYY-MM-DD"},
      {"name": "bank", "type": "string", "required": false, "description": "ชื่อธนาคาร (ค้นแบบ LIKE)"},
      {"name": "branch_id", "type": "integer", "required": false, "description": "รหัสสาขา null = ทุกสาขา"}]'::jsonb
);

-- 14. Top Customers
INSERT INTO query_templates (name, description, sql_template, params) VALUES (
    'query_top_customers',
    'ดึงลูกค้าที่ซื้อมากที่สุดในช่วงวันที่ระบุ',
    'SELECT
        a.ar_name AS ลูกค้า,
        COUNT(DISTINCT d.di_key) AS จำนวนเอกสาร,
        COALESCE(SUM(t.trd_n_amt), 0) AS ยอดสุทธิ
    FROM docinfo d
    JOIN tranpayh p ON p.tph_di = d.di_key AND p.branch_id = d.branch_id
    JOIN arfile a ON a.ar_key = p.tph_ar AND a.branch_id = p.branch_id
    JOIN transtkh h ON h.trh_di = d.di_key AND h.branch_id = d.branch_id
    JOIN transtkd t ON t.trd_trh = h.trh_key AND t.branch_id = h.branch_id
    WHERE d.di_date BETWEEN :date_from AND :date_to
      AND (:branch_id IS NULL OR d.branch_id = :branch_id)
    GROUP BY a.ar_name
    ORDER BY ยอดสุทธิ DESC
    LIMIT :limit_rows',
    '[{"name": "date_from", "type": "string", "required": true, "description": "วันเริ่ม YYYY-MM-DD"},
      {"name": "date_to", "type": "string", "required": true, "description": "วันสิ้นสุด YYYY-MM-DD"},
      {"name": "branch_id", "type": "integer", "required": false, "description": "รหัสสาขา null = ทุกสาขา"},
      {"name": "limit_rows", "type": "integer", "required": false, "description": "จำนวนแถวที่ต้องการ (default 10)"}]'::jsonb
);

-- 15. Top SKUs
INSERT INTO query_templates (name, description, sql_template, params) VALUES (
    'query_top_skus',
    'ดึงสินค้าที่ขายดีที่สุดในช่วงวันที่ระบุ',
    'SELECT
        s.sku_name AS สินค้า,
        br.brn_name AS ยี่ห้อ,
        SUM(t.trd_qty) AS จำนวน,
        COALESCE(SUM(t.trd_n_amt), 0) AS ยอดสุทธิ
    FROM transtkd t
    JOIN transtkh h ON h.trh_key = t.trd_trh AND h.branch_id = t.branch_id
    JOIN docinfo d ON d.di_key = h.trh_di AND d.branch_id = h.branch_id
    JOIN skumaster s ON s.sku_key = t.trd_sku AND s.branch_id = t.branch_id
    LEFT JOIN brand br ON br.brn_key = s.sku_brn AND br.branch_id = s.branch_id
    WHERE d.di_date BETWEEN :date_from AND :date_to
      AND (:branch_id IS NULL OR d.branch_id = :branch_id)
    GROUP BY s.sku_name, br.brn_name
    ORDER BY ยอดสุทธิ DESC
    LIMIT :limit_rows',
    '[{"name": "date_from", "type": "string", "required": true, "description": "วันเริ่ม YYYY-MM-DD"},
      {"name": "date_to", "type": "string", "required": true, "description": "วันสิ้นสุด YYYY-MM-DD"},
      {"name": "branch_id", "type": "integer", "required": false, "description": "รหัสสาขา null = ทุกสาขา"},
      {"name": "limit_rows", "type": "integer", "required": false, "description": "จำนวนแถวที่ต้องการ (default 10)"}]'::jsonb
);
