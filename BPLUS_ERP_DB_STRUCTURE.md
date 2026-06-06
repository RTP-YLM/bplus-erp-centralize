# B+ Plus ERP Database Structure Analysis

> **Source:** `bplus_erp_db.bak` — SQL Server 2019 (RTM) 15.0.2000.5  
> **Restored:** 2026-06-04 to OrbStack container `bplus-sqlserver`  
> **Database:** `bplus_erp_db` — 302 tables, 100,910 documents (2021-06 ~ 2026-06)  
> **Business:** เม้งยานยนต์ (Meng Automotive) — จำหน่ายรถจักรยานยนต์, อะไหล่, บริการ  
> **Branches:** ตากสิน 18, เอกชัย 118, เวสป้าสุขสวัสดิ์, เวสป้าตากสิน, เวสป้าบางโพ

---

## 1. สรุปภาพรวม

| กลุ่ม | จำนวน Tables | กลุ่มหลัก |
|-------|-------------|-----------|
| **Transaction (เคลื่อนไหวทุกวัน)** | 15 | DOCINFO, TRANSTKH/D/J, TRANPAYH/D/A/J, SKUMOVE, VATTABLE, ARPAYMENT, APPAYMENT, BANKSTATEMENT, ACCOUNTJOURNAL, ACCOUNTVOUCHER, SLDETAIL, ARDETAIL, APDETAIL, CASHBOOK |
| **Master Data** | 25 | SKUMASTER, GOODSMASTER, ARFILE, APFILE, ACCOUNTCHART, BRANCH, WARELOCATION, SALESMAN, BRAND, ICCAT, ICDEPT, PAYMENTTYPE, BANKFILE, etc. |
| **Config / Lookup** | 40 | DOCTYPE, DOCRUN, CRYPTUSERTAB, SCTYACCESS, SCTYTAB, TMPLDEF, etc. |
| **Campaign / Promotion** | 15 | ARCAMPAIGN, ARCBUY, ARCFREE, ARCSKU, ARCVOLUME, ARCXCHG, HOTPRICE, etc. |
| **Inventory** | 10 | SKUBALANCE, SKUALT, WAREHOUSE, WAREZONE, WARELOCATION, PACKINFO |
| **Financial** | 20 | GLBALANCE, GLPERIOD, CASHACCOUNT, CASHPERIOD, BSTMPERIOD, BANKACCOUNT, etc. |
| **e-Tax / Receipt** | 5 | ETAXCONFIG, ETAXINTF, ETAXINVOICE, ETAXSTATUS |
| **Empty / Unused** | 121 | Tables with 0 rows (ไม่ได้ใช้งาน) |

---

## 2. ⚡ Tables ที่มีความเคลื่อนไหวทุกวัน (Daily Active)

### 🔴 Tier 1 — High Volume (เคลื่อนไหวทุกวัน, >1000 rows/day)

| Table | Rows | Date Range | Unique Days | คำอธิบาย |
|-------|------|------------|-------------|----------|
| **DOCINFO** | 100,910 | 2021-06-10 → 2026-06-04 | 1,015 | **เอกสารหลัก** — header ของทุก transaction, มี DI_DATE, DI_REF, DI_DT (doctype) |
| **TRANSTKD** | 201,791 | — | — | **รายละเอียดสินค้า** — detail lines ของ stock transactions (สินค้า, ราคา, จำนวน) |
| **SKUMOVE** | 135,626 | 2023-12-31 → 2026-06-04 | 861 | **การเคลื่อนไหวสินค้า** — ทุกครั้งที่สินค้าเข้า/ออก (date ผ่าน SKM_DI → DOCINFO) |
| **TRANSTKJ** | 105,414 | — | — | **Journal ของ stock transactions** — GL posting |
| **TRANPAYJ** | 102,275 | — | — | **Journal ของ payment transactions** — GL posting |
| **BPLUSDELETELOG** | 87,984 | — | — | **Log การลบ** — ทุก record ที่ถูกลบ |
| **PRICECHANGE** | 52,962 | 2024-01-01 → 2026-06-03 | 533 | **ประวัติเปลี่ยนราคา** — log ทุกครั้งที่ราคาเปลี่ยน |

### 🟠 Tier 2 — Medium Volume (เคลื่อนไหวเกือบทุกวัน)

