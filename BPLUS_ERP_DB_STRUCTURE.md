# BPlus ERP Database Structure — Complete Reference

> **Updated:** 2026-06-08  
> **Source:** 8 BPLUSERP databases (SQL Server 2019, restored from production MDF)  
> **Reference DB:** BPLUSERP_MENGYANYONT (เม้งยานยนต์)  
> **Container:** bplus-sqlserver (Docker, port 1433)  
> **Schema Consistency:** ✅ All 8 databases share IDENTICAL table schemas (column counts verified)

---

## 1. Overview

### 1.1 Databases

| Database | Company | DOCINFO | SKUMASTER | Tables | MDF Size |
|---|---|---|---|---|---|
| BPLUSERP_MDRIVEHONDA | Honda ถาวร (M-Drive) | 350,784 | 48,544 | 303 | 2,246 MB |
| BPLUSERP_MOTOSQUARE | Motosquare | 243,397 | 80,304 | 305 | 1,844 MB |
| BPLUSERP_MOTOAHOLIC | Motoaholic | 177,032 | 82,116 | 304 | 1,505 MB |
| BPLUSERP_TRIUMPHPHARAM5 | Triumph พระราม 5 | 112,427 | 36,971 | 303 | 1,005 MB |
| BPLUSERP_MENGYANYONT | เม้งยานยนต์ | 101,109 | 44,965 | 302 | 872 MB |
| BPLUSERP_MOTOMODI | Motomodi | 54,756 | 6,928 | 318 | 519 MB |
| BPLUSERP_MOTODESMO | Motodesmo | 23,771 | 6,297 | 302 | 272 MB |
| BPLUSERP_MOTOBIKE | Motobike | 319 | 154 | 302 | 104 MB |

**Total:** ~1.06M documents, ~300 tables/DB, ~8.4 GB MDF

### 1.2 Schema Consistency

✅ **All 8 databases share IDENTICAL table schemas** — column names, data types, and column counts match exactly.

Extra tables are only timestamped temp tables created by the BPlus ERP application (e.g., `T20260606151247609`), not part of the core schema.

| Table | MENGYANYONT | MDRIVEHONDA | MOTOAHOLIC | MOTOMODI |
|---|---|---|---|---|
| DOCINFO (cols) | 50 | 50 | 50 | 50 |
| TRANSTKD (cols) | 104 | 104 | 104 | 104 |
| SKUMASTER (cols) | 74 | 74 | 74 | 74 |
| ARFILE (cols) | 31 | 31 | 31 | 31 |
| DOCTYPE (cols) | 47 | 47 | 47 | 47 |

---

## 2. Transaction Summary (BPLUSERP_MENGYANYONT — เม้งยานยนต์)

### 2.1 Date Ranges

| Table | First Record | Last Record | Unique Days |
|---|---|---|---|
| DOCINFO | 2021-06-10 | 2026-06-07 | 1,018 |
| VATTABLE | 2021-06-10 | 2026-12-24 | — |
| SKUMOVE | 2023-12-31 | 2026-06-07 | — |
| BANKSTATEMENT | 2024-01-01 | 2026-06-07 | — |

### 2.2 Monthly Volume

| Period | Documents | Avg/Day |
|---|---|---|
| 2026-06 | 142 (4 days) | ~35/day |
| 2026-05 | 1,691 | ~55/day |
| 2026-04 | 1,715 | ~57/day |
| 2026-03 | 2,868 | ~93/day |
| 2026-02 | 2,758 | ~99/day |
| 2026-01 | 3,017 | ~97/day |
| 2025-12 | 3,187 | ~103/day |

---

## 3. All Tables (302) with Row Counts

### 3.1 🔴 Tier 1 — High Volume (>10,000 rows)

| Table | Rows | Description |
|---|---|---|
| **TRANSTKD** | 202,302 | Stock transaction details (items, prices, quantities) |
| **SKUMOVE** | 135,912 | SKU movement log (every in/out) |
| **TRANSTKJ** | 105,667 | Stock transaction journal (GL posting) |
| **TRANPAYJ** | 102,433 | Payment transaction journal (GL posting) |
| **DOCINFO** | 101,109 | Master document header (center of everything) |
| **BPLUSDELETELOG** | 87,984 | Delete audit log |
| **PRICECHANGE** | 52,963 | Price change history |
| **VATTABLE** | 49,066 | VAT records |
| **TRANSTKH** | 47,118 | Stock transaction headers |
| **ARPAYMENT** | 46,432 | AR payments received |
| **ACCOUNTJOURNAL** | 45,942 | GL journal entries |
| **SKUAP** | 45,367 | SKU ↔ Supplier mapping |
| **GOODSMASTER** | 44,969 | Goods master (barcode/alias per SKU) |
| **SKUMASTER** | 44,965 | SKU master (product catalog) |
| **ARPLU** | 41,234 | AR price list per customer |
| **TRANPAYH** | 41,087 | Payment transaction headers |
| **TRANPAYA** | 38,181 | Payment apportion details |
| **TRANPAYD** | 35,488 | Payment transaction details |
| **ARDETAIL** | 33,874 | AR subledger entries |
| **BANKSTATEMENT** | 30,386 | Bank statement entries |
| **SLDETAIL** | 27,152 | Salesperson detail |
| **ARCONDITION** | 16,584 | AR due date conditions |
| **APPAYMENT** | 14,896 | AP payments made |
| **SCTYACCESS** | 14,865 | Security access control |
| **ARADDRESS** | 14,216 | AR addresses |
| **ADDRBOOK** | 13,836 | Address book |
| **SCTYTAB** | 13,505 | Security user table |
| **APDETAIL** | 12,553 | AP subledger entries |
| **ACCOUNTVOUCHER** | 12,442 | GL vouchers |
| **AROE** | 12,122 | AR order entry |
| **TRANPAYO** | 10,862 | POS paid-out |

