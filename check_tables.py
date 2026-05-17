import psycopg2
conn = psycopg2.connect('postgresql://datav:AhZIJo8W@192.168.1.77:5432/datav')
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%cache%' OR table_name LIKE '%history%' OR table_name LIKE '%agg%' ORDER BY table_name")
rows = cur.fetchall()
for r in rows:
    print(r[0])
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'monthly_history_cache' ORDER BY ordinal_position")
print("\n--- monthly_history_cache columns ---")
cols = cur.fetchall()
for c in cols:
    print(f"  {c[0]} ({c[1]})")
conn.close()
