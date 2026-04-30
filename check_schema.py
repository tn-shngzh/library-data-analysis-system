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

# Get action_types columns
print("action_types columns:")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'action_types'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"  {row[0]:20s} {row[1]}")

# Get sample data
print("\naction_types sample (2 rows):")
cur.execute("SELECT * FROM action_types LIMIT 2")
desc = [d[0] for d in cur.description]
print(f"  Columns: {desc}")
for row in cur.fetchall():
    print(f"  {row}")

# Get circulations columns
print("\ncirculations columns:")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'circulations'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"  {row[0]:20s} {row[1]}")

# Get circulations sample
print("\ncirculations sample (2 rows):")
cur.execute("SELECT * FROM circulations LIMIT 2")
desc = [d[0] for d in cur.description]
print(f"  Columns: {desc}")
for row in cur.fetchall():
    print(f"  {row}")

# Get borrowers columns
print("\nborrowers columns:")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'borrowers'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"  {row[0]:20s} {row[1]}")

# Get borrowers sample
print("\nborrowers sample (2 rows):")
cur.execute("SELECT * FROM borrowers LIMIT 2")
desc = [d[0] for d in cur.description]
print(f"  Columns: {desc}")
for row in cur.fetchall():
    print(f"  {row}")

# Get book_categories columns and data
print("\nbook_categories:")
cur.execute("SELECT * FROM book_categories ORDER BY id")
desc = [d[0] for d in cur.description]
print(f"  Columns: {desc}")
for row in cur.fetchall():
    print(f"  {row}")

cur.close()
conn.close()
