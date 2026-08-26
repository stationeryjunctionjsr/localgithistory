import asyncio

from app.db.storage_factory import get_storage


async def run():
    tables = [
        "stockReservations",
        "productNotifications",
        "productReviews",
        "reviewClassifications",
        "bundles",
        "customerSegments",
        "faqSections",
        "aboutUs",
        "privacyPolicy",
        "commissionSettings",
        "valetAvailability",
        "valetPayoutSettings",
        "pincodeSearches",
        "availabilityRequests",
        "systemSettings",
    ]
    for t in tables:
        dao = get_storage(t)
        print(f"{t}: {type(dao)}")


asyncio.run(run())