| Table | Rows | Date Range | Unique Days | คำอธิบาย |
|-------|------|------------|-------------|----------|
| **VATTABLE** | 48,972 | 2021-06-10 → 2026-12-24 | 1,010 | **ภาษีมูลค่าเพิ่ม** — VAT records ทุกเอกสาร |
| **TRANSTKH** | 46,995 | 2023-12-31 → 2026-06-04 | 861 | **Header ของ stock transactions** — รับ/ขาย/โอน/เบิก |
| **ARPAYMENT** | 46,330 | — | — | **การรับชำระลูกหนี้** — receipt records |
| **ACCOUNTJOURNAL** | 45,942 | — | — | **บัญชีรายวัน** — GL journal entries |
| **TRANPAYH** | 41,011 | 2023-12-28 → 2026-06-03 | 877 | **Header ของ payment transactions** — จ่ายเงิน/รับเงิน |
| **TRANPAYA** | 38,095 | — | — | **Apportion ของ payment** — 分配รายละเอียด |
| **TRANPAYD** | 35,420 | — | — | **Detail ของ payment** — วิธีชำระ (เงินสด/เช็ค/โอน) |
| **ARDETAIL** | 33,781 | — | — | **รายละเอียดลูกหนี้** — AR subledger |
| **BANKSTATEMENT** | 30,326 | 2024-01-01 → 2026-06-03 | 875 | **Statement ธนาคาร** — bank reconciliation (date ผ่าน BSTM_DI → DOCINFO) |
| **SLDETAIL** | 27,074 | — | — | **รายละเอียดขาย** — sales detail by salesman |

### 🟢 Tier 3 — Regular Activity

| Table | Rows | คำอธิบาย |
|-------|------|----------|
| **APPAYMENT** | 14,896 | การชำระเจ้าหนี้ |
| **APDETAIL** | 12,552 | รายละเอียดเจ้าหนี้ |
| **ACCOUNTVOUCHER** | 12,442 | ใบสำคัญบัญชี |
| **AROE** | 12,084 | ลูกหนี้ (Order Entry) |
| **TRANPAYO** | 10,862 | POS paid-out |
| **CASHBOOK** | 7,711 | สมุดเงินสด |
| **GLBALANCE** | 6,877 | ยอดคงเหลือ GL |
| **SKUBALANCE** | 5,500 | ยอดคงเหลือสินค้า (FIFO) |
| **WHTTABLE** | 3,457 | หัก ณ ที่จ่าย |
| **TRANPAYR** | 3,384 | คืนเงินมัดจำ |
| **ETAXINTF** | 1,896 | e-Tax Invoice interface |

---

## 3. 🔗 ความเชื่อมโยงระหว่าง Tables (Key Relationships)

### 3.1 Core Transaction Flow

```
                    ┌─────────────┐
                    │   DOCTYPE   │ (DT_KEY → DI_DT, DT_DOCCODE, DT_PROPERTIES)
                    │  ประเภทเอกสาร │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   DOCINFO   │ ◄── จุดศูนย์กลางของทุก transaction
                    │ (DI_KEY)    │     DI_DATE, DI_REF, DI_DT
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
    │ TRANSTKH  │   │ TRANPAYH  │   │ ACCOUNT-  │
    │ (TRH_KEY) │   │ (TPH_KEY) │   │ VOUCHER   │
    │ Stock Hdr │   │ Pmt Hdr   │   │ (VC_KEY)  │
    └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
          │               │               │
    ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
    │ TRANSTKD  │   │ TRANPAYD  │   │ ACCOUNT-  │
    │ (TRD_KEY) │   │ (TPD_KEY) │   │ JOURNAL   │
    │ Stock Det │   │ Pmt Detail│   │ (JR_KEY)  │
    │ สินค้า,ราคา│   │ เช็ค/เงินสด│   │ DR/CR     │
    └─────┬─────┘   └─────┬─────┘   └───────────┘
          │               │
    ┌─────▼─────┐   ┌─────▼─────┐
    │ SKUMOVE   │   │ TRANPAYA  │
    │ (SKM_KEY) │   │ (TPA_KEY) │
    │ เคลื่อนไหว│   │ Apportion │
    │ สินค้า     │   └───────────┘
    └───────────┘
```

### 3.2 Master Data Links

