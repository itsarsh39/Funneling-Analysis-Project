"""
Main Experiment Analysis Pipeline
Integrates SQL queries, statistical tests, power calculation, and recommendation engine.
Outputs structured JSON and console report.
"""

import os
import json
import sqlite3
import pandas as pd
import numpy as np

from power_analysis import calculate_required_sample_size, calculate_achieved_power, format_power_summary
from hypothesis_testing import (
    test_primary_metric,
    test_sample_ratio_mismatch,
    test_novelty_effect,
    analyze_stage_by_stage_lift
)
from recommendation import generate_experiment_recommendation, format_recommendation_block


def load_sql_query(query_path):
    with open(query_path, 'r') as f:
        return f.read()


def run_full_analysis(db_path="data/events.db", output_json="analysis/results.json"):
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}. Please run data/generate_data.py first.")

    conn = sqlite3.connect(db_path)

    # 1. Execute SQL Aggregations
    print("Executing SQL Aggregation Queries...")
    df_srm = pd.read_sql_query(load_sql_query("sql/01_srm_check.sql"), conn)
    df_funnel = pd.read_sql_query(load_sql_query("sql/02_funnel_by_variant.sql"), conn)
    df_daily = pd.read_sql_query(load_sql_query("sql/03_funnel_daily.sql"), conn)
    conn.close()

    # 2. Extract Key Variables for Tests
    ctrl_funnel = df_funnel[df_funnel['variant'] == 'control'].iloc[0]
    trt_funnel = df_funnel[df_funnel['variant'] == 'treatment'].iloc[0]

    obs_ctrl = int(df_srm[df_srm['variant'] == 'control']['observed_users'].iloc[0])
    obs_trt = int(df_srm[df_srm['variant'] == 'treatment']['observed_users'].iloc[0])

    c_chk, c_pur = int(ctrl_funnel['users_checkout']), int(ctrl_funnel['users_purchase'])
    t_chk, t_pur = int(trt_funnel['users_checkout']), int(trt_funnel['users_purchase'])

    # 3. Pre-registration & Power Analysis
    prereg = calculate_required_sample_size(p_baseline=0.12, mde=0.02, alpha=0.05, power=0.80)
    p_ctrl = c_pur / c_chk
    p_trt = t_pur / t_chk
    power_stats = calculate_achieved_power(p_ctrl, p_trt, c_chk, t_chk, alpha=0.05)

    # 4. Statistical Hypothesis Testing
    primary_stats = test_primary_metric(c_pur, c_chk, t_pur, t_chk, alpha=0.05)
    srm_stats = test_sample_ratio_mismatch(obs_ctrl, obs_trt, expected_split=(0.50, 0.50), threshold=0.01)
    novelty_stats = test_novelty_effect(df_daily, alpha=0.05)
    stage_stats_df = analyze_stage_by_stage_lift(df_funnel, alpha=0.05)

    # 5. Recommendation Engine
    rec = generate_experiment_recommendation(primary_stats, srm_stats, novelty_stats, stage_stats_df, power_stats)

    # 6. Compile JSON Artifact
    results = {
        'preregistration': prereg,
        'power_analysis': power_stats,
        'primary_metric': primary_stats,
        'sample_ratio_mismatch': srm_stats,
        'novelty_effect': novelty_stats,
        'stage_breakdown': stage_stats_df.to_dict(orient='records'),
        'recommendation': rec
    }

    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, 'w') as f:
        json.dump(results, f, indent=2)

    # 7. Print Console Presentation
    print("\n" + format_power_summary(prereg, power_stats))
    
    print("\n" + "=" * 78)
    print("                     PRIMARY METRIC HYPOTHESIS TEST")
    print("=" * 78)
    print(f"Control Conversion:      {c_pur:,} / {c_chk:,} ({p_ctrl * 100:.2f}%)")
    print(f"Treatment Conversion:    {t_pur:,} / {t_chk:,} ({p_trt * 100:.2f}%)")
    print(f"Absolute Lift:           {primary_stats['absolute_lift_pts']:+.2f} pts (95% CI: [{primary_stats['ci_lower_pts']:+.2f}, {primary_stats['ci_upper_pts']:+.2f}] pts)")
    print(f"Relative Lift:           {primary_stats['relative_lift_pct']:+.2f}% (95% CI: [{primary_stats['ci_relative_lower_pct']:+.2f}%, {primary_stats['ci_relative_upper_pct']:+.2f}%])")
    print(f"Z-Statistic:             {primary_stats['z_statistic']:.3f}")
    print(f"P-Value (two-tailed):    {primary_stats['p_value']:.4e} ({'Significant at alpha=0.05' if primary_stats['is_statistically_significant'] else 'Not significant'})")

    print("\n" + "=" * 78)
    print("                     SAMPLE RATIO MISMATCH (SRM) CHECK")
    print("=" * 78)
    print(f"Control Users:           {srm_stats['observed_control']:,} ({srm_stats['observed_control_pct']:.2f}%)")
    print(f"Treatment Users:         {srm_stats['observed_treatment']:,} ({srm_stats['observed_treatment_pct']:.2f}%)")
    print(f"Chi-Square Statistic:    {srm_stats['chi2_statistic']:.3f} (df=1)")
    print(f"P-Value:                 {srm_stats['p_value']:.4e}")
    print(f"Diagnostic Status:       {'[FAILED] SRM Detected!' if srm_stats['srm_detected'] else '[PASSED] No SRM Detected'}")

    print("\n" + "=" * 78)
    print("                     NOVELTY EFFECT DIAGNOSTIC")
    print("=" * 78)
    print(f"Days 1-3  (Early Window): Control = {novelty_stats['early_control_conv']:.2f}%, Treatment = {novelty_stats['early_treatment_conv']:.2f}% -> Lift = {novelty_stats['early_lift_pts']:+.2f} pts")
    print(f"Days 4-14 (Late Window):  Control = {novelty_stats['late_control_conv']:.2f}%, Treatment = {novelty_stats['late_treatment_conv']:.2f}% -> Lift = {novelty_stats['late_lift_pts']:+.2f} pts")
    print(f"Temporal Decay:          {novelty_stats['decay_magnitude_pts']:.2f} pts decay (Z = {novelty_stats['z_statistic']:.2f}, p = {novelty_stats['p_value_one_sided']:.4f})")
    print(f"Diagnostic Status:       {'[FLAGGED] Novelty Effect Significant' if novelty_stats['novelty_detected'] else '[PASSED] Stable Effect'}")

    print("\n" + "=" * 78)
    print("                     FUNNEL STAGE DECOMPOSITION (FOREST PLOT DATA)")
    print("=" * 78)
    print(f"{'Transition':<30} | {'Lift (pts)':<10} | {'95% CI':<18} | {'P-Value':<10} | {'Significant?'}")
    print("-" * 78)
    for _, row in stage_stats_df.iterrows():
        ci_str = f"[{row['ci_lower_pts']:+.2f}, {row['ci_upper_pts']:+.2f}]"
        sig_str = "YES (*)" if row['significant'] else "NO"
        print(f"{row['transition']:<30} | {row['absolute_lift_pts']:>+9.2f}% | {ci_str:<18} | {row['p_value']:<10.4f} | {sig_str}")

    print("\n" + format_recommendation_block(rec))
    print(f"\nResults successfully exported to {output_json}\n")


if __name__ == "__main__":
    run_full_analysis()
