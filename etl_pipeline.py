import os
import urllib.parse
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
RAW_DIR_CANDIDATES = [
    os.path.join(BASE_DIR, "raw_data"),
    os.path.join(BASE_DIR, "data", "raw"),
    os.path.join(BASE_DIR, "mutual_fund_analytics", "data", "raw", "raw_data"),
]
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
SQLITE_DB_PATH = os.path.join(BASE_DIR, "bluestock_mf.db")
DB_TYPE = os.environ.get("ETL_DB_TYPE", "sqlite").lower()
MSSQL_HOST = os.environ.get("ETL_MSSQL_HOST", "localhost")
MSSQL_PORT = os.environ.get("ETL_MSSQL_PORT", "1433")
MSSQL_DATABASE = os.environ.get("ETL_MSSQL_DATABASE", "master")
MSSQL_USER = os.environ.get("ETL_MSSQL_USER", "")
MSSQL_PASSWORD = os.environ.get("ETL_MSSQL_PASSWORD", "")
MSSQL_DRIVER = os.environ.get("ETL_MSSQL_DRIVER", "ODBC Driver 18 for SQL Server")
MSSQL_TRUSTED_CONNECTION = os.environ.get("ETL_MSSQL_TRUSTED_CONNECTION", "yes").lower()

os.makedirs(PROCESSED_DIR, exist_ok=True)


def resolve_raw_dir():
    for path in RAW_DIR_CANDIDATES:
        if os.path.isdir(path):
            return path
    raise FileNotFoundError(
        "Could not find raw data directory. Create one of: " + ", ".join(RAW_DIR_CANDIDATES)
    )


def resolve_raw_file(raw_dir, candidates):
    for candidate in candidates:
        path = os.path.join(raw_dir, candidate)
        if os.path.isfile(path):
            return path
    raise FileNotFoundError(f"Could not find any of: {candidates} in {raw_dir}")


def normalize_performance_columns(df):
    rename_map = {}
    for col in df.columns:
        lc = col.lower().strip()
        if lc in ("return_1yr_pct", "return_1yr", "return_1y", "return_1y_pct"):
            rename_map[col] = "return_1y"
        elif lc in ("return_3yr_pct", "return_3yr", "return_3y", "return_3y_pct"):
            rename_map[col] = "return_3y"
        elif lc in ("return_5yr_pct", "return_5yr", "return_5y", "return_5y_pct"):
            rename_map[col] = "return_5y"
        elif lc == "expense_ratio_pct":
            rename_map[col] = "expense_ratio_pct"
        elif lc == "expense_ratio":
            rename_map[col] = "expense_ratio"
    df = df.rename(columns=rename_map)
    if "return_1y" in df.columns:
        df["return_1y"] = pd.to_numeric(df["return_1y"], errors="coerce") / 100.0
    if "return_3y" in df.columns:
        df["return_3y"] = pd.to_numeric(df["return_3y"], errors="coerce") / 100.0
    if "return_5y" in df.columns:
        df["return_5y"] = pd.to_numeric(df["return_5y"], errors="coerce") / 100.0
    if "expense_ratio_pct" in df.columns:
        df["expense_ratio"] = pd.to_numeric(df["expense_ratio_pct"], errors="coerce") / 100.0
    elif "expense_ratio" in df.columns:
        df["expense_ratio"] = pd.to_numeric(df["expense_ratio"], errors="coerce")
    else:
        df["expense_ratio"] = np.nan
    return df


RAW_DIR = resolve_raw_dir()
print("Using RAW_DIR:", RAW_DIR)

print("--- Step 1, 2, 3: Data Cleaning ---")

# 1. Clean nav_history.csv
try:
    nav_path = resolve_raw_file(RAW_DIR, ["02_nav_history.csv", "nav_history.csv"])
    nav_df = pd.read_csv(nav_path)
    nav_df["date"] = pd.to_datetime(nav_df["date"], errors="coerce")
    nav_df = nav_df.sort_values(by=["amfi_code", "date"]).drop_duplicates()
    nav_df["nav"] = nav_df.groupby("amfi_code")["nav"].ffill().bfill()
    nav_df = nav_df[nav_df["nav"] > 0]
    nav_df.to_csv(os.path.join(PROCESSED_DIR, "nav_history_clean.csv"), index=False)
    print("OK nav_history.csv cleaned successfully.")
except Exception as e:
    print(f"ERROR cleaning nav_history: {e}")
    raise

