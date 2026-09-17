"""
Statistical Hypothesis Testing Module
Implements:
1. Two-proportion z-test on primary metric with 95% Confidence Intervals.
2. Chi-square Goodness-of-Fit test for Sample Ratio Mismatch (SRM).
3. Novelty Effect Difference-in-Differences test (Days 1-3 vs Days 4-14).
4. Stage-by-Stage Funnel lift decomposition with Confidence Intervals.
"""

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest, confint_proportions_2indep


def test_primary_metric(count_ctrl, nobs_ctrl, count_trt, nobs_trt, alpha=0.05):
    """
    Performs a two-proportion z-test for checkout -> purchase conversion.
    Computes absolute lift, relative lift, standard error, 95% CI, and p-value.
    """
    p_ctrl = count_ctrl / nobs_ctrl
    p_trt = count_trt / nobs_trt
    abs_lift = p_trt - p_ctrl
    rel_lift = abs_lift / p_ctrl

    # Unpooled standard error for confidence interval
    se_diff = np.sqrt((p_ctrl * (1 - p_ctrl) / nobs_ctrl) + (p_trt * (1 - p_trt) / nobs_trt))
    z_crit = stats.norm.ppf(1 - alpha / 2)
    ci_lower_abs = abs_lift - z_crit * se_diff
    ci_upper_abs = abs_lift + z_crit * se_diff

    # Relative CI
    ci_lower_rel = ci_lower_abs / p_ctrl
    ci_upper_rel = ci_upper_abs / p_ctrl

    # Two-proportion z-test (statsmodels pooled variance)
    count = np.array([count_trt, count_ctrl])
    nobs = np.array([nobs_trt, nobs_ctrl])
    z_stat, p_value = proportions_ztest(count, nobs, alternative='two-sided')

    return {
        'metric_name': 'Checkout to Purchase Conversion',
        'nobs_control': int(nobs_ctrl),
        'count_control': int(count_ctrl),
        'rate_control': float(p_ctrl),
        'nobs_treatment': int(nobs_trt),
        'count_treatment': int(count_trt),
        'rate_treatment': float(p_trt),
        'absolute_lift': float(abs_lift),
        'absolute_lift_pts': float(abs_lift * 100),
        'relative_lift_pct': float(rel_lift * 100),
        'standard_error': float(se_diff),
        'ci_lower_pts': float(ci_lower_abs * 100),
        'ci_upper_pts': float(ci_upper_abs * 100),
        'ci_relative_lower_pct': float(ci_lower_rel * 100),
        'ci_relative_upper_pct': float(ci_upper_rel * 100),
        'z_statistic': float(z_stat),
        'p_value': float(p_value),
        'is_statistically_significant': bool(p_value < alpha),
        'alpha': alpha
    }


def test_sample_ratio_mismatch(obs_ctrl, obs_trt, expected_split=(0.50, 0.50), threshold=0.01):
    """
    Performs a Chi-square goodness-of-fit test to check for Sample Ratio Mismatch (SRM).
    Industry convention uses alpha=0.01 or 0.001 to avoid false alarms.
    """
    total = obs_ctrl + obs_trt
    exp_ctrl = total * expected_split[0]
    exp_trt = total * expected_split[1]

    observed = np.array([obs_ctrl, obs_trt])
    expected = np.array([exp_ctrl, exp_trt])

    chi2_stat, p_val = stats.chisquare(f_obs=observed, f_exp=expected)
    srm_detected = bool(p_val < threshold)

    return {
        'total_users': int(total),
        'observed_control': int(obs_ctrl),
        'observed_treatment': int(obs_trt),
        'observed_control_pct': float(obs_ctrl / total * 100),
        'observed_treatment_pct': float(obs_trt / total * 100),
        'expected_control_pct': float(expected_split[0] * 100),
        'expected_treatment_pct': float(expected_split[1] * 100),
        'chi2_statistic': float(chi2_stat),
        'p_value': float(p_val),
        'threshold': threshold,
        'srm_detected': srm_detected,
        'verdict': "SAMPLE RATIO MISMATCH DETECTED (Data Integrity Issue)" if srm_detected else "PASSED (No SRM detected)"
    }


