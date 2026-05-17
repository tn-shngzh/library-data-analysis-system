import psycopg
conn = psycopg.connect('host=localhost port=5432 dbname=library_db user=postgres password=GXYL2405')
cur = conn.cursor()

print("=" * 70)
print("数据库数据质量检查报告")
print("=" * 70)

cur.execute("SELECT COUNT(*) FROM circulations")
total = cur.fetchone()[0]
print(f"\n总记录数: {total:,}")

# 1. 归还日期早于借出日期
print("\n--- 1. 归还日期早于借出日期 ---")
cur.execute("""
    SELECT COUNT(*) FROM circulations 
    WHERE status = 'returned' AND return_date < borrow_date
""")
print(f"记录数: {cur.fetchone()[0]:,}")

# 2. 没有借出记录的归还记录（同一 borrower+bib 没有 borrowed 记录）
print("\n--- 2. 归还次数 > 借出次数（同一读者+同一书） ---")
cur.execute("""
    SELECT borrower_id, bib_id,
           SUM(CASE WHEN status = 'borrowed' THEN 1 ELSE 0 END) as borrow_cnt,
           SUM(CASE WHEN status = 'returned' THEN 1 ELSE 0 END) as return_cnt
    FROM circulations
    GROUP BY borrower_id, bib_id
    HAVING SUM(CASE WHEN status = 'returned' THEN 1 ELSE 0 END) > SUM(CASE WHEN status = 'borrowed' THEN 1 ELSE 0 END)
""")
rows = cur.fetchall()
print(f"涉及记录组数: {len(rows):,}")

# 统计这些组中多出的归还记录数
extra_returns = sum(r[3] - r[2] for r in rows)
print(f"多出的归还记录数: {extra_returns:,}")

# 3. 借出日期在未来（大于当前日期）
print("\n--- 3. 借出日期在未来 ---")
from datetime import datetime
today = int(datetime.now().strftime('%Y%m%d'))
cur.execute("SELECT COUNT(*) FROM circulations WHERE borrow_date > %s", (today,))
print(f"记录数: {cur.fetchone()[0]:,}")

# 4. 借出日期异常（小于 20000101）
print("\n--- 4. 借出日期异常（小于 20000101） ---")
cur.execute("SELECT COUNT(*) FROM circulations WHERE borrow_date < 20000101")
print(f"记录数: {cur.fetchone()[0]:,}")

# 5. status 既不是 borrowed 也不是 returned
print("\n--- 5. 未知状态 ---")
cur.execute("SELECT DISTINCT status FROM circulations WHERE status NOT IN ('borrowed', 'returned')")
unknown = cur.fetchall()
print(f"状态值: {[r[0] for r in unknown]}")

# 6. 统计有 return_date 但 status = 'borrowed' 的记录
print("\n--- 6. 已借出但有归还日期 ---")
cur.execute("SELECT COUNT(*) FROM circulations WHERE status = 'borrowed' AND return_date IS NOT NULL")
print(f"记录数: {cur.fetchone()[0]:,}")

# 7. 统计无 return_date 但 status = 'returned' 的记录
print("\n--- 7. 已归还但无归还日期 ---")
cur.execute("SELECT COUNT(*) FROM circulations WHERE status = 'returned' AND return_date IS NULL")
print(f"记录数: {cur.fetchone()[0]:,}")

# 8. 同一 borrower + bib + borrow_date 的记录
print("\n--- 8. 完全重复的借阅记录 ---")
cur.execute("""
    SELECT borrower_id, bib_id, borrow_date, COUNT(*) as cnt
    FROM circulations
    GROUP BY borrower_id, bib_id, borrow_date
    HAVING COUNT(*) > 1
""")
dupes = cur.fetchall()
print(f"重复组数: {len(dupes)}")
if dupes:
    print("样本:")
    for d in dupes[:5]:
        print(f"  borrower={d[0]}, bib={d[1]}, date={d[2]}, count={d[3]}")

# 9. 按年度统计借还比例
print("\n--- 9. 年度借还统计 ---")
cur.execute("""
    SELECT 
        (borrow_date / 10000) as year,
        SUM(CASE WHEN status = 'borrowed' THEN 1 ELSE 0 END) as borrowed,
        SUM(CASE WHEN status = 'returned' THEN 1 ELSE 0 END) as returned,
        COUNT(*) as total,
        ROUND(100.0 * SUM(CASE WHEN status = 'borrowed' THEN 1 ELSE 0 END) / COUNT(*), 1) as borrow_pct
    FROM circulations
    GROUP BY year
    ORDER BY year
""")
print(f"{'年份':>6} | {'借出':>10} | {'归还':>10} | {'总计':>10} | {'借出%':>6}")
print("-" * 60)
for row in cur.fetchall():
    print(f"{row[0]:>6} | {row[1]:>10,} | {row[2]:>10,} | {row[3]:>10,} | {row[4]:>5}%")

# 汇总
print("\n" + "=" * 70)
print("汇总")
print("=" * 70)

cur.execute("""
    SELECT COUNT(*) FROM circulations 
    WHERE status = 'returned' AND return_date < borrow_date
""")
ret_before_borrow = cur.fetchone()[0]

cur.execute("""
    SELECT borrower_id, bib_id,
           SUM(CASE WHEN status = 'borrowed' THEN 1 ELSE 0 END) as borrow_cnt,
           SUM(CASE WHEN status = 'returned' THEN 1 ELSE 0 END) as return_cnt
    FROM circulations
    GROUP BY borrower_id, bib_id
    HAVING SUM(CASE WHEN status = 'returned' THEN 1 ELSE 0 END) > SUM(CASE WHEN status = 'borrowed' THEN 1 ELSE 0 END)
""")
rows = cur.fetchall()
extra_returns = sum(r[3] - r[2] for r in rows)

print(f"1. 归还日期早于借出日期: {ret_before_borrow:,} 条")
print(f"2. 归还次数 > 借出次数: {extra_returns:,} 条（多出的部分）")
print(f"3. 总不合理记录数（估算）: {ret_before_borrow + extra_returns:,} 条")
print(f"4. 合理记录数（估算）: {total - ret_before_borrow - extra_returns:,} 条")
print(f"5. 不合理记录占比: {round(100.0 * (ret_before_borrow + extra_returns) / total, 1)}%")

conn.close()
