"""
Simple and efficient data redistribution
"""
import os
import sys
os.environ['DB_PASSWORD'] = 'GXYL2405'
sys.stdout.reconfigure(encoding='utf-8')

print("Connecting to database...")
import psycopg2
import psycopg2.extras
import random

conn = psycopg2.connect(
    host='localhost', port='5432',
    dbname='library_db', user='postgres', password='GXYL2405'
)
conn.autocommit = False
cur = conn.cursor()
print("Connected!")

print("\n[1/5] Analyzing current data...")

cur.execute("""
    SELECT borrower_id, COUNT(*) as cnt FROM circulations
    GROUP BY borrower_id HAVING COUNT(*) > 2800 ORDER BY cnt DESC
""")
over_borrowers = cur.fetchall()
total_excess = sum(cnt - 2800 for _, cnt in over_borrowers)
print(f"  Over-active borrowers: {len(over_borrowers)}, excess records: {total_excess:,}")

cur.execute("""
    SELECT bib_id, COUNT(*) as cnt FROM circulations
    GROUP BY bib_id HAVING COUNT(*) > 20000 ORDER BY cnt DESC
""")
over_books = cur.fetchall()
total_excess_books = sum(cnt - 20000 for _, cnt in over_books)
print(f"  Over-borrowed books: {len(over_books)}, excess records: {total_excess_books:,}")

print("\n[2/5] Redistributing borrower records...")
cur.execute("""
    SELECT borrower_id FROM circulations
    GROUP BY borrower_id HAVING COUNT(*) <= 2800
""")
under_borrowers = [row[0] for row in cur.fetchall()]
print(f"  Available low-frequency borrowers: {len(under_borrowers)}")

random.seed(42)
total_updated = 0

for borrower_id, cnt in over_borrowers:
    excess = cnt - 2800
    if excess <= 0:
        continue
    
    cur.execute("""
        WITH ranked AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY RANDOM()) as rn
            FROM circulations WHERE borrower_id = %s
        )
        SELECT id FROM ranked WHERE rn > 2800
    """, (borrower_id,))
    ids = [row[0] for row in cur.fetchall()]
    
    if not ids:
        continue
    
    print(f"  borrower {borrower_id}: redistributing {len(ids):,} records")
    
    for i in range(0, len(ids), 10000):
        chunk = ids[i:i+10000]
        vals = [(rid, random.choice(under_borrowers)) for rid in chunk]
        
        cur.execute("DROP TABLE IF EXISTS tmp_upd")
        cur.execute("CREATE TEMP TABLE tmp_upd (id INT, nb INT)")
        psycopg2.extras.execute_values(cur, "INSERT INTO tmp_upd VALUES %s", vals)
        
        cur.execute("UPDATE circulations c SET borrower_id=t.nb FROM tmp_upd t WHERE c.id=t.id")
        conn.commit()
        cur.execute("DROP TABLE IF EXISTS tmp_upd")
        total_updated += len(chunk)

print(f"  Updated {total_updated:,} borrower records")

print("\n[3/5] Redistributing book records...")
cur.execute("""
    SELECT bib_id FROM circulations
    GROUP BY bib_id HAVING COUNT(*) <= 20000
""")
under_books = [row[0] for row in cur.fetchall()]
print(f"  Available low-frequency books: {len(under_books)}")

cur.execute("""
    SELECT bib_id, COUNT(*) as cnt FROM circulations
    GROUP BY bib_id HAVING COUNT(*) > 20000 ORDER BY cnt DESC
""")
over_books = cur.fetchall()

total_updated = 0
for bib_id, cnt in over_books:
    excess = cnt - 20000
    if excess <= 0:
        continue
    
    cur.execute("""
        WITH ranked AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY RANDOM()) as rn
            FROM circulations WHERE bib_id = %s
        )
        SELECT id FROM ranked WHERE rn > 20000
    """, (bib_id,))
    ids = [row[0] for row in cur.fetchall()]
    
    if not ids:
        continue
    
    print(f"  book {bib_id}: redistributing {len(ids):,} records")
    
    for i in range(0, len(ids), 10000):
        chunk = ids[i:i+10000]
        vals = [(rid, random.choice(under_books)) for rid in chunk]
        
        cur.execute("DROP TABLE IF EXISTS tmp_upd")
        cur.execute("CREATE TEMP TABLE tmp_upd (id INT, nb INT)")
        psycopg2.extras.execute_values(cur, "INSERT INTO tmp_upd VALUES %s", vals)
        
        cur.execute("UPDATE circulations c SET bib_id=t.nb FROM tmp_upd t WHERE c.id=t.id")
        conn.commit()
        cur.execute("DROP TABLE IF EXISTS tmp_upd")
        total_updated += len(chunk)

