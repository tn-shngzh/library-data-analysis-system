"""
Fix category distribution only
"""
import os
import sys
os.environ['DB_PASSWORD'] = 'GXYL2405'
sys.stdout.reconfigure(encoding='utf-8')

print("Connecting to database...")
import psycopg2
import random

conn = psycopg2.connect(
    host='localhost', port='5432',
    dbname='library_db', user='postgres', password='GXYL2405'
)
cur = conn.cursor()
print("Connected!")

cur.execute("SELECT category, COUNT(*) FROM book_categories GROUP BY category ORDER BY COUNT(*) DESC")
cats = {r[0]: r[1] for r in cur.fetchall()}
total = sum(cats.values())

print(f"\nTotal books: {total:,}")
print("\nCurrent distribution:")
for cat, cnt in sorted(cats.items(), key=lambda x: -x[1]):
    print(f"  {cat:15s}: {cnt:>6,} ({cnt/total*100:5.1f}%)")

# Target: Marxism ~6000, Comprehensive ~7000, Aerospace ~9000, Agriculture ~11000, Environment ~11000
targets = {
    '马克思主义': 6000,
    '综合性图书': 7000,
    '航空航天': 9000,
    '农业科学': 11000,
    '环境安全': 11000,
}

# Find categories that need to give books away
over_cats = []
under_cats = []

for cat, target in targets.items():
    current = cats.get(cat, 0)
    if current > target:
        over_cats.append((cat, current - target))
    elif current < target:
        under_cats.append((cat, target - current))

print("\nAdjustment needed:")
for cat, excess in over_cats:
    print(f"  {cat}: reduce by {excess:,}")
for cat, deficit in under_cats:
    print(f"  {cat}: add {deficit:,}")

if not over_cats or not under_cats:
    print("\nCategories are already balanced!")
    cur.close()
    conn.close()
    exit()

# Get books to move from over-represented categories
books_to_move = []
for cat, excess in over_cats:
    cur.execute("SELECT bib_id FROM book_categories WHERE category=%s ORDER BY RANDOM() LIMIT %s", (cat, excess))
    bibs = [row[0] for row in cur.fetchall()]
    books_to_move.extend([(bib, cat) for bib in bibs])

print(f"\nTotal books to move: {len(books_to_move):,}")

# Create target category list
total_deficit = sum(d for _, d in under_cats)
target_list = []
for cat, deficit in under_cats:
    count = max(1, len(books_to_move) * deficit // total_deficit)
    target_list.extend([cat] * count)

random.shuffle(target_list)
while len(target_list) < len(books_to_move):
    target_list.append(random.choice([c for c, _ in under_cats]))

# Update in batches
print("\nUpdating categories...")
batch_size = 500
total_updated = 0

for i in range(0, len(books_to_move), batch_size):
    chunk = books_to_move[i:i+batch_size]
    
    # Build the VALUES clause
    values = []
    for j, (bib, old_cat) in enumerate(chunk):
        new_cat = target_list[(i + j) % len(target_list)]
        values.append((bib, new_cat))
    
    # Use parameterized query with execute_values
    import psycopg2.extras
    cur.execute("DROP TABLE IF EXISTS tmp_cat")
    cur.execute("CREATE TEMP TABLE tmp_cat (bib_id INT, new_cat VARCHAR)")
    psycopg2.extras.execute_values(cur, "INSERT INTO tmp_cat VALUES %s", values)
    
    cur.execute("""
        UPDATE book_categories bc SET category = t.new_cat
        FROM tmp_cat t
        WHERE bc.bib_id = t.bib_id
    """)
    conn.commit()
    cur.execute("DROP TABLE IF EXISTS tmp_cat")
    
    total_updated += len(chunk)
    if (i // batch_size + 1) % 5 == 0 or i + batch_size >= len(books_to_move):
        print(f"  Progress: {total_updated:,} / {len(books_to_move):,}")

print(f"\n  Updated {total_updated:,} categories")

# Verify
print("\nNew distribution:")
cur.execute("SELECT category, COUNT(*) FROM book_categories GROUP BY category ORDER BY COUNT(*) DESC")
for r in cur.fetchall():
    print(f"  {r[0]:15s}: {r[1]:>6,}")

# Refresh views
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
