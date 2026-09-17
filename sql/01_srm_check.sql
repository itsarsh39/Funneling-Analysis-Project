-- ==============================================================================
-- Query 01: Sample Ratio Mismatch (SRM) Traffic Aggregation
-- Purpose: Count unique users per variant and compute observed vs. expected 
--          allocations (assuming 50/50 split) for Chi-Square goodness-of-fit.
-- ==============================================================================

WITH user_assignments AS (
    SELECT 
        user_id,
        variant
    FROM events
    GROUP BY user_id, variant
),
variant_counts AS (
    SELECT 
        variant,
        COUNT(DISTINCT user_id) AS observed_users
    FROM user_assignments
    GROUP BY variant
),
total_users AS (
    SELECT 
        SUM(observed_users) AS total_sample_size
    FROM variant_counts
)
SELECT 
    vc.variant,
    vc.observed_users,
    tu.total_sample_size,
    ROUND(CAST(vc.observed_users AS REAL) / tu.total_sample_size, 4) AS observed_ratio,
    0.5000 AS expected_ratio,
    ROUND(tu.total_sample_size * 0.5000, 1) AS expected_users,
    ROUND(vc.observed_users - (tu.total_sample_size * 0.5000), 1) AS difference,
    -- Chi-Square component: (O - E)^2 / E
    ROUND(
        POWER(vc.observed_users - (tu.total_sample_size * 0.5000), 2) / (tu.total_sample_size * 0.5000), 
        4
    ) AS chi_square_component
FROM variant_counts vc
CROSS JOIN total_users tu
ORDER BY vc.variant ASC;