### 3.2 🟠 Tier 2 — Medium Volume (1,000 – 10,000 rows)

| Table | Rows | Description |
|---|---|---|
| ARFILE | 8,051 | Customer master |
| ARSUMMARY | 8,051 | Customer summary (credit, ABC, etc.) |
| CASHBOOK | 7,714 | Cash book entries |
| SUBDISTRICTS | 7,446 | Thai sub-districts reference |
| APPLU | 6,951 | AP price list per supplier |
| GLBALANCE | 6,877 | GL balance by period |
| SKUBALANCE | 5,500 | Stock balance (FIFO) |
| TRANPAYI | 3,863 | Payment interest |
| WHTTABLE | 3,459 | Withholding tax |
| TRANPAYR | 3,393 | Deposit refund |
| ETAXINTF | 1,896 | e-Tax invoice interface |
| DOCRUN | 1,724 | Document running numbers |
| CASHPERIOD | 1,635 | Cash period close |
| GLANALYSISD | 1,479 | GL analysis detail |
| SKUALT | 1,380 | SKU alternates |
| SYSLOOKUP | 1,361 | System lookup values |
| DELDILOG | 1,329 | Delivery log |
| REPORTFILE | 1,278 | Report templates |
| TMPLDEF | 1,155 | Template definitions |

### 3.3 🟢 Tier 3 — Low Volume (100 – 999 rows)

| Table | Rows | Description |
|---|---|---|
| DISTRICTS | 928 | Thai districts |
| SELLANALYSISX | 834 | Sales analysis cross |
| MISCLOOKUP | 559 | Misc lookup |
| APDUETAB | 558 | AP due date table |
| ARDUETAB | 558 | AR due date table |
| MISCLAYOUT | 545 | Misc layout |
| TEMPTABLENAME | 529 | Temp table registry |
| SELLANALYSISD | 391 | Sales analysis detail |
| APADDRESS | 331 | AP addresses |
| APCONDITION | 325 | AP conditions |
| REPORTGROUP | 308 | Report groups |
| GLANALYSISH | 300 | GL analysis header |
| ACCOUNTCHART | 277 | Chart of accounts |
| ACLEVEL | 277 | Account levels |
| APFILE | 267 | Supplier master |
| APSUMMARY | 267 | Supplier summary |
| SELLANALYSISS | 259 | Sales analysis summary |
| GLANALYSISS | 232 | GL analysis summary |
| ICCOLOR | 210 | Item colors |
| BSTMPERIOD | 168 | Bank statement period |
| ICCMLOG | 159 | IC commit log |
| DASHDETAILS | 146 | Dashboard details |
| SHOWFONT | 139 | Display fonts |
| DOCTYPE | 134 | Document types |
| BPLUSLICENSE | 129 | License info |
| SQLFIELDHELPER | 128 | SQL field helper |
| BRAND | 125 | Brands |
| BRNLEVEL | 125 | Brand levels |
| CHEQUEBOOK | 122 | Cheque books |
| PAYMENTTYPE | 112 | Payment types |
| CLOSINGENTRIESD | 106 | Closing entries detail |
| SHOWCOLOR | 102 | Display colors |

### 3.4 ⚪ Tier 4 — Reference (< 100 rows)

