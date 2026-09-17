"""
Synthetic Data Generator for Funnel A/B Testing Experiment
Simulates ~60,000 users across a 14-day 6-stage e-commerce funnel:
  visit -> product_view -> add_to_cart -> checkout -> payment -> purchase

Bake-in Specifications:
1. Sample Ratio Mismatch (SRM): Traffic allocated ~48.5% Control / 51.5% Treatment.
2. Funnel Baseline: Control checkout -> purchase conversion ~12.0%.
3. Lift Localization: Upstream stages (visit->view, view->cart, cart->checkout, checkout->payment)
   have identical conversion rates. True lift is concentrated strictly at the payment step.
4. Novelty Effect: Treatment payment conversion is noticeably elevated on Days 1-3,
   decaying to a stable lift on Days 4-14.
5. Output: SQLite database (data/events.db) and CSV (data/events.csv).
"""

import os
import sqlite3
import datetime
import numpy as np
import pandas as pd

# Set random seed for exact reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

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
# Days 1-3 (Novelty spike): 42.0% -> checkout to purchase = 40% * 42% = 16.8% (+4.8 pts)
# Days 4-14 (Stabilized): 35.5% -> checkout to purchase = 40% * 35.5% = 14.2% (+2.2 pts)
P_PURCHASE_GIVEN_PAYMENT_TRT_EARLY = 0.460  # Days 1-3
P_PURCHASE_GIVEN_PAYMENT_TRT_LATE = 0.355   # Days 4-14


