"""
Robust redistribution with deadlock handling and small batches
"""
import os
import sys
os.environ['DB_PASSWORD'] = 'GXYL2405'
sys.stdout.reconfigure(encoding='utf-8')

print("Connecting to database...")
import psycopg2
import psycopg2.extras
import random
import time

conn = psycopg2.connect(
    host='localhost', port='5432',
    dbname='library_db', user='postgres', password='GXYL2405'
)
cur = conn.cursor()
print("Connected!")

def update_in_batches(cur, conn, query_template, values_list, batch_size=1000, desc="records"):
    """Update records in small batches with deadlock retry"""
    total = 0
    for i in range(0, len(values_list), batch_size):
        batch = values_list[i:i+batch_size]
        vals_str = ','.join(f"({v[0]},{v[1]})" for v in batch)
        
        retries = 3
        for attempt in range(retries):
            try:
                cur.execute(query_template % vals_str)
                conn.commit()
                total += len(batch)
                break
            except psycopg2.errors.DeadlockDetected:
                conn.rollback()
                time.sleep(0.5 * (attempt + 1))
                if attempt == retries - 1:
                    print(f"    Warning: Failed after {retries} retries for batch {i//batch_size}")
            except Exception as e:
                conn.rollback()
                print(f"    Error: {e}")
                break
    return total

# ============================================
# STEP 1: Borrower redistribution
# ============================================
print("\n[1/3] Redistributing borrower records...")

cur.execute("""
    SELECT borrower_id, COUNT(*) as cnt FROM circulations
    GROUP BY borrower_id HAVING COUNT(*) > 2800 ORDER BY cnt DESC
""")
over_borrowers = cur.fetchall()
print(f"  Over-active borrowers: {len(over_borrowers)}")

cur.execute("""
    SELECT borrower_id FROM circulations
    GROUP BY borrower_id HAVING COUNT(*) <= 2800
""")
under_borrowers = [row[0] for row in cur.fetchall()]
print(f"  Available low-frequency borrowers: {len(under_borrowers)}")

random.seed(42)
total = 0

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
    
    print(f"  borrower {borrower_id}: {len(ids):,} records to redistribute")
    
    vals = [(rid, random.choice(under_borrowers)) for rid in ids]
    
    query = """UPDATE circulations SET borrower_id = v.new_id
               FROM (VALUES %%s) AS v(id, new_id)
               WHERE circulations.id = v.id"""
    
    updated = update_in_batches(cur, conn, query, vals, batch_size=500)
    total += updated
    print(f"    -> Updated {updated:,}")

print(f"\n  Total borrower records redistributed: {total:,}")

# ============================================
# STEP 2: Book redistribution
# ============================================
print("\n[2/3] Redistributing book records...")

cur.execute("""
    SELECT bib_id, COUNT(*) as cnt FROM circulations
    GROUP BY bib_id HAVING COUNT(*) > 20000 ORDER BY cnt DESC
""")
over_books = cur.fetchall()
print(f"  Over-borrowed books: {len(over_books)}")

cur.execute("""
    SELECT bib_id FROM circulations
    GROUP BY bib_id HAVING COUNT(*) <= 20000
""")
under_books = [row[0] for row in cur.fetchall()]
print(f"  Available low-frequency books: {len(under_books)}")

total = 0
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
    
    print(f"  book {bib_id}: {len(ids):,} records to redistribute")
    
    vals = [(rid, random.choice(under_books)) for rid in ids]
    
    query = """UPDATE circulations SET bib_id = v.new_id
               FROM (VALUES %%s) AS v(id, new_id)
               WHERE circulations.id = v.id"""
    
    updated = update_in_batches(cur, conn, query, vals, batch_size=500)
    total += updated
    print(f"    -> Updated {updated:,}")

print(f"\n  Total book records redistributed: {total:,}")

# ============================================
# STEP 3: Category adjustment
# ============================================
print("\n[3/3] Adjusting categories...")

