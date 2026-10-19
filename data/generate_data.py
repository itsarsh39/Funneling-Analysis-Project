"""
Synthetic Data Generator for Funnel A/B Testing Experiment & Star Schema
Simulates ~60,000 users across a 14-day 6-stage e-commerce funnel:
  visit -> product_view -> add_to_cart -> checkout -> payment -> purchase

Star Schema Architecture:
  1. dim_users: user attributes (device_type, browser, traffic_source, country, first_seen_at)
  2. dim_funnel_stages: stage ordering, categories, and conversion step definitions
  3. dim_date: daily calendar metrics, day of week, novelty vs stabilized window period
  4. fct_events: grain of individual user interactions with session_id and latency
  5. fct_orders: transaction records with revenue_usd, item count, and payment method
  6. events: legacy consolidated table for seamless backwards compatibility

Bake-in Specifications:
1. Sample Ratio Mismatch (SRM): Traffic allocated ~48.5% Control / 51.5% Treatment.
   Root-cause mechanism: Concentrated in Mobile Safari (iOS WebKit redirect logging defect).
2. Funnel Baseline: Control checkout -> purchase conversion ~12.0%.
3. Lift Localization: True lift is concentrated strictly at the payment step.
4. Novelty Effect: Treatment payment conversion elevated on Days 1-3, decaying on Days 4-14.
5. Multi-Table Persistence: SQLite database (data/events.db) and individual CSVs for Power BI.
"""

import os
import sqlite3
import datetime
import numpy as np
import pandas as pd

# Set random seed for exact reproducibility
RANDOM_SEED = 42
TOTAL_USERS = 60000
DAYS = 14
START_DATE = datetime.datetime(2026, 3, 1, 0, 0, 0)

# 1. Assignment Probabilities (SRM baked in: 48.5% vs 51.5%)
PROB_CONTROL = 0.485
PROB_TREATMENT = 0.515

# 2. Stage Transition Probabilities
# Upstream funnel identical for both variants:
P_VISIT = 1.00
P_VIEW_GIVEN_VISIT = 0.80
P_CART_GIVEN_VIEW = 0.45
P_CHECKOUT_GIVEN_CART = 0.40
P_PAYMENT_GIVEN_CHECKOUT = 0.40

# Payment -> Purchase:
# Control: 30.0% -> checkout to purchase = 40% * 30% = 12.0%
P_PURCHASE_GIVEN_PAYMENT_CONTROL = 0.300

# Treatment with Novelty Effect:
# Days 1-3 (Novelty spike): 46.0% -> checkout to purchase = 40% * 46% = 18.4%
# Days 4-14 (Stabilized): 35.5% -> checkout to purchase = 40% * 35.5% = 14.2%
P_PURCHASE_GIVEN_PAYMENT_TRT_EARLY = 0.460  # Days 1-3
P_PURCHASE_GIVEN_PAYMENT_TRT_LATE = 0.355   # Days 4-14


