import logging
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime
from typing import Optional
from app.database import run_sync_db
from app.config import education_levels
from app.cache import cache
from app.auth import get_current_user
from app.tasks import mv_refresher

router = APIRouter(prefix="/api/borrows", tags=["借阅分析"])
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_borrow_stats():
    cache_key = "borrows:stats"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            try:
                cur.execute("""
                    SELECT total_actions, total_borrows, total_returns,
                           total_renewals, active_borrowers, borrowed_books,
                           reh_count, rei_count
                    FROM mv_borrow_stats
                """)
                mv_row = cur.fetchone()
                if mv_row and mv_row[6] is not None:
                    total_actions = mv_row[0]
                    total_borrows = mv_row[1]
                    total_returns = mv_row[2]
                    total_renewals = mv_row[3]
                    active_borrowers = mv_row[4]
                    borrowed_books = mv_row[5]
                    reh_count = mv_row[6]
                    rei_count = mv_row[7]
                else:
                    raise Exception("mv_borrow_stats missing columns")
            except Exception:
                conn.rollback()
                cur.execute("""
                    SELECT
                        COUNT(*) AS total_actions,
                        COUNT(*) FILTER (WHERE action = 'CKO') AS total_borrows,
                        COUNT(*) FILTER (WHERE action = 'CKI') AS total_returns,
                        COUNT(*) FILTER (WHERE action IN ('REH', 'REI')) AS total_renewals,
                        COUNT(DISTINCT borrower_id) FILTER (WHERE action = 'CKO') AS active_borrowers,
                        COUNT(DISTINCT bib_id) FILTER (WHERE action = 'CKO') AS borrowed_books,
                        COUNT(*) FILTER (WHERE action = 'REH') AS reh_count,
                        COUNT(*) FILTER (WHERE action = 'REI') AS rei_count
                    FROM circulations
                """)
                fallback = cur.fetchone()
                total_actions = fallback[0]
                total_borrows = fallback[1]
                total_returns = fallback[2]
                total_renewals = fallback[3]
                active_borrowers = fallback[4]
                borrowed_books = fallback[5]
                reh_count = fallback[6]
                rei_count = fallback[7]

            today = int(datetime.now().strftime('%Y%m%d'))
            cur.execute("""
                WITH global_stats AS (
                    SELECT
                        (SELECT COUNT(*) FROM book_categories) AS total_books,
                        (SELECT COUNT(*) FROM borrowers) AS total_readers,
                        (SELECT COUNT(DISTINCT category) FROM book_categories) AS category_count
                ),
                today_stats AS (
                    SELECT
                        COUNT(*) AS today_visits,
                        COUNT(*) FILTER (WHERE action = 'CKO') AS today_borrows,
                        COUNT(*) FILTER (WHERE action = 'CKI') AS today_returns
                    FROM circulations
                    WHERE action_date = %s
                )
                SELECT g.total_books, g.total_readers, g.category_count,
                       t.today_visits, t.today_borrows, t.today_returns
                FROM global_stats g, today_stats t
            """, (today,))
            g_row = cur.fetchone()
            total_books = g_row[0]
            total_readers = g_row[1]
            category_count = g_row[2]
            today_visits = g_row[3]
            today_borrows = g_row[4]
            today_returns = g_row[5]

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
                "reh_count": reh_count,
                "rei_count": rei_count
            }

            return result

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 60)
        return result
    except Exception as e:
        logger.error("获取借阅统计失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取借阅统计失败: {e}")


@router.get("/action-stats")
async def get_action_stats():
    cache_key = "borrows:action-stats"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            try:
                cur.execute("SELECT action, count FROM mv_action_stats ORDER BY count DESC")
                rows = cur.fetchall()
            except Exception:
                conn.rollback()
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

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 300)
        return result
    except Exception as e:
        logger.error("获取操作统计失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取操作统计失败: {e}")


