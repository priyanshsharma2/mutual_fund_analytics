"""
Comprehensive Data Cleaning for All 10 Mutual Fund Datasets
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
RAW_DIR = os.path.join(BASE_DIR, "raw_data")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

os.makedirs(PROCESSED_DIR, exist_ok=True)

print("=" * 80)
print("COMPREHENSIVE DATA CLEANING FOR ALL 10 DATASETS")
print("=" * 80)

# ============================================================================
# 1. FUND MASTER (01_fund_master.csv)
# ============================================================================
print("\n[1/10] Cleaning 01_fund_master.csv...")
try:
    df = pd.read_csv(os.path.join(RAW_DIR, "01_fund_master.csv"))
    
    # Parse launch_date to datetime
    df["launch_date"] = pd.to_datetime(df["launch_date"], errors="coerce")
    
    # Standardize expense_ratio_pct (should be numeric, 0.1-2.5%)
    df["expense_ratio_pct"] = pd.to_numeric(df["expense_ratio_pct"], errors="coerce")
    df["expense_ratio_pct"] = df["expense_ratio_pct"].clip(lower=0.0)
    
    # Convert percentages
    df["exit_load_pct"] = pd.to_numeric(df["exit_load_pct"], errors="coerce").fillna(0.0)
    df["min_sip_amount"] = pd.to_numeric(df["min_sip_amount"], errors="coerce").fillna(0.0)
    df["min_lumpsum_amount"] = pd.to_numeric(df["min_lumpsum_amount"], errors="coerce").fillna(0.0)
    
    # Standardize text fields
    df["fund_house"] = df["fund_house"].astype(str).str.strip()
    df["scheme_name"] = df["scheme_name"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip()
    df["risk_category"] = df["risk_category"].astype(str).str.strip()
    
    # Remove duplicates based on amfi_code
    df = df.drop_duplicates(subset=["amfi_code"], keep="first")
    
    # Remove rows with invalid amfi_code
    df = df[df["amfi_code"].notna()]
    
    df.to_csv(os.path.join(PROCESSED_DIR, "01_fund_master_clean.csv"), index=False)
    print(f"   ✓ Cleaned: {len(df)} rows")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    raise

# ============================================================================
# 2. NAV HISTORY (02_nav_history.csv)
# ============================================================================
print("[2/10] Cleaning 02_nav_history.csv...")
try:
    df = pd.read_csv(os.path.join(RAW_DIR, "02_nav_history.csv"))
    
    # Parse date to datetime
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    
    # Convert NAV to numeric
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    
    # Sort by amfi_code and date
    df = df.sort_values(by=["amfi_code", "date"]).reset_index(drop=True)
    
    # Forward fill missing NAV values (for weekends/holidays)
    df["nav"] = df.groupby("amfi_code")["nav"].transform(lambda x: x.fillna(method="ffill"))
    
    # Remove duplicates
    df = df.drop_duplicates(subset=["amfi_code", "date"], keep="first")
    
    # Filter out invalid NAV values (NAV > 0)
    df = df[df["nav"] > 0]
    
    # Remove rows with missing dates
    df = df[df["date"].notna()]
    
    df.to_csv(os.path.join(PROCESSED_DIR, "02_nav_history_clean.csv"), index=False)
    print(f"   ✓ Cleaned: {len(df)} rows")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    raise

# ============================================================================
# 3. AUM BY FUND HOUSE (03_aum_by_fund_house.csv)
# ============================================================================
print("[3/10] Cleaning 03_aum_by_fund_house.csv...")
try:
    df = pd.read_csv(os.path.join(RAW_DIR, "03_aum_by_fund_house.csv"))
    
    # Parse date
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    
    # Convert AUM values to numeric (in crore)
    df["aum_crore"] = pd.to_numeric(df["aum_crore"], errors="coerce")
    df["aum_lakh_crore"] = pd.to_numeric(df["aum_lakh_crore"], errors="coerce")
    df["num_schemes"] = pd.to_numeric(df["num_schemes"], errors="coerce")
    
    # Remove rows with invalid AUM
    df = df[(df["aum_crore"] > 0) & (df["num_schemes"] > 0)]
    
    # Standardize fund house names
    df["fund_house"] = df["fund_house"].astype(str).str.strip()
    
    # Remove duplicates
    df = df.drop_duplicates(subset=["date", "fund_house"], keep="first")
    
    df.to_csv(os.path.join(PROCESSED_DIR, "03_aum_by_fund_house_clean.csv"), index=False)
    print(f"   ✓ Cleaned: {len(df)} rows")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    raise

# ============================================================================
# 4. MONTHLY SIP INFLOWS (04_monthly_sip_inflows.csv)
# ============================================================================
print("[4/10] Cleaning 04_monthly_sip_inflows.csv...")
try:
    df = pd.read_csv(os.path.join(RAW_DIR, "04_monthly_sip_inflows.csv"))
    
    # Convert month to proper date format (YYYY-MM format)
    df["month"] = pd.to_datetime(df["month"], format="%Y-%m", errors="coerce")
    
    # Convert numeric columns
    df["sip_inflow_crore"] = pd.to_numeric(df["sip_inflow_crore"], errors="coerce")
    df["active_sip_accounts_crore"] = pd.to_numeric(df["active_sip_accounts_crore"], errors="coerce")
    df["new_sip_accounts_lakh"] = pd.to_numeric(df["new_sip_accounts_lakh"], errors="coerce")
    df["sip_aum_lakh_crore"] = pd.to_numeric(df["sip_aum_lakh_crore"], errors="coerce")
    df["yoy_growth_pct"] = pd.to_numeric(df["yoy_growth_pct"], errors="coerce").fillna(0.0)
    
    # Remove rows with missing dates
    df = df[df["month"].notna()]
    
    # Remove duplicates
    df = df.drop_duplicates(subset=["month"], keep="first")
    
    df.to_csv(os.path.join(PROCESSED_DIR, "04_monthly_sip_inflows_clean.csv"), index=False)
    print(f"   ✓ Cleaned: {len(df)} rows")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    raise

# ============================================================================
# 5. CATEGORY INFLOWS (05_category_inflows.csv)
# ============================================================================
print("[5/10] Cleaning 05_category_inflows.csv...")
try:
    df = pd.read_csv(os.path.join(RAW_DIR, "05_category_inflows.csv"))
    
    # Parse month
    df["month"] = pd.to_datetime(df["month"], format="%Y-%m", errors="coerce")
    
    # Standardize category names
    df["category"] = df["category"].astype(str).str.strip()
    
    # Convert net_inflow to numeric
    df["net_inflow_crore"] = pd.to_numeric(df["net_inflow_crore"], errors="coerce")
    
    # Remove rows with missing data
    df = df[df["month"].notna()]
    df = df[df["category"].notna()]
    
    # Remove duplicates
    df = df.drop_duplicates(subset=["month", "category"], keep="first")
    
    df.to_csv(os.path.join(PROCESSED_DIR, "05_category_inflows_clean.csv"), index=False)
    print(f"   ✓ Cleaned: {len(df)} rows")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    raise

# ============================================================================
# 6. INDUSTRY FOLIO COUNT (06_industry_folio_count.csv)
# ============================================================================
print("[6/10] Cleaning 06_industry_folio_count.csv...")
try:
    df = pd.read_csv(os.path.join(RAW_DIR, "06_industry_folio_count.csv"))
    
    # Parse month
    df["month"] = pd.to_datetime(df["month"], format="%Y-%m", errors="coerce")
    
    # Convert numeric columns
    for col in ["total_folios_crore", "equity_folios_crore", "debt_folios_crore", 
                "hybrid_folios_crore", "others_folios_crore"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Remove rows with missing month
    df = df[df["month"].notna()]
    
    # Validate that breakdown <= total
    df["total_calculated"] = (df["equity_folios_crore"] + df["debt_folios_crore"] + 
                              df["hybrid_folios_crore"] + df["others_folios_crore"])
    df = df[df["total_calculated"] <= df["total_folios_crore"] + 0.01]  # Allow small rounding error
    df = df.drop(columns=["total_calculated"])
    
    # Remove duplicates
    df = df.drop_duplicates(subset=["month"], keep="first")
    
    df.to_csv(os.path.join(PROCESSED_DIR, "06_industry_folio_count_clean.csv"), index=False)
    print(f"   ✓ Cleaned: {len(df)} rows")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    raise

# ============================================================================
# 7. SCHEME PERFORMANCE (07_scheme_performance.csv) - Already cleaned
# ============================================================================
print("[7/10] Cleaning 07_scheme_performance.csv...")
try:
    df = pd.read_csv(os.path.join(RAW_DIR, "07_scheme_performance.csv"))
    
    # Convert return columns (handle % format)
    for col in ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct", "benchmark_3yr_pct"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Convert numeric columns
    df["alpha"] = pd.to_numeric(df["alpha"], errors="coerce")
    df["beta"] = pd.to_numeric(df["beta"], errors="coerce")
    df["sharpe_ratio"] = pd.to_numeric(df["sharpe_ratio"], errors="coerce")
    df["sortino_ratio"] = pd.to_numeric(df["sortino_ratio"], errors="coerce")
    df["std_dev_ann_pct"] = pd.to_numeric(df["std_dev_ann_pct"], errors="coerce")
    df["max_drawdown_pct"] = pd.to_numeric(df["max_drawdown_pct"], errors="coerce")
    df["aum_crore"] = pd.to_numeric(df["aum_crore"], errors="coerce")
    df["expense_ratio_pct"] = pd.to_numeric(df["expense_ratio_pct"], errors="coerce")
    df["morningstar_rating"] = pd.to_numeric(df["morningstar_rating"], errors="coerce")
    
    # Validate expense_ratio (0.1% - 2.5%)
    df = df[(df["expense_ratio_pct"] >= 0.0) & (df["expense_ratio_pct"] <= 3.0)]
    
    # Validate returns are reasonable
    df = df[(df["return_1yr_pct"] > -100) & (df["return_1yr_pct"] < 500)]
    df = df[(df["return_3yr_pct"] > -100) & (df["return_3yr_pct"] < 500)]
    df = df[(df["return_5yr_pct"] > -100) & (df["return_5yr_pct"] < 500)]
    
    # Standardize text
    df["scheme_name"] = df["scheme_name"].astype(str).str.strip()
    df["fund_house"] = df["fund_house"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip()
    
    # Remove duplicates
    df = df.drop_duplicates(subset=["amfi_code"], keep="first")
    
    df.to_csv(os.path.join(PROCESSED_DIR, "07_scheme_performance_clean.csv"), index=False)
    print(f"   ✓ Cleaned: {len(df)} rows")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    raise

# ============================================================================
# 8. INVESTOR TRANSACTIONS (08_investor_transactions.csv) - Already cleaned
# ============================================================================
print("[8/10] Cleaning 08_investor_transactions.csv...")
try:
    df = pd.read_csv(os.path.join(RAW_DIR, "08_investor_transactions.csv"))
    
    # Parse transaction_date
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    
    # Standardize transaction_type
    df["transaction_type"] = df["transaction_type"].astype(str).str.strip().str.capitalize()
    type_mapping = {"Sip": "SIP", "Lumpsum": "Lumpsum", "Redemption": "Redemption"}
    df["transaction_type"] = df["transaction_type"].map(type_mapping).fillna("Other")
    
    # Convert amount to numeric
    df["amount_inr"] = pd.to_numeric(df["amount_inr"], errors="coerce")
    
    # Remove rows with invalid amounts
    df = df[df["amount_inr"] > 0]
    
    # Standardize state/city
    df["state"] = df["state"].astype(str).str.strip()
    df["city"] = df["city"].astype(str).str.strip()
    df["city_tier"] = df["city_tier"].astype(str).str.strip()
    
    # Standardize KYC status
    df["kyc_status"] = df["kyc_status"].astype(str).str.upper().str.strip()
    valid_kyc = ["VERIFIED", "PENDING", "REJECTED"]
    df = df[df["kyc_status"].isin(valid_kyc)]
    
    # Standardize age_group, gender
    df["age_group"] = df["age_group"].astype(str).str.strip()
    df["gender"] = df["gender"].astype(str).str.upper().str.strip()
    
    # Convert numeric columns
    df["annual_income_lakh"] = pd.to_numeric(df["annual_income_lakh"], errors="coerce").fillna(0.0)
    
    # Remove rows with missing critical fields
    df = df[df["transaction_date"].notna()]
    df = df[df["amfi_code"].notna()]
    df = df[df["investor_id"].notna()]
    
    df.to_csv(os.path.join(PROCESSED_DIR, "08_investor_transactions_clean.csv"), index=False)
    print(f"   ✓ Cleaned: {len(df)} rows")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    raise

# ============================================================================
# 9. PORTFOLIO HOLDINGS (09_portfolio_holdings.csv)
# ============================================================================
print("[9/10] Cleaning 09_portfolio_holdings.csv...")
try:
    df = pd.read_csv(os.path.join(RAW_DIR, "09_portfolio_holdings.csv"))
    
    # Parse portfolio_date
    df["portfolio_date"] = pd.to_datetime(df["portfolio_date"], errors="coerce")
    
    # Convert numeric columns
    df["weight_pct"] = pd.to_numeric(df["weight_pct"], errors="coerce")
    df["market_value_cr"] = pd.to_numeric(df["market_value_cr"], errors="coerce")
    df["current_price_inr"] = pd.to_numeric(df["current_price_inr"], errors="coerce")
    
    # Validate weight_pct (0-100%)
    df = df[(df["weight_pct"] >= 0) & (df["weight_pct"] <= 100)]
    
    # Validate market values > 0
    df = df[df["market_value_cr"] > 0]
    df = df[df["current_price_inr"] > 0]
    
    # Standardize text
    df["stock_symbol"] = df["stock_symbol"].astype(str).str.strip().str.upper()
    df["stock_name"] = df["stock_name"].astype(str).str.strip()
    df["sector"] = df["sector"].astype(str).str.strip()
    
    # Remove rows with missing critical data
    df = df[df["portfolio_date"].notna()]
    df = df[df["amfi_code"].notna()]
    df = df[df["stock_symbol"].notna()]
    
    # Remove duplicates
    df = df.drop_duplicates(subset=["amfi_code", "portfolio_date", "stock_symbol"], keep="first")
    
    df.to_csv(os.path.join(PROCESSED_DIR, "09_portfolio_holdings_clean.csv"), index=False)
    print(f"   ✓ Cleaned: {len(df)} rows")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    raise

# ============================================================================
# 10. BENCHMARK INDICES (10_benchmark_indices.csv)
# ============================================================================
print("[10/10] Cleaning 10_benchmark_indices.csv...")
try:
    df = pd.read_csv(os.path.join(RAW_DIR, "10_benchmark_indices.csv"))
    
    # Parse date
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    
    # Convert close_value to numeric
    df["close_value"] = pd.to_numeric(df["close_value"], errors="coerce")
    
    # Standardize index name
    df["index_name"] = df["index_name"].astype(str).str.strip().str.upper()
    
    # Remove invalid records
    df = df[df["date"].notna()]
    df = df[df["close_value"] > 0]
    df = df[df["index_name"].notna()]
    
    # Sort by index and date
    df = df.sort_values(by=["index_name", "date"]).reset_index(drop=True)
    
    # Remove duplicates
    df = df.drop_duplicates(subset=["index_name", "date"], keep="first")
    
    df.to_csv(os.path.join(PROCESSED_DIR, "10_benchmark_indices_clean.csv"), index=False)
    print(f"   ✓ Cleaned: {len(df)} rows")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    raise

# ============================================================================
# SUMMARY REPORT
# ============================================================================
print("\n" + "=" * 80)
print("DATA CLEANING COMPLETED SUCCESSFULLY!")
print("=" * 80)

print("\nCleaned Datasets Summary:")
print("-" * 80)

file_list = [
    "01_fund_master_clean.csv",
    "02_nav_history_clean.csv",
    "03_aum_by_fund_house_clean.csv",
    "04_monthly_sip_inflows_clean.csv",
    "05_category_inflows_clean.csv",
    "06_industry_folio_count_clean.csv",
    "07_scheme_performance_clean.csv",
    "08_investor_transactions_clean.csv",
    "09_portfolio_holdings_clean.csv",
    "10_benchmark_indices_clean.csv"
]

total_rows = 0
for i, fname in enumerate(file_list, 1):
    fpath = os.path.join(PROCESSED_DIR, fname)
    if os.path.exists(fpath):
        df = pd.read_csv(fpath)
        total_rows += len(df)
        print(f"{i:2d}. {fname:45s} │ {len(df):8,d} rows")
    else:
        print(f"{i:2d}. {fname:45s} │ NOT FOUND")

print("-" * 80)
print(f"{'TOTAL':47s} │ {total_rows:8,d} rows")
print("=" * 80)
print("\n✓ All cleaned datasets are ready in: data/processed/")