# 2. Clean investor_transactions.csv
try:
    tx_path = resolve_raw_file(RAW_DIR, ["08_investor_transactions.csv", "investor_transactions.csv"])
    tx_df = pd.read_csv(tx_path)
    tx_df["transaction_date"] = pd.to_datetime(tx_df["transaction_date"], errors="coerce")
    tx_df["transaction_type"] = tx_df["transaction_type"].astype(str).str.strip().str.capitalize()
    type_mapping = {"Sip": "SIP", "Lumpsum": "Lumpsum", "Redemption": "Redemption"}
    tx_df["transaction_type"] = tx_df["transaction_type"].map(type_mapping).fillna("Other")
    amount_col = next((c for c in ["amount", "amount_inr", "amt"] if c in tx_df.columns), None)
    if amount_col is None:
        raise ValueError("Could not find amount column in investor transactions file")
    tx_df["amount"] = pd.to_numeric(tx_df[amount_col], errors="coerce")
    tx_df = tx_df[tx_df["amount"] > 0]
    tx_df["kyc_status"] = tx_df["kyc_status"].astype(str).str.upper().str.strip()
    tx_df.to_csv(os.path.join(PROCESSED_DIR, "investor_transactions_clean.csv"), index=False)
    print("OK investor_transactions.csv cleaned successfully.")
except Exception as e:
    print(f"ERROR cleaning investor_transactions: {e}")
    raise

# 3. Clean scheme_performance.csv
try:
    perf_path = resolve_raw_file(RAW_DIR, ["07_scheme_performance.csv", "scheme_performance.csv"])
    perf_df = pd.read_csv(perf_path)
    perf_df = normalize_performance_columns(perf_df)
    for col in ["return_1y", "return_3y", "return_5y"]:
        if col not in perf_df.columns:
            perf_df[col] = 0.0
        else:
            perf_df[col] = perf_df[col].fillna(0.0)
    perf_df["expense_ratio"] = perf_df["expense_ratio"].fillna(0.0)
    perf_df.to_csv(os.path.join(PROCESSED_DIR, "scheme_performance_clean.csv"), index=False)
    print("OK scheme_performance.csv cleaned successfully.")
except Exception as e:
    print(f"ERROR cleaning scheme_performance: {e}")
    raise

print("\n--- Step 4: Creating Star Schema Tables ---")

schema_sql = """
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code INTEGER PRIMARY KEY,
    fund_name TEXT NOT NULL,
    category TEXT,
    risk_level TEXT
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_id TEXT PRIMARY KEY,
    date DATE,
    year INTEGER,
    month INTEGER,
    quarter INTEGER,
    day_of_week TEXT
);

CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER,
    date_id TEXT,
    nav REAL,
    FOREIGN KEY(amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY(date_id) REFERENCES dim_date(date_id)
);

CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER,
    date_id TEXT,
    investor_id TEXT,
    transaction_type TEXT,
    amount REAL,
    state TEXT,
    kyc_status TEXT,
    FOREIGN KEY(amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY(date_id) REFERENCES dim_date(date_id)
);

CREATE TABLE IF NOT EXISTS fact_performance (
    performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER,
    return_1y REAL,
    return_3y REAL,
    return_5y REAL,
    expense_ratio REAL,
    anomaly_flag INTEGER,
    FOREIGN KEY(amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER,
    date_id TEXT,
    aum_amount REAL,
    FOREIGN KEY(amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY(date_id) REFERENCES dim_date(date_id)
);
"""

def get_engine():
    if DB_TYPE == "mssql":
        if MSSQL_DATABASE.lower().endswith(".db"):
            raise ValueError(
                "MSSQL database name should not be a SQLite file name. "
                "Use the actual SQL Server database name."
            )

        driver = urllib.parse.quote_plus(MSSQL_DRIVER)
        server = MSSQL_HOST
        if "\\" in MSSQL_HOST and MSSQL_PORT:
            # Named instances do not use port in the server string.
            server = MSSQL_HOST
        elif MSSQL_PORT:
            server = f"{MSSQL_HOST},{MSSQL_PORT}"

        if MSSQL_TRUSTED_CONNECTION in ("1", "true", "yes", "y"):
            conn_str = (
                f"mssql+pyodbc://@{server}/{MSSQL_DATABASE}"
                f"?driver={driver}&trusted_connection=yes"
            )
        else:
            user = urllib.parse.quote_plus(MSSQL_USER)
            password = urllib.parse.quote_plus(MSSQL_PASSWORD)
            conn_str = (
                f"mssql+pyodbc://{user}:{password}@{server}/{MSSQL_DATABASE}"
                f"?driver={driver}"
            )
        print("Using SQL Server connection:", conn_str)
        return create_engine(conn_str)

    print("Using SQLite database:", SQLITE_DB_PATH)
    return create_engine(f"sqlite:///{SQLITE_DB_PATH}")

