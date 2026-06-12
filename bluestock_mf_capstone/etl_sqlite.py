import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR_CANDIDATES = [
    os.path.join(BASE_DIR, "raw_data"),
    os.path.join(BASE_DIR, "data", "raw"),
    os.path.join(BASE_DIR, "mutual_fund_analytics", "data", "raw", "raw_data"),
]
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
DB_PATH = os.path.join(BASE_DIR, "bluestock_mf.db")

os.makedirs(PROCESSED_DIR, exist_ok=True)


def resolve_raw_dir():
    for path in RAW_DIR_CANDIDATES:
        if os.path.isdir(path):
            return path
    raise FileNotFoundError(
        "Could not find a raw data directory. Expected one of: " + ", ".join(RAW_DIR_CANDIDATES)
    )


def resolve_raw_file(raw_dir, candidates):
    for candidate in candidates:
        path = os.path.join(raw_dir, candidate)
        if os.path.isfile(path):
            return path
    raise FileNotFoundError(f"Missing required raw file. Tried: {candidates}")


def normalize_return_columns(df):
    lowered = {col.lower(): col for col in df.columns}
    mapping = {}
    for target, variants in {
        "return_1y": ["return_1y", "1y_return", "return_1yr", "return_1_year"],
        "return_3y": ["return_3y", "3y_return", "return_3yr", "return_3_year"],
        "return_5y": ["return_5y", "5y_return", "return_5yr", "return_5_year"],
    }.items():
        for variant in variants:
            if variant in lowered:
                mapping[lowered[variant]] = target
                break
    return df.rename(columns=mapping)


def generate_dim_date(all_dates):
    unique_dates = pd.to_datetime(all_dates.dropna().unique())
    dim_date = pd.DataFrame({"date": unique_dates})
    dim_date["date_id"] = dim_date["date"].dt.strftime("%Y%m%d")
    dim_date["year"] = dim_date["date"].dt.year
    dim_date["month"] = dim_date["date"].dt.month
    dim_date["quarter"] = dim_date["date"].dt.quarter
    dim_date["day_of_week"] = dim_date["date"].dt.day_name()
    return dim_date.drop_duplicates(subset=["date_id"])


def get_fund_master(raw_dir):
    candidates = ["01_fund_master.csv", "fund_master.csv"]
    try:
        fund_master_path = resolve_raw_file(raw_dir, candidates)
        fund_master = pd.read_csv(fund_master_path)
        fund_master = fund_master.rename(
            columns={
                col: col.lower().strip()
                for col in fund_master.columns
            }
        )
        if "amfi_code" not in fund_master.columns:
            raise ValueError("fund_master source must contain an amfi_code column")

        fund_master["fund_name"] = fund_master.get("scheme_name", fund_master.get("fund_name", "Unknown"))
        fund_master["category"] = fund_master.get("category", None)
        fund_master["risk_level"] = fund_master.get("risk_category", fund_master.get("risk_level", None))
        return fund_master[["amfi_code", "fund_name", "category", "risk_level"]].drop_duplicates(subset=["amfi_code"])
    except FileNotFoundError:
        return pd.DataFrame(columns=["amfi_code", "fund_name", "category", "risk_level"])


