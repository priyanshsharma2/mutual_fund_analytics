# Mutual Fund Analytics - Data Cleaning Report

**Report Generated:** 2025-06-03  
**Status:**  **ALL 10 DATASETS CLEANED SUCCESSFULLY**

---

## Executive Summary

All 10 CSV datasets have been cleaned, validated, and prepared for analytics. A total of **87,532 rows** across all datasets have been processed with comprehensive data validation.

---

## Detailed Cleaning Summary

| # | Dataset | Raw Rows | Cleaned Rows | Key Validations |
|---|---------|----------|--------------|-----------------|
| 1 | 01_fund_master.csv | - | **40** | ✓ AMFI codes deduplicated, expense_ratio 0-3%, launch_date parsed |
| 2 | 02_nav_history.csv | - | **46,000** | ✓ Dates parsed, NAV forward-filled (holidays/weekends), NAV > 0, duplicates removed |
| 3 | 03_aum_by_fund_house.csv | - | **90** | ✓ AUM values validated > 0, fund house names standardized, date deduped |
| 4 | 04_monthly_sip_inflows.csv | - | **48** | ✓ Months (YYYY-MM) parsed, numeric columns validated, YoY growth preserved |
| 5 | 05_category_inflows.csv | - | **144** | ✓ Category names standardized, net_inflow converted to numeric, duplicates removed |
| 6 | 06_industry_folio_count.csv | - | **20** | ✓ Folio counts validated, breakdown totals ≤ total folios, dates parsed |
| 7 | 07_scheme_performance.csv | - | **40** | ✓ Returns validated (-100% to +500%), expense_ratio 0-3%, ratings 1-5 |
| 8 | 08_investor_transactions.csv | - | **32,778** | ✓ Amounts > 0, transaction_type standardized (SIP/Lumpsum/Redemption), KYC enum validated |
| 9 | 09_portfolio_holdings.csv | - | **322** | ✓ Portfolio weights 0-100%, prices > 0, stock symbols standardized, dates parsed |
| 10 | 10_benchmark_indices.csv | - | **8,050** | ✓ Close values > 0, index names standardized (NIFTY50, etc), dates parsed |
| | **TOTAL** | | **87,532** | ✓ All rows validated and deduplicated |

---

## Data Cleaning Operations Applied

### 1. **Fund Master (01_fund_master.csv)**
- Parsed `launch_date` to datetime format
- Converted and validated `expense_ratio_pct` (0.0 - 3.0%)
- Standardized fund house and scheme names (trim, strip)
- Removed duplicate AMFI codes (kept first occurrence)
- **Output:** 40 unique funds

### 2. **NAV History (02_nav_history.csv)**
- Parsed `date` to datetime
- Converted NAV to numeric (coerced errors to NaN)
- Sorted by `amfi_code` and `date`
- **Forward-filled missing NAV values** for weekends/holidays (per fund)
- Removed duplicate amfi_code+date combinations
- Filtered `nav > 0` (removed invalid/negative values)
- **Output:** 46,000 clean NAV records

### 3. **AUM by Fund House (03_aum_by_fund_house.csv)**
- Parsed `date` to datetime
- Converted AUM values to numeric (crore, lakh_crore, num_schemes)
- Validated `aum_crore > 0` and `num_schemes > 0`
- Standardized fund house names
- Removed duplicate date+fund_house combinations
- **Output:** 90 unique fund house AUM snapshots

### 4. **Monthly SIP Inflows (04_monthly_sip_inflows.csv)**
- Parsed `month` in YYYY-MM format to datetime
- Converted all numeric columns (sip_inflow_crore, accounts, growth_pct)
- Filled missing YoY growth with 0.0
- Removed duplicate months
- **Output:** 48 monthly SIP records

### 5. **Category Inflows (05_category_inflows.csv)**
- Parsed `month` to datetime
- Standardized category names (trim whitespace)
- Converted net_inflow to numeric
- Removed duplicate month+category combinations
- **Output:** 144 category inflow records

### 6. **Industry Folio Count (06_industry_folio_count.csv)**
- Parsed `month` to datetime
- Converted folio counts to numeric
- **Validated:** `equity + debt + hybrid + others ≤ total_folios` (allows 0.01 rounding error)
- Removed duplicate months
- **Output:** 20 validated monthly folio records

### 7. **Scheme Performance (07_scheme_performance.csv)**
- Converted all return columns to numeric (1yr, 3yr, 5yr, benchmark)
- Validated returns within -100% to +500% range
- Converted and validated expense_ratio (0.0 - 3.0%)
- Converted alpha, beta, Sharpe/Sortino ratios to numeric
- Standardized scheme name, fund house, and category
- Removed duplicate AMFI codes
- **Output:** 40 schemes with performance metrics

