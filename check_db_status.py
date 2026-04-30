import psycopg2
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = psycopg2.connect(
    host='localhost',
    port='5432',
    dbname='library_db',
    user='postgres',
    password='GXYL2405'
)
cur = conn.cursor()

# List all tables
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    ORDER BY table_name
""")
print("Tables in database:")
for row in cur.fetchall():
    print(f'  {row[0]}')

# Check table structures
for table in ['borrowers', 'biblios', 'circulations']:
    try:
        cur.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table}'
            ORDER BY ordinal_position
        """)
        print(f'\n{table} columns:')
        for row in cur.fetchall():
            print(f'  {row[0]} ({row[1]})')
    except:
        pass

conn.close()
