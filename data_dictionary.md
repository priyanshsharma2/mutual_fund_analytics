# Data Dictionary — Mutual Fund Analytics Schema

## 1. Dimension Tables

### `dim_fund`
Stores metadata and catalog references for all tracked mutual fund schemes.
* **amfi_code** (INTEGER, Primary Key): Unique identifier issued by the Association of Mutual Funds in India.
* **fund_name** (TEXT): Registered marketing and regulatory name of the scheme.
* **category** (TEXT): Asset class division (e.g., Equity Small Cap, Debt, Hybrid).
* **risk_level** (TEXT): Riskometer classification assigned to the fund.

### `dim_date`
Time dimension table optimized for temporal slicing and aggregation.
* **date_id** (TEXT, Primary Key): Surrogate text key structured as `YYYYMMDD`.
* **date** (DATE): Unique date format record.
* **year** (INTEGER): Calendar year digit.
* **month** (INTEGER): Calendar month digit (1 to 12).
* **quarter** (INTEGER): Business quarter value (1 to 4).
* **day_of_week** (TEXT): Plain string day representation (e.g., Monday).

---

## 2. Fact Tables

### `fact_nav`
Captures daily net asset values per scheme.
* **nav_id** (INTEGER, Primary Key Auto-Increment): Internal tracker identifier.
* **amfi_code** (INTEGER, Foreign Key -> `dim_fund`): Target scheme relation link.
* **date_id** (TEXT, Foreign Key -> `dim_date`): Transaction/Holiday date map identifier.
* **nav** (REAL): Net Asset Value per unit. Validated strictly to be greater than 0.

### `fact_transactions`
Logs actual investor operations within the platform ecosystems.
* **transaction_id** (INTEGER, Primary Key): Direct unique reference transaction key.
* **amfi_code** (INTEGER, Foreign Key -> `dim_fund`): Target fund scheme.
* **date_id** (TEXT, Foreign Key -> `dim_date`): Date of settlement.
* **investor_id** (INTEGER): Unique internal reference identifier for the specific client.
* **transaction_type** (TEXT): Validated and mapped to strict options: `SIP`, `Lumpsum`, or `Redemption`.
* **amount** (REAL): Validated financial capital amount processed (> 0).
* **state** (TEXT): Geographic state identifier tracking transaction origination.
* **kyc_status** (TEXT): Client regulatory compliance status code.

### `fact_performance`
Tracks annual historical returns data metrics.
* **performance_id** (INTEGER, Primary Key Auto-Increment): Record key identifier.
* **amfi_code** (INTEGER, Foreign Key -> `dim_fund`): Target scheme identification.
* **return_1y / return_3y / return_5y** (REAL): Historic percentage performance tracking.
* **expense_ratio** (REAL): Underlying fund maintenance charges representation.
* **anomaly_flag** (INTEGER): System warning flag indicating if `expense_ratio` lies outside standard bounds ($0.1\%$ – $2.5\%$).