def generate_experiment_data(total_users=TOTAL_USERS):
    print(f"Generating synthetic experiment data for {total_users:,} users across {DAYS} days...")

    # Assign users across 14 days (roughly uniform with slight daily Poisson noise)
    daily_weights = np.random.uniform(0.95, 1.05, size=DAYS)
    daily_probs = daily_weights / daily_weights.sum()
    user_days = np.random.choice(np.arange(1, DAYS + 1), size=total_users, p=daily_probs)

    # Assign variants with SRM (48.5% Control, 51.5% Treatment)
    variants = np.random.choice(['control', 'treatment'], size=total_users, p=[PROB_CONTROL, PROB_TREATMENT])

    events = []
    user_ids = [f"U{i+1:06d}" for i in range(total_users)]

    for i in range(total_users):
        uid = user_ids[i]
        variant = variants[i]
        day = int(user_days[i])

        # Base timestamp for the user session on that day
        day_offset_seconds = (day - 1) * 86400
        session_time_seconds = np.random.uniform(0, 86400)
        curr_timestamp = START_DATE + datetime.timedelta(seconds=day_offset_seconds + session_time_seconds)

        # Stage 1: visit (100%)
        events.append({
            'user_id': uid,
            'variant': variant,
            'day': day,
            'funnel_stage': 'visit',
            'timestamp': curr_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })

        # Stage 2: product_view
        if np.random.rand() < P_VIEW_GIVEN_VISIT:
            curr_timestamp += datetime.timedelta(seconds=int(np.random.exponential(45) + 5))
            events.append({
                'user_id': uid,
                'variant': variant,
                'day': day,
                'funnel_stage': 'product_view',
                'timestamp': curr_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
        else:
            continue

        # Stage 3: add_to_cart
        if np.random.rand() < P_CART_GIVEN_VIEW:
            curr_timestamp += datetime.timedelta(seconds=int(np.random.exponential(60) + 10))
            events.append({
                'user_id': uid,
                'variant': variant,
                'day': day,
                'funnel_stage': 'add_to_cart',
                'timestamp': curr_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
        else:
            continue

        # Stage 4: checkout
        if np.random.rand() < P_CHECKOUT_GIVEN_CART:
            curr_timestamp += datetime.timedelta(seconds=int(np.random.exponential(90) + 15))
            events.append({
                'user_id': uid,
                'variant': variant,
                'day': day,
                'funnel_stage': 'checkout',
                'timestamp': curr_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
        else:
            continue

        # Stage 5: payment
        if np.random.rand() < P_PAYMENT_GIVEN_CHECKOUT:
            curr_timestamp += datetime.timedelta(seconds=int(np.random.exponential(40) + 10))
            events.append({
                'user_id': uid,
                'variant': variant,
                'day': day,
                'funnel_stage': 'payment',
                'timestamp': curr_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
        else:
            continue

        # Stage 6: purchase (Lift and Novelty baked in here!)
        if variant == 'control':
            p_purchase = P_PURCHASE_GIVEN_PAYMENT_CONTROL
        else:
            # Treatment: Novelty effect on days 1-3
            p_purchase = P_PURCHASE_GIVEN_PAYMENT_TRT_EARLY if day <= 3 else P_PURCHASE_GIVEN_PAYMENT_TRT_LATE

        if np.random.rand() < p_purchase:
            curr_timestamp += datetime.timedelta(seconds=int(np.random.exponential(25) + 5))
            events.append({
                'user_id': uid,
                'variant': variant,
                'day': day,
                'funnel_stage': 'purchase',
                'timestamp': curr_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })

    df = pd.DataFrame(events)
    df['event_id'] = np.arange(1, len(df) + 1)
    # Reorder columns
    df = df[['event_id', 'user_id', 'variant', 'day', 'funnel_stage', 'timestamp']]
    return df


def save_data(df, output_dir="data"):
    os.makedirs(output_dir, exist_ok=True)
    db_path = os.path.join(output_dir, "events.db")
    csv_path = os.path.join(output_dir, "events.csv")

    print(f"Saving {len(df):,} events to SQLite: {db_path}...")
    conn = sqlite3.connect(db_path)
    df.to_sql("events", conn, if_exists="replace", index=False)
    
    # Create indexes for high-performance SQL queries
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_variant ON events(user_id, variant);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stage ON events(funnel_stage);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_day ON events(day);")
    conn.commit()
    conn.close()

    print(f"Saving events to CSV: {csv_path}...")
    df.to_csv(csv_path, index=False)
    print("Data persistence completed successfully.")


def print_sanity_check_distributions(df):
    print("\n" + "=" * 78)
    print("               SYNTHETIC DATA DISTRIBUTION SANITY CHECK")
    print("=" * 78)

    # 1. SRM Check
    user_variant = df[['user_id', 'variant']].drop_duplicates()
    counts = user_variant['variant'].value_counts()
    total = len(user_variant)
    ctrl_pct = counts['control'] / total * 100
    trt_pct = counts['treatment'] / total * 100

    print("\n[1] TRAFFIC ALLOCATION & SAMPLE RATIO MISMATCH (SRM):")
    print(f"  Total Unique Users:  {total:,}")
    print(f"  Control:            {counts['control']:,} ({ctrl_pct:.2f}%) [Target: 48.5%]")
    print(f"  Treatment:          {counts['treatment']:,} ({trt_pct:.2f}%) [Target: 51.5%]")
    print(f"  Imbalance:          Delta = {abs(trt_pct - ctrl_pct):.2f}% (Designed tracking/randomization bug)")

    # 2. Funnel Step-by-Step Breakdown
    stages = ['visit', 'product_view', 'add_to_cart', 'checkout', 'payment', 'purchase']
    stage_counts = df.pivot_table(index='variant', columns='funnel_stage', values='user_id', aggfunc='nunique')[stages]
    
    print("\n[2] STAGE USERS & STEP-TO-STEP CONVERSION RATES:")
    print(f"{'Stage':<18} | {'Control Users':<14} | {'Treatment Users':<15} | {'Control Step Conv':<17} | {'Trt Step Conv':<15} | {'Lift (pts)':<10}")
    print("-" * 96)
    
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

        print(f"{stage:<18} | {c_u:<14,d} | {t_u:<15,d} | {c_conv:>16.2f}% | {t_conv:>14.2f}% | {diff:>+9.2f}%")
        prev_stage = stage

    # 3. Primary Metric: Checkout -> Purchase
    c_checkout = stage_counts.loc['control', 'checkout']
    c_purchase = stage_counts.loc['control', 'purchase']
    t_checkout = stage_counts.loc['treatment', 'checkout']
    t_purchase = stage_counts.loc['treatment', 'purchase']
    
    c_rate = (c_purchase / c_checkout) * 100
    t_rate = (t_purchase / t_checkout) * 100
    abs_lift = t_rate - c_rate
    rel_lift = (abs_lift / c_rate) * 100

    print("\n[3] PRIMARY METRIC: CHECKOUT -> PURCHASE CONVERSION:")
    print(f"  Control Conversion:   {c_purchase:,} / {c_checkout:,} = {c_rate:.2f}% (Target: ~12.0%)")
    print(f"  Treatment Conversion: {t_purchase:,} / {t_checkout:,} = {t_rate:.2f}%")
    print(f"  Absolute Lift:        {abs_lift:+.2f} percentage points (Target: ~+2.3 pts)")
    print(f"  Relative Lift:        {rel_lift:+.2f}%")

    # 4. Novelty Effect: Days 1-3 vs Days 4-14
    early_df = df[df['day'] <= 3]
    late_df = df[df['day'] > 3]

    def get_checkout_conv(sub_df):
        chk = sub_df[sub_df['funnel_stage'] == 'checkout'].groupby('variant')['user_id'].nunique()
        pur = sub_df[sub_df['funnel_stage'] == 'purchase'].groupby('variant')['user_id'].nunique()
        c_rt = (pur.get('control', 0) / chk.get('control', 1)) * 100
        t_rt = (pur.get('treatment', 0) / chk.get('treatment', 1)) * 100
        return c_rt, t_rt, t_rt - c_rt

    c_early, t_early, lift_early = get_checkout_conv(early_df)
    c_late, t_late, lift_late = get_checkout_conv(late_df)

    print("\n[4] TEMPORAL BREAKDOWN (NOVELTY EFFECT CHECK):")
    print(f"  Days 1-3  (Novelty window): Control = {c_early:.2f}%, Treatment = {t_early:.2f}% -> Lift = {lift_early:+.2f} pts")
    print(f"  Days 4-14 (Stabilized):     Control = {c_late:.2f}%, Treatment = {t_late:.2f}% -> Lift = {lift_late:+.2f} pts")
    print(f"  Novelty Decay Magnitude:    {lift_early - lift_late:.2f} percentage points decay from initial spike")
    print("=" * 78 + "\n")


if __name__ == "__main__":
    df_events = generate_experiment_data()
    save_data(df_events, output_dir="data")
    print_sanity_check_distributions(df_events)
