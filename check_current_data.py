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

# Check borrower borrow counts
cur.execute("""
    SELECT borrower_id, COUNT(*) as borrow_count 
    FROM circulations 
    GROUP BY borrower_id 
    ORDER BY borrow_count DESC 
    LIMIT 20
""")
print("Top 20 borrowers by borrow count:")
for row in cur.fetchall():
    print(f'  Borrower {row[0]}: {row[1]} borrows')

# Count borrowers with >2800
cur.execute("""
    SELECT COUNT(*) FROM (
        SELECT borrower_id, COUNT(*) as cnt 
        FROM circulations 
        GROUP BY borrower_id 
        HAVING COUNT(*) > 2800
    ) t
""")
print(f'\nBorrowers with >2800 borrows: {cur.fetchone()[0]}')

# Check book borrow counts
cur.execute("""
    SELECT bib_id, COUNT(*) as borrow_count 
    FROM circulations 
    GROUP BY bib_id 
    ORDER BY borrow_count DESC 
    LIMIT 20
""")
print('\nTop 20 books by borrow count:')
for row in cur.fetchall():
    print(f'  Book {row[0]}: {row[1]} borrows')

# Count books with >20000
cur.execute("""
    SELECT COUNT(*) FROM (
        SELECT bib_id, COUNT(*) as cnt 
        FROM circulations 
        GROUP BY bib_id 
        HAVING COUNT(*) > 20000
    ) t
""")
print(f'\nBooks with >20000 borrows: {cur.fetchone()[0]}')

# Check total
cur.execute('SELECT COUNT(*) FROM circulations')
print(f'\nTotal circulation records: {cur.fetchone()[0]}')

# Check categories
cur.execute("""
    SELECT c.category_name, COUNT(b.id) as book_count
    FROM book_categories c
    LEFT JOIN (
        SELECT DISTINCT bib_id, category_id FROM (
            SELECT b.id as bib_id, b.category_id 
            FROM (SELECT DISTINCT category_id FROM circulations) c
            JOIN LATERAL (SELECT id, category_id FROM circulations WHERE circulations.bib_id = circulations.bib_id LIMIT 1) b ON true
        ) sub
    ) b ON c.id = b.category_id
    GROUP BY c.category_name
    ORDER BY book_count DESC
""")
print('\nCategory distribution (estimated):')
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1]} books')

conn.close()
print('\nDone!')
