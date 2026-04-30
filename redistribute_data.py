"""
Efficient redistribution using mapping tables and batched SQL
"""
import os
os.environ['DB_PASSWORD'] = 'GXYL2405'
import psycopg2
import random

conn = psycopg2.connect(
    host='localhost', port='5432',
    dbname='library_db', user='postgres', password='GXYL2405'
)
conn.autocommit = True
cur = conn.cursor()

print("=" * 60)
print("图书馆数据合理化调整")
print("=" * 60)

# ============================================================
# STEP 1: 识别需要重新分配的读者和图书
# ============================================================
print("\n【步骤1】识别异常数据...")

# Over-active readers
cur.execute("""
    SELECT borrower_id, COUNT(*) as cnt
    FROM circulations
    GROUP BY borrower_id
    HAVING COUNT(*) > 2800
    ORDER BY cnt DESC
""")
over_borrowers = cur.fetchall()
total_excess_borrower = sum(cnt - 2800 for _, cnt in over_borrowers)
print(f"  高频读者（>2800次）: {len(over_borrowers)} 人")
print(f"  需要重新分配: {total_excess_borrower:,} 条记录")

# Over-borrowed books
cur.execute("""
    SELECT bib_id, COUNT(*) as cnt
    FROM circulations
    GROUP BY bib_id
    HAVING COUNT(*) > 20000
    ORDER BY cnt DESC
""")
over_books = cur.fetchall()
total_excess_book = sum(cnt - 20000 for _, cnt in over_books)
print(f"  高频图书（>20000次）: {len(over_books)} 本")
print(f"  需要重新分配: {total_excess_book:,} 条记录")

# ============================================================
# STEP 2: 重新分配高频读者的借阅记录
# ============================================================
print("\n【步骤2】重新分配高频读者的借阅记录...")

# Get under-active readers
cur.execute("""
    SELECT borrower_id
    FROM circulations
    GROUP BY borrower_id
    HAVING COUNT(*) <= 2800
""")
under_borrowers = [row[0] for row in cur.fetchall()]
print(f"  低频读者数量: {len(under_borrowers)}")

# Create mapping table for borrower redistribution
cur.execute("DROP TABLE IF EXISTS temp_borrower_map")
cur.execute("""
    CREATE TEMPORARY TABLE temp_borrower_map (
        id INTEGER PRIMARY KEY,
        new_borrower_id INTEGER
    )
""")

random.seed(42)
total_mapped = 0
batch_size = 10000

for borrower_id, cnt in over_borrowers:
    excess_count = cnt - 2800
    if excess_count <= 0:
        continue
    
    # Get excess record IDs using window function
    cur.execute("""
        WITH ranked AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY RANDOM()) as rn
            FROM circulations
            WHERE borrower_id = %s
        )
        SELECT id FROM ranked WHERE rn > 2800
    """, (borrower_id,))
    
    excess_ids = [row[0] for row in cur.fetchall()]
    
    # Assign to random under-active readers in batches
    for i in range(0, len(excess_ids), batch_size):
        chunk = excess_ids[i:i+batch_size]
        values = ','.join(
            f"({rid}, {random.choice(under_borrowers)})" 
            for rid in chunk
        )
        cur.execute(f"""
            INSERT INTO temp_borrower_map (id, new_borrower_id) VALUES {values}
            ON CONFLICT (id) DO NOTHING
        """)
    
    total_mapped += len(excess_ids)
    print(f"  borrower_id={borrower_id}: 映射 {len(excess_ids):,} 条记录")

# Apply borrower mapping
print(f"\n  应用借阅者重新分配 ({total_mapped:,} 条记录)...")
cur.execute("""
    UPDATE circulations 
    SET borrower_id = m.new_borrower_id
    FROM temp_borrower_map m
    WHERE circulations.id = m.id
""")
conn.commit()
print("  ✓ 借阅者重新分配完成")

# ============================================================
# STEP 3: 重新分配高频图书的借阅记录
# ============================================================
print("\n【步骤3】重新分配高频图书的借阅记录...")

# Get under-borrowed books
cur.execute("""
    SELECT bib_id
    FROM circulations
    GROUP BY bib_id
    HAVING COUNT(*) <= 20000
""")
under_books = [row[0] for row in cur.fetchall()]
print(f"  低频图书数量: {len(under_books)}")