engine = get_engine()
with engine.connect() as conn:
    if DB_TYPE == "sqlite":
        conn.execute(text("PRAGMA foreign_keys = ON;"))
    for statement in schema_sql.strip().split(";"):
        if statement.strip():
            conn.execute(text(statement))
print("OK Star Schema tables generated safely.")

print("\n--- Step 5: Loading Data via SQLAlchemy ---")

# Load dim_date from cleaned NAV and transaction dates
combined_dates = pd.concat([nav_df["date"], tx_df["transaction_date"]], ignore_index=True)
combined_dates = pd.to_datetime(combined_dates.dropna().unique())
dim_date_df = pd.DataFrame({"date": combined_dates})
dim_date_df["date_id"] = dim_date_df["date"].dt.strftime("%Y%m%d")
dim_date_df["year"] = dim_date_df["date"].dt.year
dim_date_df["month"] = dim_date_df["date"].dt.month
dim_date_df["quarter"] = dim_date_df["date"].dt.quarter
dim_date_df["day_of_week"] = dim_date_df["date"].dt.day_name()
dim_date_df = dim_date_df.drop_duplicates(subset=["date_id"])

# Load dim_fund from raw fund master if available
try:
    fund_master_path = resolve_raw_file(RAW_DIR, ["01_fund_master.csv", "fund_master.csv"])
    fund_master_df = pd.read_csv(fund_master_path)
    fund_master_df = fund_master_df.rename(columns={col: col.lower().strip() for col in fund_master_df.columns})
    fund_master_df["fund_name"] = fund_master_df.get("scheme_name", fund_master_df.get("fund_name", "Unknown"))
    fund_master_df["category"] = fund_master_df.get("category", None)
    fund_master_df["risk_level"] = fund_master_df.get("risk_category", fund_master_df.get("risk_level", None))
    fund_master_df = fund_master_df[["amfi_code", "fund_name", "category", "risk_level"]].drop_duplicates(subset=["amfi_code"])
except FileNotFoundError:
    fund_master_df = pd.DataFrame(columns=["amfi_code", "fund_name", "category", "risk_level"])

with engine.begin() as conn:
    # If the script is rerun, reload the current dataset cleanly.
    conn.execute(text("PRAGMA foreign_keys = OFF;"))
    conn.execute(text("DELETE FROM fact_performance"))
    conn.execute(text("DELETE FROM fact_transactions"))
    conn.execute(text("DELETE FROM fact_nav"))
    conn.execute(text("DELETE FROM dim_date"))
    conn.execute(text("DELETE FROM dim_fund"))
    conn.execute(text("PRAGMA foreign_keys = ON;"))

    dim_date_df.to_sql("dim_date", conn, if_exists="append", index=False)
    if not fund_master_df.empty:
        fund_master_df.to_sql("dim_fund", conn, if_exists="append", index=False)

    nav_insert = nav_df[["amfi_code", "date", "nav"]].copy()
    nav_insert["date_id"] = nav_insert["date"].dt.strftime("%Y%m%d")
    nav_insert = nav_insert[["amfi_code", "date_id", "nav"]].drop_duplicates(subset=["amfi_code", "date_id"])
    nav_insert.to_sql("fact_nav", conn, if_exists="append", index=False)

    tx_insert = tx_df.copy()
    tx_insert["date_id"] = tx_insert["transaction_date"].dt.strftime("%Y%m%d")
    tx_columns = [
        c for c in ["amfi_code", "date_id", "investor_id", "transaction_type", "amount", "state", "kyc_status"]
        if c in tx_insert.columns
    ]
    tx_insert[tx_columns].drop_duplicates().to_sql("fact_transactions", conn, if_exists="append", index=False)

    perf_insert = perf_df.copy()
    for col in ["amfi_code", "return_1y", "return_3y", "return_5y", "expense_ratio", "anomaly_flag"]:
        if col not in perf_insert.columns:
            perf_insert[col] = 0.0
    perf_insert[["amfi_code", "return_1y", "return_3y", "return_5y", "expense_ratio", "anomaly_flag"]].drop_duplicates(subset=["amfi_code"]).to_sql(
        "fact_performance",
        conn,
        if_exists="append",
        index=False,
    )

print("OK Completion: Cleaned data has been loaded into SQLite.")