| Table | Rows | Description |
|---|---|---|
| GLANALYSISX | 100 | GL analysis cross |
| POSPAIDOUT | 91 | POS paid-out |
| UOFQTY | 85 | Units of measure |
| WARELOCATION | 85 | Warehouse locations |
| BANKFILE | 82 | Banks |
| PROVINCES | 77 | Thai provinces |
| DFREASON | 67 | Defect reasons |
| APPROVELEVEL | 64 | Approval levels |
| SALESMAN | 63 | Salespeople |
| CRYPTUSERTAB | 61 | System users |
| GLPERIOD | 37 | GL periods |
| VATPERIOD | 37 | VAT periods |
| SELLANALYSISH | 35 | Sales analysis header |
| TEMPLATEJOURNAL | 33 | Journal templates |
| ICSIZE | 31 | Item sizes |
| WHTPERIOD | 31 | WHT periods |
| GLANALYSIST | 29 | GL analysis tree |
| BUSINESSTYPE | 27 | Business types |
| BYDATAACCESS | 22 | Data access |
| POSPOLAYOUT | 21 | POS layout |
| POSNDEF | 20 | POS definitions |
| POSTICKETLAYOUT | 20 | POS ticket layout |
| SELLANALYSISG | 20 | Sales analysis group |
| APDUETABNAME | 18 | AP due table names |
| ARDUETABNAME | 18 | AR due table names |
| EXCHANGERATE | 18 | Exchange rates |
| LKUPUSRPLVL | 16 | User permission levels |
| BPAPPSERVICE | 14 | BPlus app services |
| SELLANALYSIST | 13 | Sales analysis tree |
| ICCAT | 11 | Item categories |
| ICCOMMIT | 11 | IC commit status |
| ICGL | 11 | IC GL mappings |
| WAREZONE | 11 | Warehouse zones |
| BYDATANAME | 10 | Data names |
| CONTACTSTATUS | 10 | Contact statuses |
| LOOKUPVISIT | 10 | Lookup visits |
| APPROVEGROUP | 9 | Approval groups |
| BANKATSINFO | 9 | Bank ATS info |
| BANKACCOUNT | 8 | Bank accounts |
| BPLUSCURRENTUSER | 7 | Current users |
| SHIPBY | 7 | Shipping methods |
| SHOWSHOP | 7 | Display shops |
| ARCAT | 6 | AR categories |
| BRANCH | 6 | Branches |
| CLOSINGENTRIESA | 6 | Closing entries adjustments |
| DASHVIEW | 6 | Dashboard views |
| POSPAIDIN | 6 | POS paid-in |
| PRICETAG | 6 | Price tags |
| APCAT | 4 | AP categories |
| ARDEPOSIT | 3 | AR deposits |
| CASHACCOUNT | 3 | Cash accounts |
| TEMPLATEVOUCHER | 3 | Voucher templates |
| APPRICETAB | 2 | AP price tables |
| ARPRICETAB | 2 | AR price tables |
| CLOSINGENTRIESH | 2 | Closing entries header |
| DEPTTAB | 2 | Departments |
| ICPRT | 2 | IC print settings |
| MBTYPE | 2 | Member types |
| SLCAT | 2 | Sales categories |
| WAREHOUSE | 2 | Warehouses |
| Single-row tables | 1 each | COMPANYINFO, AUTORUNCODE, COUNTRYS, VATRATE, etc. (30 tables) |

### 3.5 ⛔ Empty Tables (121) — Features Not Used

Notable unused features: ARCAMPAIGN (promotions), FIXASSET (fixed assets), MEMBER (loyalty), DELIVERYH/D (delivery), VAN* (van sales), POSCONTROL, PURCQUOTATION, TOUCHGOODS/TERMINAL, WEBCONFIG, WHITEBOARD, WHT* batch/users, and more.

---

## 4. Core Table Schemas

### 4.1 DOCINFO — Document Header (Center of Everything)
**50 columns** | FK → DOCTYPE

| Column | Type | Nullable | Description |
|---|---|---|---|
| DI_KEY | int PK | NOT NULL | Primary key |
| DI_DT | int FK | NOT NULL | → DOCTYPE.DT_KEY (document type) |
| DI_SUBS_DI | int | NULL | Substitution document |
| DI_REVISION | int | NULL | Revision number |
| DI_ACTIVE | int | NULL | Active flag |
| DI_EDIT_TIME | int | NULL | Edit count |
| DI_FLAG | int | NULL | Status flag |
| DI_REF | nvarchar(16) | NOT NULL | Document reference (e.g., SPY66906/00008) |
| DI_DATE | date | NOT NULL | Document date |
| DI_CRE_DATE | datetime | NOT NULL | Created date/time |
| DI_CRE_BY | nvarchar(15) | NOT NULL | Created by (user) |
| DI_CRE_CPTN | nvarchar(15) | NOT NULL | Created by (computer) |
| DI_CRE_LGNN | nvarchar(20) | NOT NULL | Created by (login name) |
| DI_UPD_DATE | datetime | NOT NULL | Updated date/time |
| DI_UPD_BY | nvarchar(15) | NOT NULL | Updated by |
| DI_UPD_CPTN | nvarchar(15) | NOT NULL | Updated computer |
| DI_UPD_LGNN | nvarchar(20) | NOT NULL | Updated login |
| DI_DEL_DATE | datetime | NULL | Deleted date (soft delete) |
| DI_DEL_BY | nvarchar(15) | NULL | Deleted by |
| DI_DEL_CPTN | nvarchar(15) | NULL | Deleted computer |
| DI_DEL_LGNN | nvarchar(20) | NULL | Deleted login |
| DI_PRN_TIME | smallint | NOT NULL | Print count |
| DI_PRN_DATE | datetime | NULL | Last printed |
| DI_PRN_BY | nvarchar(15) | NULL | Printed by |
| DI_PRN_CPTN | nvarchar(15) | NULL | Print computer |
| DI_PRN_LGNN | nvarchar(20) | NULL | Print login |
| DI_PRN_STATUS | int | NULL | Print status |
| DI_EXM_DATE | datetime | NULL | Examined date |
| DI_EXM_BY | nvarchar(15) | NULL | Examined by |
| DI_EXM_CPTN | nvarchar(15) | NULL | Examined computer |
| DI_EXM_LGNN | nvarchar(20) | NULL | Examined login |
| DI_APV_DATE | datetime | NULL | Approved date |
| DI_APV_BY | nvarchar(15) | NULL | Approved by |
| DI_APV_CPTN | nvarchar(15) | NULL | Approved computer |
| DI_APV_LGNN | nvarchar(20) | NULL | Approved login |
| DI_APV_STATUS | int | NULL | Approval status |
| DI_DFRS | int | NULL | Differs flag |
| DI_1ST_ITEMS | int | NULL | First item count |
| DI_1ST_AMOUNT | money | NOT NULL | First amount |
| DI_ITEMS | int | NULL | Total items |
| DI_AMOUNT | money | NOT NULL | Total amount |
| DI_AUTO | int | NULL | Auto-generated flag |
| DI_CREATOR_DI | int | NULL | Creator document reference |
| DI_REMARK | nvarchar(max) | NULL | Remarks |
| DI_GPS_LAT_S | nvarchar(20) | NULL | GPS latitude |
| DI_GPS_LONG_S | nvarchar(20) | NULL | GPS longitude |
| DI_EC_CREATOR | int | NULL | E-commerce creator |
| DI_EC_REF | nvarchar(20) | NULL | E-commerce reference |
| DI_EC_DATE | date | NULL | E-commerce date |
| DI_LASTUPD | nvarchar(17) | NULL | Last update timestamp |

