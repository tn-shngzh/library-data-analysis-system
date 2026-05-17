import psycopg

conn = psycopg.connect('host=localhost port=5432 dbname=library_db user=postgres password=GXYL2405')
conn.autocommit = True
cur = conn.cursor()

print("步骤1：备份数据...")

# 检查是否已有备份
cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'circulations_backup'")
if cur.fetchone()[0] > 0:
    print("备份表已存在，跳过创建")
    cur.execute("SELECT COUNT(*) FROM circulations_backup")
    print(f"备份表记录数: {cur.fetchone()[0]:,}")
else:
    print("创建备份表...")
    cur.execute("""
        CREATE TABLE circulations_backup AS 
        SELECT * FROM circulations
    """)
    cur.execute("SELECT COUNT(*) FROM circulations_backup")
    print(f"备份完成，记录数: {cur.fetchone()[0]:,}")

conn.close()
print("✅ 步骤1完成")
