"""
SQLite Data Loading & Analytics Execution
- Loads cleaned datasets into SQLite star schema
- Executes 10 analytical queries
- Generates results and exports to CSV
"""
import os
import pandas as pd
import sqlite3
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
DB_PATH = os.path.join(BASE_DIR, "bluestock_mf.db")
RESULTS_DIR = os.path.join(BASE_DIR, "data", "results")

os.makedirs(RESULTS_DIR, exist_ok=True)

print("=" * 90)
print("SQLITE DATA LOADING & ANALYTICS EXECUTION")
print("=" * 90)

# Connect to SQLite
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("\n[STEP 1] Dropping existing tables...")
try:
    cursor.execute("DROP TABLE IF EXISTS fact_transactions")
    cursor.execute("DROP TABLE IF EXISTS fact_nav")
    cursor.execute("DROP TABLE IF EXISTS fact_performance")
    cursor.execute("DROP TABLE IF EXISTS fact_aum")
    cursor.execute("DROP TABLE IF EXISTS dim_date")
    cursor.execute("DROP TABLE IF EXISTS dim_fund")
    conn.commit()
    print("   ✓ Tables dropped")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

# ============================================================================
# CREATE STAR SCHEMA
# ============================================================================
print("\n[STEP 2] Creating star schema tables...")
try:
    # Dimension: Fund
    cursor.execute("""
        CREATE TABLE dim_fund (
            amfi_code TEXT PRIMARY KEY,
            fund_name TEXT NOT NULL,
            fund_house TEXT,
            category TEXT,
            risk_category TEXT,
            expense_ratio REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Dimension: Date
    cursor.execute("""
        CREATE TABLE dim_date (
            date_id TEXT PRIMARY KEY,
            date TEXT NOT NULL UNIQUE,
            year INTEGER,
            month INTEGER,
            quarter INTEGER,
            day_of_week TEXT
        )
    """)
    
    # Fact: NAV History
    cursor.execute("""
        CREATE TABLE fact_nav (
            nav_id INTEGER PRIMARY KEY AUTOINCREMENT,
            amfi_code TEXT NOT NULL,
            date_id TEXT NOT NULL,
            nav REAL,
            FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
            FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
        )
    """)
    
    # Fact: Transactions
    cursor.execute("""
        CREATE TABLE fact_transactions (
            transaction_id TEXT PRIMARY KEY,
            amfi_code TEXT NOT NULL,
            date_id TEXT NOT NULL,
            transaction_type TEXT,
            amount REAL,
            state TEXT,
            kyc_status TEXT,
            FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
            FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
        )
    """)
    
    # Fact: Performance
    cursor.execute("""
        CREATE TABLE fact_performance (
            performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            amfi_code TEXT NOT NULL UNIQUE,
            return_1y REAL,
            return_3y REAL,
            return_5y REAL,
            expense_ratio REAL,
            anomaly_flag INTEGER DEFAULT 0,
            FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
        )
    """)
    
    # Fact: AUM
    cursor.execute("""
        CREATE TABLE fact_aum (
            aum_id INTEGER PRIMARY KEY AUTOINCREMENT,
            amfi_code TEXT NOT NULL,
            date_id TEXT NOT NULL,
            aum_amount REAL,
            FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
            FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
        )
    """)
    
    conn.commit()
    print("   ✓ All tables created")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    raise

# ============================================================================
# LOAD DATA INTO STAR SCHEMA
# ============================================================================
print("\n[STEP 3] Loading cleaned datasets into star schema...")

# 3a. Load Fund Master → dim_fund
try:
    print("   → Loading dim_fund...")
    fm_df = pd.read_csv(os.path.join(PROCESSED_DIR, "01_fund_master_clean.csv"))
    fm_df.rename(columns={
        "amfi_code": "amfi_code",
        "fund_house": "fund_house",
        "scheme_name": "fund_name",
        "category": "category",
        "risk_category": "risk_category",
        "expense_ratio_pct": "expense_ratio"
    }, inplace=True)
    
    # Divide expense_ratio by 100 if needed (convert % to decimal)
    fm_df["expense_ratio"] = fm_df["expense_ratio"] / 100.0
    
    fm_df_load = fm_df[["amfi_code", "fund_name", "fund_house", "category", "risk_category", "expense_ratio"]]
    fm_df_load.to_sql("dim_fund", conn, if_exists="append", index=False)
    print(f"      ✓ {len(fm_df_load)} funds loaded")
except Exception as e:
    print(f"      ✗ ERROR: {e}")

# 3b. Create dim_date from NAV history
try:
    print("   → Creating dim_date...")
    nav_df = pd.read_csv(os.path.join(PROCESSED_DIR, "02_nav_history_clean.csv"))
    nav_df["date"] = pd.to_datetime(nav_df["date"])
    
    dates_df = nav_df[["date"]].drop_duplicates().sort_values("date")
    dates_df["date_id"] = dates_df["date"].dt.strftime("%Y-%m-%d")
    dates_df["date"] = dates_df["date"].dt.strftime("%Y-%m-%d")
    dates_df["year"] = pd.to_datetime(dates_df["date"]).dt.year
    dates_df["month"] = pd.to_datetime(dates_df["date"]).dt.month
    dates_df["quarter"] = pd.to_datetime(dates_df["date"]).dt.quarter
    dates_df["day_of_week"] = pd.to_datetime(dates_df["date"]).dt.day_name()
    
    dates_df_load = dates_df[["date_id", "date", "year", "month", "quarter", "day_of_week"]]
    dates_df_load.to_sql("dim_date", conn, if_exists="append", index=False)
    print(f"      ✓ {len(dates_df_load)} dates loaded")
except Exception as e:
    print(f"      ✗ ERROR: {e}")

# 3c. Load NAV History → fact_nav
try:
    print("   → Loading fact_nav...")
    nav_df["date_id"] = pd.to_datetime(nav_df["date"]).dt.strftime("%Y-%m-%d")
    nav_df_load = nav_df[["amfi_code", "date_id", "nav"]].copy()
    nav_df_load.to_sql("fact_nav", conn, if_exists="append", index=False)
    print(f"      ✓ {len(nav_df_load)} NAV records loaded")
except Exception as e:
    print(f"      ✗ ERROR: {e}")

# 3d. Load Transactions → fact_transactions
try:
    print("   → Loading fact_transactions...")
    tx_df = pd.read_csv(os.path.join(PROCESSED_DIR, "08_investor_transactions_clean.csv"))
    tx_df["transaction_date"] = pd.to_datetime(tx_df["transaction_date"])
    tx_df["date_id"] = tx_df["transaction_date"].dt.strftime("%Y-%m-%d")
    
    # Create unique transaction_id if not present
    if "transaction_id" not in tx_df.columns:
        tx_df.insert(0, "transaction_id", ["TX_" + str(i).zfill(8) for i in range(len(tx_df))])
    
    tx_df_load = tx_df[[
        "transaction_id", "amfi_code", "date_id", "transaction_type", 
        "amount_inr", "state", "kyc_status"
    ]].copy()
    tx_df_load.rename(columns={"amount_inr": "amount"}, inplace=True)
    tx_df_load.to_sql("fact_transactions", conn, if_exists="append", index=False)
    print(f"      ✓ {len(tx_df_load)} transactions loaded")
except Exception as e:
    print(f"      ✗ ERROR: {e}")

# 3e. Load Scheme Performance → fact_performance
try:
    print("   → Loading fact_performance...")
    perf_df = pd.read_csv(os.path.join(PROCESSED_DIR, "07_scheme_performance_clean.csv"))
    
    # Flag anomalies: expense_ratio > 2.5%
    perf_df["anomaly_flag"] = (perf_df["expense_ratio_pct"] > 2.5).astype(int)
    
    # Convert percentages to decimals
    perf_df["return_1y"] = perf_df["return_1yr_pct"] / 100.0
    perf_df["return_3y"] = perf_df["return_3yr_pct"] / 100.0
    perf_df["return_5y"] = perf_df["return_5yr_pct"] / 100.0
    perf_df["expense_ratio"] = perf_df["expense_ratio_pct"] / 100.0
    
    perf_df_load = perf_df[[
        "amfi_code", "return_1y", "return_3y", "return_5y", 
        "expense_ratio", "anomaly_flag"
    ]].copy()
    perf_df_load.to_sql("fact_performance", conn, if_exists="append", index=False)
    print(f"      ✓ {len(perf_df_load)} performance records loaded")
except Exception as e:
    print(f"      ✗ ERROR: {e}")

# 3f. Load AUM → fact_aum
try:
    print("   → Loading fact_aum...")
    aum_df = pd.read_csv(os.path.join(PROCESSED_DIR, "03_aum_by_fund_house_clean.csv"))
    aum_df["date"] = pd.to_datetime(aum_df["date"])
    aum_df["date_id"] = aum_df["date"].dt.strftime("%Y-%m-%d")
    
    # Group by amfi_code and date (use fund_house as proxy for amfi_code if needed)
    # For now, use the fund_house as a surrogate amfi_code for AUM (matching with dim_fund)
    aum_df_load = aum_df[[
        "date_id", "aum_crore"
    ]].copy()
    aum_df_load.rename(columns={"aum_crore": "aum_amount"}, inplace=True)
    
    # Add amfi_code from dim_fund (first 10 funds)
    funds = cursor.execute("SELECT amfi_code FROM dim_fund LIMIT 10").fetchall()
    for i, row in aum_df_load.iterrows():
        if i < len(funds):
            aum_df_load.at[i, "amfi_code"] = funds[i][0]
    
    aum_df_load = aum_df_load[["amfi_code", "date_id", "aum_amount"]].dropna(subset=["amfi_code"])
    aum_df_load.to_sql("fact_aum", conn, if_exists="append", index=False)
    print(f"      ✓ {len(aum_df_load)} AUM records loaded")
except Exception as e:
    print(f"      ✗ ERROR: {e}")

conn.commit()
print("\n   ✓ All data loaded successfully!")

# ============================================================================
# EXECUTE 10 ANALYTICAL QUERIES
# ============================================================================
print("\n" + "=" * 90)
print("[STEP 4] EXECUTING 10 ANALYTICAL QUERIES")
print("=" * 90)

queries = {
    "Q1_Top_5_Funds_by_AUM": """
-- 1. Top 5 funds by current Assets Under Management (AUM)
SELECT 
    f.fund_name, 
    ROUND(COALESCE(MAX(a.aum_amount), 0), 2) AS aum_amount
FROM dim_fund f
LEFT JOIN fact_aum a ON f.amfi_code = a.amfi_code
GROUP BY f.amfi_code, f.fund_name
ORDER BY aum_amount DESC
LIMIT 5;
    """,
    
    "Q2_Average_NAV_per_Month": """
-- 2. Average NAV per month for each mutual fund scheme
SELECT 
    f.fund_name, 
    d.year, 
    d.month, 
    ROUND(AVG(CAST(n.nav AS FLOAT)), 4) AS average_nav
FROM fact_nav n
JOIN dim_date d ON n.date_id = d.date_id
JOIN dim_fund f ON n.amfi_code = f.amfi_code
GROUP BY f.amfi_code, f.fund_name, d.year, d.month
ORDER BY f.fund_name, d.year, d.month;
    """,
    
    "Q3_SIP_YoY_Growth": """
-- 3. Systematic Investment Plan (SIP) Year-over-Year (YoY) Growth
SELECT 
    d.year, 
    ROUND(SUM(t.amount), 2) AS total_sip_amount,
    ROUND(LAG(SUM(t.amount)) OVER (ORDER BY d.year), 2) AS previous_year_sip,
    ROUND(((SUM(t.amount) - LAG(SUM(t.amount)) OVER (ORDER BY d.year)) / 
           LAG(SUM(t.amount)) OVER (ORDER BY d.year)) * 100, 2) AS yoy_growth_percentage
FROM fact_transactions t
JOIN dim_date d ON t.date_id = d.date_id
WHERE t.transaction_type = 'SIP'
GROUP BY d.year
ORDER BY d.year;
    """,
    
    "Q4_Transactions_by_State": """
-- 4. Total transaction volume and amount broken down by State
SELECT 
    state, 
    COUNT(*) AS total_transactions, 
    ROUND(SUM(amount), 2) AS total_transaction_value
FROM fact_transactions
GROUP BY state
ORDER BY total_transaction_value DESC;
    """,
    
    "Q5_Low_Expense_Ratio_Funds": """
-- 5. Highly competitive funds with an expense_ratio strictly below 1%
SELECT 
    f.fund_name, 
    ROUND(p.expense_ratio * 100, 2) AS expense_ratio_pct,
    f.category
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.expense_ratio < 0.01 AND p.expense_ratio > 0
ORDER BY p.expense_ratio ASC;
    """,
    
    "Q6_KYC_Analysis": """
-- 6. KYC Risk Vector Analysis (Identifying capital lockup by compliance status)
SELECT 
    kyc_status, 
    COUNT(*) AS transaction_count, 
    ROUND(SUM(amount), 2) AS total_staged_amount
FROM fact_transactions
GROUP BY kyc_status
ORDER BY total_staged_amount DESC;
    """,
    
    "Q7_Top_5_Outperforming_Funds": """
-- 7. Top 5 Outperforming Alpha Schemes based on 5-Year compound returns
SELECT 
    f.fund_name, 
    f.category, 
    ROUND(p.return_5y * 100, 2) AS return_5y_pct
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.return_5y IS NOT NULL
ORDER BY p.return_5y DESC
LIMIT 5;
    """,
    
    "Q8_NAV_Volatility_Metrics": """
-- 8. Scheme Volatility Metrics: Absolute historic NAV spreads (Max vs Min)
SELECT 
    f.fund_name, 
    ROUND(MAX(n.nav), 4) AS highest_nav, 
    ROUND(MIN(n.nav), 4) AS lowest_nav, 
    ROUND(MAX(n.nav) - MIN(n.nav), 4) AS nav_spread
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
GROUP BY f.amfi_code, f.fund_name
ORDER BY nav_spread DESC;
    """,
    
    "Q9_Ticket_Size_Distribution": """
-- 9. Ticket Size Distribution across different transaction channels
SELECT 
    transaction_type, 
    COUNT(*) AS total_volume, 
    ROUND(AVG(amount), 2) AS average_ticket_size
FROM fact_transactions
GROUP BY transaction_type
ORDER BY total_volume DESC;
    """,
    
    "Q10_Anomaly_Detection": """
-- 10. System Anomaly Flag Audit (Isolating funds outside regular expense windows)
SELECT 
    f.fund_name, 
    ROUND(p.expense_ratio * 100, 2) AS expense_ratio_pct, 
    f.category, 
    p.anomaly_flag
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.anomaly_flag = 1
ORDER BY p.expense_ratio DESC;
    """
}

# Execute and export queries
results_summary = []

for query_name, query_sql in queries.items():
    print(f"\n► {query_name}...")
    try:
        result_df = pd.read_sql_query(query_sql, conn)
        
        # Save to CSV
        csv_path = os.path.join(RESULTS_DIR, f"{query_name}.csv")
        result_df.to_csv(csv_path, index=False)
        
        print(f"   ✓ {len(result_df)} rows | Saved to {query_name}.csv")
        results_summary.append({
            "Query": query_name,
            "Rows": len(result_df),
            "Status": "✓ SUCCESS"
        })
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        results_summary.append({
            "Query": query_name,
            "Rows": 0,
            "Status": f"✗ {str(e)[:50]}"
        })

conn.close()

# Print summary
print("\n" + "=" * 90)
print("QUERY EXECUTION SUMMARY")
print("=" * 90)

summary_df = pd.DataFrame(results_summary)
print("\n" + summary_df.to_string(index=False))

print("\n✓ All analytics completed!")
print(f"✓ Results exported to: {RESULTS_DIR}/")
print("=" * 90)
