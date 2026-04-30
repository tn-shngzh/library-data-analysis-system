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

# Book categories distribution
print("【1】图书类别分布 (book_categories)")
cur.execute("SELECT COUNT(*) FROM book_categories")
print(f"  总书目数: {cur.fetchone()[0]}")

cur.execute("""
    SELECT category, COUNT(*) as cnt
    FROM book_categories
    GROUP BY category
    ORDER BY cnt DESC
""")
for row in cur.fetchall():
    print(f"  {str(row[0])[:15]:15s}: {row[1]} 本")

# Circulations stats
print("\n【2】流通记录统计")
cur.execute("SELECT COUNT(*) FROM circulations")
print(f"  总记录数: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(DISTINCT bib_id) FROM circulations")
print(f"  被借阅的书目数: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(DISTINCT borrower_id) FROM circulations")
print(f"  有借阅记录的借阅者数: {cur.fetchone()[0]}")

# Top borrowers
print("\n【3】Top 10 最活跃借阅者")
cur.execute("""
    SELECT borrower_id, COUNT(*) as cnt
    FROM circulations
    GROUP BY borrower_id
    ORDER BY cnt DESC
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"  borrower_id={row[0]}: {row[1]} 次借阅")

# Borrow frequency distribution
print("\n【4】借阅频率分布 - 借阅者")
cur.execute("""
    SELECT 
        CASE 
            WHEN borrow_count <= 5 THEN '1-5次'
            WHEN borrow_count <= 20 THEN '6-20次'
            WHEN borrow_count <= 50 THEN '21-50次'
            WHEN borrow_count <= 100 THEN '51-100次'
            WHEN borrow_count <= 500 THEN '101-500次'
            ELSE '500次以上'
        END as range,
        COUNT(*) as num_borrowers
    FROM (
        SELECT borrower_id, COUNT(*) as borrow_count
        FROM circulations
        GROUP BY borrower_id
    ) sub
    GROUP BY range
    ORDER BY range
""")
for row in cur.fetchall():
    print(f"  {row[0]:12s}: {row[1]} 人")

# Book borrow frequency distribution
print("\n【5】借阅频率分布 - 书目")
cur.execute("""
    SELECT 
        CASE 
            WHEN borrow_count <= 3 THEN '1-3次'
            WHEN borrow_count <= 10 THEN '4-10次'
            WHEN borrow_count <= 50 THEN '11-50次'
            WHEN borrow_count <= 200 THEN '51-200次'
            WHEN borrow_count <= 1000 THEN '201-1000次'
            WHEN borrow_count <= 5000 THEN '1001-5000次'
            ELSE '5000次以上'
        END as range,
        COUNT(*) as num_books
    FROM (
        SELECT bib_id, COUNT(*) as borrow_count
        FROM circulations
        GROUP BY bib_id
    ) sub
    GROUP BY range
    ORDER BY range
""")
for row in cur.fetchall():
    print(f"  {row[0]:15s}: {row[1]} 本")

# Category borrow frequency
print("\n【6】类别借阅热度")
cur.execute("""
    SELECT bc.category, COUNT(c.id) as borrow_count, COUNT(DISTINCT c.bib_id) as unique_books
    FROM circulations c
    JOIN book_categories bc ON c.bib_id = bc.bib_id
    GROUP BY bc.category
    ORDER BY borrow_count DESC
""")
for row in cur.fetchall():
    print(f"  {str(row[0])[:15]:15s}: {row[1]:8d} 次借阅, {row[2]:6d} 本")

# Date range
print("\n【7】数据时间范围")
cur.execute("SELECT MIN(action_date), MAX(action_date) FROM circulations")
row = cur.fetchone()
print(f"  最早: {row[0]}, 最晚: {row[1]}")

# Action types
print("\n【8】流通操作类型")
cur.execute("SELECT action, COUNT(*) FROM circulations GROUP BY action")
for row in cur.fetchall():
    print(f"  {row[0]:10s}: {row[1]} 次")

# Check borrowers with degree info
print("\n【9】借阅者学历分布")
cur.execute("""
    SELECT degree, COUNT(*) as cnt
    FROM borrowers
    WHERE degree IS NOT NULL AND degree != ''
    GROUP BY degree
    ORDER BY cnt DESC
""")
for row in cur.fetchall():
    print(f"  {str(row[0])[:20]:20s}: {row[1]} 人")

# Borrowers without degree
cur.execute("""
    SELECT COUNT(*) FROM borrowers WHERE degree IS NULL OR degree = ''
""")
print(f"  无学历信息: {cur.fetchone()[0]} 人")

# Total borrowers
cur.execute("SELECT COUNT(*) FROM borrowers")
print(f"  总借阅者数: {cur.fetchone()[0]}")

cur.close()
conn.close()
print("\n分析完成!")
