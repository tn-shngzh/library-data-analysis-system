from fastapi import APIRouter
from app.database import get_db_connection

router = APIRouter(prefix="/api/books", tags=["图书分析"])


@router.get("/stats")
async def get_book_stats():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM book_categories")
            total_items = cur.fetchone()[0]

            cur.execute("SELECT COUNT(DISTINCT bib_id) FROM circulations WHERE action_date BETWEEN 20190401 AND 20190430")
            month_items = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM mv_book_stats WHERE borrow_count > 0")
            borrowed_items = cur.fetchone()[0]

            borrow_rate = round(borrowed_items / total_items * 100, 1) if total_items else 0
            zero_borrow = total_items - borrowed_items if total_items > borrowed_items else 0

            return {
                "total_items": total_items,
                "month_items": month_items,
                "borrow_rate": borrow_rate,
                "zero_borrow": zero_borrow
            }
    finally:
        conn.close()


@router.get("/categories")
async def get_book_categories():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT bc.category, COUNT(*) as total_items
                FROM book_categories bc
                GROUP BY bc.category
                ORDER BY total_items DESC
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
    finally:
        conn.close()


@router.get("/hot")
async def get_hot_books():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT t.bib_id, bc.name, t.category, t.borrow_count
                FROM mv_top_books t
                JOIN book_categories bc ON t.bib_id = bc.bib_id
                ORDER BY t.borrow_count DESC
                LIMIT 20
            """)
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
    finally:
        conn.close()


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

    offset = (page - 1) * page_size

    conn = get_db_connection()
    try:
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
                       COALESCE(bs.borrow_count, 0) as borrow_count
                FROM book_categories bc
                LEFT JOIN mv_book_stats bs ON bc.bib_id = bs.bib_id
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
    finally:
        conn.close()


@router.get("/categories-list")
async def get_categories_list():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT category
                FROM book_categories
                ORDER BY category
            """)
            rows = cur.fetchall()
            return [r[0] for r in rows]
    finally:
        conn.close()
