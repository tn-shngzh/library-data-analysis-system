import psycopg2
import time
conn = psycopg2.connect('host=localhost dbname=library_db user=postgres password=GXYL2405')
cur = conn.cursor()

print("=== Slow query simulation ===\n")

queries = [
    ("borrows/degree-stats", """
        SELECT b.degree, COUNT(*) as count
        FROM circulations c
        JOIN borrowers b ON c.borrower_id = b.id
        GROUP BY b.degree
        ORDER BY count DESC
    """),
    ("borrows/top-borrowers", """
        SELECT c.borrower_id, b.degree, COUNT(*) as borrow_count
        FROM circulations c
        JOIN borrowers b ON c.borrower_id = b.id
        GROUP BY c.borrower_id, b.degree
        ORDER BY borrow_count DESC
        LIMIT 15
    """),
    ("readers/top (FAILED)", """
        SELECT rs.borrower_id, rs.borrow_count, b.degree
        FROM mv_reader_stats rs
        JOIN borrowers b ON rs.borrower_id = b.id
        ORDER BY rs.borrow_count DESC
        LIMIT 15
    """),
    ("borrows/action-stats", """
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status = 'borrowed') as borrowed,
            COUNT(*) FILTER (WHERE status = 'returned') as returned,
            COUNT(*) FILTER (WHERE renew_count > 0) as renewals
        FROM circulations
    """),
    ("readers/frequency-distribution", """
        SELECT COUNT(DISTINCT borrower_id) as total FROM circulations WHERE status = 'borrowed'
    """),
]

for name, sql in queries:
    start = time.time()
    cur.execute(sql)
    rows = cur.fetchall()
    elapsed = time.time() - start
    print(f"{name}: {elapsed*1000:.0f}ms ({len(rows)} rows)")

print("\n=== Try index scan instead of seq scan ===")
cur.execute("SET enable_seqscan = off")
start = time.time()
cur.execute("""
    SELECT b.degree, COUNT(*) as count
    FROM circulations c
    JOIN borrowers b ON c.borrower_id = b.id
    GROUP BY b.degree
    ORDER BY count DESC
""")
rows = cur.fetchall()
elapsed = time.time() - start
print(f"degree-stats (enable_seqscan=off): {elapsed*1000:.0f}ms")

cur.close()
conn.close()