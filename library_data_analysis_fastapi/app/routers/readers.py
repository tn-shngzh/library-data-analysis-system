from fastapi import APIRouter
from app.database import get_db_connection
from app.config import education_levels

router = APIRouter(prefix="/api/readers", tags=["读者分析"])


@router.get("/stats")
async def get_reader_stats():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM borrowers")
            total_readers = cur.fetchone()[0]

            cur.execute("SELECT COUNT(DISTINCT borrower_id) FROM circulations WHERE action_date BETWEEN 20190401 AND 20190430")
            month_active = cur.fetchone()[0]

            cur.execute("SELECT COUNT(DISTINCT borrower_id) FROM circulations WHERE action_date BETWEEN 20190401 AND 20190430 AND action = 'CKO'")
            month_borrowers = cur.fetchone()[0]

            try:
                cur.execute("SELECT AVG(borrow_count) FROM mv_reader_stats")
                avg_borrows = cur.fetchone()[0]
            except Exception:
                cur.execute("SELECT COUNT(*)::float / NULLIF(COUNT(DISTINCT borrower_id), 0) FROM circulations")
                avg_borrows = cur.fetchone()[0]

            return {
                "total_readers": total_readers,
                "month_active": month_active,
                "month_new": month_borrowers,
                "avg_borrows": round(avg_borrows, 1) if avg_borrows else 0
            }
    finally:
        conn.close()


@router.get("/types")
async def get_reader_types():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT el.name, COUNT(b.id) as count
                FROM borrowers b
                JOIN education_levels el ON b.degree = el.code
                GROUP BY el.name
                ORDER BY count DESC
            """)
            rows = cur.fetchall()
            total = sum(r[1] for r in rows)
            return [
                {"name": r[0], "count": r[1], "percent": round(r[1] / total * 100, 1)}
                for r in rows
            ]
    finally:
        conn.close()


@router.get("/monthly-trend")
async def get_monthly_trend():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            try:
                cur.execute("SELECT month, active_count FROM mv_monthly_active ORDER BY month")
                rows = cur.fetchall()
                month_names = {
                    201901: '1月', 201902: '2月', 201903: '3月',
                    201904: '4月', 201905: '5月', 201906: '6月',
                    201907: '7月', 201908: '8月', 201909: '9月',
                    201910: '10月', 201911: '11月', 201912: '12月'
                }
                return [
                    {"month": month_names.get(r[0], str(r[0])), "count": r[1]}
                    for r in rows
                ]
            except Exception:
                months = [201901, 201902, 201903, 201904, 201905, 201906,
                          201907, 201908, 201909, 201910, 201911, 201912]
                month_names = {
                    201901: '1月', 201902: '2月', 201903: '3月',
                    201904: '4月', 201905: '5月', 201906: '6月',
                    201907: '7月', 201908: '8月', 201909: '9月',
                    201910: '10月', 201911: '11月', 201912: '12月'
                }
                result = []
                for m in months:
                    cur.execute("SELECT COUNT(DISTINCT borrower_id) FROM circulations WHERE action_date BETWEEN %s AND %s + 99", (m, m))
                    count = cur.fetchone()[0]
                    result.append({"month": month_names.get(m, str(m)), "count": count})
                return result
    finally:
        conn.close()


@router.get("/top")
async def get_top_readers():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            try:
                cur.execute("""
                    SELECT rs.borrower_id, rs.borrow_count, b.degree
                    FROM mv_reader_stats rs
                    JOIN borrowers b ON rs.borrower_id = b.id
                    ORDER BY rs.borrow_count DESC
                    LIMIT 10
                """)
                rows = cur.fetchall()
            except Exception:
                cur.execute("""
                    SELECT c.borrower_id, COUNT(*) as borrow_count, b.degree
                    FROM circulations c
                    JOIN borrowers b ON c.borrower_id = b.id
                    WHERE c.action = 'CKO'
                    GROUP BY c.borrower_id, b.degree
                    ORDER BY borrow_count DESC
                    LIMIT 10
                """)
                rows = cur.fetchall()
            return [
                {
                    "rank": i + 1,
                    "id": r[0],
                    "borrowed": r[1],
                    "type": education_levels.get(r[2], r[2])
                }
                for i, r in enumerate(rows)
            ]
    finally:
        conn.close()
