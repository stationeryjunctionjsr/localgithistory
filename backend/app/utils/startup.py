import asyncio
import os
from sqlalchemy import text
from starlette.responses import Response
from app.utils.logger import logger

async def deferred_segment_seed():
    """Seeds the system customer segments after a delay."""
    await asyncio.sleep(30)
    try:
        from app.routers.customer_segments import seed_system_segments
        await seed_system_segments()
    except Exception as e:
        logger.warning("Could not run deferred seed customer segments task: %s", e)

async def stock_cleanup_loop():
    """Periodically cleans up expired stock reservations."""
    from app.repositories.stock_reservation_repository import stock_reservation_repository
    logger.info("Stock reservation cleanup task started")
    while True:
        try:
            await stock_reservation_repository.cleanup_expired()
        except Exception as e:
            logger.error("Error in stock reservation cleanup: %s", e)
        await asyncio.sleep(60)

async def warm_critical_caches():
    """Pre-warms DB connection pool and critical API caches."""
    await asyncio.sleep(5)
    try:
        from app.config.database import get_async_session_factory
        factory = get_async_session_factory()
        
        if factory:
            async def warm_conn():
                async with factory() as session:
                    await session.execute(text("SELECT 1"))
            
            _pool_size = int(os.getenv("DB_POOL_SIZE", 5))
            _max_overflow = int(os.getenv("DB_MAX_OVERFLOW", 2))
            _total_slots = _pool_size + _max_overflow
            await asyncio.gather(*[warm_conn() for _ in range(_total_slots)])
            logger.info("DB connection pool pre-warmed (%d slots)", _total_slots)

        # Pre-warm routers
        from app.routers.products import get_public_products, get_public_product
        
        await get_public_products(
            response=Response(), category=None, categories=None, subCategory=None, search=None,
            brand=None, collection=None, popularity=None, minDiscount=None, minPrice=None,
            maxPrice=None, availability=None, page=1, limit=50, role="customer",
            categoryTag=None, sort=None, includeFacets=True, skinny=False
        )
        await get_public_products(
            response=Response(), category=None, categories=None, subCategory=None, search="test",
            brand=None, collection=None, popularity=None, minDiscount=None, minPrice=None,
            maxPrice=None, availability=None, page=1, limit=50, role="customer",
            categoryTag=None, sort=None, includeFacets=False, skinny=True
        )

        products_res = await get_public_products(
            response=Response(), category=None, categories=None, subCategory=None, search=None,
            brand=None, collection=None, popularity=None, minDiscount=None, minPrice=None,
            maxPrice=None, availability=None, page=1, limit=1, role="customer",
            categoryTag=None, sort=None, includeFacets=False, skinny=True
        )
        try:
            products_list = products_res.products if products_res.products is not None else []
            if products_list:
                p0 = products_list[0]
                p0_id = getattr(p0, "id", None)
                if p0_id:
                    await get_public_product(str(p0_id), role="customer", response=Response())
        except Exception as e:
            logger.warning("Failed to warm up get_public_product: %s", e)

        from app.routers.banners import get_public_banners
        await get_public_banners(position=None, targetAudience=None, pageType=None, pageId=None, userRole="guest")

        from app.routers.categories import get_public_categories
        await get_public_categories(forHomepage=False)

        from app.routers.brands import get_public_brands
        await get_public_brands(forHomepage=False)

        try:
            from app.routers.recommendations import get_recommendations
            await get_recommendations(current_user=None)
        except Exception as re:
            logger.warning("Failed to warm up recommendations: %s", re)

        try:
            from app.routers.delivery_charges import check_serviceability
            await check_serviceability("110001")
        except Exception as e:
            logger.warning("Failed to warm up check-serviceability: %s", e)

        logger.info("Critical API caches pre-warmed")
    except Exception as e:
        logger.warning("Cache warm-up incomplete: %s", e)
