import os
os.environ['DB_PASSWORD'] = 'GXYL2405'
import psycopg2

conn = psycopg2.connect(
    host='localhost', port='5432', 
    dbname='library_db', user='postgres', password='GXYL2405'
)
cur = conn.cursor()

# 1. 统计借阅2800次以上的读者
print("【1】借阅2800次以上的读者（平均每天2次以上）")
cur.execute("""
    SELECT borrower_id, COUNT(*) as cnt
    FROM circulations
    GROUP BY borrower_id
    HAVING COUNT(*) > 2800
    ORDER BY cnt DESC
""")
over_borrowers = cur.fetchall()
total_records_from_over = 0
for row in over_borrowers:
    print(f"  borrower_id={row[0]}: {row[1]} 次")
    total_records_from_over += row[1]
print(f"  共 {len(over_borrowers)} 人，总借阅记录 {total_records_from_over} 条")

# 2. 统计借阅20000次以上的图书
print("\n【2】被借阅20000次以上的图书")
cur.execute("""
    SELECT bib_id, COUNT(*) as cnt
    FROM circulations
    GROUP BY bib_id
    HAVING COUNT(*) > 20000
    ORDER BY cnt DESC
""")
over_books = cur.fetchall()
total_records_from_over_books = 0
for row in over_books:
    print(f"  bib_id={row[0]}: {row[1]} 次")
    total_records_from_over_books += row[1]
print(f"  共 {len(over_books)} 本，总借阅记录 {total_records_from_over_books} 条")

# 3. 统计借阅2800次以下的读者（接收方）
print("\n【3】借阅2800次以下的读者（接收方）")
cur.execute("""
    SELECT borrower_id, COUNT(*) as cnt
    FROM circulations
    GROUP BY borrower_id
    HAVING COUNT(*) <= 2800
    ORDER BY cnt ASC
""")
under_borrowers = cur.fetchall()
print(f"  共 {len(under_borrowers)} 人")
if under_borrowers:
    print(f"  最少借阅: {under_borrowers[0][1]} 次")
    print(f"  最多借阅: {under_borrowers[-1][1]} 次")

# 4. 统计借阅20000次以下的图书（接收方）
print("\n【4】被借阅20000次以下的图书（接收方）")
cur.execute("""
    SELECT bib_id, COUNT(*) as cnt
    FROM circulations
    GROUP BY bib_id
    HAVING COUNT(*) <= 20000
    ORDER BY cnt ASC
""")
under_books = cur.fetchall()
print(f"  共 {len(under_books)} 本")
if under_books:
    print(f"  最少借阅: {under_books[0][1]} 次")
    print(f"  最多借阅: {under_books[-1][1]} 次")

# 5. 各类别图书数量
print("\n【5】各类别图书数量")
cur.execute("""
    SELECT category, COUNT(*) as cnt
    FROM book_categories
    GROUP BY category
    ORDER BY cnt DESC
""")
for row in cur.fetchall():
    print(f"  {str(row[0])[:15]:15s}: {row[1]} 本")

# 6. 总流通记录数
cur.execute("SELECT COUNT(*) FROM circulations")
total = cur.fetchone()[0]
print(f"\n【6】总流通记录数: {total:,}")

cur.close()
conn.close()
