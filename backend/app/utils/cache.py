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

Single-VM mode (active):
  Each of the 4 Uvicorn workers has its own InMemoryTTLCache instance.
  invalidate() clears that worker's local copy only.  Other workers continue
  serving stale values until their TTL expires.  This is acceptable because
  all TTLs are short (≤ 60 s) and the stale window is bounded.

Multi-VM mode (commented out — see _start_invalidation_listener below):
  When REDIS_URL is set, every call to invalidate() also publishes the
  invalidated key to the Redis channel "sj:cache:invalidate".  A background
  listener task subscribes to that channel and calls the local invalidate()
  when a message arrives, propagating invalidations across all workers and VMs
  within milliseconds.
  To activate: call cache.start_invalidation_listener() from main.py lifespan.
"""

import asyncio
import time
from typing import Any, Callable, Dict, Optional


class _CacheEntry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value: 'T', ttl: float):
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

                loop = asyncio.get_running_loop()
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
        """Remove a key from the cache (accepts string key or decorated function).

        In single-VM mode this clears only the calling worker's local copy.
        In multi-VM mode (see _start_invalidation_listener), calling this also
        publishes the key to Redis so all other workers/VMs clear it too.
        """
        if callable(key_or_func):
            base_key = key_or_func._cache_key
            if not base_key:
                return
            keys_to_delete = [k for k in self._store if k == base_key or k.startswith(f"{base_key}:")]
            for k in keys_to_delete:
                self._store.pop(k, None)
            # ── MULTI-VM: publish invalidation so other workers/VMs clear too ──
            # _redis_publish(base_key)   # uncomment after activating listener below
        else:
            key = key_or_func
            self._store.pop(key, None)
            # ── MULTI-VM: publish invalidation so other workers/VMs clear too ──
            # _redis_publish(key)        # uncomment after activating listener below

    def get(self, key: str) -> 'T':
        """Return cached value or None if missing/expired."""
        entry = self._store[key] if key in self._store else None
        if entry and time.monotonic() < entry.expires_at:
            return entry.value
        return None

    def set(self, key: str, value: 'T', ttl: float = 30.0) -> None:
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

    # ── MULTI-VM CACHE INVALIDATION (commented out) ───────────────────────────
    #
    # HOW IT WORKS:
    #   invalidate() publishes the base_key to Redis channel "sj:cache:invalidate".
    #   Every worker on every VM subscribes to that channel.  When a message
    #   arrives each subscriber calls _local_invalidate(key) which clears only
    #   its own in-process store — no Redis round-trip for reads, just for the
    #   invalidation signal.
    #
    # WHY THIS IS NEEDED FOR MULTI-VM:
    #   With N VMs each running 4 workers, a product-price update on VM-1 clears
    #   VM-1's cache but VMs 2…N continue serving stale prices until their TTL
    #   expires (up to 60 s).  Redis pub/sub collapses that window to < 1 ms.
    #
    # PREREQUISITES:
    #   - pip install aioredis        (or redis[asyncio] ≥ 4.2)
    #   - REDIS_URL in environment    (already used by slowapi rate limiter)
    #   - No schema changes needed.
    #
    # TO ACTIVATE (3 steps):
    #   1. In lifespan() in main.py (inside the `if _is_elected_worker:` block):
    #          from app.utils.cache import cache
    #          asyncio.create_task(cache.start_invalidation_listener())
    #      NOTE: run in ALL workers, not just the elected one — every worker
    #      needs its own subscriber so it can clear its own local store.
    #      Move the create_task call outside the `if _is_elected_worker:` block.
    #   2. In invalidate() above, uncomment the two _redis_publish() lines.
    #   3. Remove this comment block.
    #
    # ── Implementation ────────────────────────────────────────────────────────

    # async def start_invalidation_listener(self) -> None:
    #     """Subscribe to Redis and clear local cache entries as invalidations arrive.
    #
    #     Call once per worker at startup (outside the elected-worker guard so
    #     every worker subscribes independently).
    #     """
    #     import os
    #     import aioredis
    #
    #     redis_url = os.environ.get("REDIS_URL", "")
    #     if not redis_url:
    #         logging.info("cache: REDIS_URL not set — cross-worker invalidation disabled")
    #         return
    #
    #     CHANNEL = "sj:cache:invalidate"
    #     while True:
    #         try:
    #             client = aioredis.from_url(redis_url, decode_responses=True)
    #             pubsub = client.pubsub()
    #             await pubsub.subscribe(CHANNEL)
    #             logging.info("cache: subscribed to Redis channel %r for invalidation broadcast", CHANNEL)
    #             async for message in pubsub.listen():
    #                 if message["type"] == "message":
    #                     key = message["data"]
    #                     self._local_invalidate(key)
    #                     logging.debug("cache: invalidated key %r via Redis pub/sub", key)
    #         except Exception as exc:
    #             logging.warning(
    #                 "cache: Redis invalidation listener error (%s); reconnecting in 5 s", exc
    #             )
    #             await asyncio.sleep(5)

    # def _local_invalidate(self, base_key: str) -> None:
    #     """Clear all entries matching base_key from this worker's local store.
    #     Called by the Redis subscriber — must NOT publish back to avoid loops.
    #     """
    #     keys_to_delete = [
    #         k for k in self._store
    #         if k == base_key or k.startswith(f"{base_key}:")
    #     ]
    #     for k in keys_to_delete:
    #         self._store.pop(k, None)

    # def _redis_publish(self, base_key: str) -> None:
    #     """Fire-and-forget publish to the invalidation channel.
    #     Silently drops the message if Redis is unavailable — the local
    #     invalidate() already ran, so this VM is consistent; others will
    #     catch up at their next TTL expiry.
    #     """
    #     import os
    #     import asyncio as _asyncio
    #     import aioredis
    #
    #     async def _pub():
    #         try:
    #             redis_url = os.environ.get("REDIS_URL", "")
    #             if not redis_url:
    #                 return
    #             client = aioredis.from_url(redis_url, decode_responses=True)
    #             await client.publish("sj:cache:invalidate", base_key)
    #             await client.aclose()
    #         except Exception as exc:
    #             logging.debug("cache: failed to publish invalidation for %r: %s", base_key, exc)
    #
    #     try:
    #         loop = _asyncio.get_running_loop()
    #         loop.create_task(_pub())
    #     except RuntimeError:
    #         pass  # No running loop — invalidation publish skipped
    #
    # ─────────────────────────────────────────────────────────────────────────────


# Global singleton
cache = InMemoryTTLCache()
