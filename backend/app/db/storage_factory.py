"""
Returns storage implementation for a collection. MySQL is the configured relational storage backend.
DATABASE_URL must be set.
"""

from app.config.settings import settings
from typing import Any

from app.config.database import use_oracle
from app.db.mysql_banner_dao import MySQLBannerDAO
from app.db.mysql_brand_dao import MySQLBrandDAO
from app.db.mysql_cart_dao import MySQLCartDAO
from app.db.mysql_category_dao import MySQLCategoryDAO
from app.db.mysql_feature_flag_dao import MySQLFeatureFlagDAO
from app.db.mysql_order_dao import MySQLOrderDAO
from app.db.mysql_payment_dao import MySQLPaymentDAO
from app.db.mysql_product_dao import MySQLProductDAO
from app.db.mysql_referral_settings_dao import MySQLReferralSettingsDAO
from app.db.mysql_saved_for_later_dao import MySQLSavedForLaterDAO
from app.db.mysql_session_dao import MySQLSessionDAO
from app.db.mysql_tracking_dao import MySQLTrackingDAO
from app.db.mysql_flat_daos import FLAT_DAOS
from app.db.mysql_doc_store import MySQLDocStore
from app.db.mysql_user_dao import MySQLUserDAO
from app.db.mysql_generated_daos import GENERATED_DAOS
from app.db.mysql_wishlist_dao import MySQLWishlistDAO
from app.db.mysql_bundle_dao import MySQLBundleDAO
from app.db.mysql_customer_segment_dao import MySQLCustomerSegmentDAO
from app.db.mysql_faq_section_dao import MySQLFaqSectionDAO
from app.db.mysql_valet_availability_dao import MySQLValetAvailabilityDAO
from app.db.mysql_commission_settings_dao import MySQLCommissionSettingsDAO
from app.db.mysql_seller_availability_dao import MySQLSellerAvailabilityDAO
from app.db.mysql_sub_order_dao import MySQLSubOrderDAO
from app.db.mysql_seller_request_dao import MySQLSellerRequestDAO
from app.db.mysql_ad_dao import MySQLAdDAO
from app.db.mysql_seller_payout_dao import MySQLSellerPayoutDAO
from app.db.mysql_events_dao import MySQLEventsDAO
from app.utils.file_storage import FileStorage



_MYSQL_DAO_COLLECTIONS = {
    "users": MySQLUserDAO,
    "products": MySQLProductDAO,
    "orders": MySQLOrderDAO,
    "carts": MySQLCartDAO,
    "wishlists": MySQLWishlistDAO,
    "sessions": MySQLSessionDAO,
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
    "valetAvailability": MySQLValetAvailabilityDAO,
    "commissionSettings": MySQLCommissionSettingsDAO,
    "sellerAvailability": MySQLSellerAvailabilityDAO,
    "subOrders": MySQLSubOrderDAO,
    "sellerRequests": MySQLSellerRequestDAO,
    "ads": MySQLAdDAO,
    "sellerPayouts": MySQLSellerPayoutDAO,
    "events": MySQLEventsDAO,
}


def get_storage(collection_name: str) -> Any:
    """
    Returns a storage object that implements: findAll, findById, findOne, create, update, delete.
    Use this in repositories instead of instantiating FileStorage directly.
    """
    if collection_name in _MYSQL_DAO_COLLECTIONS:
        return _MYSQL_DAO_COLLECTIONS[collection_name]()
    if collection_name in GENERATED_DAOS:
        return GENERATED_DAOS[collection_name]
    if collection_name in FLAT_DAOS:
        return FLAT_DAOS[collection_name]
    return FileStorage(collection_name)
