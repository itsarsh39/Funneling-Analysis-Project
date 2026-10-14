# 📖 Power BI DAX Measures Data Dictionary

This data dictionary documents every DAX measure implemented in the Power BI reporting model for the **E-Commerce Funnel A/B Testing & Experimentation Case Study**.

---

## 📌 Summary Table of Measures

| Measure Name | Display Folder | Data Type / Format | Mathematical Formula / Definition | Business & Statistical Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **`Total Visitors`** | `01_Volume` | Whole Number (`#,##0`) | `DISTINCTCOUNT(dim_users[user_id])` | Total unique participants entering the experiment. |
| **`Stage 1 Visit Users`** | `01_Volume` | Whole Number (`#,##0`) | `CALCULATE(DISTINCTCOUNT(fct_events[user_id]), stage_name = "visit")` | Users who logged a homepage/landing page visit. |
| **`Stage 4 Checkout Users`** | `01_Volume` | Whole Number (`#,##0`) | `CALCULATE(DISTINCTCOUNT(fct_events[user_id]), stage_name = "checkout")` | Denominator sample size for the primary conversion metric. |
| **`Stage 6 Purchase Users`** | `01_Volume` | Whole Number (`#,##0`) | `CALCULATE(DISTINCTCOUNT(fct_events[user_id]), stage_name = "purchase")` | Numerator success count for completed orders. |
| **`Checkout to Purchase Conv %`** | `02_Conversion` | Percentage (`0.00%`) | $\frac{\text{Purchase Users}}{\text{Checkout Users}}$ | Primary north-star experimentation metric. |
| **`Control Conversion Rate`** | `03_Hypothesis_Testing` | Percentage (`0.00%`) | $\frac{X_{\text{control}}}{N_{\text{control}}}$ | Baseline conversion rate of the checkout flow. |
| **`Treatment Conversion Rate`** | `03_Hypothesis_Testing` | Percentage (`0.00%`) | $\frac{X_{\text{treatment}}}{N_{\text{treatment}}}$ | Conversion rate under the modified payment experience. |
| **`Absolute Lift (pts)`** | `03_Hypothesis_Testing` | Percentage points (`+0.00;-0.00`) | $p_{\text{treatment}} - p_{\text{control}}$ | Primary effect size in percentage points. |
| **`Relative Lift %`** | `03_Hypothesis_Testing` | Percentage (`+0.00%`) | $\frac{p_{\text{treatment}} - p_{\text{control}}}{p_{\text{control}}}$ | Percent gain relative to the control baseline. |
| **`Pooled Standard Error`** | `03_Hypothesis_Testing` | Decimal (`0.0000`) | $\sqrt{\hat{p}(1-\hat{p}) \left(\frac{1}{N_c} + \frac{1}{N_t}\right)}$ | Standard error under the null hypothesis ($H_0$). |
| **`Z Statistic`** | `03_Hypothesis_Testing` | Decimal (`0.000`) | $\frac{\text{Absolute Lift}}{\text{Pooled Standard Error}}$ | Test statistic for two-proportion hypothesis testing. |
| **`Margin of Error 95%`** | `03_Hypothesis_Testing` | Decimal (`0.0000`) | $1.95996 \times SE_{\text{unpooled}}$ | Half-width of the 95% Confidence Interval. |
| **`CI Lower 95% (pts)`** | `03_Hypothesis_Testing` | Percentage points (`+0.00`) | $\text{Absolute Lift} - \text{MOE}$ | Lower bound of the true population effect size. |
| **`CI Upper 95% (pts)`** | `03_Hypothesis_Testing` | Percentage points (`+0.00`) | $\text{Absolute Lift} + \text{MOE}$ | Upper bound of the true population effect size. |
| **`Statistical Significance Flag`**| `03_Hypothesis_Testing` | String / Status Badge | $\text{IF}(\|Z\| \ge 1.96, \text{Significant}, \text{Not Significant})$ | Automated statistical test decision rule. |
| **`Observed Control Ratio`** | `04_SRM_Guardrails` | Percentage (`0.0%`) | $\frac{\text{Control Visitors}}{\text{Total Visitors}}$ | Observed split percentage to detect traffic drift. |
| **`Total SRM Chi Square`** | `04_SRM_Guardrails` | Decimal (`0.00`) | $\sum \frac{(O - E)^2}{E}$ | Goodness-of-fit statistic test for 50/50 allocation. |
| **`SRM Status Badge`** | `04_SRM_Guardrails` | String / Alert Card | $\text{SWITCH}(\chi^2 \ge 10.828, \text{"CRITICAL"}, \dots)$ | Guardrail status banner preventing premature rollout. |
| **`Early Window Lift (Days 1-3)`** | `05_Temporal_Novelty` | Percentage points (`+0.00`) | $\text{Lift}_{\text{Days 1-3}}$ | Initial curiosity / novelty spike effect size. |
| **`Stabilized Window Lift (Days 4-14)`**| `05_Temporal_Novelty`| Percentage points (`+0.00`) | $\text{Lift}_{\text{Days 4-14}}$ | Sustainable steady-state baseline for forecasting. |
| **`Novelty Decay (pts)`** | `05_Temporal_Novelty` | Percentage points (`0.00`) | $\text{Lift}_{\text{Early}} - \text{Lift}_{\text{Late}}$ | Quantitative magnitude of novelty decay. |
| **`Total Gross Revenue`** | `06_Financials` | Currency (`$#,##0.00`) | $\sum \text{fct\_orders[revenue\_usd]}$ | Gross merchandise value captured across both variants. |
| **`Average Order Value (AOV)`** | `06_Financials` | Currency (`$#,##0.00`) | $\frac{\text{Total Revenue}}{\text{Total Orders}}$ | Verifies that checkout lift didn't degrade basket size. |
| **`Annualized GMV Lift Projected`**| `06_Financials` | Currency (`$#,##0.00`) | $\text{IncRev} \times \frac{365}{14} \times \frac{\text{Stabilized Lift}}{\text{Blended Lift}}$ | Conservative annualized GMV forecast for executive planning. |

---

## 🧠 Statistical & Business Rationale

### Why calculate Standard Error & Z-Scores in DAX?
By calculating $Z$, $p$, and 95% Confidence Intervals inside DAX measures rather than hard-coding values from Python:
1. **Dynamic Slicing**: When an executive slices by **Device: Desktop** or **Channel: Organic Search**, all statistical tests (lift, confidence intervals, p-values, SRM checks) automatically recompute dynamically for that exact subpopulation.
2. **Auditability**: Stakeholders can click any card visual in Power BI and inspect the exact mathematical formula.

### Why discount Annualized GMV by Novelty Decay?
Using blended lift (+2.86 pts) over-projects annual ARR by ~30% because Days 1–3 contain a short-term curiosity spike (+5.39 pts). The `Annualized GMV Lift Projected` DAX measure dynamically applies the ratio:
$$\text{Discount Factor} = \frac{\text{Stabilized Lift (Days 4–14)}}{\text{Blended Lift (Days 1–14)}} \approx \frac{+2.19}{+2.86} = 76.6\%$$
This protects business leadership against forecasting budget shortfalls.
