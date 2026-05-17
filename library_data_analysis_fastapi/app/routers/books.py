import logging
from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.database import run_sync_db
from app.cache import cache

router = APIRouter(prefix="/api/books", tags=["图书分析"])
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_book_stats():
    cache_key = "books:stats"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM book_categories")
            total_items = cur.fetchone()[0]

            # 直接查询 circulations 表获取已借阅图书数
            cur.execute("""
                SELECT COUNT(DISTINCT bib_id)
                FROM circulations
                WHERE status = 'borrowed'
            """)
            borrowed_items = cur.fetchone()[0] or 0

            today = datetime.now().date()
            this_month = int(today.strftime('%Y%m'))
            month_start = int(f"{this_month}01")
            month_end = int(f"{this_month}31")

            # 本月借阅图书数（走索引，数据量小）
            cur.execute("""
                SELECT COUNT(DISTINCT bib_id)
                FROM circulations
                WHERE status = 'borrowed'
                AND borrow_date BETWEEN %s AND %s
            """, (month_start, month_end))
            month_row = cur.fetchone()
            month_items = month_row[0] or 0 if month_row else 0

            borrow_rate = round(borrowed_items / total_items * 100, 1) if total_items else 0
            zero_borrow = total_items - borrowed_items if total_items > borrowed_items else 0

            return {
                "total_items": total_items,
                "month_items": month_items,
                "borrow_rate": borrow_rate,
                "zero_borrow": zero_borrow
            }

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取图书统计失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取图书统计失败: {e}")


@router.get("/categories")
async def get_book_categories():
    cache_key = "books:categories"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            # 直接查询 book_categories 表按分类分组统计
            cur.execute("""
                SELECT 
                    category,
                    COUNT(*) as count,
                    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percent
                FROM book_categories
                GROUP BY category
                ORDER BY count DESC
            """)
            rows = cur.fetchall()
            return [
                {"name": r[0], "count": r[1], "percent": r[2]}
                for r in rows
            ]

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取图书分类统计失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取图书分类统计失败: {e}")


@router.get("/hot")
async def get_hot_books():
    cache_key = "books:hot"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            three_years_ago = int((datetime.now().replace(year=datetime.now().year - 3)).strftime('%Y%m%d'))
            cur.execute("""
                SELECT bc.bib_id, bc.name, bc.category, COUNT(*) as borrow_count
                FROM circulations c
                JOIN book_categories bc ON c.bib_id = bc.bib_id
                WHERE c.status = 'borrowed' AND c.borrow_date >= %s
                GROUP BY bc.bib_id, bc.name, bc.category
                ORDER BY borrow_count DESC
                LIMIT 20
            """, (three_years_ago,))
            rows = cur.fetchall()
            return [
                {
                    "rank": i + 1,
                    "bib_id": r[0],
                    "name": r[1],
                    "category": r[2],
                    "borrow_count": r[3]
                }
                for i, r in enumerate(rows)
            ]

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取热门图书失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取热门图书失败: {e}")


@router.get("/search")
async def search_books(
    keyword: str = "",
    category: str = "",
    page: int = 1,
    page_size: int = 20
):
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20
    if len(keyword) > 100:
        keyword = keyword[:100]
    if len(category) > 50:
        category = category[:50]

    offset = (page - 1) * page_size

    def _query(conn):
        with conn.cursor() as cur:
            conditions = []
            params = []

            if keyword:
                conditions.append("(bc.name ILIKE %s OR bc.category ILIKE %s)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])

            if category:
                conditions.append("bc.category = %s")
                params.append(category)

            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

            count_sql = f"SELECT COUNT(*) FROM book_categories bc{where_clause}"
            cur.execute(count_sql, params)
            total = cur.fetchone()[0]

            data_sql = f"""
                SELECT bc.bib_id, bc.name, bc.category,
                       COALESCE(ck.borrow_count, 0) as borrow_count
                FROM book_categories bc
                LEFT JOIN (
                    SELECT bib_id, COUNT(*) as borrow_count
                    FROM circulations WHERE status = 'borrowed'
                    GROUP BY bib_id
                ) ck ON bc.bib_id = ck.bib_id
                {where_clause}
                ORDER BY borrow_count DESC, bc.bib_id ASC
                LIMIT %s OFFSET %s
            """
            cur.execute(data_sql, params + [page_size, offset])
            rows = cur.fetchall()

            books = [
                {
                    "bib_id": r[0],
                    "name": r[1],
                    "category": r[2],
                    "borrow_count": r[3]
                }
                for r in rows
            ]

            total_pages = (total + page_size - 1) // page_size if total > 0 else 0

            return {
                "books": books,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }

    try:
        return await run_sync_db(_query)
    except Exception as e:
        logger.error("搜索图书失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索图书失败: {e}")


@router.get("/categories-list")
async def get_categories_list():
    cache_key = "books:categories-list"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    def _query(conn):
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT category
                FROM book_categories
                ORDER BY category
            """)
            rows = cur.fetchall()
            return [r[0] for r in rows]

    try:
        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取分类列表失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取分类列表失败: {e}")
