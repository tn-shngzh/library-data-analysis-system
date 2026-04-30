import psycopg2
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = psycopg2.connect(
    host='localhost',
    port='5432',
    dbname='library_db',
    user='postgres',
    password='GXYL2405'
)
cur = conn.cursor()

# Check current category distribution
cur.execute("""
    SELECT category, COUNT(*) as book_count 
    FROM book_categories 
    GROUP BY category 
    ORDER BY book_count DESC
""")

categories = cur.fetchall()
total = sum(row[1] for row in categories)

print(f'\nCurrent category distribution (total: {total:,} books):')
print('='*60)
for row in categories:
    pct = row[1] / total * 100
    print(f'  {row[0]:15s}: {row[1]:>7,} books ({pct:5.2f}%)')

print('='*60)

# Target distribution for comparison
targets = {
    '马克思主义': 6000,
    '综合性图书': 7000,
    '航空航天': 9000,
    '农业科学': 11000,
    '环境安全': 11000,
}

print('\nComparison with targets:')
for cat in targets:
    current = next((row[1] for row in categories if row[0] == cat), 0)
    target = targets[cat]
    diff = current - target
    print(f'  {cat}: current={current:,}, target={target:,}, diff={diff:+,}')

conn.close()
