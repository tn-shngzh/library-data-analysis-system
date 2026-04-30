"""
Efficient redistribution - apply updates immediately per entity
"""
import os
import sys
os.environ['DB_PASSWORD'] = 'GXYL2405'
sys.stdout.reconfigure(encoding='utf-8')
import psycopg2
import psycopg2.extras
import random

conn = psycopg2.connect(
    host='localhost', port='5432',
    dbname='library_db', user='postgres', password='GXYL2405'
)
conn.autocommit = False
cur = conn.cursor()

print("=" * 60)
print("Library Data Rationalization")
print("=" * 60)

# STEP 1
print("\n[Step 1] Identifying anomalous data...")

cur.execute("""
    SELECT borrower_id, COUNT(*) as cnt
    FROM circulations
    GROUP BY borrower_id
    HAVING COUNT(*) > 2800
    ORDER BY cnt DESC
""")
over_borrowers = cur.fetchall()
print(f"  High-frequency borrowers (>2800): {len(over_borrowers)} users")

cur.execute("""
    SELECT bib_id, COUNT(*) as cnt
    FROM circulations
    GROUP BY bib_id
    HAVING COUNT(*) > 20000
    ORDER BY cnt DESC
""")
over_books = cur.fetchall()
print(f"  High-frequency books (>20000): {len(over_books)} books")

# STEP 2
print("\n" + "=" * 60)
print("[Step 2] Redistributing high-frequency borrower records...")
print("=" * 60)

cur.execute("""
    SELECT borrower_id
    FROM circulations
    GROUP BY borrower_id
    HAVING COUNT(*) <= 2800
""")
under_borrowers = [row[0] for row in cur.fetchall()]
print(f"  Low-frequency borrowers: {len(under_borrowers)} users")

random.seed(42)
total_updated = 0

for borrower_id, cnt in over_borrowers:
    excess_count = cnt - 2800
    if excess_count <= 0:
        continue
    
    print(f"\n  Processing borrower_id={borrower_id} ({cnt:,} -> keep 2800)")
    
    # Get random excess records
    cur.execute("""
        WITH ranked AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY RANDOM()) as rn
            FROM circulations
            WHERE borrower_id = %s
        )
        SELECT id FROM ranked WHERE rn > 2800
    """, (borrower_id,))
    excess_ids = [row[0] for row in cur.fetchall()]
    print(f"    Records to redistribute: {len(excess_ids):,}")
    
    # Update in batches - apply immediately
    batch_size = 10000
    for i in range(0, len(excess_ids), batch_size):
        chunk = excess_ids[i:i+batch_size]
        # Create mapping for this batch
        updates = [(rid, random.choice(under_borrowers)) for rid in chunk]
        
        # Use temp table for batch update
        cur.execute("DROP TABLE IF EXISTS temp_batch")
        cur.execute("CREATE TEMP TABLE temp_batch (id INTEGER, new_borrower_id INTEGER)")
        
        psycopg2.extras.execute_values(
            cur,
            "INSERT INTO temp_batch (id, new_borrower_id) VALUES %s",
            updates,
            page_size=batch_size
        )
        
        cur.execute("""
            UPDATE circulations c
            SET borrower_id = t.new_borrower_id
            FROM temp_batch t
            WHERE c.id = t.id
        """)
        conn.commit()
        cur.execute("DROP TABLE IF EXISTS temp_batch")
        total_updated += len(chunk)
    
    print(f"    [OK] Updated {len(excess_ids):,} records")

print(f"\n  [DONE] Total borrower records redistributed: {total_updated:,}")

# STEP 3
print("\n" + "=" * 60)
print("[Step 3] Redistributing high-frequency book records...")
print("=" * 60)

cur.execute("""
    SELECT bib_id
    FROM circulations
    GROUP BY bib_id
    HAVING COUNT(*) <= 20000
""")
under_books = [row[0] for row in cur.fetchall()]
print(f"  Low-frequency books: {len(under_books)} books")

