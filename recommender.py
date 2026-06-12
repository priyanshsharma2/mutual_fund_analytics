import pandas as pd

def fund_recommender(df_portfolio, user_risk_appetite):
    """
    Outputs top 3 funds by Sharpe ratio within the matched risk grade.
    Input: risk_appetite ('Low', 'Moderate', 'High')
    """
    # Standardizing input to match dataset categorical values
    risk_map = {'Low': 'Low', 'Moderate': 'Moderate', 'High': 'High'}
    target_grade = risk_map.get(user_risk_appetite)
    
    if not target_grade:
        print("Invalid risk appetite. Please choose from 'Low', 'Moderate', or 'High'.")
        return pd.DataFrame()
    
    # Remove duplicates to ensure unique funds are evaluated
    df_unique_funds = df_portfolio.drop_duplicates(subset=['fund_id'])
    
    # Filter based on risk grade
    filtered_funds = df_unique_funds[df_unique_funds['risk_grade'] == target_grade]
    
    # Sort by Sharpe Ratio in descending order and pick top 3
    top_3 = filtered_funds.sort_values(by='sharpe_ratio', ascending=False).head(3)
    
    # Print clean recommendation table
    print(f"\n==================================================")
    print(f" TOP 3 RECOMMENDED FUNDS FOR RISK PROFILE: {user_risk_appetite.upper()}")
    print(f"==================================================")
    print(top_3[['fund_id', 'risk_grade', 'sharpe_ratio']].to_string(index=False))
    print(f"==================================================\n")
    
    return top_3[['fund_id', 'risk_grade', 'sharpe_ratio']]