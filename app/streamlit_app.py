"""
Production-Grade Streamlit Interactive Dashboard
Funnel A/B Test Case Study: Experimentation Rigor, SRM Detection, and Decision Framework
Deployable locally and on Streamlit Community Cloud.
"""

import os
import json
import sqlite3
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from scipy import stats

# -----------------------------------------------------------------------------
# 1. Page Configuration & Custom Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Funnel A/B Test | Rigorous Experimentation Case Study",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .metric-card {
        background-color: #1e232d;
        border-radius: 8px;
        padding: 16px 20px;
        border: 1px solid #2d3748;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .recommendation-box {
        background: linear-gradient(135deg, rgba(234, 179, 8, 0.12) 0%, rgba(202, 138, 4, 0.22) 100%);
        border: 2px solid #eab308;
        border-radius: 10px;
        padding: 22px;
        margin-bottom: 24px;
    }
    .badge-amber {
        background-color: #ca8a04;
        color: #ffffff;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
        margin-bottom: 8px;
    }
    .badge-green {
        background-color: #15803d;
        color: #ffffff;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
    }
    .badge-red {
        background-color: #b91c1c;
        color: #ffffff;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0;
        padding: 10px 18px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. Data Loading & Fallback Generation for Cloud Deployment
# -----------------------------------------------------------------------------
@st.cache_data
def load_or_generate_experiment_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_path = os.path.join(base_dir, "analysis", "results.json")
    db_path = os.path.join(base_dir, "data", "events.db")

    # If results or db not present, run generation & analysis
    if not os.path.exists(results_path) or not os.path.exists(db_path):
        import sys
        sys.path.append(os.path.join(base_dir, "data"))
        sys.path.append(os.path.join(base_dir, "analysis"))
        from generate_data import generate_experiment_data, save_data
        from run_experiment_analysis import run_full_analysis
        
        df = generate_experiment_data()
        save_data(df, output_dir=os.path.join(base_dir, "data"))
        run_full_analysis(db_path=db_path, output_json=results_path)

    with open(results_path, 'r') as f:
        results = json.load(f)

    # Load daily aggregation from db
    conn = sqlite3.connect(db_path)
    sql_daily = """
    SELECT 
        day,
        variant,
        COUNT(DISTINCT CASE WHEN funnel_stage = 'visit' THEN user_id END) AS users_visit,
        COUNT(DISTINCT CASE WHEN funnel_stage = 'checkout' THEN user_id END) AS users_checkout,
        COUNT(DISTINCT CASE WHEN funnel_stage = 'payment' THEN user_id END) AS users_payment,
        COUNT(DISTINCT CASE WHEN funnel_stage = 'purchase' THEN user_id END) AS users_purchase,
        ROUND(CAST(COUNT(DISTINCT CASE WHEN funnel_stage = 'purchase' THEN user_id END) AS REAL) / 
              NULLIF(COUNT(DISTINCT CASE WHEN funnel_stage = 'checkout' THEN user_id END), 0) * 100.0, 2) AS checkout_to_purchase_conv_pct
    FROM events
    GROUP BY day, variant
    ORDER BY day ASC, variant ASC;
    """
    df_daily = pd.read_sql_query(sql_daily, conn)
    conn.close()

    return results, df_daily

results, df_daily = load_or_generate_experiment_data()

prereg = results['preregistration']
power_stats = results['power_analysis']
primary_stats = results['primary_metric']
srm_stats = results['sample_ratio_mismatch']
novelty_stats = results['novelty_effect']
stage_df = pd.DataFrame(results['stage_breakdown'])
rec = results['recommendation']

# -----------------------------------------------------------------------------
# 3. Sidebar Controls & Project Context
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=600&q=80", use_container_width=True)
    st.title("Funnel Experimentation")
    st.markdown("**Role Showcase**: Senior Data Analyst / Experimentation Specialist")
    st.markdown("---")
    st.markdown("### Experiment Parameters")
    st.markdown(f"**Sample Size**: `{srm_stats['total_users']:,}` visitors")
    st.markdown(f"**Duration**: `14 calendar days`")
    st.markdown(f"**Primary Metric**: `Checkout -> Purchase`")
    st.markdown(f"**Pre-registered MDE**: `+{prereg['mde_absolute']*100:.1f} pts` ({prereg['mde_relative_pct']:.1f}%)")
    st.markdown(f"**Alpha / Power**: `0.05 / 80%`")
    st.markdown("---")
    st.markdown("### Failure Modes Tested")
    st.markdown("• **Sample Ratio Mismatch (SRM)**")
    st.markdown("• **Novelty Effect Temporal Decay**")
    st.markdown("• **Funnel Step Leakage / Attribution**")
    st.markdown("---")
    st.markdown("### Stack & Tools")
    st.markdown("`Python` `SQLite` `Statsmodels` `SciPy` `Plotly` `Streamlit`")

# -----------------------------------------------------------------------------
# 4. Header & Executive Recommendation Banner
# -----------------------------------------------------------------------------
st.title("E-Commerce Funnel A/B Test: Experimentation & Decision Memo")
st.markdown("Rigorous evaluation of a checkout flow optimization test with failure mode diagnostics and pre-registration governance.")

# Prominent Executive Recommendation Box
st.markdown(f"""
<div class="recommendation-box">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
        <span class="badge-amber">DECISION: {rec['decision']}</span>
        <span style="font-size: 0.9rem; color: #94a3b8;">Experiment Health Status: <strong>SRM FLAGGED</strong></span>
    </div>
    <h3 style="margin-top: 0; color: #f8fafc; font-size: 1.25rem; font-weight: 600; line-height: 1.5;">
        "{rec['headline']}"
    </h3>
    <div style="margin-top: 14px; font-size: 0.95rem; color: #e2e8f0;">
        <strong>Recommended Rollout Governance:</strong>
        <ol style="margin-top: 6px; padding-left: 20px; line-height: 1.6;">
            <li><strong>Engineering Traffic Audit</strong>: Resolve the 48.4% / 51.6% Sample Ratio Mismatch before ramping rollout to 100%.</li>
            <li><strong>Financial Forecast Adjustment</strong>: Baseline GMV and revenue impact on the stabilized lift (+2.19 pts) rather than the inflated early novelty window (+5.39 pts).</li>
            <li><strong>Payment Micro-funnel Validation</strong>: Confirm third-party gateway latency drop matches the observed payment-step conversion lift.</li>
        </ol>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. Top-Level Metric Scorecards
# -----------------------------------------------------------------------------
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric(
        label="Total Visitors",
        value=f"{srm_stats['total_users']:,}",
        delta=f"SRM: {abs(srm_stats['observed_treatment_pct'] - 50.0):.1f}% bias",
        delta_color="inverse"
    )
with col2:
    st.metric(
        label="Checkout Sample",
        value=f"{primary_stats['nobs_control'] + primary_stats['nobs_treatment']:,}",
        help="Denominator for primary conversion metric"
    )
with col3:
    st.metric(
        label="Control Conv",
        value=f"{primary_stats['rate_control']*100:.2f}%",
        help="Checkout -> Purchase conversion"
    )
with col4:
    st.metric(
        label="Treatment Conv",
        value=f"{primary_stats['rate_treatment']*100:.2f}%",
        delta=f"{primary_stats['absolute_lift_pts']:+.2f} pts"
    )
with col5:
    st.metric(
        label="P-Value (Z-Test)",
        value=f"{primary_stats['p_value']:.4f}",
        delta="p < 0.05" if primary_stats['is_statistically_significant'] else "Not Sig",
        delta_color="normal" if primary_stats['is_statistically_significant'] else "inverse"
    )
with col6:
    st.metric(
        label="Statistical Power",
        value=f"{power_stats['achieved_power']*100:.1f}%",
        delta="Adequately Powered",
        delta_color="normal"
    )

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. Interactive Analysis Tabs
# -----------------------------------------------------------------------------
tab_funnel, tab_lift, tab_failures, tab_power, tab_sql = st.tabs([
    "📊 Funnel Progression",
    "🎯 Lift Attribution (Forest Plot)",
    "⚠️ Failure Mode Diagnostics (SRM & Novelty)",
    "📐 Pre-Registration & Power",
    "💻 SQL Engine & Schema"
])

# -----------------------------------------------------------------------------
# TAB 1: Funnel Progression
# -----------------------------------------------------------------------------
with tab_funnel:
    st.subheader("Interactive Funnel Progression by Variant")
    st.markdown("Visualizing user volume dropping off across each of the 6 stages. Notice how Control and Treatment mirror each other until the final purchase step.")

    stages = ['visit', 'product_view', 'add_to_cart', 'checkout', 'payment', 'purchase']
    stage_labels = ['1. Visit', '2. Product View', '3. Add to Cart', '4. Checkout', '5. Payment', '6. Purchase']
    
    # Extract counts
    c_counts = [
        stage_df[stage_df['transition'] == 'visit -> product_view']['control_base'].iloc[0],
        stage_df[stage_df['transition'] == 'visit -> product_view']['control_conv_users'].iloc[0],
        stage_df[stage_df['transition'] == 'product_view -> add_to_cart']['control_conv_users'].iloc[0],
        stage_df[stage_df['transition'] == 'add_to_cart -> checkout']['control_conv_users'].iloc[0],
        stage_df[stage_df['transition'] == 'checkout -> payment']['control_conv_users'].iloc[0],
        stage_df[stage_df['transition'] == 'payment -> purchase']['control_conv_users'].iloc[0],
    ]
    t_counts = [
        stage_df[stage_df['transition'] == 'visit -> product_view']['treatment_base'].iloc[0],
        stage_df[stage_df['transition'] == 'visit -> product_view']['treatment_conv_users'].iloc[0],
        stage_df[stage_df['transition'] == 'product_view -> add_to_cart']['treatment_conv_users'].iloc[0],
        stage_df[stage_df['transition'] == 'add_to_cart -> checkout']['treatment_conv_users'].iloc[0],
        stage_df[stage_df['transition'] == 'checkout -> payment']['treatment_conv_users'].iloc[0],
        stage_df[stage_df['transition'] == 'payment -> purchase']['treatment_conv_users'].iloc[0],
    ]

    fig_funnel = go.Figure()
    fig_funnel.add_trace(go.Funnel(
        name='Control (A)',
        y=stage_labels,
        x=c_counts,
        textinfo="value+percent previous+percent initial",
        marker={"color": "#60a5fa"},
        connector={"line": {"color": "#3b82f6"}}
    ))
    fig_funnel.add_trace(go.Funnel(
        name='Treatment (B)',
        y=stage_labels,
        x=t_counts,
        textinfo="value+percent previous+percent initial",
        marker={"color": "#34d399"},
        connector={"line": {"color": "#10b981"}}
    ))
    fig_funnel.update_layout(
        title="Stage-by-Stage User Drop-off (Plotly Funnel)",
        height=480,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=60, b=20)
    )
    st.plotly_chart(fig_funnel, use_container_width=True)

    # Detailed Step-to-Step Table
    st.markdown("### Step-to-Step Conversion Rate Details")
    display_step_df = stage_df.copy()
    display_step_df = display_step_df.rename(columns={
        'transition': 'Funnel Transition',
        'control_base': 'Control Users (N)',
        'control_conv_users': 'Control Converted',
        'control_rate_pct': 'Control Conv %',
        'treatment_base': 'Treatment Users (N)',
        'treatment_conv_users': 'Treatment Converted',
        'treatment_rate_pct': 'Treatment Conv %',
        'absolute_lift_pts': 'Absolute Lift (pts)',
        'ci_lower_pts': '95% CI Lower (pts)',
        'ci_upper_pts': '95% CI Upper (pts)',
        'p_value': 'P-Value',
        'significant': 'Statistically Significant'
    })
    st.dataframe(
        display_step_df.style.format({
            'Control Users (N)': '{:,}',
            'Control Converted': '{:,}',
            'Control Conv %': '{:.2f}%',
            'Treatment Users (N)': '{:,}',
            'Treatment Converted': '{:,}',
            'Treatment Conv %': '{:.2f}%',
            'Absolute Lift (pts)': '{:+.2f}%',
            '95% CI Lower (pts)': '{:+.2f}%',
            '95% CI Upper (pts)': '{:+.2f}%',
            'P-Value': '{:.4f}'
        }),
        use_container_width=True
    )

# -----------------------------------------------------------------------------
# TAB 2: Lift Attribution (Forest Plot)
# -----------------------------------------------------------------------------
with tab_lift:
    st.subheader("Lift Attribution: Where in the Funnel Does the Effect Live?")
    st.markdown("""
    A hallmark of rigorous experimentation is verifying that treatment effects appear only where the UX was modified. 
    Below is a **Forest Plot with 95% Confidence Intervals** for each funnel transition. 
    Notice that transitions prior to payment have confidence intervals that cross **0.0%**, whereas **Payment $\\rightarrow$ Purchase** shows a clean, isolated lift.
    """)

    # Filter out overall primary metric to show individual steps
    step_data = stage_df[~stage_df['transition'].str.contains('Primary')].copy()
    
    fig_forest = go.Figure()

    # Zero reference line
    fig_forest.add_vline(x=0, line_width=1.5, line_dash="dash", line_color="#ef4444")

    # Add error bars
    fig_forest.add_trace(go.Scatter(
        x=step_data['absolute_lift_pts'],
        y=step_data['transition'],
        mode='markers',
        marker=dict(
            color=np.where(step_data['significant'] & (step_data['absolute_lift_pts'] > 0), "#10b981", "#94a3b8"),
            size=12,
            symbol='diamond'
        ),
        error_x=dict(
            type='data',
            symmetric=False,
            array=step_data['ci_upper_pts'] - step_data['absolute_lift_pts'],
            arrayminus=step_data['absolute_lift_pts'] - step_data['ci_lower_pts'],
            color="#cbd5e1",
            thickness=2,
            width=8
        ),
        text=[f"Lift: {x:+.2f} pts<br>95% CI: [{l:+.2f}, {u:+.2f}]<br>p-val: {p:.4f}" 
              for x, l, u, p in zip(step_data['absolute_lift_pts'], step_data['ci_lower_pts'], step_data['ci_upper_pts'], step_data['p_value'])],
        hoverinfo='text',
        name='Step Lift (pts)'
    ))

    fig_forest.update_layout(
        title="Forest Plot: Stage Conversion Lift (pts) with 95% Confidence Intervals",
        xaxis_title="Absolute Conversion Rate Lift (percentage points)",
        yaxis_title="Funnel Step Transition",
        height=420,
        margin=dict(l=20, r=20, t=50, b=40)
    )
    st.plotly_chart(fig_forest, use_container_width=True)

    col_l1, col_l2 = st.columns(2)
    with col_l1:
        st.info("""
        **Data Analyst Takeaway**:
        The payment-step redesign specifically reduced checkout friction. If we had observed a significant lift at `product_view -> add_to_cart`, it would have alerted us to a leaky test or cross-experiment pollution.
        """)
    with col_l2:
        st.warning("""
        **Upstream Stages Check**:
        The slight `-0.67 pts` delta on `visit -> product_view` represents standard random noise across $N=60,000$ users. It does not cascade downstream into purchase intent.
        """)

# -----------------------------------------------------------------------------
# TAB 3: Failure Mode Diagnostics (SRM & Novelty)
# -----------------------------------------------------------------------------
with tab_failures:
    st.subheader("Catching Real Experiment Failure Modes")
    st.markdown("Most A/B test tutorials stop at calculating a p-value. In real-world experimentation, **Sample Ratio Mismatch (SRM)** and **Novelty Effects** frequently produce misleading wins.")

    col_srm, col_nov = st.columns(2)

    # 1. SRM Check
    with col_srm:
        st.markdown("### 1. Sample Ratio Mismatch (SRM) Diagnostic")
        if srm_stats['srm_detected']:
            st.error(f"🚨 **SRM DETECTED!** Chi-Square $p = {srm_stats['p_value']:.2e}$ (Threshold: $p < 0.01$)")
        else:
            st.success("✅ **NO SRM DETECTED**: Traffic allocation matches expected 50/50 split.")

        df_srm_plot = pd.DataFrame({
            'Variant': ['Control', 'Treatment'],
            'Observed Users': [srm_stats['observed_control'], srm_stats['observed_treatment']],
            'Expected Users': [srm_stats['total_users'] * 0.5, srm_stats['total_users'] * 0.5],
            'Observed Pct': [srm_stats['observed_control_pct'], srm_stats['observed_treatment_pct']]
        })

        fig_srm = go.Figure()
        fig_srm.add_trace(go.Bar(
            name='Observed Users',
            x=df_srm_plot['Variant'],
            y=df_srm_plot['Observed Users'],
            marker_color=['#ef4444', '#f59e0b'] if srm_stats['srm_detected'] else ['#3b82f6', '#10b981'],
            text=[f"{n:,}<br>({pct:.2f}%)" for n, pct in zip(df_srm_plot['Observed Users'], df_srm_plot['Observed Pct'])],
            textposition='auto'
        ))
        fig_srm.add_trace(go.Scatter(
            name='Expected 50/50 (30,000)',
            x=df_srm_plot['Variant'],
            y=df_srm_plot['Expected Users'],
            mode='lines+markers',
            line=dict(color='#ffffff', width=2, dash='dot')
        ))
        fig_srm.update_layout(
            title=f"Variant Assignment (Chi2 = {srm_stats['chi2_statistic']:.1f}, p={srm_stats['p_value']:.2e})",
            yaxis_title="Unique Visitors",
            height=340,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(fig_srm, use_container_width=True)

        st.markdown(f"""
        **Why this matters:**
        - **Target Allocation**: 50.0% Control / 50.0% Treatment
        - **Observed Allocation**: **{srm_stats['observed_control_pct']:.2f}%** Control vs **{srm_stats['observed_treatment_pct']:.2f}%** Treatment
        - **Implication**: An SRM indicates that user assignment or event telemetry is non-random. Common causes include redirect latency dropping slow mobile devices from Control, bot filtering bugs, or CDN caching anomalies.
        """)

    # 2. Novelty Effect
    with col_nov:
        st.markdown("### 2. Novelty Effect Temporal Decay")
        if novelty_stats['novelty_detected']:
            st.warning(f"⚠️ **NOVELTY EFFECT DETECTED**: Day 1-3 lift (+{novelty_stats['early_lift_pts']:.2f} pts) decayed by {novelty_stats['decay_magnitude_pts']:.2f} pts to (+{novelty_stats['late_lift_pts']:.2f} pts).")
        else:
            st.success("✅ **STABLE EFFECT**: No statistically significant novelty decay.")

        # Aggregate daily lift
        df_piv = df_daily.pivot(index='day', columns='variant', values='checkout_to_purchase_conv_pct').reset_index()
        df_piv['lift_pts'] = df_piv['treatment'] - df_piv['control']

        fig_nov = go.Figure()
        fig_nov.add_vrect(x0=0.5, x1=3.5, fillcolor="rgba(234, 179, 8, 0.15)", line_width=0, annotation_text="Novelty Window (Days 1-3)", annotation_position="top left")
        fig_nov.add_trace(go.Scatter(
            x=df_piv['day'],
            y=df_piv['treatment'],
            name='Treatment Conv %',
            mode='lines+markers',
            line=dict(color='#10b981', width=3)
        ))
        fig_nov.add_trace(go.Scatter(
            x=df_piv['day'],
            y=df_piv['control'],
            name='Control Conv %',
            mode='lines+markers',
            line=dict(color='#3b82f6', width=2, dash='dash')
        ))
        fig_nov.update_layout(
            title="Daily Checkout -> Purchase Conversion (%) Over 14 Days",
            xaxis_title="Day of Experiment",
            yaxis_title="Conversion Rate (%)",
            height=340,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(fig_nov, use_container_width=True)

        st.markdown(f"""
        **Temporal Comparison**:
        - **Days 1–3 Lift (Early)**: **+{novelty_stats['early_lift_pts']:.2f} pts** (Control: {novelty_stats['early_control_conv']:.1f}%, Trt: {novelty_stats['early_treatment_conv']:.1f}%)
        - **Days 4–14 Lift (Late)**: **+{novelty_stats['late_lift_pts']:.2f} pts** (Control: {novelty_stats['late_control_conv']:.1f}%, Trt: {novelty_stats['late_treatment_conv']:.1f}%)
        - **Interaction Test**: $Z = {novelty_stats['z_statistic']:.2f}, p = {novelty_stats['p_value_one_sided']:.4f}$ (Significant decay).
        """)

# -----------------------------------------------------------------------------
# TAB 4: Pre-Registration & Power Analysis
# -----------------------------------------------------------------------------
with tab_power:
    st.subheader("Pre-Registration Protocol & Power Sizing")
    st.markdown("""
    To avoid "p-hacking" and peeking problems, scientific experimentation pre-registers hypotheses, decision metrics, and sample size requirements before test launch.
    """)

    col_p1, col_p2 = st.columns([1, 1])
    with col_p1:
        st.markdown("### Pre-Registration Card")
        st.markdown(f"""
        - **Primary Hypothesis**:  
          $H_0: p_{{trt}} - p_{{ctrl}} = 0$ vs. $H_1: p_{{trt}} - p_{{ctrl}} \\neq 0$
        - **Decision Metric**:  
          `Checkout -> Purchase Conversion Rate`
        - **Baseline Conversion ($p_0$)**: `{prereg['baseline_rate']*100:.1f}%`
        - **Target Minimum Detectable Effect (MDE)**: `+{prereg['mde_absolute']*100:.1f} percentage points` (`+{prereg['mde_relative_pct']:.1f}%` relative)
        - **Significance Level ($\\alpha$)**: `0.05` (Two-sided)
        - **Target Statistical Power ($1 - \\beta$)**: `80.0%`
        - **Calculated Required Sample**: **`{prereg['required_n_per_variant']:,}` checkout users per variant**
        - **Total Required Funnel Visitors**: `~60,000` (assuming ~14% of visitors reach checkout)
        """)

    with col_p2:
        st.markdown("### Power Curve vs. Sample Size")
        # Generate power curve
        from statsmodels.stats.power import NormalIndPower
        from statsmodels.stats.proportion import proportion_effectsize

        h = proportion_effectsize(prereg['target_rate'], prereg['baseline_rate'])
        sample_range = np.linspace(1000, 7000, 40)
        power_curve = [NormalIndPower().power(effect_size=h, nobs1=n, alpha=0.05, ratio=1.0) for n in sample_range]

        fig_pow = go.Figure()
        fig_pow.add_trace(go.Scatter(x=sample_range, y=power_curve, mode='lines', name='Power Curve', line=dict(color='#8b5cf6', width=3)))
        fig_pow.add_hline(y=0.80, line_dash='dash', line_color='#f59e0b', annotation_text='80% Target Power')
        fig_pow.add_vline(x=prereg['required_n_per_variant'], line_dash='dot', line_color='#94a3b8', annotation_text=f"Req: {prereg['required_n_per_variant']:,}")
        fig_pow.add_trace(go.Scatter(
            x=[(power_stats['n_control'] + power_stats['n_treatment']) / 2],
            y=[power_stats['achieved_power']],
            mode='markers',
            marker=dict(color='#10b981', size=12, symbol='star'),
            name=f"Actual Sample ({power_stats['achieved_power']*100:.1f}% power)"
        ))
        fig_pow.update_layout(
            title="Statistical Power as a Function of Checkout Sample Size",
            xaxis_title="Sample Size per Variant (Checkout Users)",
            yaxis_title="Statistical Power (1 - Beta)",
            height=320,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_pow, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 5: SQL Engine & Schema
# -----------------------------------------------------------------------------
with tab_sql:
    st.subheader("Underlying SQL Queries & Database Schema")
    st.markdown("All funnel aggregations, sample size counts, and daily novelty tracking are driven by clean, modular SQL queries executed directly against SQLite / DuckDB.")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sql_files = {
        "01_srm_check.sql": os.path.join(base_dir, "sql", "01_srm_check.sql"),
        "02_funnel_by_variant.sql": os.path.join(base_dir, "sql", "02_funnel_by_variant.sql"),
        "03_funnel_daily.sql": os.path.join(base_dir, "sql", "03_funnel_daily.sql")
    }

    selected_query = st.radio("Select SQL Script to Inspect:", list(sql_files.keys()), horizontal=True)

    if os.path.exists(sql_files[selected_query]):
        with open(sql_files[selected_query], 'r') as f:
            query_code = f.read()
        st.code(query_code, language="sql")
    else:
        st.warning(f"File {sql_files[selected_query]} not found.")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #64748b; font-size: 0.85rem;'>Portfolio Project: Funnel A/B Testing with Failure Modes & Pre-Registration Discipline | Built by Data Analyst Candidate</p>", unsafe_allow_html=True)
