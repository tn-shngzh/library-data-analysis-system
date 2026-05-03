import logging
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.database import init_db_pool, get_db_connection, release_db_connection
from app.routers import auth, overview, readers, books, borrows, analysis, imports, insights

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


async def refresh_materialized_views():
    while True:
        await asyncio.sleep(300)
        try:
            await asyncio.to_thread(_refresh_views_sync)
            logger.info("Materialized views refreshed successfully")
        except Exception as e:
            logger.warning(f"Failed to refresh materialized views: {e}")


def _refresh_views_sync():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            views = [
                'mv_overview_stats', 'mv_book_stats', 'mv_borrow_stats',
                'mv_action_stats', 'mv_degree_borrow_stats', 'mv_daily_borrow_trend',
                'mv_top_borrowers', 'mv_top_books', 'mv_reader_stats', 'mv_monthly_active'
            ]
            for view in views:
                try:
                    cur.execute(f"REFRESH MATERIALIZED VIEW {view}")
                except Exception as e:
                    logger.warning(f"Failed to refresh {view}: {e}")
            conn.commit()
    finally:
        release_db_connection(conn)


@asynccontextmanager
async def lifespan(app):
    init_db_pool()
    logger.info("Database connection pool initialized")
    task = asyncio.create_task(refresh_materialized_views())
    yield
    task.cancel()
    logger.info("Application shutdown")


app = FastAPI(title="图书馆数据分析系统", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请稍后重试"}
    )


app.include_router(auth.router)
app.include_router(overview.router)
app.include_router(readers.router)
app.include_router(books.router)
app.include_router(borrows.router)
app.include_router(analysis.router)
app.include_router(imports.router)
app.include_router(insights.router)


@app.get("/")
async def root():
    return {"message": "图书馆数据分析系统 API"}


@app.get("/health")
async def health_check():
    checks = {}
    try:
        def _check_db():
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            release_db_connection(conn)
            return "ok"
        checks["database"] = await asyncio.to_thread(_check_db)
    except Exception as e:
        checks["database"] = f"error: {str(e)}"

    status = "healthy" if all(v == "ok" for v in checks.values()) else "unhealthy"
    return {"status": status, "checks": checks}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