```
SKUMASTER ◄─── SKUMOVE, TRANSTKD, SKUBALANCE, GOODSMASTER, SKUAP
  │
  ├──► BRAND (SKU_BRN)
  ├──► ICCAT (SKU_ICCAT)
  ├──► ICDEPT (SKU_ICDEPT)
  ├──► ICCOLOR (SKU_ICCOLOR)
  ├──► ICSIZE (SKU_ICSIZE)
  ├──► WARELOCATION (SKU_WL)
  └──► UOFQTY (SKU_K_UTQ, SKU_S_UTQ, SKU_T_UTQ)

ARFILE ◄─── ARDETAIL, ARPAYMENT, ARSUMMARY, AROE
  │
  ├──► ACCOUNTCHART (AR_AC)
  ├──► ARCAT (AR_ARCAT)
  ├──► ARGROUP (AR_ARG)
  └──► SALESMAN (via AROE)

APFILE ◄─── APDETAIL, APPAYMENT, APSUMMARY, SKUAP
  │
  ├──► ACCOUNTCHART (AP_AC)
  ├──► APCAT (AP_APCAT)
  └──► BANKFILE (AP_BANK)

ACCOUNTCHART ◄─── GLBALANCE, ACCOUNTJOURNAL, TRANSTKD, TRANPAYD
```

### 3.3 Foreign Key Summary (Top Relationships)

| Child Table | FK Column | Parent Table | Parent Column | ความหมาย |
|------------|-----------|-------------|---------------|----------|
| TRANSTKH | TRH_DI | DOCINFO | DI_KEY | เอกสาร → Header สต็อก |
| TRANSTKD | TRD_TRH | TRANSTKH | TRH_KEY | Header → Detail สต็อก |
| TRANSTKD | TRD_SKU | SKUMASTER | SKU_KEY | Detail → สินค้า |
| TRANPAYH | TPH_DI | DOCINFO | DI_KEY | เอกสาร → Header ชำระเงิน |
| TRANPAYD | TPD_TPH | TRANPAYH | TPH_KEY | Header → Detail ชำระเงิน |
| TRANPAYA | TPA_TPH | TRANPAYH | TPH_KEY | Header → Apportion |
| ACCOUNTVOUCHER | VC_DI | DOCINFO | DI_KEY | เอกสาร → ใบสำคัญบัญชี |
| ACCOUNTJOURNAL | JR_VC | ACCOUNTVOUCHER | VC_KEY | ใบสำคัญ → บัญชีรายวัน |
| ACCOUNTJOURNAL | JR_AC | ACCOUNTCHART | AC_KEY | รายวัน → ผังบัญชี |
| VATTABLE | VAT_DI | DOCINFO | DI_KEY | เอกสาร → ภาษี |
| ARPAYMENT | ARP_DI | DOCINFO | DI_KEY | เอกสาร → รับชำระลูกหนี้ |
| APPAYMENT | APP_DI | DOCINFO | DI_KEY | เอกสาร → ชำระเจ้าหนี้ |
| BANKSTATEMENT | BSTM_DI | DOCINFO | DI_KEY | เอกสาร → Statement ธนาคาร |
| SLDETAIL | SLD_DI | DOCINFO | DI_KEY | เอกสาร → รายละเอียดขาย |
| ARDETAIL | ARD_DI | DOCINFO | DI_KEY | เอกสาร → ลูกหนี้ |
| APDETAIL | APD_DI | DOCINFO | DI_KEY | เอกสาร → เจ้าหนี้ |
| CASHBOOK | CASHB_DI | DOCINFO | DI_KEY | เอกสาร → สมุดเงินสด |
| SKUMOVE | SKM_DI | DOCINFO | DI_KEY | เอกสาร → เคลื่อนไหวสินค้า |
| SKUMOVE | SKM_SKU | SKUMASTER | SKU_KEY | เคลื่อนไหว → สินค้า |
| SKUBALANCE | SKB_SKU | SKUMASTER | SKU_KEY | คงเหลือ → สินค้า |
| SKUBALANCE | SKB_DI | DOCINFO | DI_KEY | คงเหลือ → เอกสาร |

---

## 4. 📋 ประเภทเอกสาร (DOCTYPE)

> **Column names จริง:** `DT_KEY`, `DT_DOCCODE`, `DT_THAIDESC`, `DT_ENGDESC`, `DT_PROPERTIES` (ไม่ใช่ DT_CODE/DT_NAME/DT_TYPE)

### กลุ่มหลัก

