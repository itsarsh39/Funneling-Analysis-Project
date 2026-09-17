"""
Pre-Registration Power Analysis Module
Calculates sample size requirements and post-hoc achieved power using statsmodels.

Pre-registration parameters:
- Metric: Checkout to Purchase conversion rate
- Baseline conversion rate (p1): 12.0%
- Minimum Detectable Effect (MDE, absolute): +2.0 percentage points (12.0% -> 14.0%)
- Significance level (alpha): 0.05 (two-tailed)
- Statistical power (1 - beta): 0.80 (80%)
"""

import numpy as np
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize


def calculate_required_sample_size(p_baseline=0.12, mde=0.02, alpha=0.05, power=0.80):
    """
    Computes required sample size per variant for a two-proportion test.
    
    Parameters:
    - p_baseline: Baseline conversion rate (e.g. 0.12)
    - mde: Minimum Detectable Effect (e.g. 0.02 for +2.0 pts)
    - alpha: Significance level (default 0.05)
    - power: Target statistical power (default 0.80)
    
    Returns:
    - dict with effect_size, required_n_per_variant, total_required_n
    """
    p_treatment = p_baseline + mde
    effect_size = proportion_effectsize(p_treatment, p_baseline)
    
    analysis = NormalIndPower()
    n_required = analysis.solve_power(
        effect_size=effect_size,
        power=power,
        alpha=alpha,
        ratio=1.0,
        alternative='two-sided'
    )
    
    n_per_variant = int(np.ceil(n_required))
    return {
        'baseline_rate': p_baseline,
        'target_rate': p_treatment,
        'mde_absolute': mde,
        'mde_relative_pct': (mde / p_baseline) * 100,
        'alpha': alpha,
        'target_power': power,
        'effect_size_h': effect_size,
        'required_n_per_variant': n_per_variant,
        'total_required_n': n_per_variant * 2
    }


def calculate_achieved_power(p_control, p_treatment, n_control, n_treatment, alpha=0.05):
    """
    Computes post-hoc statistical power given actual sample sizes and observed effect.
    """
    effect_size = proportion_effectsize(p_treatment, p_control)
    ratio = n_treatment / n_control
    
    analysis = NormalIndPower()
    achieved_power = analysis.power(
        effect_size=effect_size,
        nobs1=n_control,
        alpha=alpha,
        ratio=ratio,
        alternative='two-sided'
    )
    
    return {
        'n_control': n_control,
        'n_treatment': n_treatment,
        'ratio': ratio,
        'effect_size_h': effect_size,
        'alpha': alpha,
        'achieved_power': float(achieved_power),
        'is_adequately_powered': bool(achieved_power >= 0.80)
    }


def format_power_summary(prereg, achieved):
    """
    Returns a human-readable pre-registration and power analysis report.
    """
    lines = [
        "=" * 70,
        "          PRE-REGISTRATION SPECIFICATION & POWER ANALYSIS",
        "=" * 70,
        f"Hypothesis: H0: p_trt - p_ctrl = 0 vs. H1: p_trt - p_ctrl != 0",
        f"Primary Metric:         Checkout -> Purchase Conversion Rate",
        f"Baseline Rate (p0):     {prereg['baseline_rate'] * 100:.1f}%",
        f"Target MDE:             +{prereg['mde_absolute'] * 100:.1f} pts ({prereg['mde_relative_pct']:.1f}% relative)",
        f"Alpha / Target Power:   {prereg['alpha']} / {prereg['target_power'] * 100:.0f}%",
        f"Required Sample / Var:  {prereg['required_n_per_variant']:,} checkout users",
        f"Total Required Sample:  {prereg['total_required_n']:,} checkout users",
        "-" * 70,
        f"Actual Sample (Control):   {achieved['n_control']:,} checkout users",
        f"Actual Sample (Treatment): {achieved['n_treatment']:,} checkout users",
        f"Total Actual Sample:       {achieved['n_control'] + achieved['n_treatment']:,} checkout users",
        f"Achieved Power:            {achieved['achieved_power'] * 100:.1f}%",
        f"Adequacy Assessment:       {'ADEQUATELY POWERED (>=80%)' if achieved['is_adequately_powered'] else 'UNDERPOWERED (<80%)'}",
        "=" * 70
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    prereg = calculate_required_sample_size()
    # Test with sample numbers from generated data
    achieved = calculate_achieved_power(
        p_control=0.1251,
        p_treatment=0.1537,
        n_control=4206,
        n_treatment=4483
    )
    print(format_power_summary(prereg, achieved))