### 8. **Investor Transactions (08_investor_transactions.csv)**
- Parsed `transaction_date` to datetime
- **Standardized transaction_type:** SIP → SIP, Lumpsum → Lumpsum, Redemption → Redemption
- Converted `amount_inr` to numeric, filtered `amount > 0`
- Standardized state, city, tier names
- **Validated KYC status enum:** VERIFIED, PENDING, REJECTED (case-insensitive)
- Parsed age_group, gender, income to numeric where applicable
- Removed invalid records
- **Output:** 32,778 clean transactions

### 9. **Portfolio Holdings (09_portfolio_holdings.csv)**
- Parsed `portfolio_date` to datetime
- Converted weights, market values, prices to numeric
- **Validated weights:** 0% ≤ weight ≤ 100%
- Validated `market_value_cr > 0` and `current_price_inr > 0`
- Standardized stock symbols (uppercase), stock names, sectors
- Removed duplicate amfi_code+portfolio_date+stock_symbol combinations
- **Output:** 322 holdings records

### 10. **Benchmark Indices (10_benchmark_indices.csv)**
- Parsed `date` to datetime
- Converted `close_value` to numeric
- **Validated:** close_value > 0
- Standardized index names (uppercase: NIFTY50, NIFTY200, etc.)
- Sorted by index_name and date
- Removed duplicate index+date combinations
- **Output:** 8,050 clean index records

---

## Data Quality Checks Performed

 **Type Conversion:** All columns converted to appropriate types (datetime, numeric, string)  
 **Range Validation:** Expense ratios, weights, returns within realistic ranges  
 **Enum Validation:** Transaction types, KYC status, city tiers standardized  
 **Null Handling:** Missing dates removed, NAV forward-filled, amounts forward-filled  
 **Duplicate Removal:** By primary keys (amfi_code, date, investor_id)  
 **Outlier Filtering:** Negative NAVs, invalid prices, impossible returns removed  
 **Consistency Checks:** Portfolio breakdown validated against totals  
 **Text Standardization:** Trimmed whitespace, consistent case for keys

---

## Output Files

All cleaned datasets saved to: **`data/processed/`**

```
data/processed/
├── 01_fund_master_clean.csv              (6.7 KB)
├── 02_nav_history_clean.csv              (1,235.91 KB)
├── 03_aum_by_fund_house_clean.csv        (4.01 KB)
├── 04_monthly_sip_inflows_clean.csv      (1.85 KB)
├── 05_category_inflows_clean.csv         (4.15 KB)
├── 06_industry_folio_count_clean.csv     (0.85 KB)
├── 07_scheme_performance_clean.csv       (6.48 KB)
├── 08_investor_transactions_clean.csv    (3,086.62 KB)
├── 09_portfolio_holdings_clean.csv       (23.66 KB)
└── 10_benchmark_indices_clean.csv        (252.96 KB)
                                          ─────────────
                                          4,621.54 KB total
```

---

## Issues Addressed

| Issue | Resolution |
|-------|-----------|
| Missing NAV for weekends/holidays | Forward-filled by fund within groups |
| Inconsistent transaction types | Mapped to standardized enum (SIP/Lumpsum/Redemption) |
| Invalid KYC status values | Filtered to valid enum (VERIFIED, PENDING, REJECTED) |
| Out-of-range expense ratios | Kept 0-3% range (industry standard 0.1-2.5% + buffer) |
| Negative prices/NAVs | Removed entirely |
| Duplicate fund entries | Kept first occurrence, removed rest |
| Inconsistent date formats | All converted to YYYY-MM-DD format |
| Missing numeric conversions | Coerced to numeric with error handling |
| Portfolio weight inconsistencies | Validated breakdown ≤ total |

---

## Next Steps

1.  **Data Cleaning:** Complete (all 10 datasets cleaned)
2.  **SQLite Loading:** Complete (user confirmed successful)
3.  **SQL Query Conversion:** Convert queries from SQL Server → SQLite syntax
4.  **Analytics:** Run 10 queries for insights
5.  **Documentation:** Finalize data dictionary

---

## Script Reference

- **Cleaning Script:** `clean_all_datasets.py`
- **Database:** `bluestock_mf.db` (SQLite)
- **Schema:** `schema.sql`
- **Queries:** `queries.sql`

---

**Status:**  **READY FOR ANALYTICS**
