# Rigorous Funnel A/B Testing & Experimentation Case Study

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57.svg)](https://www.sqlite.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B.svg)](https://streamlit.io/)
[![Statsmodels](https://img.shields.io/badge/Statsmodels-Hypothesis%20Testing-green.svg)](https://www.statsmodels.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Portfolio Project for Data Analyst & Experimentation Roles**:  
> Demonstrating end-to-end scientific experimentation discipline—from **pre-registration power analysis** and **SQL funnel aggregations** to catching real-world experiment failure modes (**Sample Ratio Mismatch** and **Novelty Effects**) and delivering an executive-ready product recommendation.

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
     the 48.5/51.5 SRM root cause.
  2. Validate payment gateway latency and third-party checkout provider telemetry to 
     verify the payment step mechanism.
  3. Base all downstream ARR/GMV business forecasts on the stabilized late-window lift 
     (+2.19 pts) rather than the blended initial rate (+2.86 pts).
==============================================================================
```

---

## 🎯 Why This Project Stands Out

Most data analyst A/B testing projects run a simple t-test on an unvalidated Kaggle dataset. In production environments, that approach leads to expensive false positives and flawed rollouts. 

This project simulates real-world corporate experimentation rigor:
1. **Pre-Registration Discipline**: Formal hypothesis definition, MDE specification (+2.0 pts), and sample sizing prior to test execution.
2. **SQL Funnel Aggregation**: Uses production `.sql` queries against SQLite rather than doing everything in Pandas.
3. **Catching Sample Ratio Mismatch (SRM)**: Detects a subtle 48.4% / 51.6% traffic allocation defect with $\chi^2$ goodness-of-fit ($p < 10^{-14}$).
4. **Novelty Effect Quantification**: Disentangles the initial Days 1–3 novelty burst (+5.39 pts) from the sustainable steady-state lift (+2.19 pts).
5. **Funnel Attribution (Forest Plot)**: Proves that lift is isolated strictly to the modified payment step with 95% Confidence Intervals.
6. **Actionable PM Recommendation**: Delivers a plain-English decision memo tailored for product leadership.

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

---

## 📁 Repository Structure

```
.
├── data/
│   ├── generate_data.py             # Synthetic data generator (60k users, 14 days, flaws baked in)
│   ├── events.db                    # SQLite database containing 143k event-level rows
│   └── events.csv                   # CSV export of raw events
├── sql/
│   ├── 01_srm_check.sql             # SQL query: User assignment counts & Chi-Square components
│   ├── 02_funnel_by_variant.sql     # SQL query: Stage counts & step-to-step conversion
│   └── 03_funnel_daily.sql          # SQL query: Daily stage metrics for novelty tracking
├── analysis/
│   ├── power_analysis.py            # Pre-registration MDE and power calculation module
│   ├── hypothesis_testing.py        # Two-prop z-test, SRM chi-square, novelty test, stage CIs
│   ├── recommendation.py            # Plain-English recommendation generator with caveat logic
│   ├── run_experiment_analysis.py   # CLI orchestrator executing full analysis pipeline
│   └── results.json                 # Precomputed machine-readable analysis results
├── app/
│   └── streamlit_app.py             # Interactive Streamlit dashboard for Community Cloud
├── report/
│   └── experiment_writeup.md        # Comprehensive case-study experiment report
├── requirements.txt                 # Pinned dependencies for reproducible deployment
└── README.md                        # Portfolio case-study documentation
```

---

## 🚀 How to Run Locally

### 1. Clone & Setup Environment
```bash
git clone https://github.com/yourusername/funnel-ab-testing-case-study.git
cd funnel-ab-testing-case-study

# Create virtual environment (optional)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate Data & Run SQL Analysis Pipeline
```bash
# Generate synthetic dataset into SQLite
python data/generate_data.py

# Run statistical testing and recommendation pipeline
python analysis/run_experiment_analysis.py
```

### 3. Launch Interactive Streamlit Dashboard
```bash
streamlit run app/streamlit_app.py
```
Open your browser at `http://localhost:8501`.

---

## ☁️ Deploying to Streamlit Community Cloud

This repository is pre-configured for one-click deployment:
1. Fork or push this repository to GitHub.
2. Sign in to [share.streamlit.io](https://share.streamlit.io/).
3. Select your repository, branch `main`, and main file path: `app/streamlit_app.py`.
4. Deploy! The app contains fallback data initialization so it works out-of-the-box on cloud instances.

---

## 📑 Full Case Study Report

For the in-depth, interview-ready case study writeup covering causal inference threats, power curve derivations, and root-cause engineering playbooks, see:  
👉 **[`report/experiment_writeup.md`](report/experiment_writeup.md)**

---

## 👤 Author
**Data Analyst Candidate**  
Passionate about causal inference, product analytics, and experimentation rigor.  
*Connect on LinkedIn or GitHub.*