| Properties | ประเภท | Doc Codes | คำอธิบาย |
|-----------|--------|-----------|----------|
| **3xx** | Stock/Sales | SMY0-7, SPY0-7, BMMY, BPMY, KMMY, KPMY | ขายรถ, ขายอะไหล่, โอนย้าย |
| **303** | Receive | BMMY, BPMY | รับสินค้า |
| **304** | Return | GMMY, GPMY | ส่งคืน/ลดหนี้ |
| **307** | Sales | SMY0-7, SPY0-7, SCY0-7 | ขาย + คอมมิชชั่น |
| **308** | Return Sales | TMMY, TNMY, TPMY | รับคืน/ลดหนี้ |
| **309** | Internal Use | KWMY | เบิกใช้ภายใน |
| **311** | Transfer | KMMY, KPMY, KPY4-7 | โอนย้ายสินค้า |
| **332** | Count | CNT | ตรวจนับ |
| **337** | Return Parts | TPY0-7 | รับคืนอะไหล่ |
| **4xx** | AR/Receipt | RPY0-7, RIMY, RNMY | ใบเสร็จรับเงิน |
| **406** | Billing | SBMY | ใบวางบิล |
| **408** | Deposit In | DMMY, DPY0-7 | รับเงินจอง/มัดจำ |
| **409** | Deposit Refund | CMMY, CPY0-7 | คืนเงินจอง/มัดจำ |
| **5xx** | AP/Payment | PEMY, PCMY, PSMY | ใบสำคัญจ่าย |
| **6xx** | Banking | BKMY, BTMY, QIP, QPMY | ฝากเงิน, โอนเงิน, เช็ค |
| **7xx** | GL | JV, ADJ, COST, CLS | บัญชีรายวัน, ปรับปรุง |
| **8xx** | Fixed Asset | OF, PF, SF, RF, DF, FIX | ทรัพย์สินถาวร |

### Branch-Specific Doc Types

| Doc Code | Branch | คำอธิบาย |
|----------|--------|----------|
| SMY0 | ตากสิน 18 | ขายรถ |
| SMY3 | เอกชัย 118 | ขายรถ |
| SMY4 | เวสป้าสุขสวัสดิ์ | ขายรถ |
| SMY6 | เวสป้าตากสิน | ขายรถ |
| SMY7 | เวสป้าบางโพ | ขายรถ |
| SPY0-7 | ทุกสาขา | ขายอะไหล่และบริการ |
| JOY0-7 | ทุกสาขา | ใบแจ้งซ่อม |
| JPY0-7 | ทุกสาขา | ใบจองอะไหล่ |

---

## 5. 📊 Monthly Transaction Volume

| Year-Month | Documents | Avg/Day |
|-----------|-----------|---------|
| 2026-06 | 142 (4 วัน) | ~35/day |
| 2026-05 | 1,691 | ~55/day |
| 2026-04 | 1,715 | ~57/day |
| 2026-03 | 2,868 | ~93/day |
| 2026-02 | 2,758 | ~99/day |
| 2026-01 | 3,017 | ~97/day |
| 2025-12 | 3,187 | ~103/day |
| 2025-11 | 2,882 | ~96/day |
| 2025-10 | 3,143 | ~101/day |
| 2024-09 | 4,298 | ~143/day |
| 2024-08 | 4,472 | ~144/day |

**หมายเหตุ:** จำนวนเอกสารลดลงในปี 2026 อาจเนื่องจากการย้ายระบบหรือเปลี่ยนวิธีทำงาน

---

## 6. 📝 Sample Data

### 6.1 DOCINFO (เอกสารล่าสุด)

| DI_KEY | DI_DATE | DI_REF | DI_DT | ประเภท |
|--------|---------|--------|-------|--------|
| 195799 | 2026-06-04 | SPY66906/00008 | 1014 | ขายอะไหล่เวสป้าตากสิน |
| 195797 | 2026-06-04 | JOY66906/00008 | 1062 | แจ้งซ่อมเวสป้าตากสิน |
| 195796 | 2026-06-04 | JOY66906/00007 | 1062 | แจ้งซ่อมเวสป้าตากสิน |
| 195795 | 2026-06-04 | SPY76906/00022 | 1015 | ขายอะไหล่เวสป้าบางโพ |
| 195794 | 2026-06-04 | JOY76906/00019 | 1063 | แจ้งซ่อมเวสป้าบางโพ |

### 6.2 TRANSTKH (Header สต็อก)