def test_novelty_effect(daily_df, alpha=0.05):
    """
    Compares checkout->purchase lift in Days 1-3 (Novelty window) 
    vs Days 4-14 (Stabilized window) using an interaction z-test.
    """
    # Aggregate early (days 1-3)
    early = daily_df[daily_df['day'] <= 3].groupby('variant')[['users_checkout', 'users_purchase']].sum()
    late = daily_df[daily_df['day'] > 3].groupby('variant')[['users_checkout', 'users_purchase']].sum()

    # Early metrics
    c_chk_e, c_pur_e = early.loc['control', 'users_checkout'], early.loc['control', 'users_purchase']
    t_chk_e, t_pur_e = early.loc['treatment', 'users_checkout'], early.loc['treatment', 'users_purchase']
    p_ctrl_e = c_pur_e / c_chk_e
    p_trt_e = t_pur_e / t_chk_e
    lift_early = p_trt_e - p_ctrl_e
    se_early = np.sqrt(p_ctrl_e * (1 - p_ctrl_e) / c_chk_e + p_trt_e * (1 - p_trt_e) / t_chk_e)

    # Late metrics
    c_chk_l, c_pur_l = late.loc['control', 'users_checkout'], late.loc['control', 'users_purchase']
    t_chk_l, t_pur_l = late.loc['treatment', 'users_checkout'], late.loc['treatment', 'users_purchase']
    p_ctrl_l = c_pur_l / c_chk_l
    p_trt_l = t_pur_l / t_chk_l
    lift_late = p_trt_l - p_ctrl_l
    se_late = np.sqrt(p_ctrl_l * (1 - p_ctrl_l) / c_chk_l + p_trt_l * (1 - p_trt_l) / t_chk_l)

    # Difference in lifts (Novelty decay)
    decay = lift_early - lift_late
    se_decay = np.sqrt(se_early**2 + se_late**2)
    z_decay = decay / se_decay
    p_decay = 1 - stats.norm.cdf(z_decay)  # One-sided test: is early lift strictly greater?

    return {
        'early_days': '1-3',
        'late_days': '4-14',
        'early_control_conv': float(p_ctrl_e * 100),
        'early_treatment_conv': float(p_trt_e * 100),
        'early_lift_pts': float(lift_early * 100),
        'late_control_conv': float(p_ctrl_l * 100),
        'late_treatment_conv': float(p_trt_l * 100),
        'late_lift_pts': float(lift_late * 100),
        'decay_magnitude_pts': float(decay * 100),
        'z_statistic': float(z_decay),
        'p_value_one_sided': float(p_decay),
        'p_value_two_sided': float(2 * (1 - stats.norm.cdf(abs(z_decay)))),
        'novelty_detected': bool(p_decay < alpha and decay > 0)
    }


def analyze_stage_by_stage_lift(funnel_variant_df, alpha=0.05):
    """
    Computes step-to-step conversion lift and 95% Confidence Intervals for each funnel transition.
    Stages:
    1. visit -> product_view
    2. product_view -> add_to_cart
    3. add_to_cart -> checkout
    4. checkout -> payment
    5. payment -> purchase
    """
    ctrl = funnel_variant_df[funnel_variant_df['variant'] == 'control'].iloc[0]
    trt = funnel_variant_df[funnel_variant_df['variant'] == 'treatment'].iloc[0]

    transitions = [
        ('visit -> product_view', 'users_visit', 'users_product_view'),
        ('product_view -> add_to_cart', 'users_product_view', 'users_add_to_cart'),
        ('add_to_cart -> checkout', 'users_add_to_cart', 'users_checkout'),
        ('checkout -> payment', 'users_checkout', 'users_payment'),
        ('payment -> purchase', 'users_payment', 'users_purchase'),
        ('checkout -> purchase (Primary)', 'users_checkout', 'users_purchase')
    ]

    results = []
    z_crit = stats.norm.ppf(1 - alpha / 2)

    for name, denom_col, num_col in transitions:
        c_denom = ctrl[denom_col]
        c_num = ctrl[num_col]
        t_denom = trt[denom_col]
        t_num = trt[num_col]

        c_rate = c_num / c_denom
        t_rate = t_num / t_denom
        abs_diff = t_rate - c_rate
        se = np.sqrt(c_rate * (1 - c_rate) / c_denom + t_rate * (1 - t_rate) / t_denom)
        
        ci_low = (abs_diff - z_crit * se) * 100
        ci_high = (abs_diff + z_crit * se) * 100

        counts = np.array([t_num, c_num])
        nobss = np.array([t_denom, c_denom])
        _, p_val = proportions_ztest(counts, nobss, alternative='two-sided')

        results.append({
            'transition': name,
            'control_base': int(c_denom),
            'control_conv_users': int(c_num),
            'control_rate_pct': float(c_rate * 100),
            'treatment_base': int(t_denom),
            'treatment_conv_users': int(t_num),
            'treatment_rate_pct': float(t_rate * 100),
            'absolute_lift_pts': float(abs_diff * 100),
            'ci_lower_pts': float(ci_low),
            'ci_upper_pts': float(ci_high),
            'p_value': float(p_val),
            'significant': bool(p_val < alpha)
        })

    return pd.DataFrame(results)
