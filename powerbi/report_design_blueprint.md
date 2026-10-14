# 🎨 Power BI Report Design Blueprint & Wireframes

This document provides exact visual design specifications, color schemes, wireframe layouts, and visual configurations for building the **5-Page Executive Experimentation Suite** in Power BI Desktop.

---

## 🎨 Enterprise Theme & Color Palette

Use this corporate, high-contrast analytics palette:

| Element | Color Role | Hex Code | Power BI Theme Assignment |
| :--- | :--- | :--- | :--- |
| **Canvas Background** | Slate Dark / Neutral Dark | `#0E1117` or `#F8FAFC` | Page Background |
| **Visual Card Surface** | Card Surface Dark | `#1E232D` or `#FFFFFF` | Visual Background |
| **Control Variant** | Neutral Blue / Slate | `#3B82F6` / `#64748B` | Series 1 |
| **Treatment Variant** | Vibrant Indigo / Violet | `#8B5CF6` / `#6366F1` | Series 2 |
| **Positive Lift / Success** | Emerald Green | `#10B981` | Accent Positive |
| **SRM Alert / Warning** | Amber / Crimson | `#F59E0B` / `#EF4444` | Accent Warning |
| **Primary Text** | High Contrast White/Charcoal| `#F3F4F6` / `#0F172A` | Primary Data Labels |

---

## 📄 Page 1: Executive KPI & Decision Cockpit

**Goal**: Deliver a 5-second headline answer for the VP of Product and Head of Experimentation.

### Wireframe Layout:
```
+--------------------------------------------------------------------------------------------------+
| [🧪 E-COMMERCE FUNNEL EXPERIMENTATION DASHBOARD]               Slicers: [Device] [Channel] [Date] |
+--------------------------------------------------------------------------------------------------+
| EXECUTIVE BANNER: [RECOMMENDATION: SHIP WITH CAVEAT] | Lift: +2.86 pts | SRM Alert: Skewed Traffic |
+------------------------+------------------------+------------------------+-----------------------+
| TOTAL VISITORS         | CHECKOUT CONV (CTRL)   | CHECKOUT CONV (TRT)    | ABSOLUTE LIFT (pts)   |
| 60,000                 | 12.51%                 | 15.37%                 | +2.86 pts (p=0.0001)  |
| 48.4% C / 51.6% T [🚨] | 526 / 4,206 Users      | 689 / 4,483 Users      | 95% CI: [+1.41,+4.32] |
+------------------------+------------------------+------------------------+-----------------------+
| FUNNEL STEP WATERFALL COMPARING CONTROL VS TREATMENT    | REVENUE & ANNUALIZED FORECAST IMPACT   |
| (Clustered Bar Chart: Control vs Treatment across       | • Total Gross GMV: $93,911.84          |
|  visit -> view -> cart -> checkout -> payment -> buy)   | • Net Increment: +$12,569.78 (+30.9%)  |
|                                                         | • Unadjusted Run-rate: $327k / yr      |
|                                                         | • Conservative Baseline: $251k / yr    |
+---------------------------------------------------------+----------------------------------------+
```

### Visual Specifications:
1. **Executive Decision Banner**: Multi-row Card / Text box mapped to `[Executive Recommendation Banner]`.
2. **KPI Scorecard Cards**:
   * Card 1: `[Total Visitors]` + Subtitle `[Observed Control Ratio]`.
   * Card 2: `[Control Conversion Rate]` + Subtitle `[Control Checkout Users]`.
   * Card 3: `[Treatment Conversion Rate]` + Subtitle `[Treatment Checkout Users]`.
   * Card 4: `[Absolute Lift (pts)]` + Subtitle `[CI 95% Display]`. Conditional color: Green if positive.
3. **Funnel Comparison Chart**:
   * Visual: **Clustered Bar Chart** or **Funnel Visual**.
   * Y-Axis: `dim_funnel_stages[stage_name]` (sorted by `stage_order`).
   * X-Axis: `DISTINCTCOUNT(fct_events[user_id])`.
   * Legend: `dim_users[variant]`.

---

## 📄 Page 2: Funnel Flow & Forest Plot (Stage CIs)

**Goal**: Prove attribution by isolating lift to the modified payment step with 95% Confidence Intervals.