def main():
    raw_dir = resolve_raw_dir()
    print("Raw data directory:", raw_dir)
    engine = create_engine(f"sqlite:///{DB_PATH}")

    print("--- Step 1, 2, 3: Data Cleaning ---")

    # 1. Clean nav_history.csv
    try:
        nav_path = resolve_raw_file(raw_dir, ["02_nav_history.csv", "nav_history.csv"])
        nav_df = pd.read_csv(nav_path)
        nav_df["date"] = pd.to_datetime(nav_df["date"], errors="coerce")
        nav_df = nav_df.sort_values(by=["amfi_code", "date"]).drop_duplicates()
        nav_df["nav"] = nav_df.groupby("amfi_code")["nav"].ffill().bfill()
        nav_df = nav_df[nav_df["nav"] > 0]
        nav_df.to_csv(os.path.join(PROCESSED_DIR, "nav_history_clean.csv"), index=False)
        print("OK nav_history.csv cleaned successfully.")
    except Exception as e:
        print(f"ERROR cleaning nav_history: {e}")
        return

    # 2. Clean investor_transactions.csv
    try:
        tx_path = resolve_raw_file(raw_dir, ["08_investor_transactions.csv", "investor_transactions.csv"])
        tx_df = pd.read_csv(tx_path)
        tx_df["transaction_date"] = pd.to_datetime(tx_df["transaction_date"], errors="coerce")
        tx_df["transaction_type"] = tx_df["transaction_type"].astype(str).str.strip().str.capitalize()
        type_mapping = {"Sip": "SIP", "Lumpsum": "Lumpsum", "Redemption": "Redemption"}
        tx_df["transaction_type"] = tx_df["transaction_type"].map(type_mapping).fillna("Other")

        amount_col = None
        for candidate in ["amount", "amount_inr", "amt"]:
            if candidate in tx_df.columns:
                amount_col = candidate
                break
        if amount_col is None:
            raise ValueError("Could not find amount column in investor transactions file")

        tx_df["amount"] = pd.to_numeric(tx_df[amount_col], errors="coerce")
        tx_df = tx_df[tx_df["amount"] > 0]
        tx_df["kyc_status"] = tx_df["kyc_status"].astype(str).str.upper().str.strip()
        tx_df.to_csv(os.path.join(PROCESSED_DIR, "investor_transactions_clean.csv"), index=False)
        print("OK investor_transactions.csv cleaned successfully.")
    except Exception as e:
        print(f"ERROR cleaning investor_transactions: {e}")
        return

    # 3. Clean scheme_performance.csv
    try:
        perf_path = resolve_raw_file(raw_dir, ["07_scheme_performance.csv", "scheme_performance.csv"])
        perf_df = pd.read_csv(perf_path)
        perf_df = normalize_return_columns(perf_df)
        return_cols = [col for col in perf_df.columns if col.lower() in ["return_1y", "return_3y", "return_5y"]]
        for col in return_cols:
            perf_df[col] = pd.to_numeric(perf_df[col], errors="coerce").fillna(0.0)
        perf_df["expense_ratio"] = pd.to_numeric(perf_df.get("expense_ratio", pd.Series(dtype=float)), errors="coerce")
        perf_df["anomaly_flag"] = np.where(
            (perf_df["expense_ratio"] < 0.001) | (perf_df["expense_ratio"] > 0.025),
            1,
            0,
        )
        perf_df.to_csv(os.path.join(PROCESSED_DIR, "scheme_performance_clean.csv"), index=False)
        print("OK scheme_performance.csv cleaned successfully.")
    except Exception as e:
        print(f"ERROR cleaning scheme_performance: {e}")
        return

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
    investor_id INTEGER,
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

    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON;"))
        for statement in schema_sql.strip().split(";"):
            if statement.strip():
                conn.execute(text(statement))
    print("OK SQLite Star Schema tables generated safely.")

    print("\n--- Step 5: Loading Data via SQLAlchemy ---")

    try:
        combined_dates = pd.concat([nav_df["date"], tx_df["transaction_date"]])
        dim_date_df = generate_dim_date(combined_dates)

        fund_master_df = get_fund_master(raw_dir)

        with engine.begin() as conn:
            dim_date_df.to_sql("dim_date", conn, if_exists="append", index=False)
            if not fund_master_df.empty:
                fund_master_df.to_sql("dim_fund", conn, if_exists="append", index=False)

            nav_insert = nav_df[["amfi_code", "date"]].copy()
            nav_insert["date_id"] = nav_insert["date"].dt.strftime("%Y%m%d")
            nav_insert = nav_insert[["amfi_code", "date_id"]].join(nav_df[["nav"]])
            nav_insert.drop_duplicates(subset=["amfi_code", "date_id"], inplace=True)
            nav_insert.to_sql("fact_nav", conn, if_exists="append", index=False)

            tx_insert = tx_df.copy()
            tx_insert["date_id"] = tx_insert["transaction_date"].dt.strftime("%Y%m%d")
            tx_columns = [col for col in ["amfi_code", "date_id", "investor_id", "transaction_type", "amount", "state", "kyc_status"] if col in tx_insert.columns]
            tx_insert[tx_columns].drop_duplicates().to_sql("fact_transactions", conn, if_exists="append", index=False)

            perf_columns = [
                "amfi_code",
                "return_1y",
                "return_3y",
                "return_5y",
                "expense_ratio",
                "anomaly_flag",
            ]
            for col in perf_columns:
                if col not in perf_df.columns:
                    perf_df[col] = 0.0 if col.startswith("return") or col == "expense_ratio" else 0
            perf_df[perf_columns].drop_duplicates(subset=["amfi_code"]).to_sql(
                "fact_performance",
                conn,
                if_exists="append",
                index=False,
            )

        print("OK Verification Check: SQL tables populated successfully.")
    except Exception as e:
        print(f"WARNING: Extraction mapping skipped or missing core structural reference IDs: {e}")


if __name__ == "__main__":
    main()
