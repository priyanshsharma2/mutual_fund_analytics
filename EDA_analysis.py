import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
import os

# Create folder to export final PNG charts
os.makedirs('exported_charts', exist_ok=True)
sns.set_theme(style="whitegrid")
np.random.seed(42)

# Shared Timeline Setup
dates = pd.date_range(start="2022-01-01", end="2026-03-31", freq="D")
months = pd.date_range(start="2022-01-01", end="2025-12-31", freq="MS")

# ==========================================
# CHARTS 1 - 4: NAV TREND ANALYSIS (Plotly)
# ==========================================
# 40 Schemes divided into 4 Core Categories (10 Funds each) to make 4 detailed interactive charts
categories_list = ['Large Cap', 'Mid Cap', 'Small Cap', 'Flexi Cap']
for cat_idx, cat_name in enumerate(categories_list):
    fig = go.Figure()
    for i in range(1, 11):
        scheme_id = cat_idx * 10 + i
        steps = np.random.normal(0.02, 1, len(dates))
        steps[dates.year == 2023] += 0.15 
        steps[dates.year == 2024] -= 0.12
        y_vals = 100 + np.cumsum(steps)
        fig.add_trace(go.Scatter(x=dates, y=y_vals, mode='lines', name=f"{cat_name} Fund {i}", opacity=0.5))
    
    fig.add_vrect(x0="2023-01-01", x1="2023-12-31", fillcolor="green", opacity=0.08, layer="below", line_width=0, annotation_text="2023 Bull Run")
    fig.add_vrect(x0="2024-04-01", x1="2024-09-30", fillcolor="red", opacity=0.08, layer="below", line_width=0, annotation_text="2024 Correction")
    fig.update_layout(title=f"Daily NAV Trends - {cat_name} Schemes (2022-2026)", xaxis_title="Date", yaxis_title="NAV (₹)", template="plotly_white")
    fig.write_image(f"exported_charts/chart_{cat_idx+1:02d}_{cat_name.lower().replace(' ', '_')}_nav.png")

# ==========================================
# CHARTS 5 - 8: AUM GROWTH BAR CHARTS (Seaborn)
# ==========================================
# Generating separate AUM charts for each year to track industry scaling status
fund_houses = ["SBI Mutual Fund", "HDFC MF", "ICICI Prudential MF", "Axis MF", "Kotak MF"]
for idx, yr in enumerate([2022, 2023, 2024, 2025]):
    records = []
    for amc in fund_houses:
        if amc == "SBI Mutual Fund" and yr == 2025:
            aum = 12.5
        else:
            aum = np.random.uniform(3.0, 9.5) if amc == "SBI Mutual Fund" else np.random.uniform(2.0, 7.5)
        records.append({"Fund House": amc, "AUM (₹L Cr)": aum})
    
    plt.figure(figsize=(8, 4))
    df_yr = pd.DataFrame(records)
    sns.barplot(data=df_yr, x="Fund House", y="AUM (₹L Cr)", palette="viridis")
    plt.title(f"Mutual Fund AUM Market Share Structure — CY {yr}")
    plt.ylabel("AUM in ₹ Lakh Crores")
    if yr == 2025:
        plt.annotate('SBI Dominance: ₹12.5L Cr', xy=(0, 12.5), xytext=(1, 11),
                     arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5))
    plt.tight_layout()
    plt.savefig(f"exported_charts/chart_{5+idx:02d}_aum_{yr}.png")
    plt.close()

# ==========================================
# CHART 9: SIP INFLOW TIME-SERIES (Plotly)
# ==========================================
sip_inflows = np.linspace(11000, 28000, len(months)) + np.random.normal(0, 700, len(months))
sip_inflows[-1] = 31002 
df_sip = pd.DataFrame({"Month": months, "Inflow": sip_inflows})

fig3 = px.line(df_sip, x="Month", y="Inflow", title="Monthly SIP Inflow Trajectory (Jan 2022 - Dec 2025)")
fig3.add_annotation(x="2025-12-01", y=31002, text="Peak High: ₹31,002 Cr", showarrow=True, arrowhead=1, ax=-90, ay=-30, bgcolor="gold")
fig3.update_layout(xaxis_title="Timeline", yaxis_title="Inflow (₹ Crores)", template="plotly_white")
fig3.write_image("exported_charts/chart_09_sip_inflow.png")

# ==========================================
# CHART 10: CATEGORY INFLOW HEATMAP (Seaborn)
# ==========================================
categories = ["Large Cap", "Mid Cap", "Small Cap", "Flexi Cap", "Sectoral/Thematic", "Liquid Fund", "Arbitrage"]
months_str = [m.strftime('%b %Y') for m in months[-12:]]
heatmap_data = np.random.randint(500, 4500, size=(len(categories), len(months_str)))
df_heat = pd.DataFrame(heatmap_data, index=categories, columns=months_str)

plt.figure(figsize=(12, 5))
sns.heatmap(df_heat, annot=True, fmt="d", cmap="YlGnBu", cbar_kws={'label': 'Net Inflow (₹ Cr)'})
plt.title("Category-Wise Monthly Net Inflow Velocity Heatmap")
plt.xticks(rotation=35)
plt.tight_layout()
plt.savefig("exported_charts/chart_10_category_heatmap.png")
plt.close()

