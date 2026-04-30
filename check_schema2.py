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

# Get book_categories columns and data
print("book_categories:")
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'book_categories' ORDER BY ordinal_position")
print("  Columns:")
for row in cur.fetchall():
    print(f"    {row[0]:20s} {row[1]}")

cur.execute("SELECT * FROM book_categories LIMIT 20")
desc = [d[0] for d in cur.description]
print(f"\n  Data (columns: {desc}):")
for row in cur.fetchall():
    print(f"    {row}")

# Check action_types - these are actions not books!
# The "books" must be referenced by bib_id in circulations
# Let's check mv_top_books to understand how books are represented
print("\n\nmv_top_books:")
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'mv_top_books' ORDER BY ordinal_position")
for row in cur.fetchall():
    print(f"  {row[0]:20s} {row[1]}")

cur.execute("SELECT * FROM mv_top_books ORDER BY borrow_count DESC LIMIT 10")
print("\n  Top 10 books by borrow count:")
for row in cur.fetchall():
    print(f"    {row}")

# Book categories distribution - check if there's a way to link
print("\n\nmv_book_stats:")
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'mv_book_stats' ORDER BY ordinal_position")
cols = [r[0] for r in cur.fetchall()]
print(f"  Columns: {cols}")

cur.execute("SELECT * FROM mv_book_stats ORDER BY total DESC LIMIT 5")
for row in cur.fetchall():
    print(f"    {row}")

# Circulations stats
print("\n\nCirculations summary:")
cur.execute("SELECT COUNT(*) FROM circulations")
print(f"  Total records: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(DISTINCT bib_id) FROM circulations")
print(f"  Unique bib_ids (books borrowed at least once): {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(DISTINCT borrower_id) FROM circulations")
print(f"  Unique borrowers (people who borrowed): {cur.fetchone()[0]}")

# Borrower borrow frequency
print("\n\nTop 10 borrowers by borrow count:")
cur.execute("""
    SELECT borrower_id, COUNT(*) as cnt
    FROM circulations
    GROUP BY borrower_id
    ORDER BY cnt DESC
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"  borrower_id={row[0]}: {row[1]} borrows")

# Borrow distribution - how many borrowers have X borrows
print("\n\nBorrow frequency distribution:")
cur.execute("""
    SELECT borrow_count, COUNT(*) as num_borrowers
    FROM (
        SELECT borrower_id, COUNT(*) as borrow_count
        FROM circulations
        GROUP BY borrower_id
    ) sub
    GROUP BY borrow_count
    ORDER BY borrow_count DESC
    LIMIT 20
""")
for row in cur.fetchall():
    print(f"  {row[1]:5d} 人借了 {row[0]:5d} 次")

# Books borrow frequency distribution
print("\n\nBook borrow frequency distribution:")
cur.execute("""
    SELECT borrow_count, COUNT(*) as num_books
    FROM (
        SELECT bib_id, COUNT(*) as borrow_count
        FROM circulations
        GROUP BY bib_id
    ) sub
    GROUP BY borrow_count
    ORDER BY borrow_count DESC
    LIMIT 20
""")
for row in cur.fetchall():
    print(f"  {row[1]:5d} 本书被借了 {row[0]:5d} 次")

# Check degree distribution of borrowers
print("\n\nBorrower degree distribution:")
cur.execute("""
    SELECT degree, COUNT(*) as cnt
    FROM borrowers
    WHERE degree IS NOT NULL
    GROUP BY degree
    ORDER BY cnt DESC
    LIMIT 20
""")
for row in cur.fetchall():
    print(f"  {str(row[0])[:20]:20s}: {row[1]}")

cur.close()
conn.close()
