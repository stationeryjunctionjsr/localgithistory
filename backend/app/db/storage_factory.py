"""
Returns storage implementation for a collection. Oracle is the only supported storage backend.
DATABASE_URL must be set — JSON file fallback is disabled.
"""

from app.config.settings import settings
from typing import Any

from app.config.database import use_oracle
from app.db.mysql_banner_dao import MySQLBannerDAO
from app.db.mysql_brand_dao import MySQLBrandDAO
from app.db.mysql_cart_dao import MySQLCartDAO
from app.db.mysql_category_dao import MySQLCategoryDAO
from app.db.mysql_coupon_dao import MySQLCouponDAO
from app.db.mysql_feature_flag_dao import MySQLFeatureFlagDAO
from app.db.mysql_order_dao import MySQLOrderDAO
from app.db.mysql_payment_dao import MySQLPaymentDAO
from app.db.mysql_product_dao import MySQLProductDAO
from app.db.mysql_referral_settings_dao import MySQLReferralSettingsDAO
from app.db.mysql_saved_for_later_dao import MySQLSavedForLaterDAO
from app.db.mysql_session_dao import MySQLSessionDAO
from app.db.mysql_tracking_dao import MySQLTrackingDAO
from app.db.mysql_typed_doc_configs import TYPED_DOC_DAOS
from app.db.mysql_doc_store import MySQLDocStore
from app.db.mysql_user_dao import MySQLUserDAO
from app.db.mysql_generated_daos import GENERATED_DAOS
from app.db.mysql_wishlist_dao import MySQLWishlistDAO
from app.db.mysql_bundle_dao import MySQLBundleDAO
from app.db.mysql_customer_segment_dao import MySQLCustomerSegmentDAO
from app.db.mysql_faq_section_dao import MySQLFaqSectionDAO
from app.utils.file_storage import FileStorage

_MYSQL_DAO_COLLECTIONS = {
    "users": MySQLUserDAO,
    "products": MySQLProductDAO,
    "orders": MySQLOrderDAO,
    "carts": MySQLCartDAO,
    "wishlists": MySQLWishlistDAO,
    "sessions": MySQLSessionDAO,
    "coupons": MySQLCouponDAO,
    "brands": MySQLBrandDAO,
    "categories": MySQLCategoryDAO,
    "banners": MySQLBannerDAO,
    "featureFlags": MySQLFeatureFlagDAO,
    "tracking": MySQLTrackingDAO,
    "payments": MySQLPaymentDAO,
    "savedForLater": MySQLSavedForLaterDAO,
    "referralSettings": MySQLReferralSettingsDAO,
    "bundles": MySQLBundleDAO,
    "customerSegments": MySQLCustomerSegmentDAO,
    "faqSections": MySQLFaqSectionDAO,
    "valetAvailability": lambda: MySQLDocStore("sj_valet_availability"),
}


def get_storage(collection_name: str) -> Any:
    """
    Returns a storage object that implements: findAll, findById, findOne, create, update, delete.
    Use this in repositories instead of instantiating FileStorage directly.
    Oracle is the preferred backend — falls back to JSON file storage if not configured.
    """
    if not use_oracle():
        return FileStorage(collection_name)
    if collection_name in _MYSQL_DAO_COLLECTIONS:
        return _MYSQL_DAO_COLLECTIONS[collection_name]()
    if collection_name in GENERATED_DAOS:
        return GENERATED_DAOS[collection_name]
    if collection_name in TYPED_DOC_DAOS:
        return TYPED_DOC_DAOS[collection_name]
    return FileStorage(collection_name)
