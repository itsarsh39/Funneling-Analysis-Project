-- ==============================================================================
-- Statistical Test: Two-Proportion Z-Test & 95% Confidence Intervals in Pure SQL
-- Dialect: ANSI SQL / SQLite Compatible
-- Metric: Primary conversion rate (Checkout -> Purchase)
-- Null Hypothesis (H0): Conversion rate is equal between Control and Treatment (p_t - p_c = 0).
-- Decision Rule: Reject H0 if |Z| >= 1.96 (two-tailed alpha = 0.05).
-- ==============================================================================

WITH stage_metrics AS (
    SELECT 
        u.variant,
        COUNT(DISTINCT CASE WHEN fe.funnel_stage = 'checkout' THEN fe.user_id END) AS n_checkout,
        COUNT(DISTINCT CASE WHEN fe.funnel_stage = 'purchase' THEN fe.user_id END) AS n_purchase
    FROM fct_events fe
    JOIN dim_users u ON fe.user_id = u.user_id
    GROUP BY u.variant
),
pivoted AS (
    SELECT 
        MAX(CASE WHEN variant = 'control' THEN n_checkout END) AS n_ctrl,
        MAX(CASE WHEN variant = 'control' THEN n_purchase END) AS x_ctrl,
        MAX(CASE WHEN variant = 'treatment' THEN n_checkout END) AS n_trt,
        MAX(CASE WHEN variant = 'treatment' THEN n_purchase END) AS x_trt
    FROM stage_metrics
),
base_rates AS (
    SELECT 
        n_ctrl,
        x_ctrl,
        n_trt,
        x_trt,
        CAST(x_ctrl AS REAL) / n_ctrl AS p_ctrl,
        CAST(x_trt AS REAL) / n_trt AS p_trt,
        CAST(x_ctrl + x_trt AS REAL) / (n_ctrl + n_trt) AS p_pooled
    FROM pivoted
),
standard_errors AS (
    SELECT 
        n_ctrl,
        x_ctrl,
        n_trt,
        x_trt,
        p_ctrl,
        p_trt,
        p_pooled,
        -- Absolute Lift: p_trt - p_ctrl
        (p_trt - p_ctrl) AS absolute_lift,
        -- Relative Lift: (p_trt - p_ctrl) / p_ctrl
        (p_trt - p_ctrl) / p_ctrl AS relative_lift,
        -- Pooled SE for Z-score: sqrt(p_pool * (1 - p_pool) * (1/n_c + 1/n_t))
        SQRT(p_pooled * (1.0 - p_pooled) * ((1.0 / n_ctrl) + (1.0 / n_trt))) AS se_pooled,
        -- Unpooled SE for Confidence Interval: sqrt( (p_c*(1-p_c)/n_c) + (p_t*(1-p_t)/n_t) )
        SQRT(((p_ctrl * (1.0 - p_ctrl)) / n_ctrl) + ((p_trt * (1.0 - p_trt)) / n_trt)) AS se_diff
    FROM base_rates
)
SELECT 
    n_ctrl AS control_sample_size,
    x_ctrl AS control_conversions,
    ROUND(p_ctrl * 100.0, 2) AS control_conversion_rate_pct,
    n_trt AS treatment_sample_size,
    x_trt AS treatment_conversions,
    ROUND(p_trt * 100.0, 2) AS treatment_conversion_rate_pct,
    -- Lift Metrics
    ROUND(absolute_lift * 100.0, 2) AS absolute_lift_pts,
    ROUND(relative_lift * 100.0, 2) AS relative_lift_pct,
    -- Z-Test Statistics
    ROUND(absolute_lift / se_pooled, 3) AS z_statistic,
    -- 95% Confidence Interval (Z_crit = 1.95996)
    ROUND((absolute_lift - (1.95996 * se_diff)) * 100.0, 2) AS ci_lower_95_pts,
    ROUND((absolute_lift + (1.95996 * se_diff)) * 100.0, 2) AS ci_upper_95_pts,
    -- Hypothesis Decision
    CASE 
        WHEN ABS(absolute_lift / se_pooled) >= 1.96 THEN 'STATISTICALLY SIGNIFICANT (p < 0.05)'
        ELSE 'NOT STATISTICALLY SIGNIFICANT (Fail to Reject H0)'
    END AS hypothesis_test_verdict
FROM standard_errors;
