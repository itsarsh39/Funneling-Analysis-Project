-- ==============================================================================
-- Statistical Diagnostic: SRM Root-Cause Multi-Dimensional Cross-Tabulation
-- Purpose: Pinpoint the exact device/browser subgroup driving the Sample Ratio Mismatch (SRM).
-- Mechanism: Calculates segment-level Chi-Square cell contributions assuming 50/50 split.
-- ==============================================================================

WITH segment_counts AS (
    SELECT 
        device_type,
        browser,
        COUNT(DISTINCT CASE WHEN variant = 'control' THEN user_id END) AS ctrl_users,
        COUNT(DISTINCT CASE WHEN variant = 'treatment' THEN user_id END) AS trt_users,
        COUNT(DISTINCT user_id) AS total_segment_users
    FROM dim_users
    GROUP BY device_type, browser
),
segment_srm AS (
    SELECT 
        device_type,
        browser,
        ctrl_users,
        trt_users,
        total_segment_users,
        ROUND(CAST(ctrl_users AS REAL) / total_segment_users * 100.0, 1) AS ctrl_share_pct,
        ROUND(CAST(trt_users AS REAL) / total_segment_users * 100.0, 1) AS trt_share_pct,
        -- Expected users per variant in this slice
        (total_segment_users * 0.5000) AS expected_users_per_variant,
        -- Slice Chi-Square component: (O_c - E)^2 / E + (O_t - E)^2 / E
        ROUND(
            (POWER(ctrl_users - (total_segment_users * 0.5), 2) / (total_segment_users * 0.5)) +
            (POWER(trt_users - (total_segment_users * 0.5), 2) / (total_segment_users * 0.5)),
            2
        ) AS segment_chi2_statistic
    FROM segment_counts
)
SELECT 
    device_type,
    browser,
    ctrl_users,
    trt_users,
    total_segment_users,
    ctrl_share_pct,
    trt_share_pct,
    segment_chi2_statistic,
    CASE 
        WHEN segment_chi2_statistic >= 10.828 THEN '[CRITICAL SKEW] Root-Cause Driver (p < 0.001)'
        WHEN segment_chi2_statistic >= 6.635  THEN '[MODERATE SKEW] Potential Leak (p < 0.01)'
        ELSE '[BALANCED] Randomization Valid'
    END AS segment_srm_verdict
FROM segment_srm
ORDER BY segment_chi2_statistic DESC;
