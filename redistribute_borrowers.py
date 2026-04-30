"""
Step 1: Redistribute borrower records from over-active readers to under-active readers
- Readers with >2800 borrows will have their excess redistributed
- Total records remain the same, just borrower_id changes
"""
import os
os.environ['DB_PASSWORD'] = 'GXYL2405'
import psycopg2
import random

conn = psycopg2.connect(
    host='localhost', port='5432',
    dbname='library_db', user='postgres', password='GXYL2405'
)
cur = conn.cursor()
random.seed(42)

print("=" * 60)
print("Step 1: 重新分配高频读者的借阅记录")
print("=" * 60)

# 1. Find readers with >2800 borrows
cur.execute("""
    SELECT borrower_id, COUNT(*) as cnt
    FROM circulations
    GROUP BY borrower_id
    HAVING COUNT(*) > 2800
    ORDER BY cnt DESC
""")
over_borrowers = {row[0]: row[1] for row in cur.fetchall()}
print(f"\n找到 {len(over_borrowers)} 个借阅超过2800次的读者")

total_excess = sum(cnt - 2800 for cnt in over_borrowers.values())
print(f"需要重新分配的借阅记录总数: {total_excess:,}")

# 2. Get the record IDs for these over-borrowers
records_to_redistribute = []
for borrower_id in over_borrowers:
    cur.execute("""
        SELECT id FROM circulations
        WHERE borrower_id = %s
        ORDER BY RANDOM()
        LIMIT %s
    """, (borrower_id, over_borrowers[borrower_id] - 2800))
    excess_ids = [row[0] for row in cur.fetchall()]
    records_to_redistribute.extend(excess_ids)
    print(f"  borrower_id={borrower_id}: 取 {len(excess_ids)} 条记录用于重新分配")

print(f"\n共收集 {len(records_to_redistribute):,} 条记录需要重新分配")

# 3. Get under-active borrowers (those with <=2800 borrows) as redistribution targets
cur.execute("""
    SELECT borrower_id, COUNT(*) as cnt
    FROM circulations
    GROUP BY borrower_id
    HAVING COUNT(*) <= 2800
""")
under_borrowers = {row[0]: row[1] for row in cur.fetchall()}
print(f"\n找到 {len(under_borrowers)} 个借阅2800次以下的读者作为接收方")

# Select a subset of under_borrowers to receive the redistributed records
# We want to give more to those with fewer borrows to balance the distribution
under_borrower_list = list(under_borrowers.keys())
random.shuffle(under_borrower_list)

# Take enough recipients to distribute the excess records
num_recipients = min(len(under_borrower_list), 20000)  # Use up to 20000 recipients
recipients = under_borrower_list[:num_recipients]
records_per_recipient = len(records_to_redistribute) // len(recipients)
print(f"选择 {len(recipients)} 个接收者，每人分配约 {records_per_recipient} 条记录")

# 4. Update the borrower_id for excess records in batches
batch_size = 5000
print(f"\n开始批量更新 (每批 {batch_size} 条)...")

for i in range(0, len(records_to_redistribute), batch_size):
    batch_ids = records_to_redistribute[i:i+batch_size]
    batch_recipients = []
    for j in range(len(batch_ids)):
        recipient_idx = (i + j) % len(recipients)
        batch_recipients.append(recipients[recipient_idx])
    
    # Build update query with individual values
    values_str = ','.join(
        f"({rid}, {rids[0]})" 
        for rid, rids in zip(batch_ids, [[recipients[(i+j) % len(recipients)] for j in range(len(batch_ids))][idx]] 
        for idx in range(len(batch_ids)))
    )
    # More efficient: use executemany
    update_data = list(zip(batch_ids, batch_recipients))
    
    update_query = """
        UPDATE circulations SET borrower_id = new_id
        FROM (VALUES %s) AS v(id, new_id)
        WHERE circulations.id = v.id
    """ % ','.join(f"({r[0]}, {r[1]})" for r in update_data)
    
    cur.execute(update_query)
    conn.commit()
    
    if (i // batch_size + 1) % 10 == 0 or i + batch_size >= len(records_to_redistribute):
        print(f"  已更新 {min(i + batch_size, len(records_to_redistribute)):,} / {len(records_to_redistribute):,} 条")

# 5. Verify redistribution
print("\n验证重新分配结果...")
cur.execute("""
    SELECT borrower_id, COUNT(*) as cnt
    FROM circulations
    GROUP BY borrower_id
    HAVING COUNT(*) > 2800
    ORDER BY cnt DESC
    LIMIT 5
""")
remaining_over = cur.fetchall()
if remaining_over:
    print(f"  仍有 {len(remaining_over)} 个读者超过2800次:")
    for row in remaining_over:
        print(f"    borrower_id={row[0]}: {row[1]} 次")
else:
    print("  ✓ 所有读者借阅次数均不超过2800次")

print("\nStep 1 完成!")
cur.close()
conn.close()
