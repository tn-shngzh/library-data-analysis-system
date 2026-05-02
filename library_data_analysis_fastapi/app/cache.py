import threading
import time
import logging
from typing import Any, Optional


class MemoryCache:
    def __init__(self):
        self._store: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._logger = logging.getLogger(__name__)
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def _cleanup_loop(self):
        while True:
            time.sleep(60)
            self._remove_expired()
            self._logger.info(
                "缓存统计 - 命中: %d, 未命中: %d, 命中率: %.1f%%, 缓存条目: %d",
                self._hits, self._misses,
                (self._hits / (self._hits + self._misses) * 100) if (self._hits + self._misses) > 0 else 0,
                len(self._store)
            )

    def _remove_expired(self):
        now = time.time()
        with self._lock:
            expired_keys = [k for k, v in self._store.items() if v["expires_at"] <= now]
            for k in expired_keys:
                del self._store[k]

    def cache_get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None
            if entry["expires_at"] <= time.time():
                del self._store[key]
                self._misses += 1
                return None
            self._hits += 1
            return entry["value"]

    def cache_set(self, key: str, value: Any, ttl: int):
        with self._lock:
            self._store[key] = {"value": value, "expires_at": time.time() + ttl}

    def cache_invalidate(self, prefix: str):
        with self._lock:
            keys_to_remove = [k for k in self._store if k.startswith(prefix)]
            for k in keys_to_remove:
                del self._store[k]

    def cache_clear(self):
        with self._lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0

    def get_stats(self) -> dict:
        with self._lock:
            total = self._hits + self._misses
            return {
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(self._hits / total * 100, 1) if total > 0 else 0,
                "entries": len(self._store)
            }


cache = MemoryCache()
