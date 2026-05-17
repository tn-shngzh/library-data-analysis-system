import logging
import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.database import init_db_pool, get_db_connection, release_db_connection
from app.routers import auth, overview, readers, books, borrows, analysis, imports, insights, intelligence, statistics, report

logging.basicConfig(
    level=logging.WARNING,
    format='%(message)s',
    handlers=[
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
    warmup = asyncio.create_task(warmup_caches())
    yield
    task.cancel()
    warmup.cancel()
    logger.info("Application shutdown")


SLOW_ENDPOINTS = [
    "/api/overview/historical-stats",
    "/api/borrows/stats",
    "/api/borrows/top-books",
    "/api/borrows/top-borrowers",
    "/api/borrows/recent",
    "/api/books/hot",
    "/api/readers/frequency-distribution",
]


async def warmup_caches():
    await asyncio.sleep(3)
    logger.info("Starting cache warmup...")
    import httpx
    from app.auth import create_access_token
    token = create_access_token({"sub": "admin"})
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=120, headers=headers) as client:
        for path in SLOW_ENDPOINTS:
            try:
                resp = await client.get(path)
                logger.info(f"Warmup %s -> %s (%sms)", path, resp.status_code, resp.headers.get("x-response-time", "?"))
            except Exception as e:
                logger.warning(f"Warmup %s failed: %s", path, e)
    logger.info("Cache warmup complete")


app = FastAPI(title="图书馆数据分析系统", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_request_time(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Response-Time"] = f"{process_time:.0f}"
    return response


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
app.include_router(intelligence.router)
app.include_router(statistics.router)
app.include_router(report.router)


@app.get("/")
async def root():
    return {"message": "图书馆数据分析系统 API"}


@app.get("/health")
async def health_check():
    import psutil
    from app.cache import cache
    
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

    try:
        import os
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        checks["memory"] = {
            "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
            "vms_mb": round(memory_info.vms / 1024 / 1024, 2)
        }
    except ImportError:
        checks["memory"] = "psutil not available"

    try:
        stats = cache.cache_stats() if hasattr(cache, 'cache_stats') else {}
        checks["cache"] = stats if stats else "available"
    except Exception as e:
        checks["cache"] = f"error: {str(e)}"

    try:
        uptime = psutil.boot_time()
        from datetime import datetime
        server_start_dt = datetime.fromtimestamp(uptime)
        uptime_seconds = int(time.time() - uptime)
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        if hours >= 24:
            days = hours // 24
            hours = hours % 24
            uptime_str = f"{days}天{hours}小时{minutes}分钟"
        elif hours > 0:
            uptime_str = f"{hours}小时{minutes}分钟{seconds}秒"
        else:
            uptime_str = f"{minutes}分钟{seconds}秒"
        checks["uptime"] = {
            "server_start": server_start_dt.isoformat(),
            "uptime_seconds": uptime_seconds,
            "uptime_human": uptime_str
        }
    except Exception:
        checks["uptime"] = "unknown"

    status = "healthy" if all(v == "ok" or (isinstance(v, dict) and "error" not in str(v)) for v in [checks.get("database")]) else "unhealthy"
    return {"status": status, "checks": checks}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
