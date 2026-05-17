import psycopg

conn = psycopg.connect('host=localhost port=5432 dbname=library_db user=postgres password=GXYL2405')
cur = conn.cursor()

print("=" * 70)
print("深入分析冲突记录")
print("=" * 70)

# 查看冲突记录对的完整信息
print("\n--- 冲突记录对详情 ---")
cur.execute("""
    WITH swapped AS (
        SELECT id, borrower_id, bib_id, return_date AS new_borrow_date, borrow_date AS old_borrow_date,
               return_time, borrow_time, status
        FROM circulations 
        WHERE status = 'returned' AND return_date < borrow_date
    )
    SELECT 
        s.id AS swap_id, s.borrower_id, s.bib_id, 
        s.old_borrow_date, s.new_borrow_date,
        c.id AS existing_id, c.borrow_date AS existing_borrow_date, c.return_date AS existing_return_date,
        c.status AS existing_status
    FROM swapped s
    JOIN circulations c ON s.borrower_id = c.borrower_id 
                        AND s.bib_id = c.bib_id 
                        AND s.new_borrow_date = c.borrow_date
    WHERE c.id != s.id
    LIMIT 20
""")
rows = cur.fetchall()
print(f"找到 {len(rows)} 对冲突记录\n")
for row in rows:
    print(f"要修复的记录: id={row[0]}, borrower={row[1]}, bib={row[2]}")
    print(f"  当前: borrow={row[3]}, return={row[4]}")
    print(f"  交换后: borrow={row[4]}, return={row[3]}")
    print(f"已存在的记录: id={row[5]}, borrow={row[6]}, return={row[7]}, status={row[8]}")
    print()

conn.close()
