import pandas as pd

def run_validation():
    print("=== STEP 5: DATA EXPLORATION & VALIDATION ===\n")
    
    try:
        # Load files safely
        fund_master = pd.read_csv('mutual_fund_analytics/data/raw/cleaned_data/01_fund_master.csv') 
        nav_history = pd.read_csv('mutual_fund_analytics/data/raw/cleaned_data/02_nav_history.csv') 
        
        # Task 6: Explore Fund Master
        print("--- Task 6: Fund Master Exploration ---")
        print(f"Total Unique Fund Houses: {fund_master['fund_house'].nunique()}")
        print(f"Unique Categories: {fund_master['category'].dropna().unique()}")
        print(f"Unique Risk Categories: {fund_master['risk_category'].dropna().unique()}\n")
        
        # Task 7: Validate AMFI codes
        print("--- Task 7: AMFI Code Validation ---")
        # Ensure we treat both as strings or numeric uniformly to avoid type-mismatch bugs
        master_codes = set(fund_master['amfi_code'].dropna().astype(int))
        history_codes = set(nav_history['amfi_code'].dropna().astype(int))
        
        missing_in_history = master_codes - history_codes
        
        if not missing_in_history:
            print("[OK] Quality Check Passed: All fund master AMFI codes exist in history records!")
        else:
            print(f"[WARNING] Quality Check Anomaly: {len(missing_in_history)} codes in master are missing from history.")
            print(f"Sample missing codes: {list(missing_in_history)[:5]}")
            
    except FileNotFoundError as e:
        print(f"[ERROR] File not found. Make sure your CSV files are inside 'mutual_fund_analytics/data/raw/cleaned_data/'. Detail: {e}")
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")

if __name__ == "__main__":
    run_validation()