| TRH_KEY | TRH_DI | TRH_BR | TRH_SHIP_DATE | TRH_CANCEL_DATE |
|---------|--------|--------|---------------|-----------------|
| 52613 | 195799 | 103 | 2026-06-04 | 2026-06-05 |
| 52612 | 195798 | 102 | 2026-06-04 | 2026-06-05 |
| 52611 | 195797 | 103 | 2026-06-04 | 2026-07-04 |

### 6.3 TRANSTKD (Detail สต็อก)

| TRD_KEY | TRD_TRH | TRD_SKU | TRD_MAN_D | TRD_EXP_D |
|---------|---------|---------|-----------|-----------|
| 265010 | 52613 | 5106 | 2026-06-04 | 2027-06-04 |
| 265009 | 52613 | 17264 | 2026-06-04 | 2027-06-04 |
| 265008 | 52613 | 49342 | 2026-06-04 | 2027-06-04 |

### 6.4 TRANPAYH (Header ชำระเงิน)

| TPH_KEY | TPH_DI | TPH_BR | TPH_SHIP_DATE |
|---------|--------|--------|---------------|
| 48704 | 195791 | 1 | 2026-06-03 |
| 48703 | 195790 | 101 | 2026-06-03 |
| 48702 | 195789 | 101 | 2026-06-03 |

### 6.5 ACCOUNTJOURNAL (บัญชีรายวัน)

| JR_KEY | JR_VC | JR_SEQ | JR_AC | JR_DEBIT | JR_CREDIT |
|--------|-------|--------|-------|----------|-----------|
| 373933 | 98796 | 2 | 1091 | 0.00 | 65.42 |
| 373932 | 98796 | 1 | 1090 | 65.42 | 0.00 |
| 373931 | 98795 | 2 | 1090 | 0.00 | 65.42 |

---

## 7. 🏗️ แผนผัง DB สำหรับ Centralize

### 7.1 Tables ที่ต้อง Sync ทุกวัน (Priority 1)

```
DOCINFO ──────────────── จุดศูนย์กลาง, sync ก่อน
  ├── TRANSTKH ────────── Header สต็อก
  │   └── TRANSTKD ────── Detail สต็อก
  ├── TRANPAYH ────────── Header ชำระเงิน
  │   ├── TRANPAYD ────── Detail ชำระเงิน
  │   └── TRANPAYA ────── Apportion
  ├── ACCOUNTVOUCHER ──── ใบสำคัญบัญชี
  │   └── ACCOUNTJOURNAL ─ บัญชีรายวัน
  ├── VATTABLE ────────── ภาษี
  ├── ARPAYMENT ────────── รับชำระลูกหนี้
  ├── APPAYMENT ────────── ชำระเจ้าหนี้
  ├── BANKSTATEMENT ────── Statement ธนาคาร
  ├── CASHBOOK ────────── สมุดเงินสด
  ├── SLDETAIL ────────── รายละเอียดขาย
  ├── ARDETAIL ────────── ลูกหนี้
  ├── APDETAIL ────────── เจ้าหนี้
  └── SKUMOVE ────────── เคลื่อนไหวสินค้า
```

### 7.2 Master Data (Priority 2 — Sync เมื่อมีการเปลี่ยนแปลง)

```
SKUMASTER ─── สินค้า (SKU) — 44,964 rows
  └── GOODSMASTER ─── สินค้า (Goods) — 44,968 rows
  └── SKUAP ────────── SKU↔ผู้ขาย mapping — 45,366 rows
ARFILE ─── ลูกหนี้ — 8,032 rows
  └── ARPLU ──────── รายการราคาต่อลูกค้า (AR Price List Unit) — 41,233 rows
  └── ARADDRESS ──── ที่อยู่ลูกหนี้ — 14,176 rows
  └── ARSUMMARY ──── สรุปยอด — 8,032 rows
APFILE ─── เจ้าหนี้ — 267 rows
ACCOUNTCHART ─── ผังบัญชี — 277 rows
SALESMAN ─── พนักงานขาย
BRANCH ─── สาขา (6 rows: 0=ไม่ระบุ, 1=MY00, 101=MY04, 102=MY03, 103=MY06, 104=MY07)
WARELOCATION ─── คลังสินค้า
PAYMENTTYPE ─── วิธีชำระ
BANKFILE ─── ธนาคาร
ADDRBOOK ─── สมุดที่อยู่ — 13,802 rows
ARCONDITION ─── เงื่อนไข Campaign — 16,556 rows
```

