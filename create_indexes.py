import psycopg2
import time
conn = psycopg2.connect('host=localhost dbname=library_db user=postgres password=GXYL2405')
cur = conn.cursor()

print("=== Creating missing indexes ===")

indexes_to_create = [
    "CREATE INDEX IF NOT EXISTS idx_circ_status_borrower ON circulations(status, borrower_id)",
    "CREATE INDEX IF NOT EXISTS idx_circ_status_action ON circulations(status, action)",
    "CREATE INDEX IF NOT EXISTS idx_circ_bib_status ON circulations(bib_id, status)",
]

for sql in indexes_to_create:
    try:
        cur.execute(sql)
        print(f"Created: {sql}")
    except Exception as e:
        print(f"Error: {e}")

conn.commit()

print("\n=== Test queries after index creation ===")

print("\n1. borrows/degree-stats:")
start = time.time()
cur.execute("""
    SELECT b.degree, COUNT(*) as count
    FROM circulations c
    JOIN borrowers b ON c.borrower_id = b.id
    WHERE c.status = 'borrowed'
    GROUP BY b.degree
    ORDER BY count DESC
""")
print(f"   {len(cur.fetchall())} rows in {(time.time()-start)*1000:.0f}ms")

print("\n2. borrows/top-borrowers:")
start = time.time()
cur.execute("""
    SELECT c.borrower_id, b.degree, COUNT(*) as borrow_count
    FROM circulations c
    JOIN borrowers b ON c.borrower_id = b.id
    WHERE c.status = 'borrowed'
    GROUP BY c.borrower_id, b.degree
    ORDER BY borrow_count DESC
    LIMIT 15
""")
print(f"   {len(cur.fetchall())} rows in {(time.time()-start)*1000:.0f}ms")

print("\n3. readers/top:")
start = time.time()
cur.execute("""
    SELECT c.borrower_id, b.degree, COUNT(*) as borrow_count
    FROM circulations c
    JOIN borrowers b ON c.borrower_id = b.id
    WHERE c.status = 'borrowed'
    GROUP BY c.borrower_id, b.degree
    ORDER BY borrow_count DESC
    LIMIT 15
""")
print(f"   {len(cur.fetchall())} rows in {(time.time()-start)*1000:.0f}ms")

print("\n4. readers/frequency-distribution (step 1):")
start = time.time()
cur.execute("SELECT COUNT(DISTINCT borrower_id) FROM circulations WHERE status = 'borrowed'")
print(f"   {cur.fetchone()[0]} readers in {(time.time()-start)*1000:.0f}ms")

print("\n5. borrows/action-stats:")
start = time.time()
cur.execute("SELECT * FROM mv_action_stats")
print(f"   {len(cur.fetchall())} rows in {(time.time()-start)*1000:.0f}ms")

cur.close()
conn.close()
print("\n=== Done ===")