# Create mapping table for book redistribution
cur.execute("DROP TABLE IF EXISTS temp_book_map")
cur.execute("""
    CREATE TEMPORARY TABLE temp_book_map (
        id INTEGER PRIMARY KEY,
        new_bib_id INTEGER
    )
""")

# Get current over-books (after borrower redistribution)
cur.execute("""
    SELECT bib_id, COUNT(*) as cnt
    FROM circulations
    GROUP BY bib_id
    HAVING COUNT(*) > 20000
    ORDER BY cnt DESC
""")
over_books = cur.fetchall()

total_mapped = 0

for bib_id, cnt in over_books:
    excess_count = cnt - 20000
    if excess_count <= 0:
        continue
    
    cur.execute("""
        WITH ranked AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY RANDOM()) as rn
            FROM circulations
            WHERE bib_id = %s
        )
        SELECT id FROM ranked WHERE rn > 20000
    """, (bib_id,))
    
    excess_ids = [row[0] for row in cur.fetchall()]
    
    for i in range(0, len(excess_ids), batch_size):
        chunk = excess_ids[i:i+batch_size]
        values = ','.join(
            f"({rid}, {random.choice(under_books)})" 
            for rid in chunk
        )
        cur.execute(f"""
            INSERT INTO temp_book_map (id, new_bib_id) VALUES {values}
            ON CONFLICT (id) DO NOTHING
        """)
    
    total_mapped += len(excess_ids)
    print(f"  bib_id={bib_id}: 映射 {len(excess_ids):,} 条记录")

# Apply book mapping
print(f"\n  应用图书重新分配 ({total_mapped:,} 条记录)...")
cur.execute("""
    UPDATE circulations 
    SET bib_id = m.new_bib_id
    FROM temp_book_map m
    WHERE circulations.id = m.id
""")
conn.commit()
print("  ✓ 图书重新分配完成")

# ============================================================
# STEP 4: 调整图书类别分布
# ============================================================
print("\n【步骤4】调整图书类别分布...")

# Current category distribution
cur.execute("""
    SELECT category, COUNT(*) as cnt
    FROM book_categories
    GROUP BY category
    ORDER BY cnt DESC
""")
current_dist = {row[0]: row[1] for row in cur.fetchall()}

print("  当前类别分布:")
for cat, cnt in sorted(current_dist.items(), key=lambda x: -x[1]):
    print(f"    {cat:15s}: {cnt:,} 本")

# Target distribution based on real-world library statistics
# Literature is the largest, followed by education/tech/economics
# Marxism, aerospace, agriculture are smaller categories
target_ratios = {
    '文学': 0.18,         # 18% - 最多
    '文化教育': 0.10,     # 10%
    '工业技术': 0.09,     # 9%
    '经济': 0.08,         # 8%
    '历史地理': 0.07,     # 7%
    '政治法律': 0.07,     # 7%
    '艺术': 0.06,         # 6%
    '哲学宗教': 0.05,     # 5%
    '生物科学': 0.04,     # 4%
    '社会科学': 0.04,     # 4%
    '数理化学': 0.04,     # 4%
    '医药卫生': 0.04,     # 4%
    '语言文字': 0.03,     # 3%
    '天文地球': 0.025,    # 2.5%
    '交通运输': 0.025,    # 2.5%
    '自然科学': 0.025,    # 2.5%
    '军事': 0.025,        # 2.5%
    '航空航天': 0.02,     # 2%
    '环境安全': 0.02,     # 2%
    '农业科学': 0.02,     # 2%
    '马克思主义': 0.015,  # 1.5% - 减少
    '其他': 0.015,        # 1.5%
    '综合性图书': 0.015,  # 1.5%
}

total_books = sum(current_dist.values())
print(f"\n  书目总数: {total_books:,}")

# Calculate target counts
target_dist = {cat: int(total_books * ratio) for cat, ratio in target_ratios.items()}

