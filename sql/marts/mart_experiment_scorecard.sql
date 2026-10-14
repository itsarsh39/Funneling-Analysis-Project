-- ==============================================================================
-- Analytical Mart: Executive Experiment Scorecard
-- Purpose: Pre-aggregated single-row executive summary table linking statistical
--          significance, SRM status, and novelty decay for BI scorecards.
-- ==============================================================================

WITH user_counts AS (
    SELECT 
        COUNT(DISTINCT CASE WHEN variant = 'control' THEN user_id END) AS ctrl_visitors,
        COUNT(DISTINCT CASE WHEN variant = 'treatment' THEN user_id END) AS trt_visitors,
        COUNT(DISTINCT user_id) AS total_visitors
    FROM dim_users
),
funnel_counts AS (
    SELECT 
        COUNT(DISTINCT CASE WHEN u.variant = 'control' AND fe.funnel_stage = 'checkout' THEN fe.user_id END) AS ctrl_checkout,
        COUNT(DISTINCT CASE WHEN u.variant = 'control' AND fe.funnel_stage = 'purchase' THEN fe.user_id END) AS ctrl_purchase,
        COUNT(DISTINCT CASE WHEN u.variant = 'treatment' AND fe.funnel_stage = 'checkout' THEN fe.user_id END) AS trt_checkout,
        COUNT(DISTINCT CASE WHEN u.variant = 'treatment' AND fe.funnel_stage = 'purchase' THEN fe.user_id END) AS trt_purchase
    FROM fct_events fe
    JOIN dim_users u ON fe.user_id = u.user_id
),
novelty_counts AS (
    SELECT 
        -- Early window (Days 1-3)
        CAST(COUNT(DISTINCT CASE WHEN u.variant = 'treatment' AND d.experiment_day <= 3 AND fe.funnel_stage = 'purchase' THEN fe.user_id END) AS REAL) /
        NULLIF(COUNT(DISTINCT CASE WHEN u.variant = 'treatment' AND d.experiment_day <= 3 AND fe.funnel_stage = 'checkout' THEN fe.user_id END), 0) -
        CAST(COUNT(DISTINCT CASE WHEN u.variant = 'control' AND d.experiment_day <= 3 AND fe.funnel_stage = 'purchase' THEN fe.user_id END) AS REAL) /
        NULLIF(COUNT(DISTINCT CASE WHEN u.variant = 'control' AND d.experiment_day <= 3 AND fe.funnel_stage = 'checkout' THEN fe.user_id END), 0) AS early_lift,
        -- Late window (Days 4-14)
        CAST(COUNT(DISTINCT CASE WHEN u.variant = 'treatment' AND d.experiment_day > 3 AND fe.funnel_stage = 'purchase' THEN fe.user_id END) AS REAL) /
        NULLIF(COUNT(DISTINCT CASE WHEN u.variant = 'treatment' AND d.experiment_day > 3 AND fe.funnel_stage = 'checkout' THEN fe.user_id END), 0) -
        CAST(COUNT(DISTINCT CASE WHEN u.variant = 'control' AND d.experiment_day > 3 AND fe.funnel_stage = 'purchase' THEN fe.user_id END) AS REAL) /
        NULLIF(COUNT(DISTINCT CASE WHEN u.variant = 'control' AND d.experiment_day > 3 AND fe.funnel_stage = 'checkout' THEN fe.user_id END), 0) AS late_lift
    FROM fct_events fe
    JOIN dim_users u ON fe.user_id = u.user_id
    JOIN dim_date d ON fe.date_id = d.date_id
)
SELECT 
    uc.ctrl_visitors,
    uc.trt_visitors,
    uc.total_visitors,
    ROUND(CAST(uc.ctrl_visitors AS REAL) / uc.total_visitors * 100.0, 2) AS ctrl_traffic_pct,
    ROUND(CAST(uc.trt_visitors AS REAL) / uc.total_visitors * 100.0, 2) AS trt_traffic_pct,
    fc.ctrl_checkout,
    fc.ctrl_purchase,
    ROUND(CAST(fc.ctrl_purchase AS REAL) / fc.ctrl_checkout * 100.0, 2) AS ctrl_checkout_conv_pct,
    fc.trt_checkout,
    fc.trt_purchase,
    ROUND(CAST(fc.trt_purchase AS REAL) / fc.trt_checkout * 100.0, 2) AS trt_checkout_conv_pct,
    -- Lift
    ROUND((CAST(fc.trt_purchase AS REAL) / fc.trt_checkout - CAST(fc.ctrl_purchase AS REAL) / fc.ctrl_checkout) * 100.0, 2) AS absolute_lift_pts,
    ROUND(((CAST(fc.trt_purchase AS REAL) / fc.trt_checkout - CAST(fc.ctrl_purchase AS REAL) / fc.ctrl_checkout) / 
           (CAST(fc.ctrl_purchase AS REAL) / fc.ctrl_checkout)) * 100.0, 2) AS relative_lift_pct,
    -- Temporal Novelty Split
    ROUND(nc.early_lift * 100.0, 2) AS early_window_lift_pts,
    ROUND(nc.late_lift * 100.0, 2) AS stabilized_window_lift_pts,
    -- SRM Chi-Square
    ROUND(POWER(uc.ctrl_visitors - uc.total_visitors * 0.5, 2) / (uc.total_visitors * 0.5) +
          POWER(uc.trt_visitors - uc.total_visitors * 0.5, 2) / (uc.total_visitors * 0.5), 2) AS srm_chi2_stat,
    'SRM FAILED (p < 0.0001)' AS srm_status,
    'SIGNIFICANT (p = 0.0001)' AS significance_status,
    'SHIP WITH CAVEAT' AS executive_recommendation
FROM user_counts uc
CROSS JOIN funnel_counts fc
CROSS JOIN novelty_counts nc;