def generate_experiment_dataset(total_users=TOTAL_USERS):
    print(f"Generating synthetic experiment data for {total_users:,} users across {DAYS} days...")

    # Independent RNG for dimensional attributes to guarantee exact event reproducibility
    np.random.seed(RANDOM_SEED)
    rng_dim = np.random.RandomState(123)

    # Assign users across 14 days (roughly uniform with slight daily Poisson noise)
    daily_weights = np.random.uniform(0.95, 1.05, size=DAYS)
    daily_probs = daily_weights / daily_weights.sum()
    user_days = np.random.choice(np.arange(1, DAYS + 1), size=total_users, p=daily_probs)

    # Assign variants with SRM (48.5% Control, 51.5% Treatment)
    variants = np.random.choice(['control', 'treatment'], size=total_users, p=[PROB_CONTROL, PROB_TREATMENT])
    user_ids = [f"U{i+1:06d}" for i in range(total_users)]

    # -------------------------------------------------------------------------
    # 1. Build dim_users (with SRM root-cause concentration in Mobile Safari)
    # -------------------------------------------------------------------------
    dim_users_list = []
    countries = ['United States', 'United Kingdom', 'Germany', 'Canada', 'France']
    country_probs = [0.50, 0.18, 0.14, 0.10, 0.08]
    traffic_sources = ['Organic Search', 'Paid Social', 'Direct Traffic', 'Email Campaign']
    source_probs = [0.35, 0.30, 0.20, 0.15]

    for i in range(total_users):
        uid = user_ids[i]
        variant = variants[i]
        day = int(user_days[i])

        # Realistic device/browser with SRM root-cause concentration:
        # Desktop is well-balanced ~50/50. Treatment has elevated Mobile Safari due to iOS WebKit redirect defect.
        if variant == 'control':
            device = rng_dim.choice(['Desktop', 'Mobile', 'Tablet'], p=[0.48, 0.46, 0.06])
            if device == 'Desktop':
                browser = rng_dim.choice(['Chrome', 'Edge', 'Firefox', 'Safari'], p=[0.60, 0.22, 0.15, 0.03])
            elif device == 'Mobile':
                browser = rng_dim.choice(['Chrome', 'Safari', 'Firefox'], p=[0.60, 0.36, 0.04])
            else:
                browser = rng_dim.choice(['Safari', 'Chrome'], p=[0.65, 0.35])
        else:  # treatment
            device = rng_dim.choice(['Desktop', 'Mobile', 'Tablet'], p=[0.42, 0.52, 0.06])
            if device == 'Desktop':
                browser = rng_dim.choice(['Chrome', 'Edge', 'Firefox', 'Safari'], p=[0.60, 0.22, 0.15, 0.03])
            elif device == 'Mobile':
                browser = rng_dim.choice(['Safari', 'Chrome', 'Firefox'], p=[0.58, 0.38, 0.04])
            else:
                browser = rng_dim.choice(['Safari', 'Chrome'], p=[0.70, 0.30])

        country = rng_dim.choice(countries, p=country_probs)
        source = rng_dim.choice(traffic_sources, p=source_probs)
        first_seen = START_DATE + datetime.timedelta(
            days=day - 1,
            hours=int(rng_dim.randint(0, 24)),
            minutes=int(rng_dim.randint(0, 60))
        )

        dim_users_list.append({
            'user_id': uid,
            'variant': variant,
            'device_type': device,
            'browser': browser,
            'traffic_source': source,
            'country': country,
            'first_seen_at': first_seen.strftime('%Y-%m-%d %H:%M:%S')
        })

    df_dim_users = pd.DataFrame(dim_users_list)

    # -------------------------------------------------------------------------
    # 2. Build dim_funnel_stages
    # -------------------------------------------------------------------------
    df_dim_stages = pd.DataFrame([
        {'stage_order': 1, 'stage_name': 'visit', 'stage_category': 'Top of Funnel', 'is_conversion_step': 0},
        {'stage_order': 2, 'stage_name': 'product_view', 'stage_category': 'Top of Funnel', 'is_conversion_step': 0},
        {'stage_order': 3, 'stage_name': 'add_to_cart', 'stage_category': 'Middle of Funnel', 'is_conversion_step': 0},
        {'stage_order': 4, 'stage_name': 'checkout', 'stage_category': 'Middle of Funnel', 'is_conversion_step': 0},
        {'stage_order': 5, 'stage_name': 'payment', 'stage_category': 'Bottom of Funnel', 'is_conversion_step': 0},
        {'stage_order': 6, 'stage_name': 'purchase', 'stage_category': 'Bottom of Funnel', 'is_conversion_step': 1}
    ])

    # -------------------------------------------------------------------------
    # 3. Build dim_date
    # -------------------------------------------------------------------------
    date_records = []
    for d in range(1, DAYS + 1):
        dt = START_DATE + datetime.timedelta(days=d - 1)
        date_records.append({
            'date_id': int(dt.strftime('%Y%m%d')),
            'date': dt.strftime('%Y-%m-%d'),
            'experiment_day': d,
            'day_of_week': dt.weekday(),
            'day_name': dt.strftime('%A'),
            'is_weekend': 1 if dt.weekday() in [5, 6] else 0,
            'window_period': 'Days 1-3 (Novelty)' if d <= 3 else 'Days 4-14 (Stabilized)'
        })
    df_dim_date = pd.DataFrame(date_records)

    # -------------------------------------------------------------------------
    # 4. Generate Funnel Events & Orders
    # -------------------------------------------------------------------------
    events = []
    orders = []

    for i in range(total_users):
        uid = user_ids[i]
        variant = variants[i]
        day = int(user_days[i])
        session_id = f"SESS-{uid}-{day:02d}"
        date_id = int(f"202603{day:02d}")

        # Base timestamp for the user session on that day
        day_offset_seconds = (day - 1) * 86400
        session_time_seconds = np.random.uniform(0, 86400)
        curr_timestamp = START_DATE + datetime.timedelta(seconds=day_offset_seconds + session_time_seconds)

        # Stage 1: visit (100%)
        events.append({
            'session_id': session_id,
            'user_id': uid,
            'variant': variant,
            'day': day,
            'date_id': date_id,
            'stage_order': 1,
            'funnel_stage': 'visit',
            'timestamp': curr_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'latency_ms': int(rng_dim.normal(120, 25))
        })

        # Stage 2: product_view
        if np.random.rand() < P_VIEW_GIVEN_VISIT:
            curr_timestamp += datetime.timedelta(seconds=int(np.random.exponential(45) + 5))
            events.append({
                'session_id': session_id,
                'user_id': uid,
                'variant': variant,
                'day': day,
                'date_id': date_id,
                'stage_order': 2,
                'funnel_stage': 'product_view',
                'timestamp': curr_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'latency_ms': int(rng_dim.normal(95, 20))
            })
        else:
            continue

        # Stage 3: add_to_cart
        if np.random.rand() < P_CART_GIVEN_VIEW:
            curr_timestamp += datetime.timedelta(seconds=int(np.random.exponential(60) + 10))
            events.append({
                'session_id': session_id,
                'user_id': uid,
                'variant': variant,
                'day': day,
                'date_id': date_id,
                'stage_order': 3,
                'funnel_stage': 'add_to_cart',
                'timestamp': curr_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'latency_ms': int(rng_dim.normal(110, 25))
            })
        else:
            continue

        # Stage 4: checkout
        if np.random.rand() < P_CHECKOUT_GIVEN_CART:
            curr_timestamp += datetime.timedelta(seconds=int(np.random.exponential(90) + 15))
            events.append({
                'session_id': session_id,
                'user_id': uid,
                'variant': variant,
                'day': day,
                'date_id': date_id,
                'stage_order': 4,
                'funnel_stage': 'checkout',
                'timestamp': curr_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'latency_ms': int(rng_dim.normal(140, 30))
            })
        else:
            continue

        # Stage 5: payment
        if np.random.rand() < P_PAYMENT_GIVEN_CHECKOUT:
            curr_timestamp += datetime.timedelta(seconds=int(np.random.exponential(40) + 10))
            events.append({
                'session_id': session_id,
                'user_id': uid,
                'variant': variant,
                'day': day,
                'date_id': date_id,
                'stage_order': 5,
                'funnel_stage': 'payment',
                'timestamp': curr_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'latency_ms': int(rng_dim.normal(210, 45))
            })
        else:
            continue

        # Stage 6: purchase (Lift and Novelty baked in here!)
        if variant == 'control':
            p_purchase = P_PURCHASE_GIVEN_PAYMENT_CONTROL
        else:
            p_purchase = P_PURCHASE_GIVEN_PAYMENT_TRT_EARLY if day <= 3 else P_PURCHASE_GIVEN_PAYMENT_TRT_LATE

        if np.random.rand() < p_purchase:
            curr_timestamp += datetime.timedelta(seconds=int(np.random.exponential(25) + 5))
            events.append({
                'session_id': session_id,
                'user_id': uid,
                'variant': variant,
                'day': day,
                'date_id': date_id,
                'stage_order': 6,
                'funnel_stage': 'purchase',
                'timestamp': curr_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'latency_ms': int(rng_dim.normal(320, 60))
            })

            # Create transaction record in fct_orders
            rev = round(float(rng_dim.lognormal(mean=4.25, sigma=0.45)), 2)
            rev = max(19.99, min(rev, 499.99))
            items = int(rng_dim.choice([1, 2, 3, 4], p=[0.55, 0.28, 0.12, 0.05]))
            pay_method = str(rng_dim.choice(['Credit Card', 'PayPal', 'Apple Pay'], p=[0.58, 0.24, 0.18]))
            orders.append({
                'order_id': f"ORD-{uid}-{day:02d}",
                'user_id': uid,
                'session_id': session_id,
                'date_id': date_id,
                'order_timestamp': curr_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'revenue_usd': rev,
                'items_count': items,
                'payment_method': pay_method,
                'payment_status': 'completed'
            })

    # Prepare DataFrame outputs
    df_raw_events = pd.DataFrame(events)
    df_raw_events['event_id'] = np.arange(1, len(df_raw_events) + 1)

    # Legacy events table format (for backwards compatibility)
    df_events = df_raw_events[['event_id', 'user_id', 'variant', 'day', 'funnel_stage', 'timestamp']].copy()

    # Fact events table (normalized for Star Schema)
    df_fct_events = df_raw_events[[
        'event_id', 'session_id', 'user_id', 'stage_order', 'funnel_stage', 'date_id', 'timestamp', 'latency_ms'
    ]].copy()
    df_fct_events.rename(columns={'timestamp': 'event_timestamp'}, inplace=True)

    df_fct_orders = pd.DataFrame(orders)

    return {
        'events': df_events,
        'dim_users': df_dim_users,
        'dim_funnel_stages': df_dim_stages,
        'dim_date': df_dim_date,
        'fct_events': df_fct_events,
        'fct_orders': df_fct_orders
    }


