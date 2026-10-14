-- ==============================================================================
-- Statistical Test: Heterogeneous Treatment Effects (HTE) by Segment
-- Purpose: Inspect whether checkout-to-purchase lift varies across user sub-populations
--          (device types, acquisition channels, and countries) to detect subgroup bias.
-- ==============================================================================

-- 1. Lift by Device Type
WITH device_funnel AS (
    SELECT 
        u.device_type,
        u.variant,
        COUNT(DISTINCT CASE WHEN fe.funnel_stage = 'checkout' THEN fe.user_id END) AS checkout_users,
        COUNT(DISTINCT CASE WHEN fe.funnel_stage = 'purchase' THEN fe.user_id END) AS purchase_users
    FROM fct_events fe
    JOIN dim_users u ON fe.user_id = u.user_id
    GROUP BY u.device_type, u.variant
),
device_pivoted AS (
    SELECT 
        device_type,
        MAX(CASE WHEN variant = 'control' THEN checkout_users END) AS ctrl_n,
        MAX(CASE WHEN variant = 'control' THEN purchase_users END) AS ctrl_x,
        MAX(CASE WHEN variant = 'treatment' THEN checkout_users END) AS trt_n,
        MAX(CASE WHEN variant = 'treatment' THEN purchase_users END) AS trt_x
    FROM device_funnel
    GROUP BY device_type
)
SELECT 
    'Device Type' AS segment_dimension,
    device_type AS segment_value,
    ctrl_n AS control_n,
    ctrl_x AS control_conversions,
    ROUND(CAST(ctrl_x AS REAL) / ctrl_n * 100.0, 2) AS control_conv_pct,
    trt_n AS treatment_n,
    trt_x AS treatment_conversions,
    ROUND(CAST(trt_x AS REAL) / trt_n * 100.0, 2) AS treatment_conv_pct,
    ROUND((CAST(trt_x AS REAL) / trt_n - CAST(ctrl_x AS REAL) / ctrl_n) * 100.0, 2) AS absolute_lift_pts,
    ROUND(((CAST(trt_x AS REAL) / trt_n - CAST(ctrl_x AS REAL) / ctrl_n) / (CAST(ctrl_x AS REAL) / ctrl_n)) * 100.0, 1) AS relative_lift_pct
FROM device_pivoted

UNION ALL

-- 2. Lift by Traffic Source
SELECT 
    'Traffic Source' AS segment_dimension,
    u.traffic_source AS segment_value,
    COUNT(DISTINCT CASE WHEN u.variant = 'control' AND fe.funnel_stage = 'checkout' THEN fe.user_id END) AS control_n,
    COUNT(DISTINCT CASE WHEN u.variant = 'control' AND fe.funnel_stage = 'purchase' THEN fe.user_id END) AS control_conversions,
    ROUND(CAST(COUNT(DISTINCT CASE WHEN u.variant = 'control' AND fe.funnel_stage = 'purchase' THEN fe.user_id END) AS REAL) / 
          NULLIF(COUNT(DISTINCT CASE WHEN u.variant = 'control' AND fe.funnel_stage = 'checkout' THEN fe.user_id END), 0) * 100.0, 2) AS control_conv_pct,
    COUNT(DISTINCT CASE WHEN u.variant = 'treatment' AND fe.funnel_stage = 'checkout' THEN fe.user_id END) AS treatment_n,
    COUNT(DISTINCT CASE WHEN u.variant = 'treatment' AND fe.funnel_stage = 'purchase' THEN fe.user_id END) AS treatment_conversions,
    ROUND(CAST(COUNT(DISTINCT CASE WHEN u.variant = 'treatment' AND fe.funnel_stage = 'purchase' THEN fe.user_id END) AS REAL) / 
          NULLIF(COUNT(DISTINCT CASE WHEN u.variant = 'treatment' AND fe.funnel_stage = 'checkout' THEN fe.user_id END), 0) * 100.0, 2) AS treatment_conv_pct,
    ROUND((CAST(COUNT(DISTINCT CASE WHEN u.variant = 'treatment' AND fe.funnel_stage = 'purchase' THEN fe.user_id END) AS REAL) / 
           NULLIF(COUNT(DISTINCT CASE WHEN u.variant = 'treatment' AND fe.funnel_stage = 'checkout' THEN fe.user_id END), 0) -
           CAST(COUNT(DISTINCT CASE WHEN u.variant = 'control' AND fe.funnel_stage = 'purchase' THEN fe.user_id END) AS REAL) / 
           NULLIF(COUNT(DISTINCT CASE WHEN u.variant = 'control' AND fe.funnel_stage = 'checkout' THEN fe.user_id END), 0)) * 100.0, 2) AS absolute_lift_pts,
    ROUND(((CAST(COUNT(DISTINCT CASE WHEN u.variant = 'treatment' AND fe.funnel_stage = 'purchase' THEN fe.user_id END) AS REAL) / 
            NULLIF(COUNT(DISTINCT CASE WHEN u.variant = 'treatment' AND fe.funnel_stage = 'checkout' THEN fe.user_id END), 0) -
            CAST(COUNT(DISTINCT CASE WHEN u.variant = 'control' AND fe.funnel_stage = 'purchase' THEN fe.user_id END) AS REAL) / 
            NULLIF(COUNT(DISTINCT CASE WHEN u.variant = 'control' AND fe.funnel_stage = 'checkout' THEN fe.user_id END), 0)) /
           (CAST(COUNT(DISTINCT CASE WHEN u.variant = 'control' AND fe.funnel_stage = 'purchase' THEN fe.user_id END) AS REAL) / 
            NULLIF(COUNT(DISTINCT CASE WHEN u.variant = 'control' AND fe.funnel_stage = 'checkout' THEN fe.user_id END), 0))) * 100.0, 1) AS relative_lift_pct
FROM fct_events fe
JOIN dim_users u ON fe.user_id = u.user_id
GROUP BY u.traffic_source

ORDER BY segment_dimension ASC, absolute_lift_pts DESC;
