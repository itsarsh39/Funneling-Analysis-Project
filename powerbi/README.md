# 📊 Power BI Enterprise Reporting Suite

This directory contains the production-grade **Power BI reporting package** for the **E-Commerce Funnel A/B Testing & Experimentation Project**.

It bridges raw event-level data with executive-ready decision cockpits, statistical hypothesis testing in DAX, Sample Ratio Mismatch (SRM) guardrails, and financial scenario simulators.

---

## 📁 Power BI Directory Structure

```
powerbi/
├── README.md                      # Master setup & quickstart guide (this document)
├── data_model_guide.md            # Star Schema relationship specifications and sorting rules
├── dax_measures.dax               # Copy-pasteable DAX measure library (volume, stats, SRM, financials)
├── DAX_DICTIONARY.md              # Mathematical and business dictionary for all 25+ DAX measures
├── report_design_blueprint.md     # Visual layouts, color palettes, and wireframes for all 5 pages
├── power_query_m_scripts.m        # Ready-to-use Power Query (M) automated ingestion scripts
└── export_powerbi_data.py         # Automated pipeline to verify and refresh Power BI feeds
```

---

## ⚡ 5-Minute Quickstart: Building the Report in Power BI Desktop

### Step 1: Open Power BI Desktop & Ingest Data
Choose either of the two connection options:

* **Option A: Direct CSV Ingestion (Recommended & Fastest)**:
  1. In Power BI Desktop, click **Get Data** -> **Text/CSV**.
  2. Select the 5 dimensional tables located in `data/`:
     * `data/dim_users.csv`
     * `data/dim_funnel_stages.csv`
     * `data/dim_date.csv`
     * `data/fct_events.csv`
     * `data/fct_orders.csv`
  3. Click **Load** (or open the **Power Query Advanced Editor** and paste the scripts from [`power_query_m_scripts.m`](file:///c:/Users/WIN/Downloads/Funneling%20Analysis%20Project/powerbi/power_query_m_scripts.m)).

* **Option B: Direct SQLite Database Ingestion**:
  1. Install the SQLite ODBC Driver on Windows.
  2. Click **Get Data** -> **ODBC** -> connect to `data/events.db`.
  3. Select the star schema tables or the unified analytical view `vw_unified_events`.

---

### Step 2: Configure Relationships (Star Schema)
Navigate to the **Model View** (`Ctrl + 3`) and verify that relationships are configured with **Many-to-One (`* : 1`)** and **Single cross-filter direction**:

```
dim_users (1)          ------> (*) fct_events (user_id)
dim_funnel_stages (1)  ------> (*) fct_events (stage_order)
dim_date (1)           ------> (*) fct_events (date_id)
dim_users (1)          ------> (*) fct_orders (user_id)
dim_date (1)           ------> (*) fct_orders (date_id)
```
*(For detailed column settings and sort-by rules, see [`data_model_guide.md`](file:///c:/Users/WIN/Downloads/Funneling%20Analysis%20Project/powerbi/data_model_guide.md)).*

---

### Step 3: Create the `_Measures` Table & Paste DAX
1. In the **Home** tab, click **Enter Data**.
2. Set the table name to `_Measures` and click **Load**.
3. Open [`dax_measures.dax`](file:///c:/Users/WIN/Downloads/Funneling%20Analysis%20Project/powerbi/dax_measures.dax).
4. Create each measure in the `_Measures` table (or paste them in groups).
5. Delete the blank dummy column in `_Measures`.

---

### Step 4: Assemble the 5 Report Pages
Follow the layout wireframes and visual specs in [`report_design_blueprint.md`](file:///c:/Users/WIN/Downloads/Funneling%20Analysis%20Project/powerbi/report_design_blueprint.md):

1. **Page 1: Executive KPI & Decision Cockpit**:
   * Headline Executive Recommendation Banner (`[Executive Recommendation Banner]`).
   * 4 KPI cards: Visitors, Control Conv %, Treatment Conv %, Absolute Lift (+2.86 pts, p=0.0001).
   * Funnel drop-off comparison (Control vs Treatment).
   * Financial summary (+30.9% gross revenue delta).

2. **Page 2: Funnel Flow & Forest Plot (Attribution)**:
   * Stage-by-stage forest plot with 95% Confidence Intervals proving lift is strictly isolated to `payment -> purchase` (+7.34 pts).
   * Step-to-step drop-off matrix.

3. **Page 3: Temporal Trends & Novelty Effect Tracker**:
   * 14-day daily conversion trend line chart showing the Days 1–3 spike (+5.39 pts) and Days 4–14 stabilization (+2.19 pts).
   * Rolling novelty decay half-life tracking.

4. **Page 4: SRM Diagnostics & Root-Cause Explorer**:
   * Chi-Square Goodness-of-Fit card ($\chi^2 = 61.57$, $p < 0.0001$).
   * Interactive slice-and-dice matrix isolating the bug to **Mobile Safari** ($65.9\%$ Treatment vs $34.1\%$ Control) due to an iOS WebKit redirect logging issue.

5. **Page 5: Financial Impact & What-If Revenue Simulator**:
   * What-if numeric parameters for **Monthly Visitors**, **Assumed Lift (pts)**, and **Rollout %**.
   * Dynamic calculation of annualized incremental Gross Merchandise Value (GMV).

---

## 💼 Resume & Portfolio Bullets

Use these bullet points when showcasing this project on your resume, LinkedIn, or in interviews:

* *Designed and built a Kimball-style Star Schema data model (60k users, 143k events) in SQLite and Power BI Desktop to evaluate an e-commerce checkout A/B test.*
* *Authored a library of 25+ production DAX measures calculating dynamic Two-Proportion Z-tests, 95% Confidence Intervals, and Chi-Square Sample Ratio Mismatch (SRM) guardrails.*
* *Uncovered a subtle 48.4%/51.6% SRM defect via dimension-level SQL cross-tabulations and Power BI matrix diagnostics, isolating the root cause to Mobile Safari iOS redirect logging.*
* *Quantified a 3.20 pt novelty effect decay between early and late test windows, implementing a DAX-adjusted GMV forecasting model that prevented an executive over-projection of \$76k/year.*
