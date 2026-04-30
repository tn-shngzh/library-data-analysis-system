"""
Rebalance book categories - move books from over-represented to under-represented categories
"""
import psycopg2
import psycopg2.extras
import random
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("Connecting to database...")
conn = psycopg2.connect(
    host='localhost',
    port='5432',
    dbname='library_db',
    user='postgres',
    password='GXYL2405'
)
cur = conn.cursor()
print("Connected!\n")

# Get current distribution
cur.execute("""
    SELECT category, COUNT(*) as book_count 
    FROM book_categories 
    GROUP BY category 
    ORDER BY book_count DESC
""")
categories = {row[0]: row[1] for row in cur.fetchall()}
total = sum(categories.values())

print(f"Total books: {total:,}")
print(f"\nCurrent distribution:")
for cat, cnt in sorted(categories.items(), key=lambda x: -x[1]):
    pct = cnt / total * 100
    print(f"  {cat}: {cnt:,} ({pct:.2f}%)")

# Target for over-represented categories
targets = {
    '马克思主义': 6000,
    '综合性图书': 7000,
    '航空航天': 9000,
    '农业科学': 11000,
    '环境安全': 11000,
}

# Find books to move
books_to_move = []
for cat, target in targets.items():
    current = categories.get(cat, 0)
    if current > target:
        excess = current - target
        print(f"\nMoving {excess:,} books from '{cat}'")
        cur.execute(
            "SELECT bib_id FROM book_categories WHERE category=%s ORDER BY RANDOM() LIMIT %s",
            (cat, excess)
        )
        bibs = [row[0] for row in cur.fetchall()]
        books_to_move.extend(bibs)
        print(f"  Selected {len(bibs):,} books to move")

print(f"\nTotal books to move: {len(books_to_move):,}")

# Find under-represented categories to receive books
# All categories that are NOT in the targets list
all_cats = list(categories.keys())
receiver_cats = [c for c in all_cats if c not in targets]

print(f"\nReceiver categories ({len(receiver_cats)} total):")
for cat in receiver_cats:
    print(f"  {cat}: {categories[cat]:,}")

# Randomly assign each book to a receiver category
random.shuffle(books_to_move)
updates = [(bib, random.choice(receiver_cats)) for bib in books_to_move]

print(f"\nUpdating {len(updates):,} book categories...")

# Update in batches using temporary table
batch_size = 1000
total_updated = 0

for i in range(0, len(updates), batch_size):
    chunk = updates[i:i+batch_size]
    
    # Create temp table and insert
    cur.execute("DROP TABLE IF EXISTS tmp_cat_update")
    cur.execute("CREATE TEMP TABLE tmp_cat_update (bib_id INT, new_cat VARCHAR)")
    psycopg2.extras.execute_values(cur, "INSERT INTO tmp_cat_update VALUES %s", chunk)
    
    # Update
    cur.execute("""
        UPDATE book_categories bc 
        SET category = t.new_cat
        FROM tmp_cat_update t
        WHERE bc.bib_id = t.bib_id
    """)
    conn.commit()
    
    # Drop temp table
    cur.execute("DROP TABLE IF EXISTS tmp_cat_update")
    
    total_updated += len(chunk)
    if (i // batch_size + 1) % 5 == 0 or i + batch_size >= len(updates):
        print(f"  Progress: {total_updated:,} / {len(updates):,}")

print(f"\nUpdated {total_updated:,} categories")

# Show new distribution
print(f"\nNew distribution:")
cur.execute("""
    SELECT category, COUNT(*) as book_count 
    FROM book_categories 
    GROUP BY category 
    ORDER BY book_count DESC
""")
for row in cur.fetchall():
    pct = row[1] / total * 100
    print(f"  {row[0]}: {row[1]:,} ({pct:.2f}%)")

# Refresh materialized views
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

cur.close()
conn.close()
print("\nDone!")