### 7.3 Config (Priority 3 — Sync ครั้งเดียว)

```
DOCTYPE ─── ประเภทเอกสาร
DOCRUN ─── เลข running
COMPANYINFO ─── ข้อมูลบริษัท
GLPERIOD ─── งวดบัญชี
```

---

## 8. 🔑 Key Columns สำหรับ Join

### DOCINFO (จุดศูนย์กลาง)

- `DI_KEY` — Primary Key (ใช้ join กับทุก transaction)
- `DI_DATE` — วันที่เอกสาร
- `DI_REF` — เลขที่เอกสาร (เช่น SPY66906/00008)
- `DI_DT` — FK → DOCTYPE.DT_KEY
- `DI_AMOUNT` — ยอดเงิน
- `DI_CRE_DATE` — วันเวลาสร้าง

### TRANSTKH + TRANSTKD (Stock)

- `TRH_DI` → DOCINFO.DI_KEY
- `TRD_TRH` → TRANSTKH.TRH_KEY
- `TRD_SKU` → SKUMASTER.SKU_KEY
- `TRD_GOODS` → GOODSMASTER.GOODS_KEY
- `TRD_QTY` — จำนวน
- `TRD_N_AMT` — ยอดสุทธิ

### TRANPAYH + TRANPAYD (Payment)

- `TPH_DI` → DOCINFO.DI_KEY
- `TPH_AR` → ARFILE.AR_KEY (ลูกหนี้)
- `TPH_AP` → APFILE.AP_KEY (เจ้าหนี้)
- `TPD_TPH` → TRANPAYH.TPH_KEY
- `TPD_PMT` → PAYMENTTYPE.PMT_KEY
- `TPD_BAHT` — จำนวนเงิน

### ARDETAIL / APDETAIL (Subledger)

- `ARD_DI` / `APD_DI` → DOCINFO.DI_KEY
- `ARD_AR` → ARFILE.AR_KEY
- `APD_AP` → APFILE.AP_KEY
- `ARD_N_AMT` / `APD_N_AMT` — ยอดสุทธิ

---

## 9. ⚠️ ข้อสังเกต

1. **Branch Pattern:** Doc types มี suffix เป็นเลขสาขา (SMY0=ตากสิน, SMY3=เอกชัย, SMY4=เวสป้าสุขสวัสดิ์, SMY6=เวสป้าตากสิน, SMY7=เวสป้าบางโพ)

2. **Doc Reference Format:** `{DocCode}{BranchCode}{YearMonth}/{Running}` เช่น `SPY66906/00008`
   - SPY = ขายอะไหล่
   - 6 = เวสป้าตากสิน
   - 6906 = ปี 69 (พ.ศ. 2569) เดือน 06
   - /00008 = เลข running

3. **Currency:** ใช้ `money` type, มีระบบ multi-currency (TPD_PMT_CRNCY, TPD_PMT_XCHG)

4. **Audit Trail:** ทุก table มี `*_LASTUPD` column, DOCINFO มี CRE/UPD/DEL/APV/EXM dates

5. **FIFO Costing:** SKUBALANCE มี FIFO costing (SKB_FIFO, SKB_COST)

6. **e-Tax:** มีระบบ e-Tax Invoice (ETAXCONFIG, ETAXINTF, ETAXINVOICE, ETAXSTATUS)

7. **Campaign System:** มีระบบโปรโมชั่นซับซ้อน (ARCAMPAIGN + sub-tables)

8. **Empty Tables (121):** มี 121 tables ที่มี 0 rows รวมถึง ARCAMPAIGN, HOTPRICE, ETAXINVOICE, ETAXSTATUS, FIXASSET, MEMBER, DELIVERYD/H, VAN*, POSCONTROL ฯลฯ — features ที่ยังไม่ได้ใช้งานในระบบนี้

9. **SKUMOVE/BANKSTATEMENT ไม่มี date column โดยตรง** — ต้อง JOIN ผ่าน `*_DI → DOCINFO.DI_DATE` เสมอ

10. **Tables ขนาดใหญ่ที่ไม่ใช่ transaction:** SKUAP (45,366), ARPLU (41,233) เป็น master data pricing/vendor mapping — ต้อง sync ด้วย

---

*Generated: 2026-06-04 | Verified: 2026-06-04 | Source: bplus_erp_db.bak (SQL Server 2019) | Live container: bplus-sqlserver*
