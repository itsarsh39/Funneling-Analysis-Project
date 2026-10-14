# Rigorous Funnel A/B Testing & Experimentation Case Study

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-SQLite%20Star%20Schema-003B57.svg)](https://www.sqlite.org/)
[![Power BI](https://img.shields.io/badge/Power%20BI-Enterprise%20Suite-F2C811.svg?logo=powerbi&logoColor=black)](powerbi/README.md)
[![SQL](https://img.shields.io/badge/SQL-Advanced%20Window%20%26%20Marts-CC292B.svg)](sql/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B.svg)](https://streamlit.io/)
[![Statsmodels](https://img.shields.io/badge/Statsmodels-Hypothesis%20Testing-green.svg)](https://www.statsmodels.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Portfolio Project for Senior Data Analyst, Analytics Engineer & Experimentation Roles**:  
> Demonstrating end-to-end scientific experimentation discipline—from **pre-registration power analysis** and **Kimball-style Star Schema modeling** to **advanced SQL window sessionization**, **in-database statistical hypothesis testing**, **Sample Ratio Mismatch (SRM) root-cause isolation**, and a **5-page enterprise Power BI reporting suite**.

---

## 📌 Headline Finding & Executive Decision

```text
==============================================================================
               EXECUTIVE RECOMMENDATION: [SHIP WITH CAVEAT]
==============================================================================
Treatment lifted checkout conversion +2.86pts (p=0.0001, adequately powered at 97%), 
concentrated entirely at the payment step (payment -> purchase) -- recommend shipping 
with a caveat that a Sample Ratio Mismatch (SRM) was detected (observed 48.4% Control / 
51.6% Treatment, Chi-square p=4.28e-15), indicating a traffic routing or logging defect 
that must be investigated and resolved before full rollout.

KEY AUDIT ACTIONS & GUARDRAILS:
  1. Audit frontend redirect and variant logging triggers with Engineering to isolate 
     the 48.5/51.5 SRM root cause (isolated to Mobile Safari iOS redirect logging).
  2. Validate payment gateway latency and third-party checkout provider telemetry to 
     verify the payment step mechanism.
  3. Base all downstream ARR/GMV business forecasts on the stabilized late-window lift 
     (+2.19 pts) rather than the blended initial rate (+2.86 pts).
==============================================================================
```

---

## 🎯 Why This Project Stands Out

Most data analyst A/B testing projects run a simple t-test on an unvalidated Kaggle dataset. In production environments, that approach leads to expensive false positives and flawed rollouts. 

This project simulates real-world corporate experimentation and analytics engineering:
1. **Kimball Star Schema Data Architecture**: 60,000 users and 143,000 events structured into clean dimensional entities (`dim_users`, `dim_funnel_stages`, `dim_date`) and facts (`fct_events`, `fct_orders`).
2. **Heavy-Duty SQL Engineering**:
   * **Window Functions & Sessionization**: Uses `ROW_NUMBER()`, `LAG()`, and `LEAD()` to track session progression, step elapsed duration, and bounce detection.
   * **In-Database Hypothesis Testing**: Pure SQL scripts compute the Two-Proportion Z-Test, pooled standard error, and 95% Confidence Interval boundaries natively.
   * **SRM Root-Cause Isolation Query**: Dimension-level cross-tabulations that pinpoint the exact device/browser subgroup (**Mobile Safari**, $\chi^2 = 1399.93, p < 0.0001$) causing the traffic allocation bug.
   * **Heterogeneous Treatment Effects (HTE)**: Evaluates segment-level lift across devices, browsers, and marketing acquisition channels.
3. **Enterprise Power BI Reporting Suite**:
   * Production data model with 1-to-many relationships and sort hierarchies.
   * **25+ DAX Measures Library**: Recomputes Z-scores, margins of error, SRM chi-square alerts, and revenue metrics dynamically upon user slicing.
   * **5-Page Executive Cockpit**: Executive Scorecard, Funnel Forest Plot with CIs, Temporal Novelty Tracker, SRM Root-Cause Explorer, and What-If Revenue Simulator.
4. **Pre-Registration Discipline**: Formal hypothesis definition, MDE specification (+2.0 pts), and sample sizing prior to test execution.
5. **Catching Sample Ratio Mismatch (SRM)**: Detects a subtle 48.4% / 51.6% traffic allocation defect with $\chi^2$ goodness-of-fit ($p < 10^{-14}$).
6. **Novelty Effect Quantification**: Disentangles the initial Days 1–3 novelty burst (+5.39 pts) from the sustainable steady-state lift (+2.19 pts).
7. **Financial & GMV Impact Modeling**: Quantifies gross revenue ($93.9k), Average Order Value (AOV: $77.30), and discounts annualized ARR projections by novelty decay to prevent budget shortfalls.

---

## 📊 Summary of Results

| Metric / Dimension | Control | Treatment | Lift / Result | Test & Significance |
| :--- | :--- | :--- | :--- | :--- |
| **Total Visitors** | 29,039 (48.4%) | 30,961 (51.6%) | +3.20% gap | $\chi^2 = 61.57, p = 4.28 \times 10^{-15}$ (🚨 **SRM Alert**) |
| **Checkout Sample ($N$)** | 4,206 | 4,483 | 8,689 total | **97.1% Achieved Power** (Target: 80%) |
| **Checkout $\rightarrow$ Purchase Conv** | **12.51%** | **15.37%** | **+2.86 pts** (+22.89% rel) | $Z = 3.85, p = 0.0001$ (✅ **Significant**) |
| **95% Confidence Interval** | — | — | `[+1.41 pts, +4.32 pts]` | Wald & Wilson score interval |
| **Days 1–3 Lift (Novelty)** | 12.51% | 17.90% | **+5.39 pts** | Initial curiosity spike |
| **Days 4–14 Lift (Stabilized)** | 12.50% | 14.69% | **+2.19 pts** | **Sustainable baseline for forecasting** |
| **Payment Step Transition** | 30.49% | 37.84% | **+7.34 pts** | $p < 0.0001$ (**Isolated mechanism**) |
| **Total Gross Revenue** | $40,671.03 | $53,240.81 | **+$12,569.78** (+30.9%) | AOV steady: Control $77.32 vs Treatment $77.27 |
| **Stabilized Annual GMV Run-Rate** | — | — | **+$250,940 / year** | Discounted for novelty decay |

---

## 🏛️ Star Schema Data Architecture

The project implements a Kimball dimensional model in SQLite (`data/events.db`) and exports clean CSVs ready for Power BI:

```
                 +-----------------------+
                 |       dim_date        |
                 +-----------------------+
                 | PK  date_id (int)     |
                 |     date (date)       |
                 |     experiment_day    |
                 |     window_period     |
                 +-----------+-----------+
                             | 1
                             | 
                             | *
+--------------------+   +---+-------------------+   +-----------------------+
|     dim_users      |   |      fct_events       |   |   dim_funnel_stages   |
+--------------------+   +-----------------------+   +-----------------------+
| PK user_id (text)  |<--+ FK user_id            +-->| PK stage_order (int)  |
|    variant         | * | FK stage_order        | * |    stage_name (text)  |
|    device_type     |   | FK date_id            |   |    stage_category     |
|    browser         |   |    session_id         |   |    is_conversion_step |
|    traffic_source  |   |    event_timestamp    |   +-----------------------+
|    country         |   |    latency_ms         |
+---------+----------+   +-----------------------+
          | 1
          |
          | *
+---------+----------+
|     fct_orders     |
+--------------------+
| PK order_id (text) |
| FK user_id         |
| FK date_id         |
|    order_timestamp |
|    revenue_usd     |
|    items_count     |
|    payment_method  |
+--------------------+
```

---

## 📁 Repository Structure

```
.
├── data/
│   ├── generate_data.py                  # Synthetic data generator (Star Schema + flaws baked in)
│   ├── events.db                         # SQLite database with 6 tables/views and performance indexes
│   ├── dim_users.csv                     # User dimension (device, browser, channel, country)
│   ├── dim_funnel_stages.csv             # Funnel stage ordering and category definitions
│   ├── dim_date.csv                      # Experiment calendar dimension with window periods
│   ├── fct_events.csv                    # Event-level fact records (143k rows)
│   ├── fct_orders.csv                    # Transaction orders and GMV fact records (1,215 rows)
│   └── events.csv                        # Consolidated event log (backwards-compatible)
├── sql/
│   ├── 00_schema_ddl.sql                 # DDL creating Star Schema tables, indexes, and views
│   ├── 01_srm_check.sql                  # Baseline SRM traffic allocation check
│   ├── 02_funnel_by_variant.sql          # Stage counts & step-to-step conversion
│   ├── 03_funnel_daily.sql               # Daily stage metrics for novelty tracking
│   ├── transformations/
│   │   ├── 01_sessionization_window.sql  # LAG/LEAD window functions, session breaks, bounce detection
│   │   └── 02_funnel_transition_attribution.sql # Drop-off volume & step-to-step retention rates
│   ├── statistical_tests/
│   │   ├── 01_srm_chi_square_in_sql.sql  # Pure SQL Chi-Square Goodness-of-Fit test for SRM
│   │   ├── 02_two_prop_z_test_in_sql.sql # Pure SQL Two-Prop Z-Test, Pooled SE & 95% Confidence Intervals
│   │   ├── 03_heterogeneous_treatment_effects.sql # Subgroup lift across device, source, country
│   │   └── 04_srm_root_cause_isolation.sql # Multi-dimensional query isolating Mobile Safari defect
│   └── marts/
│       ├── mart_funnel_daily.sql         # BI mart: Daily conversion and stage progressions
│       ├── mart_experiment_scorecard.sql # BI mart: Executive scorecard with precomputed stats
│       └── mart_revenue_impact.sql       # BI mart: GMV, AOV, ARPU, and stabilized annual forecasts
├── powerbi/
│   ├── README.md                         # Master 5-minute setup and quickstart guide
│   ├── data_model_guide.md               # Star Schema relationship settings and sort hierarchies
│   ├── dax_measures.dax                  # Copy-pasteable library of 25+ DAX measures
│   ├── DAX_DICTIONARY.md                 # Complete statistical and business DAX dictionary
│   ├── report_design_blueprint.md        # Wireframes, layout specs, and color palettes for 5 pages
│   ├── power_query_m_scripts.m           # Automated M-scripts for Power Query data ingestion
│   └── export_powerbi_data.py            # Automated pipeline to refresh and validate Power BI feeds
├── analysis/
│   ├── power_analysis.py                 # Pre-registration MDE and power calculation module
│   ├── hypothesis_testing.py             # Two-prop z-test, SRM chi-square, novelty test, stage CIs
│   ├── recommendation.py                 # Plain-English recommendation generator with caveat logic
│   ├── run_experiment_analysis.py        # CLI orchestrator executing full analysis pipeline
│   └── results.json                      # Precomputed machine-readable analysis results
├── app/
│   └── streamlit_app.py                  # Interactive Streamlit dashboard for Community Cloud
├── report/
│   └── experiment_writeup.md             # Comprehensive case-study experiment report
├── requirements.txt                      # Pinned dependencies for reproducible deployment
└── README.md                             # Portfolio case-study documentation
```

---

## 🚀 How to Run Locally

### 1. Setup Environment
```bash
git clone https://github.com/yourusername/funnel-ab-testing-case-study.git
cd funnel-ab-testing-case-study

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate Star Schema & Refresh Feeds
```bash
# Generates Star Schema in SQLite and exports clean CSVs
python data/generate_data.py

# Verify Power BI data feeds
python powerbi/export_powerbi_data.py
```

### 3. Run SQL Statistical Testing & Analysis Pipeline
```bash
# Run statistical hypothesis testing and recommendation pipeline
python analysis/run_experiment_analysis.py
```

### 4. Explore Power BI Suite
* Open **Power BI Desktop**.
* Follow the [**`powerbi/README.md`**](powerbi/README.md) guide to load the dimensional tables from `data/`, paste the measures from [`powerbi/dax_measures.dax`](powerbi/dax_measures.dax), and build the 5-page dashboard using [`powerbi/report_design_blueprint.md`](powerbi/report_design_blueprint.md).

### 5. Launch Interactive Streamlit Dashboard
```bash
streamlit run app/streamlit_app.py
```
Open your browser at `http://localhost:8501`.

---

## 📑 Full Case Study Report

For the in-depth, interview-ready case study writeup covering causal inference threats, power curve derivations, and root-cause engineering playbooks, see:  
👉 **[`report/experiment_writeup.md`](report/experiment_writeup.md)**

---

## 👤 Author
**Data Analyst Candidate**  
Passionate about causal inference, product analytics, SQL data modeling, and experimentation rigor.  
*Connect on LinkedIn or GitHub.*