@router.get("/degree-stats")
async def get_degree_stats():
    cache_key = "borrows:degree-stats"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            try:
                cur.execute("SELECT degree, degree_name, count FROM mv_degree_borrow_stats ORDER BY count DESC")
                rows = cur.fetchall()
            except Exception:
                conn.rollback()
                try:
                    cur.execute("""
                        SELECT b.degree, el.name, COUNT(*) as count
                        FROM circulations c
                        JOIN borrowers b ON c.borrower_id = b.id
                        JOIN education_levels el ON b.degree = el.code
                        GROUP BY b.degree, el.name
                        ORDER BY count DESC
                    """)
                    rows = cur.fetchall()
                except Exception:
                    conn.rollback()
                    cur.execute("""
                        SELECT b.degree, b.degree, COUNT(*) as count
                        FROM circulations c
                        JOIN borrowers b ON c.borrower_id = b.id
                        GROUP BY b.degree
                        ORDER BY count DESC
                    """)
                    raw_rows = cur.fetchall()
                    rows = [(r[0], education_levels.get(r[0], r[0]), r[1]) for r in raw_rows]
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

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 300)
        return result
    except Exception as e:
        logger.error("获取学历统计失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取学历统计失败: {e}")


@router.get("/daily-trend")
async def get_daily_trend():
    cached = cache.cache_get("borrows:daily-trend")
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            try:
                cur.execute("SELECT action_date, count FROM mv_daily_borrow_trend")
                rows = cur.fetchall()
            except Exception:
                conn.rollback()
                cur.execute("""
                    SELECT action_date, COUNT(*) as count
                    FROM circulations
                    GROUP BY action_date
                    ORDER BY action_date
                """)
                rows = cur.fetchall()
            result = [
                {"date": str(r[0]), "count": r[1]}
                for r in rows
            ]
            return result

    try:
        result = await run_sync_db(_query)
        cache.cache_set("borrows:daily-trend", result, 300)
        return result
    except Exception as e:
        logger.error("获取日趋势失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取日趋势失败: {e}")


@router.get("/top-borrowers")
async def get_top_borrowers():
    cache_key = "borrows:top-borrowers"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            try:
                cur.execute("SELECT borrower_id, degree, borrow_count FROM mv_top_borrowers LIMIT 15")
                rows = cur.fetchall()
            except Exception:
                conn.rollback()
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

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 300)
        return result
    except Exception as e:
        logger.error("获取热门借阅者失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取热门借阅者失败: {e}")


