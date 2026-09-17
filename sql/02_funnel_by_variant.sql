-- ==============================================================================
-- Query 02: Funnel Aggregation by Variant
-- Purpose: Compute unique users entering each funnel stage, step-to-step 
--          conversion rates, and the primary metric (checkout -> purchase).
-- ==============================================================================

WITH stage_users AS (
    SELECT 
        variant,
        COUNT(DISTINCT CASE WHEN funnel_stage = 'visit' THEN user_id END) AS users_visit,
        COUNT(DISTINCT CASE WHEN funnel_stage = 'product_view' THEN user_id END) AS users_product_view,
        COUNT(DISTINCT CASE WHEN funnel_stage = 'add_to_cart' THEN user_id END) AS users_add_to_cart,
        COUNT(DISTINCT CASE WHEN funnel_stage = 'checkout' THEN user_id END) AS users_checkout,
        COUNT(DISTINCT CASE WHEN funnel_stage = 'payment' THEN user_id END) AS users_payment,
        COUNT(DISTINCT CASE WHEN funnel_stage = 'purchase' THEN user_id END) AS users_purchase
    FROM events
    GROUP BY variant
)
SELECT 
    variant,
    users_visit,
    users_product_view,
    ROUND(CAST(users_product_view AS REAL) / NULLIF(users_visit, 0) * 100.0, 2) AS conv_visit_to_view_pct,
    users_add_to_cart,
    ROUND(CAST(users_add_to_cart AS REAL) / NULLIF(users_product_view, 0) * 100.0, 2) AS conv_view_to_cart_pct,
    users_checkout,
    ROUND(CAST(users_checkout AS REAL) / NULLIF(users_add_to_cart, 0) * 100.0, 2) AS conv_cart_to_checkout_pct,
    users_payment,
    ROUND(CAST(users_payment AS REAL) / NULLIF(users_checkout, 0) * 100.0, 2) AS conv_checkout_to_payment_pct,
    users_purchase,
    ROUND(CAST(users_purchase AS REAL) / NULLIF(users_payment, 0) * 100.0, 2) AS conv_payment_to_purchase_pct,
    -- Primary Metric: Checkout -> Purchase conversion
    ROUND(CAST(users_purchase AS REAL) / NULLIF(users_checkout, 0) * 100.0, 2) AS primary_checkout_to_purchase_conv_pct
FROM stage_users
ORDER BY variant ASC;
