-- ==============================================================================
-- Query 03: Daily Funnel Metrics & Novelty Tracking
-- Purpose: Compute daily funnel progression and checkout-to-purchase conversion
--          to inspect temporal decay and novelty effects between Days 1-3 and Days 4-14.
-- ==============================================================================

SELECT 
    day,
    CASE WHEN day <= 3 THEN 'Days 1-3 (Novelty)' ELSE 'Days 4-14 (Stabilized)' END AS window_period,
    variant,
    COUNT(DISTINCT CASE WHEN funnel_stage = 'visit' THEN user_id END) AS users_visit,
    COUNT(DISTINCT CASE WHEN funnel_stage = 'checkout' THEN user_id END) AS users_checkout,
    COUNT(DISTINCT CASE WHEN funnel_stage = 'payment' THEN user_id END) AS users_payment,
    COUNT(DISTINCT CASE WHEN funnel_stage = 'purchase' THEN user_id END) AS users_purchase,
    -- Step-level Payment to Purchase Conversion (%)
    ROUND(
        CAST(COUNT(DISTINCT CASE WHEN funnel_stage = 'purchase' THEN user_id END) AS REAL) / 
        NULLIF(COUNT(DISTINCT CASE WHEN funnel_stage = 'payment' THEN user_id END), 0) * 100.0, 
        2
    ) AS payment_to_purchase_conv_pct,
    -- Primary Metric: Checkout to Purchase Conversion (%)
    ROUND(
        CAST(COUNT(DISTINCT CASE WHEN funnel_stage = 'purchase' THEN user_id END) AS REAL) / 
        NULLIF(COUNT(DISTINCT CASE WHEN funnel_stage = 'checkout' THEN user_id END), 0) * 100.0, 
        2
    ) AS checkout_to_purchase_conv_pct
FROM events
GROUP BY day, variant
ORDER BY day ASC, variant ASC;
