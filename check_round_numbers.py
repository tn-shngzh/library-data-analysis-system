import psycopg2
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = psycopg2.connect(
    host='localhost',
    port='5432',
    dbname='library_db',
    user='postgres',
    password='GXYL2405'
)
cur = conn.cursor()

# 检查各类别书籍数量
cur.execute("""
    SELECT category, COUNT(*) as book_count 
    FROM book_categories 
    GROUP BY category 
    ORDER BY book_count DESC
""")

categories = cur.fetchall()
total = sum(row[1] for row in categories)

print(f'\n当前类别分布 (总计：{total:,} 本书):')
print('='*60)
for row in categories:
    count = row[1]
    # 检查是否是整百、整千
    is_round = count % 1000 == 0 or (count % 100 == 0 and count < 10000)
    marker = ' ← 整百/整千' if is_round else ''
    pct = count / total * 100
    print(f'  {row[0]:15s}: {count:>7,} ({pct:5.2f}%){marker}')

print('='*60)

conn.close()