@router.get("/top-books")
async def get_top_borrowed_books():
    cache_key = "borrows:top-books"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            try:
                cur.execute("""
                    SELECT t.bib_id, t.category, t.borrow_count, bc.name
                    FROM mv_top_books t
                    LEFT JOIN book_categories bc ON t.bib_id = bc.bib_id
                    ORDER BY t.borrow_count DESC
                    LIMIT 15
                """)
                rows = cur.fetchall()
            except Exception:
                conn.rollback()
                cur.execute("""
                    SELECT c.bib_id, bc.category, COUNT(*) as borrow_count, bc.name
                    FROM circulations c
                    LEFT JOIN book_categories bc ON c.bib_id = bc.bib_id
                    WHERE c.action = 'CKO'
                    GROUP BY c.bib_id, bc.category, bc.name
                    ORDER BY borrow_count DESC
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

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 300)
        return result
    except Exception as e:
        logger.error("获取热门借阅图书失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取热门借阅图书失败: {e}")


@router.get("/recent")
async def get_recent_borrows():
    cache_key = "borrows:recent"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
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

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 60)
        return result
    except Exception as e:
        logger.error("获取最近借阅记录失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取最近借阅记录失败: {e}")


@router.post("/borrow")
async def borrow_book(request: Request):
    username = get_current_user(request)

    body = await request.json()
    book_id = body.get("book_id")
    if not book_id:
        raise HTTPException(status_code=400, detail="缺少图书 ID")
    try:
        book_id = int(book_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="图书 ID 格式错误")

    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("SELECT role FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            role = user[0] if user else 'user'

            if role == 'admin':
                raise HTTPException(status_code=403, detail="管理员账号无法借阅")

            cur.execute("SELECT id FROM borrowers WHERE name = %s", (username,))
            borrower = cur.fetchone()
            if not borrower:
                raise HTTPException(status_code=404, detail="读者不存在")

            borrower_id = borrower[0]
            action_date = int(datetime.now().strftime('%Y%m%d'))
            action_time = datetime.now().strftime('%H:%M:%S')

            cur.execute("""
                SELECT COUNT(*)
                FROM circulations cko
                LEFT JOIN circulations cki ON cki.borrower_id = cko.borrower_id
                    AND cki.bib_id = cko.bib_id
                    AND cki.action = 'CKI'
                    AND cki.action_date >= cko.action_date
                WHERE cko.borrower_id = %s AND cko.bib_id = %s AND cko.action = 'CKO'
                AND cki.id IS NULL
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
            return circ_id

    try:
        circ_id = await run_sync_db(_query)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("借阅操作失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"借阅操作失败: {e}")

    mv_refresher.schedule_refresh('mv_borrow_stats', 'mv_daily_borrow_trend', 'mv_top_books')
    cache.cache_invalidate('borrows:')
    cache.cache_invalidate('overview:')

    return {"success": True, "circulation_id": circ_id}


@router.post("/return")
async def return_book(request: Request):
    username = get_current_user(request)

    body = await request.json()
    book_id = body.get("book_id")
    if not book_id:
        raise HTTPException(status_code=400, detail="缺少图书 ID")
    try:
        book_id = int(book_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="图书 ID 格式错误")

    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("SELECT role FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            role = user[0] if user else 'user'

            if role == 'admin':
                raise HTTPException(status_code=403, detail="管理员账号无法归还")

            cur.execute("SELECT id FROM borrowers WHERE name = %s", (username,))
            borrower = cur.fetchone()
            if not borrower:
                raise HTTPException(status_code=404, detail="读者不存在")

            borrower_id = borrower[0]
            action_date = int(datetime.now().strftime('%Y%m%d'))
            action_time = datetime.now().strftime('%H:%M:%S')

            cur.execute("""
                SELECT COUNT(*)
                FROM circulations cko
                LEFT JOIN circulations cki ON cki.borrower_id = cko.borrower_id
                    AND cki.bib_id = cko.bib_id
                    AND cki.action = 'CKI'
                    AND cki.action_date >= cko.action_date
                WHERE cko.borrower_id = %s AND cko.bib_id = %s AND cko.action = 'CKO'
                AND cki.id IS NULL
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
            return circ_id

    try:
        circ_id = await run_sync_db(_query)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("归还操作失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"归还操作失败: {e}")

    mv_refresher.schedule_refresh('mv_borrow_stats', 'mv_daily_borrow_trend', 'mv_top_books')
    cache.cache_invalidate('borrows:')
    cache.cache_invalidate('overview:')

    return {"success": True, "circulation_id": circ_id}


@router.post("/renew")
async def renew_book(request: Request):
    username = get_current_user(request)

    body = await request.json()
    book_id = body.get("book_id")
    if not book_id:
        raise HTTPException(status_code=400, detail="缺少图书 ID")
    try:
        book_id = int(book_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="图书 ID 格式错误")

    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("SELECT role FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            role = user[0] if user else 'user'

            if role == 'admin':
                raise HTTPException(status_code=403, detail="管理员账号无法续借")

            cur.execute("SELECT id FROM borrowers WHERE name = %s", (username,))
            borrower = cur.fetchone()
            if not borrower:
                raise HTTPException(status_code=404, detail="读者不存在")

            borrower_id = borrower[0]

            cur.execute("""
                SELECT COUNT(*)
                FROM circulations cko
                LEFT JOIN circulations cki ON cki.borrower_id = cko.borrower_id
                    AND cki.bib_id = cko.bib_id
                    AND cki.action = 'CKI'
                    AND cki.action_date >= cko.action_date
                WHERE cko.borrower_id = %s AND cko.bib_id = %s AND cko.action = 'CKO'
                AND cki.id IS NULL
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
            return circ_id

    try:
        circ_id = await run_sync_db(_query)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("续借操作失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"续借操作失败: {e}")

    mv_refresher.schedule_refresh('mv_borrow_stats', 'mv_daily_borrow_trend', 'mv_top_books')
    cache.cache_invalidate('borrows:')
    cache.cache_invalidate('overview:')

    return {"success": True, "message": "续借成功"}


@router.get("/my")
async def get_my_borrows(request: Request):
    username = get_current_user(request)

    def _auth(conn):
        with conn.cursor() as cur:
            cur.execute("SELECT role FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            role = user[0] if user else 'user'

            if role == 'admin':
                return None

            cur.execute("SELECT id FROM borrowers WHERE name = %s", (username,))
            borrower = cur.fetchone()
            if not borrower:
                return None

            return borrower[0]

    try:
        borrower_id = await run_sync_db(_auth)
    except Exception as e:
        logger.error("获取用户借阅信息失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取用户借阅信息失败: {e}")

    if borrower_id is None:
        return []

    def _query(conn):
        with conn.cursor() as cur:
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

    try:
        return await run_sync_db(_query)
    except Exception as e:
        logger.error("获取我的借阅记录失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取我的借阅记录失败: {e}")
