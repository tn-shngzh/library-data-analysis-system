import os
os.environ['DB_PASSWORD'] = 'GXYL2405'
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port='5432',
    dbname='library_db',
    user='postgres',
    password='GXYL2405'
)
cur = conn.cursor()

print("Tables:")
cur.execute("""
    SELECT tablename FROM pg_tables WHERE schemaname='public'
    ORDER BY tablename
""")
for row in cur.fetchall():
    print(f"  {row[0]}")

print("\nMaterialized Views:")
cur.execute("""
    SELECT matviewname FROM pg_matviews WHERE schemaname='public'
    ORDER BY matviewname
""")
for row in cur.fetchall():
    print(f"  {row[0]}")

cur.close()
conn.close()
