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

# Check book_categories
print("\n【1】图书类别分布")
cur.execute("""
    SELECT c.name, COUNT(at.id) as book_count
    FROM book_categories c
    LEFT JOIN action_types at ON at.category_id = c.id
    GROUP BY c.id, c.name
    ORDER BY book_count DESC
""")
for row in cur.fetchall():
    print(f"  {row[0]:15s}: {row[1]} 本")

# Total records
print("\n【2】基本统计")
cur.execute("SELECT COUNT(*) FROM action_types")
print(f"  书目总数 (action_types): {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM circulations")
print(f"  流通记录总数: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM borrowers")
print(f"  借阅者总数 (borrowers): {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM users")
print(f"  系统用户数: {cur.fetchone()[0]}")

# Book borrow frequency (top 10)
print("\n【3】被借阅次数最多的书目 (Top 10)")
cur.execute("""
    SELECT at.name, at.category_id, COUNT(c.id) as borrow_count
    FROM action_types at
    LEFT JOIN circulations c ON c.bib_id = at.bib_id
    GROUP BY at.id, at.name, at.category_id
    ORDER BY borrow_count DESC
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"  {str(row[0])[:35]:35s} - 借阅 {row[2]} 次")

# Books with zero borrows
print("\n【4】未被借阅的书目")
cur.execute("""
    SELECT COUNT(*) FROM action_types at
    WHERE NOT EXISTS (SELECT 1 FROM circulations c WHERE c.bib_id = at.bib_id)
""")
print(f"  未被借阅: {cur.fetchone()[0]} 本")

# Borrower borrow frequency (top 10)
print("\n【5】借阅者频率 (Top 10)")
cur.execute("""
    SELECT br.id, COUNT(c.id) as borrow_count
    FROM borrowers br
    LEFT JOIN circulations c ON c.borrower_id = br.id
    GROUP BY br.id
    ORDER BY borrow_count DESC
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"  borrower_id={row[0]} - 借阅 {row[1]} 次")

# Circulation date distribution
print("\n【6】流通记录时间分布 (最近12个月)")
cur.execute("""
    SELECT 
        EXTRACT(YEAR FROM transaction_date) as year,
        EXTRACT(MONTH FROM transaction_date) as month,
        COUNT(*) as count
    FROM circulations
    GROUP BY year, month
    ORDER BY year DESC, month DESC
    LIMIT 12
""")
for row in cur.fetchall():
    print(f"  {int(row[0])}-{int(row[1]):02d}: {row[2]} 条")

# Category popularity
print("\n【7】类别受欢迎程度 (总借阅次数)")
cur.execute("""
    SELECT c.name, COUNT(circ.id) as total_borrows
    FROM book_categories c
    LEFT JOIN action_types at ON at.category_id = c.id
    LEFT JOIN circulations circ ON circ.bib_id = at.bib_id
    GROUP BY c.id, c.name
    ORDER BY total_borrows DESC
""")
for row in cur.fetchall():
    print(f"  {row[0]:15s}: {row[1]} 次借阅")

# Sample data from action_types
print("\n【8】action_types 表结构示例")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'action_types'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"  {row[0]:20s} {row[1]}")

# Sample rows
print("\n【9】action_types 示例数据 (3条)")
cur.execute("SELECT bib_id, name, category_id FROM action_types LIMIT 3")
for row in cur.fetchall():
    print(f"  bib_id={row[0]}, name={row[1]}, category_id={row[2]}")

# Sample circulations
print("\n【10】circulations 表结构示例")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'circulations'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"  {row[0]:20s} {row[1]}")

cur.close()
conn.close()
print("\n" + "=" * 60)
print("分析完成!")