print(f"  Updated {total_updated:,} book records")

print("\n[4/5] Adjusting categories...")
cur.execute("SELECT category, COUNT(*) FROM book_categories GROUP BY category ORDER BY COUNT(*) DESC")
cats = {r[0]: r[1] for r in cur.fetchall()}
total = sum(cats.values())

targets = {'马克思主义': 0.01, '综合性图书': 0.012, '航空航天': 0.015, '农业科学': 0.018, '环境安全': 0.018}
over_c = [(c, cnt - int(total * targets[c])) for c, cnt in cats.items() if c in targets and cnt > total * targets[c] * 1.005]
under_c = [(c, int(total * targets[c]) - cats[c]) for c, cnt in cats.items() if c in targets and cnt < total * targets[c] * 0.995]

if over_c and under_c:
    to_move = []
    for cat, excess in over_c:
        cur.execute("SELECT bib_id FROM book_categories WHERE category=%s ORDER BY RANDOM() LIMIT %s", (cat, excess))
        to_move.extend([row[0] for row in cur.fetchall()])
    
    print(f"  Moving {len(to_move):,} books between categories")
    
    under_list = []
    for cat, def_ in under_c:
        under_list.extend([cat] * max(1, len(to_move) * def_ // sum(d for _, d in under_c)))
    random.shuffle(under_list)
    while len(under_list) < len(to_move):
        under_list.append(random.choice([c for c, _ in under_c]))
    
    for i in range(0, len(to_move), 1000):
        chunk = to_move[i:i+1000]
        vals = [(bib, under_list[i+j % len(under_list)]) for j, bib in enumerate(chunk)]
        cur.execute("DROP TABLE IF EXISTS tmp_upd")
        cur.execute("CREATE TEMP TABLE tmp_upd (bib INT, nc VARCHAR)")
        psycopg2.extras.execute_values(cur, "INSERT INTO tmp_upd VALUES %s", vals)
        cur.execute("UPDATE book_categories bc SET category=t.nc FROM tmp_upd t WHERE bc.bib_id=t.bib")
        conn.commit()
        cur.execute("DROP TABLE IF EXISTS tmp_upd")
    print("  Categories updated")
else:
    print("  Categories already reasonable")

print("\n[5/5] Refreshing views and verifying...")
cur.execute("SELECT matviewname FROM pg_matviews WHERE schemaname='public'")
for row in cur.fetchall():
    try:
        cur.execute(f"REFRESH MATERIALIZED VIEW {row[0]}")
        conn.commit()
        print(f"  [OK] {row[0]}")
    except Exception as e:
        print(f"  [FAIL] {row[0]}: {e}")
        conn.rollback()

print("\n--- Results ---")
cur.execute("SELECT borrower_id, COUNT(*) FROM circulations GROUP BY borrower_id ORDER BY COUNT(*) DESC LIMIT 5")
for r in cur.fetchall():
    print(f"  Top borrower: {r[0]} = {r[1]:,}")

cur.execute("SELECT COUNT(*) FROM (SELECT borrower_id FROM circulations GROUP BY borrower_id HAVING COUNT(*)>2800) s")
print(f"  Borrowers >2800: {cur.fetchone()[0]}")

cur.execute("SELECT bib_id, COUNT(*) FROM circulations GROUP BY bib_id ORDER BY COUNT(*) DESC LIMIT 5")
for r in cur.fetchall():
    print(f"  Top book: {r[0]} = {r[1]:,}")

cur.execute("SELECT COUNT(*) FROM (SELECT bib_id FROM circulations GROUP BY bib_id HAVING COUNT(*)>20000) s")
print(f"  Books >20000: {cur.fetchone()[0]}")

cur.execute("SELECT category, COUNT(*) FROM book_categories GROUP BY category ORDER BY COUNT(*) DESC")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]:,}")

cur.close()
conn.close()
print("\nDone!")
