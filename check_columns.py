import psycopg
conn = psycopg.connect('host=localhost dbname=library_db user=postgres password=postgres')
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'circulations' ORDER BY ordinal_position")
print('Circulations table columns:')
for row in cur.fetchall():
    print(' -', row[0])
cur.close()
conn.close()