# Re-check over-books after borrower redistribution
cur.execute("""
    SELECT bib_id, COUNT(*) as cnt
    FROM circulations
    GROUP BY bib_id
    HAVING COUNT(*) > 20000
    ORDER BY cnt DESC
""")
over_books = cur.fetchall()

total_updated = 0

for bib_id, cnt in over_books:
    excess_count = cnt - 20000
    if excess_count <= 0:
        continue
    
    print(f"\n  Processing bib_id={bib_id} ({cnt:,} -> keep 20000)")
    
    cur.execute("""
        WITH ranked AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY RANDOM()) as rn
            FROM circulations
            WHERE bib_id = %s
        )
        SELECT id FROM ranked WHERE rn > 20000
    """, (bib_id,))
    excess_ids = [row[0] for row in cur.fetchall()]
    print(f"    Records to redistribute: {len(excess_ids):,}")
    
    batch_size = 10000
    for i in range(0, len(excess_ids), batch_size):
        chunk = excess_ids[i:i+batch_size]
        updates = [(rid, random.choice(under_books)) for rid in chunk]
        
        cur.execute("DROP TABLE IF EXISTS temp_batch")
        cur.execute("CREATE TEMP TABLE temp_batch (id INTEGER, new_bib_id INTEGER)")
        
        psycopg2.extras.execute_values(
            cur,
            "INSERT INTO temp_batch (id, new_bib_id) VALUES %s",
            updates,
            page_size=batch_size
        )
        
        cur.execute("""
            UPDATE circulations c
            SET bib_id = t.new_bib_id
            FROM temp_batch t
            WHERE c.id = t.id
        """)
        conn.commit()
        cur.execute("DROP TABLE IF EXISTS temp_batch")
        total_updated += len(chunk)
    
    print(f"    [OK] Updated {len(excess_ids):,} records")

print(f"\n  [DONE] Total book records redistributed: {total_updated:,}")

# STEP 4 - Category redistribution
print("\n" + "=" * 60)
print("[Step 4] Adjusting book category distribution...")
print("=" * 60)

cur.execute("""
    SELECT category, COUNT(*) as cnt
    FROM book_categories
    GROUP BY category
    ORDER BY cnt DESC
""")
current_dist = {row[0]: row[1] for row in cur.fetchall()}
total_books = sum(current_dist.values())

print(f"  Total books: {total_books:,}")
print("\n  Current distribution:")
for cat, cnt in sorted(current_dist.items(), key=lambda x: -x[1]):
    print(f"    {cat:15s}: {cnt:>6,} ({cnt/total_books*100:5.1f}%)")

target_ratios = {
    '马克思主义': 0.01,
    '综合性图书': 0.012,
    '航空航天': 0.015,
    '农业科学': 0.018,
    '环境安全': 0.018,
}

over_cats = []
under_cats = []

for cat, cnt in current_dist.items():
    ratio = cnt / total_books
    target_ratio = target_ratios.get(cat, None)
    
    if target_ratio and ratio > target_ratio + 0.005:
        excess = cnt - int(total_books * target_ratio)
        if excess > 0:
            over_cats.append((cat, excess))
    
    if target_ratio and ratio < target_ratio - 0.005:
        deficit = int(total_books * target_ratio) - cnt
        if deficit > 0:
            under_cats.append((cat, deficit))

