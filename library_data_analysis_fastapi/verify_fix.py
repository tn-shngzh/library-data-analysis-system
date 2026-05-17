import psycopg

conn = psycopg.connect('host=localhost port=5432 dbname=library_db user=postgres password=GXYL2405')
cur = conn.cursor()

print("=" * 70)
print("步骤3：验证修复结果")
print("=" * 70)

# 1. 总记录数
cur.execute("SELECT COUNT(*) FROM circulations")
total = cur.fetchone()[0]
print(f"\n总记录数: {total:,}")

# 2. 按状态统计
cur.execute("""
    SELECT status, COUNT(*) 
    FROM circulations 
    GROUP BY status
""")
print("\n--- 按状态统计 ---")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]:,}")

# 3. 日期颠倒检查
cur.execute("""
    SELECT COUNT(*) FROM circulations 
    WHERE status = 'returned' AND return_date < borrow_date
""")
print(f"\n日期颠倒的记录: {cur.fetchone()[0]:,}")

# 4. 归还日期早于借出日期（所有状态）
cur.execute("""
    SELECT COUNT(*) FROM circulations 
    WHERE return_date IS NOT NULL AND return_date < borrow_date
""")
print(f"归还日期 < 借出日期: {cur.fetchone()[0]:,}")

# 5. 借出日期在未来
from datetime import datetime
today = int(datetime.now().strftime('%Y%m%d'))
cur.execute("SELECT COUNT(*) FROM circulations WHERE borrow_date > %s", (today,))
print(f"借出日期在未来: {cur.fetchone()[0]:,}")

# 6. 年度借还统计
print("\n--- 年度借还统计 ---")
cur.execute("""
    SELECT 
        (borrow_date / 10000) as year,
        SUM(CASE WHEN status = 'borrowed' THEN 1 ELSE 0 END) as borrowed,
        SUM(CASE WHEN status = 'returned' THEN 1 ELSE 0 END) as returned,
        COUNT(*) as total
    FROM circulations
    GROUP BY year
    ORDER BY year
""")
print(f"{'年份':>6} | {'借出':>10} | {'归还':>10} | {'总计':>10}")
print("-" * 50)
for row in cur.fetchall():
    print(f"{row[0]:>6} | {row[1]:>10,} | {row[2]:>10,} | {row[3]:>10,}")

# 7. 借出/归还比例
print("\n--- 借还比例 ---")
cur.execute("""
    SELECT 
        SUM(CASE WHEN status = 'borrowed' THEN 1 ELSE 0 END) as borrowed,
        SUM(CASE WHEN status = 'returned' THEN 1 ELSE 0 END) as returned,
        COUNT(*) as total,
        ROUND(100.0 * SUM(CASE WHEN status = 'borrowed' THEN 1 ELSE 0 END) / COUNT(*), 1) as borrow_pct
    FROM circulations
""")
row = cur.fetchone()
print(f"借出: {row[0]:,} ({row[3]}%)")
print(f"归还: {row[1]:,}")
print(f"总计: {row[2]:,}")

conn.close()
print("\n✅ 步骤3完成")
