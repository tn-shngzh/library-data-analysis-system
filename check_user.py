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

cur.execute("SELECT id, username, role FROM users WHERE username = 'user'")
user = cur.fetchone()
if user:
    print(f"User 'user' exists: id={user[0]}, username={user[1]}, role={user[2]}")
else:
    print("User 'user' does not exist")
    
# List all users
cur.execute("SELECT id, username, role FROM users ORDER BY id LIMIT 5")
users = cur.fetchall()
print("\nAll users:")
for u in users:
    print(f"  id={u[0]}, username={u[1]}, role={u[2]}")

cur.close()
conn.close()
