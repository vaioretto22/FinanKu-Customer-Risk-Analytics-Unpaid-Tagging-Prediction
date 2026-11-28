"""Quick end-to-end check: can Python reach PostgreSQL, and do the database figures match the CSV files?
Run from the project root:  python check_db.py
Only aggregate numbers are printed."""
import pandas as pd
from src.db import get_engine, run_query

engine = get_engine()
print("Connected to:", run_query("SELECT current_database() AS db, version() AS version", engine=engine).iloc[0].tolist()[0])

sql_rates = run_query("""
    SELECT window_id, SUM(customers) AS customers, SUM(tagged) AS tagged
    FROM vw_tagging_cube GROUP BY window_id ORDER BY window_id""", engine=engine)
print(sql_rates)

csv_all = pd.read_csv("data/raw/finanku_data_all.csv")
csv_val = pd.read_csv("data/raw/finanku_data_validasi.csv")
expected = {1: (len(csv_all), int(csv_all["Unpaid Tagging"].sum())), 2: (len(csv_val), int(csv_val["Unpaid Tagging"].sum()))}
for _, r in sql_rates.iterrows():
    exp = expected[int(r["window_id"])]
    ok = (int(r["customers"]), int(r["tagged"])) == exp
    print(f"window {int(r['window_id'])}: SQL=({int(r['customers'])}, {int(r['tagged'])}) CSV={exp} -> {'MATCH' if ok else 'MISMATCH'}")