**Indexes:** CLUSTERED PK(DI_KEY), IX(DI_DATE), IX(DI_DATE, DI_REF), IX(DI_REF), IX(DI_DT), IX(DI_ACTIVE, DI_CREATOR_DI)

### 4.2 DOCTYPE — Document Type Definitions
**47 columns**

| Column | Type | Description |
|---|---|---|
| DT_KEY | int PK | Primary key (matches DI_DT) |
| DT_DOCCODE | nvarchar(4) | Document code (SMY0, SPY7, etc.) |
| DT_THAIDESC | nvarchar(120) | Thai description |
| DT_ENGDESC | nvarchar(120) | English description |
| DT_PROPERTIES | int | Type category (303=Receive, 307=Sales, 4xx=AR, etc.) |
| DT_RUNTYPE | smallint | Running number type |
| DT_PREFIX | nvarchar(4) | Reference prefix |
| DT_DIGIT | smallint | Running digit count |
| DT_BOOKSIZE | int | Book size |
| DT_ACCESS | smallint | Access level |
| DT_CANEDIT | nchar(1) | Editable flag |
| DT_ENABLE | nchar(1) | Enabled flag |
| DT_ETAXINVOICE | nchar(1) | e-Tax invoice flag |
| DT_ETAX_TYPECODE | nvarchar(4) | e-Tax type code |
| DT_LASTUPD | nvarchar(17) | Last update |

### 4.3 TRANSTKH — Stock Transaction Header
**35 columns** | FK → DOCINFO, BRANCH, DEPTTAB

| Column | Type | Description |
|---|---|---|
| TRH_KEY | int PK | Primary key |
| TRH_DI | int FK | → DOCINFO.DI_KEY |
| TRH_DEPT | int FK | → DEPTTAB |
| TRH_BR | int FK | → BRANCH |
| TRH_MKTP | int | Market point |
| TRH_PRMT | int | Promotion |
| TRH_N_QTY | money | Net quantity |
| TRH_N_ITEMS | int | Net items |
| TRH_SB | int | Sub-branch |
| TRH_SHIP_DATE | date | Ship date |
| TRH_VAT_TY | smallint | VAT type |
| TRH_VAT | money | VAT amount |
| TRH_VAT_R | money | VAT rate |
| TRH_PRJ | int | Project |
| TRH_CANCEL_DATE | date | Cancel date |
| TRH_REFER_XREF | nvarchar(24) | External reference |
| TRH_REFER_IREF | nvarchar(16) | Internal reference |
| TRH_LASTUPD | nvarchar(17) | Last update |

### 4.4 TRANSTKD — Stock Transaction Detail
**104 columns** | FK → TRANSTKH, SKUMASTER, GOODSMASTER

| Column | Type | Description |
|---|---|---|
| TRD_KEY | int PK | Primary key |
| TRD_TRH | int FK | → TRANSTKH.TRH_KEY |
| TRD_SEQ | int | Sequence number |
| TRD_GOODS | int FK | → GOODSMASTER.GOODS_KEY |
| TRD_SKU | int FK | → SKUMASTER.SKU_KEY |
| TRD_KEYIN | nvarchar(24) | Keyed-in code |
| TRD_QTY | money | Quantity |
| TRD_Q_FREE | money | Free quantity |
| TRD_U_PRC | float | Unit price |
| TRD_G_SELL | money | Gross selling price |
| TRD_G_VAT | money | Gross VAT |
| TRD_G_AMT | money | Gross amount |
| TRD_N_SELL | money | Net selling price |
| TRD_N_VAT | money | Net VAT |
| TRD_N_AMT | money | **Net amount (key field)** |
| TRD_B_SELL | money | Base selling price |
| TRD_B_AMT | money | Base amount |
| TRD_COST_TY | smallint | Cost type |
| TRD_LOT_NO | nvarchar(16) | Lot number |
| TRD_SERIAL | nvarchar(30) | Serial number |
| TRD_EXP_D | date | Expiry date |
| TRD_MAN_D | date | Manufacture date |
| TRD_WL | int | Warehouse location |
| TRD_TO_WL | int | Transfer to location |
| TRD_REFER_DI | int | Reference document |
| TRD_REFER_TRH | int | Reference header |
| TRD_CAMPAIGN | int | Campaign reference |
| TRD_ICCOLOR | int | Item color |
| TRD_LASTUPD | nvarchar(17) | Last update |

