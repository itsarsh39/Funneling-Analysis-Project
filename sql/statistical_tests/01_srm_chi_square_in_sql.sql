-- ==============================================================================
-- Statistical Test: Sample Ratio Mismatch (SRM) Goodness-of-Fit in Pure SQL
-- Dialect: ANSI SQL / SQLite Compatible
-- Null Hypothesis (H0): Variant traffic follows the intended 50/50 allocation ratio.
-- Decision Rule: If Chi-Square > 6.635 (p < 0.01) or > 10.828 (p < 0.001), reject H0.
-- ==============================================================================

WITH observed AS (
    SELECT 
        variant,
        COUNT(DISTINCT user_id) AS observed_users
    FROM dim_users
    GROUP BY variant
),
totals AS (
    SELECT 
        SUM(observed_users) AS total_users,
        0.5000 AS expected_ratio
    FROM observed
),
chi_square_components AS (
    SELECT 
        o.variant,
        o.observed_users,
        t.total_users,
        ROUND(CAST(o.observed_users AS REAL) / t.total_users, 4) AS observed_ratio,
        t.expected_ratio,
        ROUND(t.total_users * t.expected_ratio, 1) AS expected_users,
        ROUND(o.observed_users - (t.total_users * t.expected_ratio), 1) AS diff_from_expected,
        -- Chi-Square cell formula: (O - E)^2 / E
        POWER(o.observed_users - (t.total_users * t.expected_ratio), 2) / (t.total_users * t.expected_ratio) AS chi2_cell
    FROM observed o
    CROSS JOIN totals t
),
overall_test AS (
    SELECT 
        SUM(chi2_cell) AS total_chi2_statistic,
        1 AS degrees_of_freedom,
        6.635 AS critical_value_alpha_01,
        10.828 AS critical_value_alpha_001
    FROM chi_square_components
)
SELECT 
    c.variant,
    c.observed_users,
    c.total_users,
    (c.observed_ratio * 100.0) AS observed_pct,
    (c.expected_ratio * 100.0) AS expected_pct,
    c.diff_from_expected,
    ROUND(c.chi2_cell, 3) AS cell_chi2_contribution,
    ROUND(ot.total_chi2_statistic, 3) AS total_chi2_statistic,
    CASE 
        WHEN ot.total_chi2_statistic > ot.critical_value_alpha_001 THEN 'CRITICAL ALERT: SRM Severe (p < 0.001)'
        WHEN ot.total_chi2_statistic > ot.critical_value_alpha_01 THEN 'WARNING: SRM Detected (p < 0.01)'
        ELSE 'PASSED: Traffic Ratio Balanced'
    END AS srm_diagnostic_result
FROM chi_square_components c
CROSS JOIN overall_test ot
ORDER BY c.variant ASC;
