import psycopg2
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("="*70)
print("图书馆数据合理化调整 - 最终验证报告")
print("="*70)

conn = psycopg2.connect(
    host='localhost',
    port='5432',
    dbname='library_db',
    user='postgres',
    password='GXYL2405'
)
cur = conn.cursor()

# 1. 读者借阅量验证
print("\n【1】读者借阅量验证")
cur.execute("""
    SELECT borrower_id, COUNT(*) as cnt 
    FROM circulations 
    GROUP BY borrower_id 
    HAVING COUNT(*) > 2800
""")
over_readers = cur.fetchall()
print(f"  借阅次数 > 2800 的读者数量: {len(over_readers)}")
if over_readers:
    for r in over_readers[:5]:
        print(f"    读者 {r[0]}: {r[1]} 次")

cur.execute("""
    SELECT MAX(cnt) FROM (
        SELECT COUNT(*) as cnt FROM circulations GROUP BY borrower_id
    ) t
""")
print(f"  读者最高借阅次数: {cur.fetchone()[0]}")

# 2. 图书借阅量验证
print("\n【2】图书借阅量验证")
cur.execute("""
    SELECT bib_id, COUNT(*) as cnt 
    FROM circulations 
    GROUP BY bib_id 
    HAVING COUNT(*) > 20000
""")
over_books = cur.fetchall()
print(f"  借阅次数 > 20000 的图书数量: {len(over_books)}")
if over_books:
    for r in over_books[:5]:
        print(f"    图书 {r[0]}: {r[1]} 次")

cur.execute("""
    SELECT MAX(cnt) FROM (
        SELECT COUNT(*) as cnt FROM circulations GROUP BY bib_id
    ) t
""")
print(f"  图书最高借阅次数: {cur.fetchone()[0]}")

# 3. 类别分布验证
print("\n【3】图书类别分布验证")
cur.execute("""
    SELECT category, COUNT(*) as book_count 
    FROM book_categories 
    GROUP BY category 
    ORDER BY book_count DESC
""")
categories = cur.fetchall()
total = sum(row[1] for row in categories)
print(f"  图书总数: {total:,}")
print(f"  {'类别':<15s} {'数量':>8s} {'占比':>8s}")
print(f"  {'-'*35}")
for row in categories:
    pct = row[1] / total * 100
    print(f"  {row[0]:<15s} {row[1]:>8,} {pct:>7.2f}%")

# 4. 数据完整性验证
print("\n【4】数据完整性验证")
cur.execute('SELECT COUNT(*) FROM circulations')
print(f"  借阅记录总数: {cur.fetchone()[0]:,}")

cur.execute('SELECT COUNT(*) FROM (SELECT DISTINCT borrower_id FROM circulations) t')
print(f"  活跃读者数: {cur.fetchone()[0]:,}")

cur.execute('SELECT COUNT(*) FROM (SELECT DISTINCT bib_id FROM circulations) t')
print(f"  被借阅图书数: {cur.fetchone()[0]:,}")

conn.close()

print("\n" + "="*70)
print("验证完成！")
print("="*70)
