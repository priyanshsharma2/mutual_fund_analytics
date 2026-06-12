import os
import json
import requests
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def fetch_and_save_nav(scheme_code, scheme_name):
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    print(f"Fetching data for {scheme_name} (Code: {scheme_code})...")
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            
            # Extract historical NAV array from JSON response
            nav_list = data.get('data', [])
            
            if not nav_list:
                print(f"[WARNING] No data returned for scheme code {scheme_code}")
                return
            
            # Convert to DataFrame
            df = pd.DataFrame(nav_list)
            
            # Add scheme identifier data to the columns
            df['scheme_code'] = scheme_code
            df['scheme_name'] = scheme_name
            
            # Reorder for clean formatting
            df = df[['scheme_code', 'scheme_name', 'date', 'nav']]
            
            # Ensure target directory exists
            api_dir = os.path.join(BASE_DIR, "data", "raw", "api_data")
            os.makedirs(api_dir, exist_ok=True)
            
            # Save file
            file_name = os.path.join(api_dir, f"nav_{scheme_code}.csv")
            df.to_csv(file_name, index=False)
            print(f"[OK] Saved raw data to: {file_name}")
        else:
            print(f"[ERROR] Failed to fetch data. HTTP Status: {response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")


def main():
    # Task 4: Fetch HDFC Top 100 Direct
    fetch_and_save_nav("125497", "HDFC Top 100 Direct")
    
    print("\n" + "="*40 + "\n")
    
    # Task 5: Fetch 5 Key Bluechip Schemes
    schemes = {
        "119551": "SBI Bluechip",
        "120503": "ICICI Bluechip",
        "118632": "Nippon Large Cap",
        "119092": "Axis Bluechip",
        "120841": "Kotak Bluechip"
    }
    
    for code, name in schemes.items():
        fetch_and_save_nav(code, name)


if __name__ == "__main__":
    main()
