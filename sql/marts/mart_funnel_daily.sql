-- ==============================================================================
-- Analytical Mart: Daily Funnel Progression & Temporal Novelty Metrics
-- Purpose: Pre-aggregated daily funnel metrics optimized for Power BI time-series 
--          visuals and rolling conversion lift tracking.
-- ==============================================================================

SELECT 
    d.date,
    d.experiment_day,
    d.day_name,
    d.is_weekend,
    d.window_period,
    u.variant,
    COUNT(DISTINCT CASE WHEN fe.funnel_stage = 'visit' THEN fe.user_id END) AS users_visit,
    COUNT(DISTINCT CASE WHEN fe.funnel_stage = 'product_view' THEN fe.user_id END) AS users_view,
    COUNT(DISTINCT CASE WHEN fe.funnel_stage = 'add_to_cart' THEN fe.user_id END) AS users_cart,
    COUNT(DISTINCT CASE WHEN fe.funnel_stage = 'checkout' THEN fe.user_id END) AS users_checkout,
    COUNT(DISTINCT CASE WHEN fe.funnel_stage = 'payment' THEN fe.user_id END) AS users_payment,
    COUNT(DISTINCT CASE WHEN fe.funnel_stage = 'purchase' THEN fe.user_id END) AS users_purchase,
    -- Step Conversion Rates
    ROUND(
        CAST(COUNT(DISTINCT CASE WHEN fe.funnel_stage = 'payment' THEN fe.user_id END) AS REAL) /
        NULLIF(COUNT(DISTINCT CASE WHEN fe.funnel_stage = 'checkout' THEN fe.user_id END), 0) * 100.0, 
        2
    ) AS conv_checkout_to_payment_pct,
    ROUND(
        CAST(COUNT(DISTINCT CASE WHEN fe.funnel_stage = 'purchase' THEN fe.user_id END) AS REAL) /
        NULLIF(COUNT(DISTINCT CASE WHEN fe.funnel_stage = 'payment' THEN fe.user_id END), 0) * 100.0, 
        2
    ) AS conv_payment_to_purchase_pct,
    -- Primary Metric: Checkout -> Purchase
    ROUND(
        CAST(COUNT(DISTINCT CASE WHEN fe.funnel_stage = 'purchase' THEN fe.user_id END) AS REAL) /
        NULLIF(COUNT(DISTINCT CASE WHEN fe.funnel_stage = 'checkout' THEN fe.user_id END), 0) * 100.0, 
        2
    ) AS checkout_to_purchase_conv_pct
FROM fct_events fe
JOIN dim_users u ON fe.user_id = u.user_id
JOIN dim_date d ON fe.date_id = d.date_id
GROUP BY d.date, d.experiment_day, d.day_name, d.is_weekend, d.window_period, u.variant
ORDER BY d.experiment_day ASC, u.variant ASC;