### 4.5 TRANPAYH — Payment Transaction Header
**28 columns** | FK → DOCINFO, ARFILE, APFILE, BRANCH

| Column | Type | Description |
|---|---|---|
| TPH_KEY | int PK | Primary key |
| TPH_DI | int FK | → DOCINFO.DI_KEY |
| TPH_AR | int FK | → ARFILE.AR_KEY (customer) |
| TPH_AP | int FK | → APFILE.AP_KEY (supplier) |
| TPH_DEPT | int | Department |
| TPH_BR | int | Branch |
| TPH_SLMN | int | Salesman |
| TPH_SHIP_DATE | date | Ship date |
| TPH_CANCEL_DATE | date | Cancel date |
| TPH_WHT_TYPE | int | WHT type |
| TPH_LASTUPD | nvarchar(17) | Last update |

### 4.6 TRANPAYD — Payment Transaction Detail
**36 columns** | FK → TRANPAYH, PAYMENTTYPE

| Column | Type | Description |
|---|---|---|
| TPD_KEY | int PK | Primary key |
| TPD_TPH | int FK | → TRANPAYH.TPH_KEY |
| TPD_PMT | int FK | → PAYMENTTYPE.PMT_KEY |
| TPD_BAHT | money | **Amount in THB** |
| TPD_CARD_NO | nvarchar(16) | Credit card number |
| TPD_CQIN_OWNER | nvarchar(120) | Cheque owner |
| TPD_CQIN_BANK | int | Cheque bank |
| TPD_CQIN_CHEQUE_NO | nvarchar(20) | Cheque number |
| TPD_CHEQUE_DD | date | Cheque date |
| TPD_CASHAC | int | Cash account |
| TPD_BNKAC | int | Bank account |
| TPD_PMT_CRNCY | nvarchar(20) | Currency code |
| TPD_PMT_XCHG | nvarchar(12) | Exchange rate |
| TPD_LASTUPD | nvarchar(17) | Last update |

### 4.7 TRANPAYA — Payment Apportion
**FK → TRANPAYH** | Allocates payment to specific AR/AP details

### 4.8 SKUMASTER — Product/SKU Master
**74 columns**

| Column | Type | Description |
|---|---|---|
| SKU_KEY | int PK | Primary key |
| SKU_CODE | nvarchar(24) | SKU code |
| SKU_NAME | nvarchar(60) | Thai name |
| SKU_E_NAME | nvarchar(120) | English name |
| SKU_BARCODE | nvarchar(24) | Barcode |
| SKU_BRN | int FK | → BRAND |
| SKU_ICCAT | int FK | → ICCAT (category) |
| SKU_ICCOLOR | int FK | → ICCOLOR |
| SKU_ICSIZE | int FK | → ICSIZE |
| SKU_ICDEPT | int FK | → ICDEPT (department) |
| SKU_S_UTQ | int FK | → UOFQTY (sell unit) |
| SKU_T_UTQ | int FK | → UOFQTY (transfer unit) |
| SKU_K_UTQ | int FK | → UOFQTY (purchase unit) |
| SKU_VAT_TY | smallint | VAT type |
| SKU_VAT | money | VAT rate |
| SKU_COST_TY | smallint | Cost type |
| SKU_STD_COST | float | Standard cost |
| SKU_STOCK | smallint | Stockable flag |
| SKU_WL | int FK | → WARELOCATION |
| SKU_ENABLE | nchar(1) | Enabled |
| SKU_P_ENABLE | nchar(1) | POS enabled |
| SKU_MIN_QTY | money | Minimum stock |
| SKU_MAX_QTY | money | Maximum stock |
| SKU_LAST_O | date | Last ordered |
| SKU_LAST_R | date | Last received |
| SKU_LAST_RCOST | float | Last received cost |
| SKU_SINCE | date | Created date |
| SKU_SPEC | nvarchar(max) | Specifications |
| SKU_REMARK | nvarchar(255) | Remarks |
| SKU_LASTUPD | nvarchar(17) | Last update |

### 4.9 GOODSMASTER — Goods/Barcode Master
**15 columns** | FK → SKUMASTER, UOFQTY

| Column | Type | Description |
|---|---|---|
| GOODS_KEY | int PK | Primary key |
| GOODS_CODE | nvarchar(24) | Barcode/code |
| GOODS_SKU | int FK | → SKUMASTER.SKU_KEY |
| GOODS_UTQ | int FK | → UOFQTY |
| GOODS_WEIGHT | money | Weight |
| GOODS_PRICE | money | Price |
| GOODS_ALIAS | nvarchar(120) | Thai alias |
| GOODS_E_ALIAS | nvarchar(120) | English alias |
| GOODS_ENABLE | nchar(1) | Enabled |