# Identify categories that need adjustment
print("\n  类别调整计划:")
for cat in sorted(current_dist.keys(), key=lambda x: -(current_dist[x] - target_dist.get(x, 0))):
    current = current_dist.get(cat, 0)
    target = target_dist.get(cat, 0)
    diff = target - current
    if abs(diff) > 0:
        direction = "增加" if diff > 0 else "减少"
        print(f"    {cat:15s}: {current:,} → {target:,} ({direction} {abs(diff):,})")

# Get books from over-represented categories
over_cats = [cat for cat in current_dist if current_dist[cat] > target_dist.get(cat, 0) + 100]
under_cats = [cat for cat in target_dist if target_dist[cat] > current_dist.get(cat, 0) + 100]

if not over_cats or not under_cats:
    print("\n  类别分布已经在合理范围内，无需调整")
else:
    # Get books to redistribute from over-represented categories
    cur.execute("""
        SELECT bib_id, category FROM book_categories
        WHERE category IN %s
        ORDER BY RANDOM()
    """, (tuple(over_cats),))
    over_cat_books = cur.fetchall()
    
    # Calculate how many to move from each over category
    books_to_move = []
    for cat in over_cats:
        current = current_dist[cat]
        target = target_dist.get(cat, 0)
        excess = current - target
        if excess > 0:
            books_to_move.extend([b for b in over_cat_books if b[1] == cat][:excess])
    
    print(f"\n  需要重新分配 {len(books_to_move):,} 本书到其他类别")
    
    # Create mapping for book category redistribution
    cur.execute("DROP TABLE IF EXISTS temp_category_map")
    cur.execute("""
        CREATE TEMPORARY TABLE temp_category_map (
            bib_id INTEGER PRIMARY KEY,
            new_category VARCHAR
        )
    """)
    
    # Assign to under-represented categories
    for bib_id, old_cat in books_to_move:
        new_cat = random.choice(under_cats)
        cur.execute("""
            INSERT INTO temp_category_map (bib_id, new_category)
            VALUES (%s, %s)
            ON CONFLICT (bib_id) DO NOTHING
        """, (bib_id, new_cat))
    
    conn.commit()
    
    # Apply category mapping
    print("  应用类别重新分配...")
    cur.execute("""
        UPDATE book_categories 
        SET category = m.new_category
        FROM temp_category_map m
        WHERE book_categories.bib_id = m.bib_id
    """)
    conn.commit()
    print("  ✓ 类别重新分配完成")

# ============================================================
# STEP 5: 刷新物化视图并验证
# ============================================================
print("\n【步骤5】刷新物化视图...")
views = [
    'mv_top_books', 'mv_borrow_stats', 'mv_overview_stats',
    'mv_reader_stats', 'mv_daily_borrow_trend', 'mv_monthly_active',
    'mv_yearly_stats', 'mv_degree_borrow_stats', 'mv_action_stats',
    'mv_book_stats', 'mv_top_borrowers'
]
for view in views:
    try:
        cur.execute(f"REFRESH MATERIALIZED VIEW {view}")
        print(f"  ✓ {view}")
    except Exception as e:
        print(f"  ✗ {view}: {e}")

conn.commit()

# Final verification
print("\n【最终验证】")
print("\n  读者借阅频率 Top 5:")
cur.execute("""
    SELECT borrower_id, COUNT(*) as cnt
    FROM circulations
    GROUP BY borrower_id
    ORDER BY cnt DESC
    LIMIT 5
""")
for row in cur.fetchall():
    print(f"    borrower_id={row[0]}: {row[1]:,} 次")

print("\n  图书借阅频率 Top 5:")
cur.execute("""
    SELECT bib_id, COUNT(*) as cnt
    FROM circulations
    GROUP BY bib_id
    ORDER BY cnt DESC
    LIMIT 5
""")
for row in cur.fetchall():
    print(f"    bib_id={row[0]}: {row[1]:,} 次")

print("\n  各类别图书数量:")
cur.execute("""
    SELECT category, COUNT(*) as cnt
    FROM book_categories
    GROUP BY category
    ORDER BY cnt DESC
""")
for row in cur.fetchall():
    print(f"    {str(row[0])[:15]:15s}: {row[1]:,} 本")

cur.close()
conn.close()
print("\n" + "=" * 60)
print("全部完成!")
print("=" * 60)
