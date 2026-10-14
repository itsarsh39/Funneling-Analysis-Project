# 📐 Power BI Data Modeling & Relationship Guide

This guide details the Star Schema architecture, relationship configurations, and column metadata necessary to construct the data model in **Power BI Desktop**.

---

## 🏛️ Star Schema Architecture Diagram

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

## 🔗 Table Relationships Configuration

In Power BI Desktop, navigate to the **Model View** (`Ctrl + 3`) and verify or establish these relationships:

| From (Fact Table) | Foreign Key Column | To (Dimension Table) | Primary Key Column | Cardinality | Cross Filter Direction | Active? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `fct_events` | `user_id` | `dim_users` | `user_id` | Many-to-One (`* : 1`) | Single (`dim_users` filters `fct_events`) | **Yes** |
| `fct_events` | `stage_order` | `dim_funnel_stages` | `stage_order` | Many-to-One (`* : 1`) | Single (`dim_funnel_stages` filters `fct_events`) | **Yes** |
| `fct_events` | `date_id` | `dim_date` | `date_id` | Many-to-One (`* : 1`) | Single (`dim_date` filters `fct_events`) | **Yes** |
| `fct_orders` | `user_id` | `dim_users` | `user_id` | Many-to-One (`* : 1`) | Single (`dim_users` filters `fct_orders`) | **Yes** |
| `fct_orders` | `date_id` | `dim_date` | `date_id` | Many-to-One (`* : 1`) | Single (`dim_date` filters `fct_orders`) | **Yes** |

> [!IMPORTANT]
> **Cardinality Rules**: Always configure `Single` cross-filter direction pointing from Dimension down to Fact. Do **not** enable Bi-Directional filtering to prevent ambiguity in filter propagation.

---

## 🗂️ Column Formats & Sorting Rules

To ensure visuals sort chronologically and logically:

1. **`dim_funnel_stages`**:
   * Select column `stage_name`.
   * In the top ribbon, click **Sort by Column** -> select `stage_order`.
   * *Outcome*: Visuals display stages as `visit -> product_view -> add_to_cart -> checkout -> payment -> purchase` rather than alphabetical order.

2. **`dim_date`**:
   * Select column `day_name`.
   * Click **Sort by Column** -> select `day_of_week`.
   * Mark `dim_date` as a formal Date Table using the `date` column.

3. **`fct_orders`**:
   * Column `revenue_usd`: Data type `Decimal number`, Format `Currency` (`$#,##0.00`).
   * Column `items_count`: Data type `Whole number`, Default summarization `Sum`.

4. **`dim_users`**:
   * Set Default Summarization for all columns to `Do Not Summarize`.

---

## 🚀 Setting Up the `_Measures` Table

1. In the **Home** ribbon, click **Enter Data**.
2. Name the table `_Measures` and column `MeasurePlaceholder`. Click **Load**.
3. Create any new measure inside `_Measures`.
4. Delete the empty column `MeasurePlaceholder`.
5. The `_Measures` table will automatically float to the top of the Data pane with a calculator icon (`➗`).
