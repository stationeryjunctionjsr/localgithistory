import logging
"""
Lightweight in-memory TTL cache for the backend.

Usage:
    from app.utils.cache import ttl_cache

    # Bare decorator (uses default TTL)
    @ttl_cache(ttl=30)
    async def expensive():
        ...

    # Invalidate a specific key
    ttl_cache.invalidate("expensive")

Design goals:
  - Zero external dependencies (no Redis needed).
  - Safe for asyncio (no threading lock needed since CPython GIL protects dict ops).
  - Per-key TTL support.
  - Works for async functions only.
"""

import asyncio
import time
from typing import Any, Callable, Dict, Optional


class _CacheEntry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value: Any, ttl: float):
        self.value = value
        self.expires_at = time.monotonic() + ttl


class InMemoryTTLCache:
    """Global singleton TTL cache."""

    def __init__(self):
        self._store: Dict[str, _CacheEntry] = {}
        # Pending coroutines – prevents stampede when many requests arrive simultaneously.
        self._inflight: Dict[str, asyncio.Future] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ttl_cache(self, ttl: float = 30.0, key: Optional[str] = None):
        """
        Decorator factory.  Wraps an *async* function with TTL caching.

        Args:
            ttl:  Seconds before the cached value expires.
            key:  Override cache key (default: function qualified name).
        """
        import functools

        def decorator(func: Callable):
            base_key = key or f"{func.__module__}.{func.__qualname__}"

            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate a unique key based on arguments (ignoring Request/Response objects)
                def filter_arg(v):
                    return type(v).__name__ not in ("Request", "Response")

                filtered_args = tuple(a for a in args if filter_arg(a))
                filtered_kwargs = {k: v for k, v in kwargs.items() if filter_arg(v)}
                args_repr = f"{filtered_args}_{sorted(filtered_kwargs.items())}"
                cache_key = f"{base_key}:{hash(args_repr)}"

                entry = self._store[cache_key] if cache_key in self._store else None
                if entry and time.monotonic() < entry.expires_at:
                    return entry.value

                # Stampede protection: if a coroutine for this key is already
                # executing, await its result instead of launching a duplicate.
                if cache_key in self._inflight:
                    try:
                        return await asyncio.shield(self._inflight[cache_key])
                    except Exception as e:
                        logging.warning("cache: awaiting in-flight task for key %r failed; will fetch fresh: %s", cache_key, e, exc_info=e)  # fallthrough to fetch fresh

                loop = asyncio.get_event_loop()
                future: asyncio.Future = loop.create_future()
                self._inflight[cache_key] = future
                try:
                    result = await func(*args, **kwargs)
                    self._store[cache_key] = _CacheEntry(result, ttl)
                    future.set_result(result)
                    return result
                except Exception as exc:
                    future.set_exception(exc)
                    raise
                finally:
                    self._inflight.pop(cache_key, None)

            wrapper._cache_key = base_key  # expose for invalidation
            wrapper._cache = self
            return wrapper

        return decorator

    def invalidate(self, key_or_func) -> None:
        """Remove a key from the cache (accepts string key or decorated function)."""
        if callable(key_or_func):
            base_key = key_or_func._cache_key
            if not base_key:
                return
            keys_to_delete = [k for k in self._store if k == base_key or k.startswith(f"{base_key}:")]
            for k in keys_to_delete:
                self._store.pop(k, None)
        else:
            key = key_or_func
            self._store.pop(key, None)

    def get(self, key: str) -> Any:
        """Return cached value or None if missing/expired."""
        entry = self._store[key] if key in self._store else None
        if entry and time.monotonic() < entry.expires_at:
            return entry.value
        return None

    def set(self, key: str, value: Any, ttl: float = 30.0) -> None:
        """Manually set a cache entry."""
        self._store[key] = _CacheEntry(value, ttl)

    def clear(self) -> None:
        """Wipe all entries."""
        self._store.clear()

    def evict_expired(self) -> int:
        """Remove expired entries; returns eviction count."""
        now = time.monotonic()
        expired = [k for k, v in self._store.items() if now >= v.expires_at]
        for k in expired:
            del self._store[k]
        return len(expired)


# Global singleton
cache = InMemoryTTLCache()
