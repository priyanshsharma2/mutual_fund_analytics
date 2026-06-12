import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def audit_datasets():
    raw_data_dir = os.path.join(BASE_DIR, "data", "raw", "raw_data")
    
    # Check if the folder exists and has files
    if not os.path.exists(raw_data_dir):
        print(f"Error: Place your 10 CSV files inside the '{raw_data_dir}' folder first.")
        return

    csv_files = [f for f in os.listdir(raw_data_dir) if f.endswith('.csv')]
    
    print(f"Found {len(csv_files)} CSV files to audit.\n")
    print("="*50)

    for file in csv_files:
        file_path = os.path.join(raw_data_dir, file)
        print(f"\n[AUDITING FILE]: {file}")
        
        try:
            # Load dataset
            df = pd.read_csv(file_path)
            
            # Print basic structural information
            print(f"-> Shape (Rows, Columns): {df.shape}")
            print("\n-> Data Types:")
            print(df.dtypes)
            print("\n-> First 3 Rows:")
            print(df.head(3))
            
            # Basic anomaly spotting
            missing_vals = df.isnull().sum().sum()
            if missing_vals > 0:
                print(f"\n[WARNING] Found {missing_vals} missing values in this file.")
            else:
                print("\n[OK] Structure looks stable (No missing values detected).")
                
        except Exception as e:
            print(f"[ERROR] Error reading {file}: {e}")
            
        print("-" * 50)

def clean_datasets():
    """Handle missing values in all CSV files"""
    raw_data_dir = os.path.join(BASE_DIR, "data", "raw", "raw_data")
    cleaned_dir = os.path.join(BASE_DIR, "data", "raw", "cleaned_data")
    
    # Create cleaned_data directory if it doesn't exist
    os.makedirs(cleaned_dir, exist_ok=True)
    
    csv_files = [f for f in os.listdir(raw_data_dir) if f.endswith('.csv')]
    
    print(f"\nCLEANING {len(csv_files)} CSV FILES...")
    print("="*50)
    
    for file in csv_files:
        file_path = os.path.join(raw_data_dir, file)
        output_path = os.path.join(cleaned_dir, file)
        
        print(f"\n[CLEANING]: {file}")
        
        try:
            df = pd.read_csv(file_path)
            original_shape = df.shape
            
            # Display missing values by column
            missing_by_col = df.isnull().sum()
            if missing_by_col.sum() > 0:
                print("   Missing values by column:")
                for col, count in missing_by_col[missing_by_col > 0].items():
                    print(f"   - {col}: {count} missing")
            
            # Strategy: Forward fill for time-series data, then backward fill
            df = df.ffill()
            df = df.bfill()
            
            # For remaining NaN in numeric columns, use median
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            for col in numeric_cols:
                if df[col].isnull().sum() > 0:
                    df[col].fillna(df[col].median(), inplace=True)
            
            # For remaining NaN in object columns, use mode or drop
            object_cols = df.select_dtypes(include=['object']).columns
            for col in object_cols:
                if df[col].isnull().sum() > 0:
                    mode_val = df[col].mode()
                    if len(mode_val) > 0:
                        df[col].fillna(mode_val[0], inplace=True)
                    else:
                        df[col].fillna('Unknown', inplace=True)
            
            # Remove rows where all values are NaN
            df = df.dropna(how='all')
            
            # Save cleaned file
            df.to_csv(output_path, index=False)
            
            final_shape = df.shape
            print(f"   Before: {original_shape[0]} rows | After: {final_shape[0]} rows")
            print(f"   [OK] Saved to: {output_path}")
            
        except Exception as e:
            print(f"   [ERROR] Failed to clean {file}: {e}")
    
    print("\n" + "="*50)
    print("Cleaning complete! Files saved to:", cleaned_dir)

if __name__ == "__main__":
    audit_datasets()
    clean_datasets()