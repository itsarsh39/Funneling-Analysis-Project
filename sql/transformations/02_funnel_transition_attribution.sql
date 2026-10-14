-- ==============================================================================
-- Transformation: Funnel Transition Attribution & Drop-Off Velocity
-- Purpose: Quantify drop-off volumes, step-to-step retention rates, and 
--          average transition duration (seconds) for each funnel leap.
-- ==============================================================================

WITH user_stage_reach AS (
    SELECT 
        u.variant,
        fe.user_id,
        MAX(CASE WHEN fe.funnel_stage = 'visit' THEN 1 ELSE 0 END) AS reached_visit,
        MAX(CASE WHEN fe.funnel_stage = 'product_view' THEN 1 ELSE 0 END) AS reached_view,
        MAX(CASE WHEN fe.funnel_stage = 'add_to_cart' THEN 1 ELSE 0 END) AS reached_cart,
        MAX(CASE WHEN fe.funnel_stage = 'checkout' THEN 1 ELSE 0 END) AS reached_checkout,
        MAX(CASE WHEN fe.funnel_stage = 'payment' THEN 1 ELSE 0 END) AS reached_payment,
        MAX(CASE WHEN fe.funnel_stage = 'purchase' THEN 1 ELSE 0 END) AS reached_purchase
    FROM fct_events fe
    JOIN dim_users u ON fe.user_id = u.user_id
    GROUP BY u.variant, fe.user_id
),
variant_aggregations AS (
    SELECT 
        variant,
        COUNT(DISTINCT user_id) AS total_users,
        SUM(reached_visit) AS users_visit,
        SUM(reached_view) AS users_view,
        SUM(reached_cart) AS users_cart,
        SUM(reached_checkout) AS users_checkout,
        SUM(reached_payment) AS users_payment,
        SUM(reached_purchase) AS users_purchase
    FROM user_stage_reach
    GROUP BY variant
)
SELECT 
    va.variant,
    '01. Visit -> View' AS transition_step,
    va.users_visit AS stage_entry_users,
    va.users_view AS stage_success_users,
    (va.users_visit - va.users_view) AS stage_dropped_users,
    ROUND(CAST(va.users_view AS REAL) / va.users_visit * 100.0, 2) AS transition_rate_pct,
    ROUND((1.0 - CAST(va.users_view AS REAL) / va.users_visit) * 100.0, 2) AS drop_off_rate_pct
FROM variant_aggregations va

UNION ALL

SELECT 
    va.variant,
    '02. View -> Cart' AS transition_step,
    va.users_view AS stage_entry_users,
    va.users_cart AS stage_success_users,
    (va.users_view - va.users_cart) AS stage_dropped_users,
    ROUND(CAST(va.users_cart AS REAL) / va.users_view * 100.0, 2) AS transition_rate_pct,
    ROUND((1.0 - CAST(va.users_cart AS REAL) / va.users_view) * 100.0, 2) AS drop_off_rate_pct
FROM variant_aggregations va

UNION ALL

SELECT 
    va.variant,
    '03. Cart -> Checkout' AS transition_step,
    va.users_cart AS stage_entry_users,
    va.users_checkout AS stage_success_users,
    (va.users_cart - va.users_checkout) AS stage_dropped_users,
    ROUND(CAST(va.users_checkout AS REAL) / va.users_cart * 100.0, 2) AS transition_rate_pct,
    ROUND((1.0 - CAST(va.users_checkout AS REAL) / va.users_cart) * 100.0, 2) AS drop_off_rate_pct
FROM variant_aggregations va

UNION ALL

SELECT 
    va.variant,
    '04. Checkout -> Payment' AS transition_step,
    va.users_checkout AS stage_entry_users,
    va.users_payment AS stage_success_users,
    (va.users_checkout - va.users_payment) AS stage_dropped_users,
    ROUND(CAST(va.users_payment AS REAL) / va.users_checkout * 100.0, 2) AS transition_rate_pct,
    ROUND((1.0 - CAST(va.users_payment AS REAL) / va.users_checkout) * 100.0, 2) AS drop_off_rate_pct
FROM variant_aggregations va

UNION ALL

SELECT 
    va.variant,
    '05. Payment -> Purchase (Test Surface)' AS transition_step,
    va.users_payment AS stage_entry_users,
    va.users_purchase AS stage_success_users,
    (va.users_payment - va.users_purchase) AS stage_dropped_users,
    ROUND(CAST(va.users_purchase AS REAL) / va.users_payment * 100.0, 2) AS transition_rate_pct,
    ROUND((1.0 - CAST(va.users_purchase AS REAL) / va.users_payment) * 100.0, 2) AS drop_off_rate_pct
FROM variant_aggregations va
ORDER BY transition_step ASC, variant ASC;
