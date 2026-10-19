"""
SQL Query Runner for Funneling Analysis Project
Executes SQL queries against the local SQLite database (data/events.db)
Usage:
    python run_sql.py
    python run_sql.py sql/01_srm_check.sql
    python run_sql.py sql/statistical_tests/01_srm_chi_square_in_sql.sql
"""

import os
import sys
import sqlite3
import pandas as pd

def run_query(sql_file: str = "sql/01_srm_check.sql", db_path: str = "data/events.db"):
    if not os.path.exists(db_path):
        print(f"Error: Database not found at '{db_path}'.")
        print("Please run 'python data/generate_data.py' to generate the database.")
        sys.exit(1)

    if not os.path.exists(sql_file):
        print(f"Error: SQL file not found at '{sql_file}'.")
        sys.exit(1)

    with open(sql_file, "r", encoding="utf-8") as f:
        query = f.read()

    print(f"\n[+] Executing: {sql_file}")
    print(f"[+] Target DB: {db_path}\n")

    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(query, conn)
        # Format table output nicely
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        print(df.to_string(index=False))
        print(f"\n[+] Query completed successfully ({len(df)} row{'s' if len(df) != 1 else ''} returned).\n")
    except Exception as e:
        print(f"[!] Error executing query: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    sql_path = sys.argv[1] if len(sys.argv) > 1 else "sql/01_srm_check.sql"
    run_query(sql_path)
