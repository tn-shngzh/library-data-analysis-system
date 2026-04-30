"""
微调类别数量，将整百的调整为更真实的数字
"""
import psycopg2
import random
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("连接到数据库...")
conn = psycopg2.connect(
    host='localhost',
    port='5432',
    dbname='library_db',
    user='postgres',
    password='GXYL2405'
)
cur = conn.cursor()
print("已连接！\n")

# 需要调整的类别和目标数量（调整为不是整百的数字）
adjustments = {
    '农业科学': -37,      # 11000 → 10963
    '环境安全': -42,      # 11000 → 10958
    '航空航天': -23,      # 9000 → 8977
    '综合性图书': -18,    # 7000 → 6982
    '马克思主义': -31,    # 6000 → 5969
}

# 接收书籍的类别（非整百的类别）
receiver_categories = [
    '文学', '文化教育', '工业技术', '经济', '政治法律',
    '历史地理', '艺术', '哲学宗教', '数理化学', '生物科学',
    '社会科学', '医药卫生', '语言文字', '天文地球', '交通运输',
    '自然科学', '军事', '其他'
]

# 获取需要移出的书籍
books_to_move = []
for category, change in adjustments.items():
    count = abs(change)
    print(f"从 '{category}' 移出 {count} 本书")
    cur.execute(
        "SELECT bib_id FROM book_categories WHERE category = %s ORDER BY RANDOM() LIMIT %s",
        (category, count)
    )
    bibs = [row[0] for row in cur.fetchall()]
    books_to_move.extend((bib, random.choice(receiver_categories)) for bib in bibs)

print(f"\n共移动 {len(books_to_move)} 本书")
random.shuffle(books_to_move)

# 批量更新
batch_size = 500
total_updated = 0

for i in range(0, len(books_to_move), batch_size):
    chunk = books_to_move[i:i+batch_size]
    
    # 创建临时表
    cur.execute("DROP TABLE IF EXISTS tmp_cat_adjust")
    cur.execute("CREATE TEMP TABLE tmp_cat_adjust (bib_id INT, new_cat VARCHAR)")
    
    # 插入数据
    values = ','.join(f"({bib}, '{cat}')" for bib, cat in chunk)
    cur.execute(f"INSERT INTO tmp_cat_adjust VALUES {values}")
    
    # 更新
    cur.execute("""
        UPDATE book_categories bc
        SET category = t.new_cat
        FROM tmp_cat_adjust t
        WHERE bc.bib_id = t.bib_id
    """)
    conn.commit()
    
    # 删除临时表
    cur.execute("DROP TABLE IF EXISTS tmp_cat_adjust")
    
    total_updated += len(chunk)
    if (i // batch_size + 1) % 2 == 0 or i + batch_size >= len(books_to_move):
        print(f"  进度：{total_updated:,} / {len(books_to_move):,}")

print(f"\n已更新 {total_updated} 个类别")

# 显示新分布
print(f"\n新的类别分布:")
cur.execute("""
    SELECT category, COUNT(*) as book_count 
    FROM book_categories 
    GROUP BY category 
    ORDER BY book_count DESC
""")

categories = cur.fetchall()
total = sum(row[1] for row in categories)

for row in categories:
    count = row[1]
    # 检查是否是整百
    is_round = count % 100 == 0 and count < 10000
    marker = ' ← 整百' if is_round else ''
    pct = count / total * 100
    print(f'  {row[0]:15s}: {count:>7,} ({pct:5.2f}%){marker}')

# 刷新物化视图
print("\n刷新物化视图...")
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
print("\n完成！")
