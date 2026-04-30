import os
os.environ['DB_PASSWORD'] = 'GXYL2405'
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port='5432',
    dbname='library_db',
    user='postgres',
    password='GXYL2405'
)
cur = conn.cursor()

print("=" * 60)
print("数据库数据分析")
print("=" * 60)

# 1. Book categories distribution
print("\n【1】图书类别分布")
cur.execute("""
    SELECT c.name, COUNT(b.id) as book_count
    FROM book_categories c
    LEFT JOIN books b ON b.category_id = c.id
    GROUP BY c.id, c.name
    ORDER BY book_count DESC
""")
for row in cur.fetchall():
    print(f"  {row[0]:15s}: {row[1]} 本")

# 2. Total books and circulations
print("\n【2】基本统计")
cur.execute("SELECT COUNT(*) FROM books")
print(f"  图书总数: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM circulations")
print(f"  借阅记录总数: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM users")
print(f"  用户总数: {cur.fetchone()[0]}")

# 3. Book borrow frequency (top 10)
print("\n【3】被借阅次数最多的图书 (Top 10)")
cur.execute("""
    SELECT b.name, b.category_id, COUNT(c.id) as borrow_count
    FROM books b
    LEFT JOIN circulations c ON c.bib_id = b.bib_id
    GROUP BY b.id, b.name, b.category_id
    ORDER BY borrow_count DESC
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"  {row[0][:30]:30s} - 借阅 {row[2]} 次")

# 4. Books with zero borrows
print("\n【4】未被借阅的图书")
cur.execute("""
    SELECT COUNT(*) FROM books b
    WHERE NOT EXISTS (SELECT 1 FROM circulations c WHERE c.bib_id = b.bib_id)
""")
print(f"  未被借阅: {cur.fetchone()[0]} 本")

# 5. User borrow frequency
print("\n【5】用户借阅频率 (Top 10)")
cur.execute("""
    SELECT u.username, COUNT(c.id) as borrow_count
    FROM users u
    LEFT JOIN circulations c ON c.borrower_id = u.id
    GROUP BY u.id, u.username
    ORDER BY borrow_count DESC
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"  {row[0]:15s} - 借阅 {row[1]} 次")

# 6. Users with zero borrows
print("\n【6】无借阅记录的用户")
cur.execute("""
    SELECT COUNT(*) FROM users u
    WHERE NOT EXISTS (SELECT 1 FROM circulations c WHERE c.borrower_id = u.id)
""")
print(f"  无借阅记录: {cur.fetchone()[0]} 人")

# 7. Circulation date distribution
print("\n【7】借阅记录时间分布")
cur.execute("""
    SELECT 
        EXTRACT(YEAR FROM transaction_date) as year,
        EXTRACT(MONTH FROM transaction_date) as month,
        COUNT(*) as count
    FROM circulations
    GROUP BY year, month
    ORDER BY year, month
    LIMIT 12
""")
for row in cur.fetchall():
    print(f"  {int(row[0])}-{int(row[1]):02d}: {row[2]} 条")

# 8. Category popularity (by total borrows)
print("\n【8】类别受欢迎程度 (总借阅次数)")
cur.execute("""
    SELECT c.name, COUNT(circ.id) as total_borrows
    FROM book_categories c
    LEFT JOIN books b ON b.category_id = c.id
    LEFT JOIN circulations circ ON circ.bib_id = b.bib_id
    GROUP BY c.id, c.name
    ORDER BY total_borrows DESC
""")
for row in cur.fetchall():
    print(f"  {row[0]:15s}: {row[1]} 次借阅")

cur.close()
conn.close()
print("\n" + "=" * 60)
print("分析完成!")
