"""
Returns storage implementation for a collection. Oracle is the only supported storage backend.
DATABASE_URL must be set — JSON file fallback is disabled.
"""

from app.config.settings import settings
from typing import Any

from app.config.database import use_oracle
from app.db.banner_dao import OracleBannerDAO
from app.db.brand_dao import OracleBrandDAO
from app.db.cart_dao import OracleCartDAO
from app.db.category_dao import OracleCategoryDAO
from app.db.coupon_dao import OracleCouponDAO
from app.db.feature_flag_dao import OracleFeatureFlagDAO
from app.db.order_dao import OracleOrderDAO
from app.db.payment_dao import OraclePaymentDAO
from app.db.product_dao import OracleProductDAO
from app.db.referral_settings_dao import OracleReferralSettingsDAO
from app.db.saved_for_later_dao import OracleSavedForLaterDAO
from app.db.session_dao import OracleSessionDAO
from app.db.tracking_dao import OracleTrackingDAO
from app.db.typed_doc_configs import TYPED_DOC_DAOS
from app.db.doc_store import OracleDocStore
from app.db.user_dao import OracleUserDAO
from app.db.wishlist_dao import OracleWishlistDAO
from app.utils.file_storage import FileStorage

_ORACLE_DAO_COLLECTIONS = {
    "users": OracleUserDAO,
    "products": OracleProductDAO,
    "orders": OracleOrderDAO,
    "carts": OracleCartDAO,
    "wishlists": OracleWishlistDAO,
    "sessions": OracleSessionDAO,
    "coupons": lambda: OracleDocStore("sj_coupons", doc_column="payload"),
    "brands": OracleBrandDAO,
    "categories": OracleCategoryDAO,
    "banners": OracleBannerDAO,
    "featureFlags": OracleFeatureFlagDAO,
    "tracking": OracleTrackingDAO,
    "payments": OraclePaymentDAO,
    "savedForLater": OracleSavedForLaterDAO,
    "referralSettings": OracleReferralSettingsDAO,
    "stockReservations": lambda: OracleDocStore("sj_stock_reservations"),
    "productNotifications": lambda: OracleDocStore("sj_product_notifications"),
    "productReviews": lambda: OracleDocStore("sj_product_reviews"),
    "reviewClassifications": lambda: OracleDocStore("sj_review_classifications"),
    "bundles": lambda: OracleDocStore("sj_bundles"),
    "customerSegments": lambda: OracleDocStore("sj_customer_segments", doc_column="payload"),
    "faqSections": lambda: OracleDocStore("sj_faq_sections"),
    "aboutUs": lambda: OracleDocStore("sj_about_us"),
    "privacyPolicy": lambda: OracleDocStore("sj_privacy_policy"),
}


def get_storage(collection_name: str) -> Any:
    """
    Returns a storage object that implements: findAll, findById, findOne, create, update, delete.
    Use this in repositories instead of instantiating FileStorage directly.
    Oracle is the preferred backend — falls back to JSON file storage if not configured.
    """
    if not use_oracle():
        return FileStorage(collection_name)
    if collection_name in _ORACLE_DAO_COLLECTIONS:
        return _ORACLE_DAO_COLLECTIONS[collection_name]()
    if collection_name in TYPED_DOC_DAOS:
        return TYPED_DOC_DAOS[collection_name]
    return FileStorage(collection_name)
