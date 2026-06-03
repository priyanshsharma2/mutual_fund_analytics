-- ==========================================
-- MUTUAL FUND ANALYTICS - SQLITE QUERIES
-- ==========================================
-- Converted from SQL Server to SQLite syntax
-- All queries return valid results for analytics

-- 1. Top 5 funds by current Assets Under Management (AUM)
SELECT 
    f.fund_name, 
    ROUND(COALESCE(MAX(a.aum_amount), 0), 2) AS aum_amount
FROM dim_fund f
LEFT JOIN fact_aum a ON f.amfi_code = a.amfi_code
GROUP BY f.amfi_code, f.fund_name
ORDER BY aum_amount DESC
LIMIT 5;

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

-- 4. Total transaction volume and amount broken down by State
SELECT 
    state, 
    COUNT(*) AS total_transactions, 
    ROUND(SUM(amount), 2) AS total_transaction_value
FROM fact_transactions
GROUP BY state
ORDER BY total_transaction_value DESC;

-- 5. Highly competitive funds with an expense_ratio strictly below 1%
SELECT 
    f.fund_name, 
    ROUND(p.expense_ratio * 100, 2) AS expense_ratio_pct,
    f.category
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.expense_ratio < 0.01 AND p.expense_ratio > 0
ORDER BY p.expense_ratio ASC;

-- 6. KYC Risk Vector Analysis (Identifying capital lockup by compliance status)
SELECT 
    kyc_status, 
    COUNT(*) AS transaction_count, 
    ROUND(SUM(amount), 2) AS total_staged_amount
FROM fact_transactions
GROUP BY kyc_status
ORDER BY total_staged_amount DESC;

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

-- 9. Ticket Size Distribution across different transaction channels
SELECT 
    transaction_type, 
    COUNT(*) AS total_volume, 
    ROUND(AVG(amount), 2) AS average_ticket_size
FROM fact_transactions
GROUP BY transaction_type
ORDER BY total_volume DESC;

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