### 4.10 ARFILE — Customer Master
**31 columns**

| Column | Type | Description |
|---|---|---|
| AR_KEY | int PK | Primary key |
| AR_CODE | nvarchar(12) | Customer code (often tax ID) |
| AR_NAME | nvarchar(100) | Customer name |
| AR_ARCAT | int FK | → ARCAT |
| AR_AC | int FK | → ACCOUNTCHART |
| AR_ENABLE | nchar(1) | Enabled |
| AR_ACCESS | smallint | Access level |
| AR_SLMNCODE | nvarchar(12) | Salesman code |
| AR_ARL | int FK | → ARLINE |
| AR_ARTY | int FK | → ARTYPE |
| AR_ARG | int FK | → ARGROUP |
| AR_ARR | int FK | → ARAREA |
| AR_DEPT | int FK | → DEPTTAB |
| AR_MBCODE | nvarchar(20) | Member code |
| AR_TAG | nvarchar(120) | Tags |
| AR_LASTUPD | nvarchar(17) | Last update |

### 4.11 APFILE — Supplier Master
**21 columns**

| Column | Type | Description |
|---|---|---|
| AP_KEY | int PK | Primary key |
| AP_CODE | nvarchar(12) | Supplier code |
| AP_NAME | nvarchar(100) | Supplier name |
| AP_TAXID | nvarchar(15) | Tax ID |
| AP_APCAT | int FK | → APCAT |
| AP_AC | int FK | → ACCOUNTCHART |
| AP_BANK | int FK | → BANKFILE |
| AP_ENABLE | nchar(1) | Enabled |
| AP_LASTUPD | nvarchar(17) | Last update |

### 4.12 ACCOUNTCHART — Chart of Accounts
**15 columns** | Hierarchical (parent-child)

| Column | Type | Description |
|---|---|---|
| AC_KEY | int PK | Primary key |
| AC_CODE | nvarchar(16) | Account code (e.g., 1111010) |
| AC_THAIDESC | nvarchar(120) | Thai description |
| AC_ENGDESC | nvarchar(120) | English description |
| AC_TYPE | smallint | 1=Asset, 2=Liability, 3=Equity, 4=Revenue, 5=Expense |
| AC_PROPERTIES | int | Sub-type (301=Cash, 302=Bank, etc.) |
| AC_ENABLE | nchar(1) | Enabled |
| AC_PARENT | int | Parent account |
| AC_LEVEL | int | Tree level |

### 4.13 ACCOUNTVOUCHER + ACCOUNTJOURNAL — GL Entries

**ACCOUNTVOUCHER (4 cols):** VC_KEY, VC_DI (→DOCINFO), VC_REMARK, VC_LASTUPD

**ACCOUNTJOURNAL (13 cols):**

| Column | Type | Description |
|---|---|---|
| JR_KEY | int PK | Primary key |
| JR_VC | int FK | → ACCOUNTVOUCHER.VC_KEY |
| JR_SEQ | int | Sequence |
| JR_AC | int FK | → ACCOUNTCHART.AC_KEY |
| JR_BR | int FK | → BRANCH |
| JR_DEPT | int FK | → DEPTTAB |
| JR_PRJ | int FK | → PRJTAB |
| JR_DEBIT | money | Debit amount |
| JR_CREDIT | money | Credit amount |
| JR_A_DEBIT | money | Adjusted debit |
| JR_A_CREDIT | money | Adjusted credit |

### 4.14 VATTABLE — VAT Records
**43 columns** | FK → DOCINFO

Key fields: VAT_DI, VAT_TYPE, VAT_RATE, VAT_REF, VAT_DATE, VAT_SV (service value), VAT_VAT, VAT_SNV (non-VAT value), VAT_A_* (adjusted amounts)

### 4.15 Other Transaction Tables

| Table | Cols | FK | Description |
|---|---|---|---|
| TRANSTKJ | 11 | DI, AC, DEPT | Stock GL journal |
| TRANPAYJ | — | DI, AC, DEPT | Payment GL journal |
| TRANPAYO | — | DI | POS paid-out |
| TRANPAYI | — | DI | Payment interest |
| TRANPAYR | — | DI | Deposit refund |
| TRANPAYF | — | — | (empty) |
| TRANPAYP | — | — | (empty) |
| SKUMOVE | 15 | DI, SKU, AC, WL | SKU movement |
| SKUBALANCE | 15 | SKU, DI | Stock balance (FIFO) |
| ARDETAIL | 32 | DI, AR | AR subledger |
| APDETAIL | 46 | DI, AP | AP subledger |
| ARPAYMENT | 9 | DI, PMT | AR payments |
| APPAYMENT | 9 | DI, PMT | AP payments |
| SLDETAIL | 11 | DI, SLMN | Salesperson detail |
| CASHBOOK | 13 | DI, CASHAC | Cash book |
| BANKSTATEMENT | 16 | DI, BNKAC | Bank statement |
| WHTTABLE | 20 | DI | Withholding tax |
| AROE | 15 | DI, AR, SLMN | AR order entry |

---

## 5. Master Data Tables

### 5.1 BRANCH (6 rows)

