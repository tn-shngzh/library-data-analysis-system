import psycopg

conn = psycopg.connect('host=localhost port=5432 dbname=library_db user=postgres password=GXYL2405')
cur = conn.cursor()

print("=" * 70)
print("检查唯一约束和重复记录")
print("=" * 70)

# 1. 查看约束信息
print("\n--- 1. circulations 表的约束 ---")
cur.execute("""
    SELECT conname, contype, pg_get_constraintdef(oid)
    FROM pg_constraint
    WHERE conrelid = 'circulations'::regclass
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} - {row[2]}")

# 2. 查看表结构
print("\n--- 2. circulations 表结构 ---")
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'circulations'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

# 3. 统计交换日期后会产生重复的记录
print("\n--- 3. 交换日期后会产生的重复记录 ---")
cur.execute("""
    WITH swapped AS (
        SELECT id, borrower_id, bib_id, return_date AS new_borrow_date
        FROM circulations 
        WHERE status = 'returned' AND return_date < borrow_date
    )
    SELECT s.borrower_id, s.bib_id, s.new_borrow_date, COUNT(*) as cnt
    FROM swapped s
    JOIN circulations c ON s.borrower_id = c.borrower_id 
                        AND s.bib_id = c.bib_id 
                        AND s.new_borrow_date = c.borrow_date
    GROUP BY s.borrower_id, s.bib_id, s.new_borrow_date
    HAVING COUNT(*) > 0
    LIMIT 10
""")
rows = cur.fetchall()
print(f"会产生冲突的记录组数: {len(rows)}")
if rows:
    print("样本:")
    for row in rows:
        print(f"  borrower={row[0]}, bib={row[1]}, new_borrow_date={row[2]}, existing_count={row[3]}")

# 4. 查看这些冲突记录的详细信息
print("\n--- 4. 冲突记录详情 ---")
cur.execute("""
    WITH swapped AS (
        SELECT id, borrower_id, bib_id, return_date AS new_borrow_date, borrow_date AS old_borrow_date
        FROM circulations 
        WHERE status = 'returned' AND return_date < borrow_date
    )
    SELECT s.id, s.borrower_id, s.bib_id, s.old_borrow_date, s.new_borrow_date, c.id AS existing_id
    FROM swapped s
    JOIN circulations c ON s.borrower_id = c.borrower_id 
                        AND s.bib_id = c.bib_id 
                        AND s.new_borrow_date = c.borrow_date
    LIMIT 5
""")
for row in cur.fetchall():
    print(f"  要修复的记录: id={row[0]}, borrower={row[1]}, bib={row[2]}, old_borrow={row[3]}, new_borrow={row[4]}")
    print(f"    已存在的记录: id={row[5]}")

conn.close()
print("\n✅ 检查完成")