cur.execute("SELECT category, COUNT(*) FROM book_categories GROUP BY category ORDER BY COUNT(*) DESC")
cats = {r[0]: r[1] for r in cur.fetchall()}
total_books = sum(cats.values())

targets = {
    '马克思主义': 0.01,
    '综合性图书': 0.012,
    '航空航天': 0.015,
    '农业科学': 0.018,
    '环境安全': 0.018,
}

over_c = [(c, cnt - int(total_books * targets[c])) for c, cnt in cats.items() 
          if c in targets and cnt > total_books * targets[c] * 1.005]
under_c = [(c, int(total_books * targets[c]) - cats[c]) for c, cnt in cats.items() 
           if c in targets and cnt < total_books * targets[c] * 0.995]

if over_c and under_c:
    to_move = []
    for cat, excess in over_c:
        cur.execute("SELECT bib_id FROM book_categories WHERE category=%s ORDER BY RANDOM() LIMIT %s", (cat, excess))
        to_move.extend([row[0] for row in cur.fetchall()])
    
    print(f"  Moving {len(to_move):,} books between categories")
    
    under_list = []
    total_deficit = sum(d for _, d in under_c)
    for cat, def_ in under_c:
        count = max(1, len(to_move) * def_ // total_deficit)
        under_list.extend([cat] * count)
    random.shuffle(under_list)
    while len(under_list) < len(to_move):
        under_list.append(random.choice([c for c, _ in under_c]))
    
    query = """UPDATE book_categories SET category = v.nc
               FROM (VALUES %%s) AS v(bib, nc)
               WHERE book_categories.bib_id = v.bib"""
    
    vals = [(to_move[i], under_list[i % len(under_list)]) for i in range(len(to_move))]
    
    # Convert to string format for VALUES
    total_cat = 0
    for i in range(0, len(vals), 500):
        batch = vals[i:i+500]
        vals_str = ','.join(f"({bib},'{nc}')" for bib, nc in batch)
        
        retries = 3
        for attempt in range(retries):
            try:
                cur.execute(query % vals_str)
                conn.commit()
                total_cat += len(batch)
                break
            except psycopg2.errors.DeadlockDetected:
                conn.rollback()
                time.sleep(0.5)
            except Exception as e:
                conn.rollback()
                print(f"    Error: {e}")
                break
    
    print(f"  -> Updated {total_cat:,} categories")
else:
    print("  Categories already reasonable")

# ============================================
# Refresh views
# ============================================
print("\nRefreshing materialized views...")
cur.execute("SELECT matviewname FROM pg_matviews WHERE schemaname='public'")
for row in cur.fetchall():
    try:
        cur.execute(f"REFRESH MATERIALIZED VIEW {row[0]}")
        conn.commit()
        print(f"  [OK] {row[0]}")
    except Exception as e:
        print(f"  [FAIL] {row[0]}: {e}")
        conn.rollback()

# ============================================
# Results
# ============================================
print("\n" + "=" * 50)
print("RESULTS")
print("=" * 50)

print("\nTop borrowers:")
cur.execute("SELECT borrower_id, COUNT(*) FROM circulations GROUP BY borrower_id ORDER BY COUNT(*) DESC LIMIT 5")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]:,}")

cur.execute("SELECT COUNT(*) FROM (SELECT borrower_id FROM circulations GROUP BY borrower_id HAVING COUNT(*)>2800) s")
print(f"\nBorrowers >2800: {cur.fetchone()[0]}")

print("\nTop books:")
cur.execute("SELECT bib_id, COUNT(*) FROM circulations GROUP BY bib_id ORDER BY COUNT(*) DESC LIMIT 5")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]:,}")

cur.execute("SELECT COUNT(*) FROM (SELECT bib_id FROM circulations GROUP BY bib_id HAVING COUNT(*)>20000) s")
print(f"\nBooks >20000: {cur.fetchone()[0]}")

print("\nCategories:")
cur.execute("SELECT category, COUNT(*) FROM book_categories GROUP BY category ORDER BY COUNT(*) DESC")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]:,}")

cur.close()
conn.close()
print("\nDone!")