| BR_KEY | BR_CODE | BR_THAIDESC |
|---|---|---|
| 0 | 00 | ไม่ระบุสาขา (ไม่ใช้) |
| 1 | MY00 | ตากสิน 18 (สนญ) |
| 101 | MY04 | เวสป้าสุขสวัสดิ์ |
| 102 | MY03 | เอกชัย 118 |
| 103 | MY06 | เวสป้าตากสิน |
| 104 | MY07 | เวสป้าบางโพ |

### 5.2 Other Master Tables

| Table | Rows | Description |
|---|---|---|
| SALESMAN | 63 | Salespeople |
| BRAND | 125 | Product brands (hierarchical) |
| ICCAT | 11 | Item categories |
| ICDEPT | 18 | Item departments (hierarchical) |
| ICCOLOR | 210 | Item colors |
| ICSIZE | 31 | Item sizes |
| UOFQTY | 85 | Units of measure |
| WAREHOUSE | 2 | Warehouses |
| WARELOCATION | 85 | Warehouse locations |
| WAREZONE | 11 | Warehouse zones |
| BANKFILE | 82 | Banks |
| PAYMENTTYPE | 112 | Payment methods |
| ACCOUNTCHART | 277 | Chart of accounts (hierarchical) |
| DEPTTAB | 2 | Departments |
| PRJTAB | 1 | Projects |
| COMPANYINFO | 1 | Company info |

---

## 6. Document Reference Format

```
{DocCode}{BranchCode}{YearMonth}/{Running}
  SPY    6         6906    /00008

  SPY  = ขายอะไหล่ (Doc Type)
  6    = เวสป้าตากสิน (Branch: 0=ตากสิน, 4=สุขสวัสดิ์, 6=เวสป้าตากสิน, 7=เวสป้าบางโพ)
  6906 = พ.ศ. 2569 เดือน 06
  /00008 = เลข running
```

---

## 7. DOCTYPE Reference (134 types)

### By Properties Category

| Properties | Category | Doc Codes |
|---|---|---|
| **206** | Repair | JOY0, JOY4, JOY6, JOY7 (ใบแจ้งซ่อม) |
| **207** | Parts Reservation | JPY0, JPY4, JPY6, JPY7 (ใบจองอะไหล่) |
| **303** | Receive | BMMY (รถ), BPMY (อะไหล่) |
| **304** | Return to Supplier | GMMY (รถ), GPMY (อะไหล่) |
| **307** | Sales | SMY0-7 (รถ), SPY0-7 (อะไหล่), SCY (commission), RNMY (เสร็จรับเงินรถ) |
| **308** | Sales Return | TMMY (รถ), TNMY (ดาวน์), TPMY (เคลม) |
| **309** | Internal Use | KWMY (เบิกใช้ภายใน) |
| **311** | Transfer | KMMY (รถ), KPMY, KPY4-7 (อะไหล่) |
| **332** | Count | CNT (ตรวจนับ) |
| **333** | Cost Adjustment | AJMY |
| **334** | Opening Balance | BAMY |
| **335** | Inventory Adjustment | AJI |
| **337** | Parts Return | TPY0-7, TCMY |
| **402** | AR Debit Note | DNMY |
| **403** | AR Credit Note | CNMY, CDMY (ส่วนลดโปรโมชั่น) |
| **404** | Receipt | RPY0-7 (อะไหล่), RIMY (ไฟแนนซ์), RNMY (รถ) |
| **406** | Billing | SBMY |
| **408** | Deposit In | DMMY (จองรถ), DPY0-7 (มัดจำอะไหล่) |
| **409** | Deposit Refund | CMMY (คืนจองรถ), CPY0-7 (คืนมัดจำ) |
| **501** | AP Opening | APB |
| **502** | AP Voucher | PCMY (เงินสดย่อย), PEMY (เช็ค/โอน) |
| **505** | AP Payment | PSMY |
| **507** | AP Approval | PAMY |
| **602** | Cash Deposit | BKMY |
| **604** | Cash Withdrawal | BWMY |
| **607** | Bank Transfer | BTMY |
| **701** | GL Journal | JV, ADJ |
| **704** | Cost | COST |
| **705** | Closing | CLS |
| **801-806** | Fixed Asset | OF, PF, SF, RF, DF, FIX |

---

## 8. Foreign Key Relationships (Core Chain)