if over_cats and under_cats:
    print("\n  Adjustment plan:")
    for cat, excess in sorted(over_cats, key=lambda x: -x[1]):
        print(f"    {cat:15s}: reduce {excess:,} books")
    for cat, deficit in sorted(under_cats, key=lambda x: -x[1]):
        print(f"    {cat:15s}: add {deficit:,} books")
    
    books_to_move = []
    for cat, excess in over_cats:
        cur.execute("""
            SELECT bib_id FROM book_categories
            WHERE category = %s
            ORDER BY RANDOM()
            LIMIT %s
        """, (cat, excess))
        books_to_move.extend([(row[0], cat) for row in cur.fetchall()])
    
    print(f"\n  Books to redistribute: {len(books_to_move):,}")
    
    total_deficit = sum(d for _, d in under_cats)
    under_cat_list = []
    for cat, deficit in under_cats:
        count = max(1, int(len(books_to_move) * deficit / total_deficit))
        under_cat_list.extend([cat] * count)
    
    random.shuffle(under_cat_list)
    while len(under_cat_list) < len(books_to_move):
        under_cat_list.append(random.choice([c for c, _ in under_cats]))
    
    # Apply updates in batches
    batch_size = 1000
    for i in range(0, len(books_to_move), batch_size):
        chunk = books_to_move[i:i+batch_size]
        
        cur.execute("DROP TABLE IF EXISTS temp_cat_batch")
        cur.execute("CREATE TEMP TABLE temp_cat_batch (bib_id INTEGER, new_category VARCHAR)")
        
        values = []
        for bib_id, old_cat in chunk:
            new_cat = under_cat_list[i % len(under_cat_list)]
            values.append((bib_id, new_cat))
        
        psycopg2.extras.execute_values(
            cur,
            "INSERT INTO temp_cat_batch (bib_id, new_category) VALUES %s",
            values,
            page_size=batch_size
        )
        
        cur.execute("""
            UPDATE book_categories bc
            SET category = t.new_category
            FROM temp_cat_batch t
            WHERE bc.bib_id = t.bib_id
        """)
        conn.commit()
        cur.execute("DROP TABLE IF EXISTS temp_cat_batch")
    
    print(f"  [OK] {len(books_to_move):,} books reassigned categories")
else:
    print("\n  Category distribution is reasonable")

# STEP 5 - Refresh views
print("\n" + "=" * 60)
print("[Step 5] Refreshing materialized views...")
print("=" * 60)

cur.execute("SELECT matviewname FROM pg_matviews WHERE schemaname = 'public' ORDER BY matviewname")
views = [row[0] for row in cur.fetchall()]

for view in views:
    try:
        cur.execute(f"REFRESH MATERIALIZED VIEW {view}")
        conn.commit()
        print(f"  [OK] {view}")
    except Exception as e:
        print(f"  [FAIL] {view}: {e}")
        conn.rollback()

# STEP 6 - Verify
print("\n" + "=" * 60)
print("[Final Verification]")
print("=" * 60)

print("\n  Top 5 borrowers:")
cur.execute("""
    SELECT borrower_id, COUNT(*) as cnt FROM circulations
    GROUP BY borrower_id ORDER BY cnt DESC LIMIT 5
""")
for row in cur.fetchall():
    print(f"    borrower_id={row[0]}: {row[1]:,}")

cur.execute("SELECT COUNT(*) FROM (SELECT borrower_id FROM circulations GROUP BY borrower_id HAVING COUNT(*) > 2800) sub")
print(f"\n  Borrowers with >2800: {cur.fetchone()[0]}")

print("\n  Top 5 books:")
cur.execute("""
    SELECT bib_id, COUNT(*) as cnt FROM circulations
    GROUP BY bib_id ORDER BY cnt DESC LIMIT 5
""")
for row in cur.fetchall():
    print(f"    bib_id={row[0]}: {row[1]:,}")

cur.execute("SELECT COUNT(*) FROM (SELECT bib_id FROM circulations GROUP BY bib_id HAVING COUNT(*) > 20000) sub")
print(f"\n  Books with >20000: {cur.fetchone()[0]}")

print("\n  Books by category:")
cur.execute("SELECT category, COUNT(*) as cnt FROM book_categories GROUP BY category ORDER BY cnt DESC")
for row in cur.fetchall():
    print(f"    {str(row[0])[:15]:15s}: {row[1]:>6,}")

cur.close()
conn.close()

print("\n" + "=" * 60)
print("[DONE] All data rationalized!")
print("=" * 60)