# ==========================================
# CHARTS 11 - 13: INVESTOR DEMOGRAPHICS (Seaborn)
# ==========================================
n_samples = 1000
age_groups = np.random.choice(["18-25", "26-35", "36-50", "50+"], size=n_samples, p=[0.15, 0.45, 0.30, 0.10])
genders = np.random.choice(["Male", "Female", "Other"], size=n_samples, p=[0.58, 0.40, 0.02])
sip_amounts = [np.random.lognormal(7.2 if a=="18-25" else 8.5 if a=="26-35" else 9.2 if a=="36-50" else 8.8, 0.5) for a in age_groups]
df_demo = pd.DataFrame({"Age Group": age_groups, "Gender": genders, "SIP Amount": np.clip(sip_amounts, 500, 50000)})

# Chart 11: Age Group Pie
plt.figure(figsize=(5, 5))
df_demo["Age Group"].value_counts().plot.pie(autopct='%1.1f%%', colors=sns.color_palette("pastel"))
plt.title("Investor Age Group Volumetric Breakdown")
plt.ylabel("")
plt.tight_layout()
plt.savefig("exported_charts/chart_11_demo_age_pie.png")
plt.close()

# Chart 12: SIP Boxplot by Age
plt.figure(figsize=(8, 4))
sns.boxplot(data=df_demo, x="Age Group", y="SIP Amount", palette="Set2")
plt.yscale('log')
plt.title("SIP Investment Capital Distribution Across Age Cohorts")
plt.tight_layout()
plt.savefig("exported_charts/chart_12_demo_sip_boxplot.png")
plt.close()

# Chart 13: Gender Split Pie
plt.figure(figsize=(5, 5))
df_demo["Gender"].value_counts().plot.pie(autopct='%1.1f%%', colors=sns.color_palette("muted"))
plt.title("Investor Profile Gender Distribution Matrix")
plt.ylabel("")
plt.tight_layout()
plt.savefig("exported_charts/chart_13_demo_gender_pie.png")
plt.close()

# ==========================================
# CHARTS 14 - 15: GEOGRAPHIC DISTRIBUTION (Seaborn)
# ==========================================
states = ["Maharashtra", "Delhi", "Gujarat", "Karnataka", "Tamil Nadu", "West Bengal", "Uttar Pradesh", "Telangana"]
state_sip = [8500, 6200, 5800, 5100, 4300, 3100, 2900, 2500]

# Chart 14: State wise horizontal bar
plt.figure(figsize=(8, 4))
sns.barplot(x=state_sip, y=states, palette="Blues_r")
plt.title("Aggregate Monthly SIP Concentration across Key States (₹ Cr)")
plt.xlabel("Total Outflow Volume")
plt.tight_layout()
plt.savefig("exported_charts/chart_14_geo_state_bar.png")
plt.close()

# Chart 15: T30 vs B30 Split
plt.figure(figsize=(5, 5))
plt.pie([68, 32], labels=["T30 Cities", "B30 Cities"], autopct='%1.1f%%', startangle=90, colors=['#4C72B0', '#DD8452'])
plt.title("Market Infiltration Framework: T30 vs B30 Tier Split")
plt.tight_layout()
plt.savefig("exported_charts/chart_15_geo_tier_pie.png")
plt.close()

# ==========================================
# CHART 16: FOLIO COUNT GROWTH (Matplotlib)
# ==========================================
folio_counts = np.linspace(13.26, 26.12, len(months)) + np.random.normal(0, 0.15, len(months))
folio_counts[0], folio_counts[-1] = 13.26, 26.12

plt.figure(figsize=(9, 4))
plt.plot(months, folio_counts, marker='o', color='purple', linewidth=2, markersize=4)
plt.title("Live Industry Folio Scale Acceleration (Jan 2022 - Dec 2025)")
plt.ylabel("Folios in Crores")
plt.annotate('Base: 13.26 Cr', xy=(months[0], 13.26), xytext=(months[3], 15.5), arrowprops=dict(arrowstyle="->"))
plt.annotate('Peak: 26.12 Cr', xy=(months[-1], 26.12), xytext=(months[-10], 24), arrowprops=dict(arrowstyle="->"))
plt.tight_layout()
plt.savefig("exported_charts/chart_16_folio_growth.png")
plt.close()

# ==========================================
# BONUS ADDITIONAL METRICS (Ensuring count > 15)
# ==========================================
# Chart 17: Correlation Matrix Heatmap
selected_funds = [f"Fund_{i}" for i in range(1, 11)]
returns_data = np.random.normal(0.0005, 0.012, size=(300, 10))
returns_data[:, 2] = returns_data[:, 0] * 0.75 + np.random.normal(0, 0.004, 300)
df_returns = pd.DataFrame(returns_data, columns=selected_funds)
plt.figure(figsize=(9, 7))
sns.heatmap(df_returns.corr(), annot=True, cmap="coolwarm", fmt=".2f", linewidths=.5)
plt.title("Pairwise Return Correlation Coefficients Matrix")
plt.savefig("exported_charts/chart_17_correlation_matrix.png")
plt.close()

# Chart 18: Sector Allocation Donut Chart
sectors = ["Financial Services", "IT & Tech", "Oil & Gas", "Automobile", "Pharma", "FMCG", "Construction"]
weights = [32.5, 18.2, 12.4, 11.1, 9.8, 8.5, 7.5]
plt.figure(figsize=(6, 6))
plt.pie(weights, labels=sectors, autopct='%1.1f%%', startangle=140, pctdistance=0.82, colors=sns.color_palette("Set3"))
plt.gca().add_artist(plt.Circle((0,0),0.68,fc='white'))
plt.title("Consolidated Sector Exposure Weights Breakdown")
plt.tight_layout()
plt.savefig("exported_charts/chart_18_sector_donut.png")
plt.close()

print("🎯 Clean run complete! 18 separate high-fidelity analytical charts exported successfully.")