```
                         DOCTYPE (DT_KEY)
                              │
                         ┌────▼────┐
                         │ DOCINFO │ ◄─── Center of ALL transactions
                         │ (DI_KEY)│
                         └────┬────┘
              ┌───────────────┼───────────────┐
              │               │               │
        ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼──────────┐
        │ TRANSTKH  │  │ TRANPAYH  │  │ ACCOUNTVOUCHER │
        │ (TRH_KEY) │  │ (TPH_KEY) │  │ (VC_KEY)       │
        │ FK→DI     │  │ FK→DI,AR  │  │ FK→DI          │
        └─────┬─────┘  │ FK→AP,BR  │  └─────┬──────────┘
              │        └─────┬─────┘        │
        ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼──────────┐
        │ TRANSTKD  │  │ TRANPAYD  │  │ ACCOUNTJOURNAL │
        │ (TRD_KEY) │  │ (TPD_KEY) │  │ (JR_KEY)       │
        │ FK→TRH    │  │ FK→TPH    │  │ FK→VC,AC       │
        │ FK→SKU    │  │ FK→PMT    │  │ FK→BR,DEPT,PRJ │
        │ FK→GOODS  │  └─────┬─────┘  └────────────────┘
        └─────┬─────┘        │
              │        ┌─────▼─────┐
        ┌─────▼─────┐  │ TRANPAYA  │
        │  SKUMOVE  │  │ (FK→TPH)  │
        │ FK→DI     │  └───────────┘
        │ FK→SKU    │
        └───────────┘

Other FK chains:
  VATTABLE    → DOCINFO (VAT_DI)
  ARPAYMENT   → DOCINFO (ARP_DI), PAYMENTTYPE
  APPAYMENT   → DOCINFO (APP_DI), PAYMENTTYPE
  ARDETAIL    → DOCINFO (ARD_DI), ARFILE
  APDETAIL    → DOCINFO (APD_DI), APFILE
  SLDETAIL    → DOCINFO (SLD_DI), SALESMAN
  CASHBOOK    → DOCINFO (CASHB_DI), CASHACCOUNT
  BANKSTATEMENT → DOCINFO (BSTM_DI), BANKACCOUNT
  WHTTABLE    → DOCINFO (WHT_DI)
  AROE        → DOCINFO (AROE_DI), ARFILE, SALESMAN

Master chains:
  SKUMASTER   → BRAND, ICCAT, ICCOLOR, ICSIZE, ICDEPT, UOFQTY(×3), WARELOCATION
  GOODSMASTER → SKUMASTER, UOFQTY
  ARFILE      → ARCAT, ACCOUNTCHART, ARGROUP, ARLINE, ARTYPE, ARAREA, DEPTTAB
  APFILE      → APCAT, ACCOUNTCHART, BANKFILE, DEPTTAB
  SKUAP       → SKUMASTER, APFILE
  ARPLU       → ARPRICETAB, GOODSMASTER
```

---

## 9. Indexes (Key Tables)

### DOCINFO
- CLUSTERED PK: DI_KEY
- IX: DI_DATE, (DI_DATE + DI_REF), DI_REF, DI_DT, (DI_ACTIVE + DI_CREATOR_DI)

### TRANSTKH
- CLUSTERED PK: TRH_KEY
- IX: TRH_DI, TRH_BR, TRH_DEPT, TRH_MKTP, TRH_PRJ, TRH_PRMT

### TRANSTKD
- CLUSTERED PK: TRD_KEY
- IX: TRD_TRH, TRD_SKU, TRD_AC, TRD_REFER_DI, TRD_REFER_TRD

### SKUMASTER
- CLUSTERED PK: SKU_KEY
- IX: SKU_BRN, SKU_ICCAT, SKU_ICCOLOR, SKU_ICDEPT, SKU_ICSIZE, SKU_SKUALT, SKU_WL, (SKU_NAME + ENABLE + ACCESS)

### SKUMOVE
- CLUSTERED PK: SKM_KEY
- IX: SKM_DI, SKM_SKU, SKM_WL, SKM_AC, (SKM_SKU + SKM_WL)

### ARFILE
- CLUSTERED PK: AR_KEY
- IX: AR_AC, AR_ARCAT, AR_ARG, AR_ARL, (AR_CODE + ENABLE + ACCESS)

### ARDETAIL / APDETAIL
- CLUSTERED PK: ARD_KEY / APD_KEY
- IX: ARD_DI, ARD_AR, (ARD_AR + ARD_DI + ARD_B_AMT)
- IX: APD_DI, APD_AP, (APD_AP + APD_DI + APD_B_AMT)

---

## 10. Observations

1. **Branch Pattern:** Doc types have branch suffix (SMY0=ตากสิน18, SMY4=เวสป้าสุขสวัสดิ์, etc.)

2. **Money type:** All monetary fields use SQL Server `money` type (19,4 precision)

3. **Audit Trail:** Every table has `*_LASTUPD` column. DOCINFO tracks CRE/UPD/DEL/PRN/EXM/APV with user + computer + login

4. **FIFO Costing:** SKUBALANCE tracks FIFO cost per SKU per document

5. **Multi-currency:** TRANPAYD supports foreign currency (TPD_PMT_CRNCY, TPD_PMT_XCHG)

6. **Hierarchical Masters:** BRAND, ACCOUNTCHART, ICDEPT, BRNLEVEL use parent-child tree (LEVEL, ABS_INDEX, PARENT, FIRSTCHILD)

7. **e-Tax Integration:** ETAXCONFIG, ETAXINTF tables support e-Tax Invoice

8. **121 Empty Tables:** Features not in use at these companies (promotions, fixed assets, loyalty, van sales, etc.)

9. **All 8 DBs identical schema:** Only data volume and temp tables differ. ETL can use the same extraction logic for all companies.

10. **No explicit foreign keys in MSSQL:** Most FK relationships are enforced at application level, not database constraints. Only some tables have actual FK constraints defined.

---

*Generated: 2026-06-08 | Source: 8 BPLUSERP databases | Container: bplus-sqlserver (Docker, SQL Server 2019 Express)*
