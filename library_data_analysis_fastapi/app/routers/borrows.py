from fastapi import APIRouter, HTTPException, Request, Depends
from datetime import datetime
from app.database import get_db
from app.config import education_levels
from app.auth import get_current_user

router = APIRouter(prefix="/api/borrows", tags=["借阅分析"])


@router.get("/stats")
async def get_borrow_stats(request: Request, conn=Depends(get_db)):
    username = get_current_user(request)

    with conn.cursor() as cur:
        cur.execute("SELECT role FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        role = user[0] if user else 'user'

        cur.execute("""
            SELECT total_actions, total_borrows, total_returns,
                   total_renewals, active_borrowers, borrowed_books
            FROM mv_borrow_stats
        """)
        row = cur.fetchone()
        if row:
            total_actions = row[0]
            total_borrows = row[1]
            total_returns = row[2]
            total_renewals = row[3]
            active_borrowers = row[4]
            borrowed_books = row[5]
        else:
            cur.execute("SELECT COUNT(*) FROM circulations")
            total_actions = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM circulations WHERE action = 'CKO'")
            total_borrows = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM circulations WHERE action = 'CKI'")
            total_returns = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM circulations WHERE action IN ('REH', 'REI')")
            total_renewals = cur.fetchone()[0]

            cur.execute("SELECT COUNT(DISTINCT borrower_id) FROM circulations WHERE action = 'CKO'")
            active_borrowers = cur.fetchone()[0]

            cur.execute("SELECT COUNT(DISTINCT bib_id) FROM circulations WHERE action = 'CKO'")
            borrowed_books = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM book_categories")
        total_books = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM borrowers")
        total_readers = cur.fetchone()[0]

        today = int(datetime.now().strftime('%Y%m%d'))
        cur.execute("SELECT COUNT(*) FROM circulations WHERE action_date = %s", (today,))
        today_visits = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM circulations WHERE action_date = %s AND action = 'CKO'", (today,))
        today_borrows = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM circulations WHERE action_date = %s AND action = 'CKI'", (today,))
        today_returns = cur.fetchone()[0]

        cur.execute("SELECT COUNT(DISTINCT category) FROM book_categories")
        category_count = cur.fetchone()[0]

        result = {
            "total_actions": total_actions,
            "total_borrows": total_borrows,
            "total_returns": total_returns,
            "total_renewals": total_renewals,
            "active_borrowers": active_borrowers,
            "borrowed_books": borrowed_books,
            "total_books": total_books,
            "total_readers": total_readers,
            "today_visits": today_visits,
            "today_borrows": today_borrows,
            "today_returns": today_returns,
            "category_count": category_count,
            "cko_count": total_borrows,
            "cki_count": total_returns,
            "reh_count": 0,
            "rei_count": total_renewals,
            "role": role
        }

        if role == 'user':
            cur.execute("SELECT id FROM borrowers WHERE name = %s", (username,))
            borrower = cur.fetchone()
            if borrower:
                borrower_id = borrower[0]

                cur.execute(
                    "SELECT COUNT(*) FROM circulations WHERE borrower_id = %s AND action = 'CKO'",
                    (borrower_id,)
                )
                my_borrows = cur.fetchone()[0]

                cur.execute(
                    "SELECT COUNT(*) FROM circulations WHERE borrower_id = %s AND action = 'CKI'",
                    (borrower_id,)
                )
                my_returns = cur.fetchone()[0]

                cur.execute(
                    "SELECT COUNT(DISTINCT bib_id) FROM circulations WHERE borrower_id = %s AND action = 'CKO' AND NOT EXISTS (SELECT 1 FROM circulations c2 WHERE c2.borrower_id = circulations.borrower_id AND c2.bib_id = circulations.bib_id AND c2.action = 'CKI' AND c2.action_date >= circulations.action_date)",
                    (borrower_id,)
                )
                my_current_borrowed = cur.fetchone()[0]

                result["my_borrows"] = my_borrows
                result["my_returns"] = my_returns
                result["my_current_borrowed"] = my_current_borrowed
            else:
                result["my_borrows"] = 0
                result["my_returns"] = 0
                result["my_current_borrowed"] = 0

        return result


@router.get("/action-stats")
async def get_action_stats(conn=Depends(get_db)):
    with conn.cursor() as cur:
        try:
            cur.execute("SELECT action, count FROM mv_action_stats ORDER BY count DESC")
            rows = cur.fetchall()
        except Exception:
            cur.execute("SELECT action, COUNT(*) as count FROM circulations GROUP BY action ORDER BY count DESC")
            rows = cur.fetchall()
        total = sum(r[1] for r in rows)
        action_names = {'CKO': '借出', 'CKI': '归还', 'REH': '到馆续借', 'REI': '网上续借'}
        result = []
        for i, r in enumerate(rows):
            pct = round(r[1] / total * 100, 1) if total else 0
            if i == len(rows) - 1:
                pct = round(100.0 - sum(round(rr[1] / total * 100, 1) for rr in rows[:-1]), 1)
            result.append({
                "action": r[0],
                "name": action_names.get(r[0], r[0]),
                "count": r[1],
                "percent": pct
            })
        return result


@router.get("/degree-stats")
async def get_degree_stats(conn=Depends(get_db)):
    with conn.cursor() as cur:
        try:
            cur.execute("SELECT degree, degree_name, count FROM mv_degree_borrow_stats ORDER BY count DESC")
            rows = cur.fetchall()
        except Exception:
            cur.execute("""
                SELECT b.degree, el.name, COUNT(*) as count
                FROM circulations c
                JOIN borrowers b ON c.borrower_id = b.id
                JOIN education_levels el ON b.degree = el.code
                GROUP BY b.degree, el.name
                ORDER BY count DESC
            """)
            rows = cur.fetchall()
        total = sum(r[2] for r in rows)
        result = []
        for i, r in enumerate(rows):
            pct = round(r[2] / total * 100, 1) if total else 0
            if i == len(rows) - 1:
                pct = round(100.0 - sum(round(rr[2] / total * 100, 1) for rr in rows[:-1]), 1)
            result.append({
                "code": r[0],
                "name": r[1],
                "count": r[2],
                "percent": pct
            })
        return result


@router.get("/daily-trend")
async def get_daily_trend(conn=Depends(get_db)):
    with conn.cursor() as cur:
        try:
            cur.execute("SELECT action_date, count FROM mv_daily_borrow_trend")
            rows = cur.fetchall()
        except Exception:
            cur.execute("""
                SELECT action_date, COUNT(*) as count
                FROM circulations
                GROUP BY action_date
                ORDER BY action_date
            """)
            rows = cur.fetchall()
        return [
            {"date": str(r[0]), "count": r[1]}
            for r in rows
        ]


@router.get("/top-borrowers")
async def get_top_borrowers(conn=Depends(get_db)):
    with conn.cursor() as cur:
        try:
            cur.execute("SELECT borrower_id, degree, borrow_count FROM mv_top_borrowers LIMIT 15")
            rows = cur.fetchall()
        except Exception:
            cur.execute("""
                SELECT c.borrower_id, b.degree, COUNT(*) as borrow_count
                FROM circulations c
                JOIN borrowers b ON c.borrower_id = b.id
                WHERE c.action = 'CKO'
                GROUP BY c.borrower_id, b.degree
                ORDER BY borrow_count DESC
                LIMIT 15
            """)
            rows = cur.fetchall()
        return [
            {
                "rank": i + 1,
                "borrower_id": r[0],
                "degree": education_levels.get(r[1], r[1]),
                "borrow_count": r[2]
            }
            for i, r in enumerate(rows)
        ]


@router.get("/top-books")
async def get_top_borrowed_books(conn=Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT t.bib_id, t.category, t.borrow_count, bc.name
            FROM mv_top_books t
            LEFT JOIN book_categories bc ON t.bib_id = bc.bib_id
            ORDER BY t.borrow_count DESC
            LIMIT 15
        """)
        rows = cur.fetchall()
        return [
            {
                "rank": i + 1,
                "bib_id": r[0],
                "category": r[1] if r[1] else '未知',
                "borrow_count": r[2],
                "name": r[3] if r[3] else '未知'
            }
            for i, r in enumerate(rows)
        ]


@router.get("/recent")
async def get_recent_borrows(conn=Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT c.action_date, c.action_time, c.borrower_id, c.bib_id,
                   c.action, b.degree, bc.category, bc.name
            FROM circulations c
            JOIN borrowers b ON c.borrower_id = b.id
            LEFT JOIN book_categories bc ON c.bib_id = bc.bib_id
            WHERE c.action = 'CKO'
            ORDER BY c.action_date DESC, c.action_time DESC
            LIMIT 20
        """)
        rows = cur.fetchall()
        return [
            {
                "date": str(r[0]),
                "time": str(r[1]) if r[1] else '',
                "borrower_id": r[2],
                "bib_id": r[3],
                "action": r[4],
                "degree": education_levels.get(r[5], r[5]),
                "category": r[6] if r[6] else '未知',
                "title": r[7] if r[7] else '未知'
            }
            for r in rows
        ]


@router.post("/borrow")
async def borrow_book(request: Request, conn=Depends(get_db)):
    username = get_current_user(request)

    with conn.cursor() as cur:
        cur.execute("SELECT role FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        role = user[0] if user else 'user'

        if role == 'admin':
            raise HTTPException(status_code=403, detail="管理员账号无法借阅")

        body = await request.json()
        book_id = body.get("book_id")
        if not book_id:
            raise HTTPException(status_code=400, detail="缺少图书 ID")

        cur.execute("SELECT id FROM borrowers WHERE name = %s", (username,))
        borrower = cur.fetchone()
        if not borrower:
            raise HTTPException(status_code=404, detail="读者不存在")

        borrower_id = borrower[0]
        action_date = int(datetime.now().strftime('%Y%m%d'))
        action_time = datetime.now().strftime('%H:%M:%S')

        cur.execute("""
            SELECT COUNT(*) FROM circulations
            WHERE borrower_id = %s AND bib_id = %s AND action = 'CKO'
            AND NOT EXISTS (
                SELECT 1 FROM circulations c2
                WHERE c2.borrower_id = c.borrower_id AND c2.bib_id = c.bib_id
                AND c2.action = 'CKI' AND c2.action_date >= c.action_date
            )
        """, (borrower_id, book_id))
        if cur.fetchone()[0] > 0:
            raise HTTPException(status_code=400, detail="您已借阅此书且尚未归还")

        cur.execute("""
            INSERT INTO circulations (bib_id, borrower_id, action, action_date, action_time)
            VALUES (%s, %s, 'CKO', %s, %s)
            RETURNING id
        """, (book_id, borrower_id, action_date, action_time))

        circ_id = cur.fetchone()[0]
        conn.commit()

        try:
            for mv in ['mv_borrow_stats', 'mv_daily_borrow_trend', 'mv_monthly_active']:
                try:
                    cur.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {mv}")
                except Exception:
                    cur.execute(f"REFRESH MATERIALIZED VIEW {mv}")
            conn.commit()
        except Exception:
            pass

        return {"success": True, "circulation_id": circ_id}


@router.post("/return")
async def return_book(request: Request, conn=Depends(get_db)):
    username = get_current_user(request)

    with conn.cursor() as cur:
        cur.execute("SELECT role FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        role = user[0] if user else 'user'

        if role == 'admin':
            raise HTTPException(status_code=403, detail="管理员账号无法归还")

        body = await request.json()
        book_id = body.get("book_id")
        if not book_id:
            raise HTTPException(status_code=400, detail="缺少图书 ID")

        cur.execute("SELECT id FROM borrowers WHERE name = %s", (username,))
        borrower = cur.fetchone()
        if not borrower:
            raise HTTPException(status_code=404, detail="读者不存在")

        borrower_id = borrower[0]
        action_date = int(datetime.now().strftime('%Y%m%d'))
        action_time = datetime.now().strftime('%H:%M:%S')

        cur.execute("""
            SELECT COUNT(*) FROM circulations
            WHERE borrower_id = %s AND bib_id = %s AND action = 'CKO'
            AND NOT EXISTS (
                SELECT 1 FROM circulations c2
                WHERE c2.borrower_id = c.borrower_id AND c2.bib_id = c.bib_id
                AND c2.action = 'CKI' AND c2.action_date >= c.action_date
            )
        """, (borrower_id, book_id))
        if cur.fetchone()[0] == 0:
            raise HTTPException(status_code=400, detail="未找到该书的借阅记录")

        cur.execute("""
            INSERT INTO circulations (bib_id, borrower_id, action, action_date, action_time)
            VALUES (%s, %s, 'CKI', %s, %s)
            RETURNING id
        """, (book_id, borrower_id, action_date, action_time))

        circ_id = cur.fetchone()[0]
        conn.commit()

        try:
            for mv in ['mv_borrow_stats', 'mv_daily_borrow_trend', 'mv_monthly_active']:
                try:
                    cur.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {mv}")
                except Exception:
                    cur.execute(f"REFRESH MATERIALIZED VIEW {mv}")
            conn.commit()
        except Exception:
            pass

        return {"success": True, "circulation_id": circ_id}


@router.post("/renew")
async def renew_book(request: Request, conn=Depends(get_db)):
    username = get_current_user(request)

    with conn.cursor() as cur:
        cur.execute("SELECT role FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        role = user[0] if user else 'user'

        if role == 'admin':
            raise HTTPException(status_code=403, detail="管理员账号无法续借")

        body = await request.json()
        book_id = body.get("book_id")
        if not book_id:
            raise HTTPException(status_code=400, detail="缺少图书 ID")

        cur.execute("SELECT id FROM borrowers WHERE name = %s", (username,))
        borrower = cur.fetchone()
        if not borrower:
            raise HTTPException(status_code=404, detail="读者不存在")

        borrower_id = borrower[0]

        cur.execute("""
            SELECT COUNT(*) FROM circulations
            WHERE borrower_id = %s AND bib_id = %s AND action = 'CKO'
            AND NOT EXISTS (
                SELECT 1 FROM circulations c2
                WHERE c2.borrower_id = c.borrower_id AND c2.bib_id = c.bib_id
                AND c2.action = 'CKI' AND c2.action_date >= c.action_date
            )
        """, (borrower_id, book_id))
        if cur.fetchone()[0] == 0:
            raise HTTPException(status_code=400, detail="未找到该书的借阅记录，无法续借")

        action_date = int(datetime.now().strftime('%Y%m%d'))
        action_time = datetime.now().strftime('%H:%M:%S')

        cur.execute("""
            INSERT INTO circulations (bib_id, borrower_id, action, action_date, action_time)
            VALUES (%s, %s, 'REH', %s, %s)
            RETURNING id
        """, (book_id, borrower_id, action_date, action_time))

        circ_id = cur.fetchone()[0]
        conn.commit()

        try:
            for mv in ['mv_borrow_stats', 'mv_daily_borrow_trend', 'mv_monthly_active']:
                try:
                    cur.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {mv}")
                except Exception:
                    cur.execute(f"REFRESH MATERIALIZED VIEW {mv}")
            conn.commit()
        except Exception:
            pass

        return {"success": True, "message": "续借成功"}


@router.get("/my")
async def get_my_borrows(request: Request, conn=Depends(get_db)):
    username = get_current_user(request)

    with conn.cursor() as cur:
        cur.execute("SELECT role FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        role = user[0] if user else 'user'

        if role == 'admin':
            return []

        cur.execute("SELECT id FROM borrowers WHERE name = %s", (username,))
        borrower = cur.fetchone()
        if not borrower:
            return []

        borrower_id = borrower[0]
        cur.execute("""
            SELECT c.bib_id, bc.name, bc.category, c.action, c.action_date, c.action_time
            FROM circulations c
            LEFT JOIN book_categories bc ON c.bib_id = bc.bib_id
            WHERE c.borrower_id = %s
            ORDER BY c.action_date DESC, c.action_time DESC
            LIMIT 50
        """, (borrower_id,))
        rows = cur.fetchall()
        return [
            {
                "bib_id": r[0],
                "title": r[1] if r[1] else '未知',
                "category": r[2] if r[2] else '未知',
                "action": r[3],
                "action_name": '借出' if r[3] == 'CKO' else '归还' if r[3] == 'CKI' else r[3],
                "date": str(r[4]),
                "time": str(r[5]) if r[5] else ''
            }
            for r in rows
        ]
