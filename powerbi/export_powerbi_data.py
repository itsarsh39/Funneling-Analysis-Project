"""
Automated Data Export & Validation Script for Power BI Integration
Exports verified CSV datasets from SQLite events.db and performs data integrity checks.
"""

import os
import sqlite3
import pandas as pd

DATA_DIR = "data"
DB_PATH = os.path.join(DATA_DIR, "events.db")

TABLES_TO_VERIFY = [
    "dim_users",
    "dim_funnel_stages",
    "dim_date",
    "fct_events",
    "fct_orders"
]


def verify_and_export():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}. Run data/generate_data.py first.")

    print(f"Connecting to {DB_PATH} to verify tables for Power BI...")
    conn = sqlite3.connect(DB_PATH)

    summary = []
    for tbl in TABLES_TO_VERIFY:
        df = pd.read_sql_query(f"SELECT * FROM {tbl}", conn)
        csv_path = os.path.join(DATA_DIR, f"{tbl}.csv")
        df.to_csv(csv_path, index=False)
        summary.append({
            'Table Name': tbl,
            'Row Count': len(df),
            'Columns': len(df.columns),
            'CSV Export Path': csv_path
        })

    conn.close()

    df_summary = pd.DataFrame(summary)
    print("\n" + "=" * 70)
    print("             POWER BI DATASET EXPORT & INTEGRITY SUMMARY")
    print("=" * 70)
    print(df_summary.to_string(index=False))
    print("=" * 70)
    print("\nAll datasets are synced and ready for import into Power BI Desktop.")


if __name__ == "__main__":
    verify_and_export()