### Visual Specifications:
1. **Stage-by-Stage Forest Plot (Confidence Interval Error Bars)**:
   * Visual: **Clustered Column / Line Chart** or **Scatter Plot with Error Bars**.
   * X-Axis: Funnel Transition (`visit->view`, `view->cart`, `cart->checkout`, `checkout->payment`, `payment->purchase`).
   * Center Marker: Transition Lift (pts).
   * Upper / Lower Error Bounds: 95% Confidence Interval limits.
   * *Key Takeaway*: Upstream transitions straddle 0% (insignificant); only `payment -> purchase` shows a distinct +7.34 pts spike ($p < 0.0001$).
2. **Step Drop-off Matrix**:
   * Visual: **Matrix Visual**.
   * Rows: `dim_funnel_stages[stage_name]`.
   * Columns: `dim_users[variant]`.
   * Values: `[Visitors]`, `Step Conversion %`, `Step Drop-off %`.

---

## 📄 Page 3: Temporal Trends & Novelty Effect Tracker

**Goal**: Disentangle the initial Days 1–3 novelty burst from steady-state conversion.

### Visual Specifications:
1. **Daily Conversion Rate Line Chart**:
   * Visual: **Line Chart**.
   * X-Axis: `dim_date[experiment_day]` (Day 1 to 14).
   * Y-Axis: `[Checkout to Purchase Conv %]`.
   * Legend: `dim_users[variant]`.
   * Reference Band: Constant line at Control baseline ($12.5\%$).
   * Annotation: Shaded vertical band on Days 1–3 labeled "Novelty Spike (+5.39 pts)".
2. **Cumulative Lift vs Daily Lift**:
   * Visual: **Dual-Axis Line and Clustered Column Chart**.
   * Shows daily lift decaying from $+5.39\text{ pts}$ to $+2.19\text{ pts}$ over time.
3. **Window Period Comparison Card**:
   * Shows `[Early Window Lift (Days 1-3)]` vs `[Stabilized Window Lift (Days 4-14)]`.

---

## 📄 Page 4: SRM Diagnostics & Root-Cause Explorer

**Goal**: Identify the exact technical logging/routing bug driving the 48.4% / 51.6% Sample Ratio Mismatch.

### Visual Specifications:
1. **SRM Headline Alert Card**:
   * Value: `[Total SRM Chi Square]` ($\chi^2 = 61.57$).
   * Status Text: `[SRM Status Badge]` ("CRITICAL ALERT: SRM Severe, p < 0.001").
2. **Segment SRM Cross-Tabulation Matrix**:
   * Visual: **Matrix Visual**.
   * Rows: `dim_users[device_type]` -> `dim_users[browser]`.
   * Columns: `dim_users[variant]`.
   * Values: `[Total Visitors]`, `% of Segment Traffic`, `Segment Chi-Square`.
   * Conditional Formatting: Highlight background red/amber when Treatment share deviates $> 54\%$.
   * *Finding*: Highlights **Mobile Safari** ($65.9\%$ Treatment vs $34.1\%$ Control) as the primary root-cause defect.
3. **Traffic Allocation by Country & Traffic Source**:
   * Visual: **100% Stacked Bar Chart** confirming other slices remain balanced ~50/50.

---

## 📄 Page 5: Financial Impact & What-If Revenue Simulator

**Goal**: Give finance and product managers an interactive ROI model for rollout decision-making.

### Visual Specifications:
1. **Actual Experiment Financials**:
   * Cards: `[Total Gross Revenue]`, `[Incremental Revenue]`, `[Control AOV]`, `[Treatment AOV]`.
2. **Interactive What-If Scenario Parameters**:
   * Create numeric range parameters in Power BI (**Modeling** -> **New Parameter**):
     * `Monthly Visitor Scale`: 100,000 to 2,000,000 (Step: 100,000).
     * `Assumed Conversion Lift (pts)`: +0.50 pts to +4.00 pts (Default: +2.19 pts stabilized).
     * `Average Order Value ($)`: $50 to $150 (Default: $77.30).
     * `Rollout Allocation %`: 10% to 100% (Default: 100%).
3. **Simulated Incremental ARR Card**:
   ```dax
   Simulated Annual Incremental Revenue = 
   VAR MonthlyVisitors = [Monthly Visitor Scale Value]
   VAR Lift = [Assumed Conversion Lift Value] / 100
   VAR AOV = [Average Order Value Value]
   VAR Rollout = [Rollout Allocation % Value] / 100
   RETURN
   (MonthlyVisitors * 12) * Lift * AOV * Rollout
   ```
   * Displays the dynamic projected dollar return under different rollout and market scenarios.
