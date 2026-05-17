import psycopg2
conn = psycopg2.connect('host=localhost dbname=library_db user=postgres password=GXYL2405')
cur = conn.cursor()
cur.execute("""
    SELECT indexname, indexdef 
    FROM pg_indexes 
    WHERE tablename IN ('circulations', 'borrowers', 'book_categories')
    ORDER BY tablename, indexname
""")
print('Current indexes:')
for row in cur.fetchall():
    print(f'  {row[0]}')

print('\nTable sizes:')
cur.execute("""
    SELECT 
        'circulations' as tbl,
        pg_size_pretty(pg_total_relation_size('circulations')) as size,
        (SELECT COUNT(*) FROM circulations) as rows
""")
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1]} ({row[2]:,} rows)')

cur.close()
conn.close()