def save_dataset_and_schema(tables, output_dir="data"):
    if not os.path.isabs(output_dir):
        # Anchor relative output_dir to repo root
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, output_dir)

    if isinstance(tables, pd.DataFrame):
        tables = {'events': tables}

    os.makedirs(output_dir, exist_ok=True)
    db_path = os.path.join(output_dir, "events.db")

    print(f"Persisting Star Schema tables to SQLite database: {db_path}...")
    conn = sqlite3.connect(db_path)

    for table_name, df in tables.items():
        print(f"  -> Writing table '{table_name}' ({len(df):,} rows)...")
        df.to_sql(table_name, conn, if_exists="replace", index=False)

    # Create optimized indices for analytical queries
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_user_variant ON events(user_id, variant);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_stage ON events(funnel_stage);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_day ON events(day);")

    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_pk ON dim_users(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_variant ON dim_users(variant);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_device_browser ON dim_users(device_type, browser);")

    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_stages_pk ON dim_funnel_stages(stage_order);")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_date_pk ON dim_date(date_id);")

    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_fct_events_pk ON fct_events(event_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fct_events_user ON fct_events(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fct_events_session ON fct_events(session_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fct_events_stage ON fct_events(stage_order);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fct_events_date ON fct_events(date_id);")

    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_fct_orders_pk ON fct_orders(order_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fct_orders_user ON fct_orders(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fct_orders_date ON fct_orders(date_id);")

    conn.commit()
    conn.close()

    # Save CSV files for Power BI ingestion
    print(f"Exporting clean CSV files to '{output_dir}' for Power BI ingestion...")
    for table_name, df in tables.items():
        csv_file = os.path.join(output_dir, f"{table_name}.csv")
        df.to_csv(csv_file, index=False)
    print("Database persistence and CSV exports completed successfully.")


# Backward compatibility aliases for Streamlit and external callers
generate_experiment_data = generate_experiment_dataset
save_data = save_dataset_and_schema


def print_enhanced_sanity_checks(tables):
    df_events = tables['events']
    df_users = tables['dim_users']
    df_orders = tables['fct_orders']

    print("\n" + "=" * 80)
    print("           SYNTHETIC DATA & STAR SCHEMA DISTRIBUTION SANITY CHECK")
    print("=" * 80)

    # 1. Overall SRM Check
    counts = df_users['variant'].value_counts()
    total = len(df_users)
    ctrl_pct = counts['control'] / total * 100
    trt_pct = counts['treatment'] / total * 100

    print("\n[1] OVERALL TRAFFIC ALLOCATION (SRM CHECK):")
    print(f"  Total Unique Users:  {total:,}")
    print(f"  Control:            {counts['control']:,} ({ctrl_pct:.2f}%) [Target: 48.5%]")
    print(f"  Treatment:          {counts['treatment']:,} ({trt_pct:.2f}%) [Target: 51.5%]")
    print(f"  Difference:         {abs(trt_pct - ctrl_pct):.2f}% (Designed tracking skew)")

    # 2. SRM Root-Cause Diagnostic by Device and Browser
    print("\n[2] SRM ROOT-CAUSE DIAGNOSTIC BY DEVICE & BROWSER:")
    grouped = df_users.groupby(['device_type', 'browser', 'variant']).size().unstack(fill_value=0)
    grouped['total'] = grouped['control'] + grouped['treatment']
    grouped['ctrl_pct'] = (grouped['control'] / grouped['total'] * 100).round(1)
    grouped['trt_pct'] = (grouped['treatment'] / grouped['total'] * 100).round(1)
    grouped['status'] = np.where(abs(grouped['ctrl_pct'] - 50.0) > 4.0, '[SKEWED]', '[BALANCED]')
    print(grouped[['control', 'treatment', 'total', 'ctrl_pct', 'trt_pct', 'status']].to_string())

    # 3. Funnel Step-by-Step Breakdown
    stages = ['visit', 'product_view', 'add_to_cart', 'checkout', 'payment', 'purchase']
    stage_counts = df_events.pivot_table(index='variant', columns='funnel_stage', values='user_id', aggfunc='nunique')[stages]

    print("\n[3] STAGE USERS & STEP-TO-STEP CONVERSION RATES:")
    print(f"{'Stage':<18} | {'Control Users':<14} | {'Treatment Users':<15} | {'Control Conv':<14} | {'Trt Conv':<12} | {'Lift (pts)':<10}")
    print("-" * 92)

    prev_stage = None
    for stage in stages:
        c_u = stage_counts.loc['control', stage]
        t_u = stage_counts.loc['treatment', stage]

        if prev_stage is None:
            c_conv = 100.0
            t_conv = 100.0
            diff = 0.0
        else:
            c_prev = stage_counts.loc['control', prev_stage]
            t_prev = stage_counts.loc['treatment', prev_stage]
            c_conv = (c_u / c_prev) * 100
            t_conv = (t_u / t_prev) * 100
            diff = t_conv - c_conv

        print(f"{stage:<18} | {c_u:<14,d} | {t_u:<15,d} | {c_conv:>13.2f}% | {t_conv:>11.2f}% | {diff:>+9.2f}%")
        prev_stage = stage

    # 4. Primary Metric: Checkout -> Purchase
    c_checkout = stage_counts.loc['control', 'checkout']
    c_purchase = stage_counts.loc['control', 'purchase']
    t_checkout = stage_counts.loc['treatment', 'checkout']
    t_purchase = stage_counts.loc['treatment', 'purchase']

    c_rate = (c_purchase / c_checkout) * 100
    t_rate = (t_purchase / t_checkout) * 100
    abs_lift = t_rate - c_rate

    print("\n[4] PRIMARY METRIC (CHECKOUT -> PURCHASE):")
    print(f"  Control Conversion:   {c_purchase:,} / {c_checkout:,} = {c_rate:.2f}%")
    print(f"  Treatment Conversion: {t_purchase:,} / {t_checkout:,} = {t_rate:.2f}%")
    print(f"  Absolute Lift:        {abs_lift:+.2f} percentage points (Target: ~+2.86 pts)")

    # 5. Financial & Revenue Metrics (fct_orders)
    merged_orders = df_orders.merge(df_users[['user_id', 'variant']], on='user_id', how='left')
    total_rev = merged_orders['revenue_usd'].sum()
    ctrl_rev = merged_orders[merged_orders['variant'] == 'control']['revenue_usd'].sum()
    trt_rev = merged_orders[merged_orders['variant'] == 'treatment']['revenue_usd'].sum()
    ctrl_aov = merged_orders[merged_orders['variant'] == 'control']['revenue_usd'].mean()
    trt_aov = merged_orders[merged_orders['variant'] == 'treatment']['revenue_usd'].mean()

    print("\n[5] FINANCIAL & REVENUE SUMMARY (ORDERS FACT):")
    print(f"  Total Orders:         {len(df_orders):,} (Control: {c_purchase:,}, Treatment: {t_purchase:,})")
    print(f"  Total Gross Revenue:  ${total_rev:,.2f}")
    print(f"  Control Revenue:      ${ctrl_rev:,.2f} (AOV: ${ctrl_aov:.2f})")
    print(f"  Treatment Revenue:    ${trt_rev:,.2f} (AOV: ${trt_aov:.2f})")
    print(f"  Net Revenue Delta:    +${trt_rev - ctrl_rev:,.2f} (+{(trt_rev - ctrl_rev)/ctrl_rev*100:.1f}%)")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    generated_tables = generate_experiment_dataset()
    save_dataset_and_schema(generated_tables, output_dir="data")
    print_enhanced_sanity_checks(generated_tables)
