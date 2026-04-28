from fastapi import APIRouter, Depends
from datetime import datetime
from app.database import get_db

router = APIRouter(prefix="/api/overview", tags=["数据总览"])


@router.get("/stats")
async def get_overview_stats(conn=Depends(get_db)):
    with conn.cursor() as cur:
        today = datetime.now().date()
        today_int = int(today.strftime('%Y%m%d'))
        this_month_start = int(today.replace(day=1).strftime('%Y%m%d'))
        this_month_end = int(today.strftime('%Y%m%d'))

        cur.execute("SELECT COUNT(DISTINCT borrower_id) FROM circulations WHERE action_date BETWEEN %s AND %s", (this_month_start, this_month_end))
        active_readers = cur.fetchone()[0] or 0

        cur.execute("SELECT COUNT(DISTINCT borrower_id) FROM circulations WHERE action_date = %s", (today_int,))
        today_visits = cur.fetchone()[0] or 0

        cur.execute("SELECT COUNT(DISTINCT category) FROM book_categories")
        total_categories = cur.fetchone()[0]

        try:
            cur.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM borrowers) as total_readers,
                    (SELECT COUNT(*) FROM circulations) as total_borrows,
                    %s as active_readers,
                    (SELECT COUNT(*) FROM book_categories) as total_books,
                    (SELECT COUNT(*) FROM circulations WHERE action = 'CKO') as cko_count,
                    (SELECT COUNT(*) FROM circulations WHERE action = 'CKI') as cki_count,
                    (SELECT COUNT(*) FROM circulations WHERE action = 'REH') as reh_count,
                    (SELECT COUNT(*) FROM circulations WHERE action = 'REI') as rei_count,
                    %s as today_visits,
                    %s as total_categories
            """, (active_readers, today_visits, total_categories))
            row = cur.fetchone()
            
            return {
                "total_readers": row[0],
                "total_borrows": row[1],
                "active_readers": active_readers,
                "total_books": row[3],
                "cko_count": row[4],
                "cki_count": row[5],
                "reh_count": row[6],
                "rei_count": row[7],
                "today_visits": today_visits,
                "total_categories": total_categories
            }
        except Exception as e:
            print(f"Error fetching stats: {e}")
            cur.execute("SELECT COUNT(*) FROM borrowers")
            total_readers = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM circulations")
            total_borrows = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM book_categories")
            total_books = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM circulations WHERE action = 'CKO'")
            cko_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM circulations WHERE action = 'CKI'")
            cki_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM circulations WHERE action = 'REH'")
            reh_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM circulations WHERE action = 'REI'")
            rei_count = cur.fetchone()[0]

            return {
                "total_readers": total_readers,
                "total_borrows": total_borrows,
                "active_readers": active_readers,
                "total_books": total_books,
                "cko_count": cko_count,
                "cki_count": cki_count,
                "reh_count": reh_count,
                "rei_count": rei_count,
                "today_visits": today_visits,
                "total_categories": total_categories
            }


@router.get("/reader-types")
@router.get("/categories", include_in_schema=False)
async def get_reader_types(conn=Depends(get_db)):
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
        result = []
        for i, r in enumerate(rows):
            pct = round(r[1] / total * 100, 1) if total else 0
            if i == len(rows) - 1:
                pct = round(100.0 - sum(round(rr[1] / total * 100, 1) for rr in rows[:-1]), 1)
            result.append({"name": r[0], "count": r[1], "percent": pct})
        return result


@router.get("/recent-books")
async def get_recent_books(conn=Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT c.action_date, c.action, b.degree
            FROM circulations c
            JOIN borrowers b ON c.borrower_id = b.id
            WHERE c.action = 'CKO'
            ORDER BY c.action_date DESC, c.action_time DESC
            LIMIT 5
        """)
        rows = cur.fetchall()
        return [
            {
                "date": str(r[0]),
                "action": r[1],
                "degree": r[2]
            }
            for r in rows
        ]
