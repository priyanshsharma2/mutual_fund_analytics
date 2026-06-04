import pandas as pd

# Load the 4th file
df = pd.read_csv('mutual_fund_analytics/data/raw/raw_data/04_monthly_sip_inflows.csv')

# 1. See which columns have the missing values
print("--- Missing Values Per Column ---")
print(df.isnull().sum())

# 2. Look at the actual rows that contain the missing values
print("\n--- Rows with Missing Values ---")
missing_rows = df[df.isnull().any(axis=1)]
print(missing_rows)