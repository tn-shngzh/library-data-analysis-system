import os
import psycopg2

os.environ['DB_PASSWORD'] = 'GXYL2405'

conn = psycopg2.connect(
    host='localhost',
    port='5432',
    dbname='library_db',
    user='postgres',
    password='GXYL2405'
)
cur = conn.cursor()

cur.execute("""
    SELECT tablename FROM pg_tables WHERE schemaname='public' 
    UNION 
    SELECT matviewname FROM pg_matviews WHERE schemaname='public'
""")
tables = [r[0] for r in cur.fetchall()]
print('Tables/Views:', tables)

needed = ['book_categories', 'mv_top_books', 'mv_borrow_stats', 'circulations']
for n in needed:
    status = "EXISTS" if n in tables else "MISSING"
    print(f'{n}: {status}')

cur.close()
conn.close()
