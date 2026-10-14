-- ==============================================================================
-- Analytical Mart: Revenue & Financial Business Impact Analysis
-- Purpose: Quantifies gross revenue, Average Order Value (AOV), Revenue Per User (ARPU),
--          and annualized GMV business forecasts based on stabilized lift (+2.19 pts).
-- ==============================================================================

WITH user_base AS (
    SELECT 
        variant,
        COUNT(DISTINCT user_id) AS total_visitors
    FROM dim_users
    GROUP BY variant
),
order_aggregations AS (
    SELECT 
        u.variant,
        COUNT(DISTINCT o.order_id) AS total_orders,
        SUM(o.revenue_usd) AS gross_revenue_usd,
        AVG(o.revenue_usd) AS average_order_value_usd,
        SUM(o.items_count) AS total_items_sold,
        CAST(SUM(o.items_count) AS REAL) / COUNT(DISTINCT o.order_id) AS average_basket_size
    FROM fct_orders o
    JOIN dim_users u ON o.user_id = u.user_id
    GROUP BY u.variant
),
combined_metrics AS (
    SELECT 
        ub.variant,
        ub.total_visitors,
        oa.total_orders,
        oa.gross_revenue_usd,
        oa.average_order_value_usd,
        ROUND(oa.gross_revenue_usd / ub.total_visitors, 2) AS arpu_usd,
        oa.total_items_sold,
        oa.average_basket_size
    FROM user_base ub
    JOIN order_aggregations oa ON ub.variant = oa.variant
),
comparison AS (
    SELECT 
        MAX(CASE WHEN variant = 'control' THEN total_visitors END) AS ctrl_users,
        MAX(CASE WHEN variant = 'control' THEN gross_revenue_usd END) AS ctrl_rev,
        MAX(CASE WHEN variant = 'control' THEN average_order_value_usd END) AS ctrl_aov,
        MAX(CASE WHEN variant = 'control' THEN arpu_usd END) AS ctrl_arpu,
        MAX(CASE WHEN variant = 'treatment' THEN total_visitors END) AS trt_users,
        MAX(CASE WHEN variant = 'treatment' THEN gross_revenue_usd END) AS trt_rev,
        MAX(CASE WHEN variant = 'treatment' THEN average_order_value_usd END) AS trt_aov,
        MAX(CASE WHEN variant = 'treatment' THEN arpu_usd END) AS trt_arpu
    FROM combined_metrics
)
SELECT 
    '14-Day Experiment Actuals' AS timeframe,
    ROUND(ctrl_rev, 2) AS control_revenue_usd,
    ROUND(trt_rev, 2) AS treatment_revenue_usd,
    ROUND(trt_rev - ctrl_rev, 2) AS incremental_revenue_usd,
    ROUND(((trt_rev - ctrl_rev) / ctrl_rev) * 100.0, 1) AS revenue_growth_pct,
    ROUND(ctrl_aov, 2) AS control_aov,
    ROUND(trt_aov, 2) AS treatment_aov,
    ctrl_arpu AS control_arpu,
    trt_arpu AS treatment_arpu,
    -- Annualized Projection (365 / 14 days) based on conservative stabilized baseline lift
    ROUND((trt_rev - ctrl_rev) * (365.0 / 14.0), 2) AS unadjusted_annualized_lift_usd,
    -- Guardrail adjusted projection discounting novelty burst (scaled to +2.19 pts / +2.86 pts = ~76.6% factor)
    ROUND((trt_rev - ctrl_rev) * (365.0 / 14.0) * (2.19 / 2.86), 2) AS conservative_stabilized_annualized_gmv_usd
FROM comparison;
