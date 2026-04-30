"""
Efficient redistribution using SQL CTEs and batched updates
"""
import os
os.environ['DB_PASSWORD'] = 'GXYL2405'
import psycopg2
import random

conn = psycopg2.connect(
    host='localhost', port='5432',
    dbname='library_db', user='postgres', password='GXYL2405'
)
conn.autocommit = True  # For faster bulk updates
cur = conn.cursor()

print("=" * 60)
print("重新分配高频读者和图书的借阅记录")
print("=" * 60)

# ============================================================
# STEP 1: Identify over-active readers and their excess records
# ============================================================
print("\n【步骤1】识别高频读者（>2800次借阅）")

cur.execute("""
    SELECT borrower_id, COUNT(*) as cnt
    FROM circulations
    GROUP BY borrower_id
    HAVING COUNT(*) > 2800
    ORDER BY cnt DESC
""")
over_borrowers = cur.fetchall()
print(f"  找到 {len(over_borrowers)} 个高频读者")
total_excess_borrower = sum(cnt - 2800 for _, cnt in over_borrowers)
print(f"  需要重新分配 {total_excess_borrower:,} 条记录")

# ============================================================
# STEP 2: Identify over-borrowed books and their excess records
# ============================================================
print("\n【步骤2】识别高频图书（>20000次借阅）")

cur.execute("""
    SELECT bib_id, COUNT(*) as cnt
    FROM circulations
    GROUP BY bib_id
    HAVING COUNT(*) > 20000
    ORDER BY cnt DESC
""")
over_books = cur.fetchall()
print(f"  找到 {len(over_books)} 本高频图书")
total_excess_book = sum(cnt - 20000 for _, cnt in over_books)
print(f"  需要重新分配 {total_excess_book:,} 条记录")

# ============================================================
# STEP 3: Redistribute borrower_id for over-active readers
# ============================================================
print("\n【步骤3】重新分配高频读者的借阅记录...")

# Get under-active readers
cur.execute("""
    SELECT borrower_id
    FROM circulations
    GROUP BY borrower_id
    HAVING COUNT(*) <= 2800
""")
under_borrowers = [row[0] for row in cur.fetchall()]
random.shuffle(under_borrowers)
print(f"  找到 {len(under_borrowers)} 个低频读者作为接收方")

# For each over-borrower, mark excess records and reassign
# We'll use a temporary table to track which records to update
cur.execute("DROP TABLE IF EXISTS temp_redistribute")
cur.execute("""
    CREATE TEMPORARY TABLE temp_redistribute (
        id INTEGER,
        new_borrower_id INTEGER,
        new_bib_id INTEGER
    )
""")

# Process over-borrowers
for borrower_id, cnt in over_borrowers:
    excess_count = cnt - 2800
    if excess_count <= 0:
        continue
    
    print(f"\n  处理 borrower_id={borrower_id}: 需要重新分配 {excess_count:,} 条记录")
    
    # Select random excess records (not the first 2800)
    cur.execute("""
        WITH ranked AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY RANDOM()) as rn
            FROM circulations
            WHERE borrower_id = %s
        )
        SELECT id FROM ranked
        WHERE rn > 2800
    """, (borrower_id,))
    excess_record_ids = [row[0] for row in cur.fetchall()]
    
    # Assign to random under-active readers
    # Use chunks for efficiency
    chunk_size = 10000
    for i in range(0, len(excess_record_ids), chunk_size):
        chunk = excess_record_ids[i:i+chunk_size]
        # Assign each record to a random under-active reader
        values = []
        for rid in chunk:
            new_bid = random.choice(under_borrowers)
            values.append(f"({rid}, {new_bid})")
        
        cur.execute("""
            UPDATE circulations SET borrower_id = v.new_borrower_id
            FROM (VALUES %s) AS v(id, new_borrower_id)
            WHERE circulations.id = v.id
        """ % ','.join(values))

conn.commit()
print("\n  高频读者记录重新分配完成!")

# ============================================================
# STEP 4: Redistribute bib_id for over-borrowed books
# ============================================================
print("\n【步骤4】重新分配高频图书的借阅记录...")

# Get under-borrowed books (those with <= 20000 borrows)
cur.execute("""
    SELECT bib_id
    FROM circulations
    GROUP BY bib_id
    HAVING COUNT(*) <= 20000
""")
under_books = [row[0] for row in cur.fetchall()]
random.shuffle(under_books)
print(f"  找到 {len(under_books)} 本低频图书作为接收方")

# Process over-books
cur.execute("""
    SELECT bib_id, COUNT(*) as cnt
    FROM circulations
    GROUP BY bib_id
    HAVING COUNT(*) > 20000
    ORDER BY cnt DESC
""")
over_books = cur.fetchall()

for bib_id, cnt in over_books:
    excess_count = cnt - 20000
    if excess_count <= 0:
        continue
    
    print(f"\n  处理 bib_id={bib_id}: 需要重新分配 {excess_count:,} 条记录")
    
    # Select random excess records
    cur.execute("""
        WITH ranked AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY RANDOM()) as rn
            FROM circulations
            WHERE bib_id = %s
        )
        SELECT id FROM ranked
        WHERE rn > 20000
    """, (bib_id,))
    excess_record_ids = [row[0] for row in cur.fetchall()]
    
    # Assign to random under-borrowed books
    chunk_size = 10000
    for i in range(0, len(excess_record_ids), chunk_size):
        chunk = excess_record_ids[i:i+chunk_size]
        values = []
        for rid in chunk:
            new_bib = random.choice(under_books)
            values.append(f"({rid}, {new_bib})")
        
        cur.execute("""
            UPDATE circulations SET bib_id = v.new_bib_id
            FROM (VALUES %s) AS v(id, new_bib_id)
            WHERE circulations.id = v.id
        """ % ','.join(values))

conn.commit()
print("\n  高频图书记录重新分配完成!")

# ============================================================
# STEP 5: Verify results
# ============================================================
print("\n【步骤5】验证结果...")

print("\n  读者借阅频率分布（前10）:")
cur.execute("""
    SELECT borrower_id, COUNT(*) as cnt
    FROM circulations
    GROUP BY borrower_id
    ORDER BY cnt DESC
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"    borrower_id={row[0]}: {row[1]:,} 次")

cur.execute("""
    SELECT COUNT(*) FROM (
        SELECT borrower_id FROM circulations
        GROUP BY borrower_id HAVING COUNT(*) > 2800
    ) sub
""")
over_count = cur.fetchone()[0]
print(f"  超过2800次的读者数: {over_count}")

print("\n  图书借阅频率分布（前10）:")
cur.execute("""
    SELECT bib_id, COUNT(*) as cnt
    FROM circulations
    GROUP BY bib_id
    ORDER BY cnt DESC
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"    bib_id={row[0]}: {row[1]:,} 次")

cur.execute("""
    SELECT COUNT(*) FROM (
        SELECT bib_id FROM circulations
        GROUP BY bib_id HAVING COUNT(*) > 20000
    ) sub
""")
over_count = cur.fetchone()[0]
print(f"  超过20000次的图书数: {over_count}")

cur.close()
conn.close()
print("\n" + "=" * 60)
print("重新分配完成!")
print("=" * 60)
