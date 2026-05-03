import asyncio
import logging
from app.database import get_db_connection, release_db_connection

logger = logging.getLogger(__name__)


class MVRefresher:
    def __init__(self):
        self._pending = set()
        self._task = None

    def schedule_refresh(self, *view_names: str):
        for name in view_names:
            self._pending.add(name)
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._refresh())

    async def _refresh(self):
        await asyncio.sleep(1)
        views = list(self._pending)
        self._pending.clear()
        try:
            await asyncio.to_thread(self._refresh_sync, views)
        except Exception as e:
            logger.warning("物化视图刷新失败: %s", e)

    def _refresh_sync(self, views):
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                for view in views:
                    try:
                        cur.execute(f"REFRESH MATERIALIZED VIEW {view}")
                    except Exception as e:
                        logger.warning("刷新物化视图 %s 失败: %s", view, e)
            conn.commit()
        finally:
            release_db_connection(conn)


mv_refresher = MVRefresher()
