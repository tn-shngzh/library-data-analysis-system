import psycopg

conn = psycopg.connect('host=localhost port=5432 dbname=library_db user=postgres password=GXYL2405')
conn.autocommit = True
cur = conn.cursor()

print("=" * 70)
print("步骤2：修复日期颠倒的记录")
print("=" * 70)

# 1. 先删除唯一约束
print("\n步骤2.1：删除唯一约束...")
cur.execute("""
    ALTER TABLE circulations 
    DROP CONSTRAINT IF EXISTS borrow_records_borrower_id_bib_id_borrow_date_key
""")
print("✅ 唯一约束已删除")

# 2. 修复日期颠倒的记录
print("\n步骤2.2：修复日期颠倒的记录...")
cur.execute("""
    UPDATE circulations 
    SET borrow_date = return_date, 
        return_date = borrow_date
    WHERE status = 'returned' AND return_date < borrow_date
""")
print(f"✅ 已修复 {cur.rowcount:,} 条记录")

# 3. 验证修复结果
print("\n步骤2.3：验证修复结果...")
cur.execute("""
    SELECT COUNT(*) FROM circulations 
    WHERE status = 'returned' AND return_date < borrow_date
""")
count_after = cur.fetchone()[0]
print(f"修复后仍存在的颠倒记录: {count_after:,}")

# 4. 重新创建唯一约束（如果可能）
print("\n步骤2.4：尝试重新创建唯一约束...")
try:
    cur.execute("""
        ALTER TABLE circulations 
        ADD CONSTRAINT borrow_records_borrower_id_bib_id_borrow_date_key 
        UNIQUE (borrower_id, bib_id, borrow_date)
    """)
    print("✅ 唯一约束重新创建成功")
except Exception as e:
    print(f"⚠️ 唯一约束重新创建失败: {e}")
    print("保留约束删除状态")

conn.close()
print("\n✅ 步骤2完成")
