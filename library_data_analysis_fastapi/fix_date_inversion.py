import psycopg
from datetime import datetime

conn = psycopg.connect('host=localhost port=5432 dbname=library_db user=postgres password=GXYL2405')
conn.autocommit = True
cur = conn.cursor()

print("=" * 70)
print("步骤2：修复日期颠倒的记录")
print("=" * 70)

# 统计需要修复的记录数
cur.execute("""
    SELECT COUNT(*) FROM circulations 
    WHERE status = 'returned' AND return_date < borrow_date
""")
count_before = cur.fetchone()[0]
print(f"\n需要修复的记录数: {count_before:,}")

# 显示一些样本
print("\n样本数据（修复前）:")
cur.execute("""
    SELECT id, borrower_id, bib_id, borrow_date, return_date, status
    FROM circulations 
    WHERE status = 'returned' AND return_date < borrow_date
    LIMIT 5
""")
for row in cur.fetchall():
    print(f"  ID={row[0]}, borrower={row[1]}, bib={row[2]}, borrow={row[3]}, return={row[4]}, status={row[5]}")

# 执行修复：交换 borrow_date 和 return_date
print("\n开始修复...")
cur.execute("""
    UPDATE circulations 
    SET borrow_date = return_date, 
        return_date = borrow_date
    WHERE status = 'returned' AND return_date < borrow_date
""")
print(f"✅ 已修复 {cur.rowcount:,} 条记录")

# 验证修复结果
cur.execute("""
    SELECT COUNT(*) FROM circulations 
    WHERE status = 'returned' AND return_date < borrow_date
""")
count_after = cur.fetchone()[0]
print(f"\n修复后仍存在的颠倒记录: {count_after:,}")

# 显示修复后的样本
print("\n样本数据（修复后）:")
cur.execute("""
    SELECT id, borrower_id, bib_id, borrow_date, return_date, status
    FROM circulations 
    WHERE status = 'returned' AND return_date >= borrow_date
    ORDER BY return_date - borrow_date DESC
    LIMIT 5
""")
for row in cur.fetchall():
    print(f"  ID={row[0]}, borrower={row[1]}, bib={row[2]}, borrow={row[3]}, return={row[4]}, status={row[5]}")

conn.close()
print("\n✅ 步骤2完成")
