# Client payload to database audit

Audit date: 17 September 2026  
Scope: current backend source, all 55 router modules (236 state-changing routes), their request models, repositories, DAO write methods, and the MySQL schema. No source code was changed.

## Executive result

The application cannot currently start in the committed workspace. Importing `app.main` fails while Pydantic rebuilds `Product`: `Dict` is used but never imported in `app/models/product.py`. The configured Python version is 3.14.2.

This prevented live API/DB probes. The findings below are static, deterministic traces from request model to repository/DAO and are not merely type-style warnings. The separate `TrackingEvent.model_rebuild()` reference would cause a further import failure after the Product issue is corrected.

| Severity | Result |
| --- | --- |
| Blocker | No route can be served until the startup import failure is fixed. |
| Critical | Orders cannot be created; all user updates fail; product and brand creates fail; wishlist adds fail. |
| Critical | The common relational DAO wipes omitted fields during partial updates for ten table groups. |
| High | Several fields are accepted by route schemas but are silently discarded or stored in a format that cannot be read back. |

## Blockers and deterministic endpoint failures

| Endpoint group | Client values affected | Table(s) | What happens |
| --- | --- | --- | --- |
| All endpoints | Every request | All | `app.main` imports `Product`; `Product.model_rebuild()` cannot resolve `Dict`. The app fails before registering a route. `TrackingEvent.model_rebuild()` names a class that does not exist, giving a second startup blocker. |
| `POST /api/orders` | Every valid order payload, notably `shippingAddress` and `billingAddress` | `sj_orders`, `sj_order_items` | `MySQLOrderDAO.create()` references `update_data` and `existing`, neither of which exists in `create()`. It raises `NameError` before inserting the order header or items. |
| All user-profile/admin user write routes, including `/api/users/me/preferences`, `/me/deactivate`, `/me/duty-status`, approval/deactivation and UPI endpoints | Every `UserUpdate` payload | `sj_users`, `sj_user_addresses`, `sj_seller_pincodes`, `sj_seller_zones` | `MySQLUserDAO.update()` reads `update_data.gstNumber`, although `UserUpdate` defines `gstin`, then later binds undefined `is_active` and `approval_status`. Every normal Pydantic `UserUpdate` fails before commit. |
| `POST /api/products` | Every `ProductCreate` payload | `sj_products` and product child tables | `ProductRepository.create()` reads `categoryId`, `brandId`, `price`, `unit`, and `thumbnail`, which are absent from `ProductCreate`. It raises `AttributeError`; no product is saved. |
| `POST /api/brands` | `name`, `logoUrl`, `showInMobileHomepage`, `isActive` | `sj_brands` | The repository converts the request to `BrandInternalCreate`, which has no `logoUrl` or `imageUrl`; `MySQLBrandDAO.create()` then accesses those missing attributes. The create fails. |
| `PUT /api/brands/{id}` | All brand update values | `sj_brands` | The DAO builds `BrandInternalUpdate` then accesses nonexistent `slug`, `logoUrl`, and `imageUrl` fields. The update fails. |
| `POST /api/wishlist` | `productId` | `sj_wishlists`, `sj_wishlist_items` | `WishlistRepository.addItem()` receives a dict but uses `item._id` and `item.product`. That raises `AttributeError`; the item is not saved. |
| `PUT /api/search-tags/{id}` | Every `SearchTagUpdate` payload | `sj_search_tags` and child tables | `SearchTagRepository.update()` uses mapping unpacking (`{**update_data}`) on a Pydantic model. It raises `TypeError`; the request cannot persist. |
| `PUT /api/support-tickets/{id}/status` with `assignedTo` | `status`, `assignedTo` | `sj_support_tickets` | The router writes `update_data.assignedTo` on a dict, raising `AttributeError`. Even without that value, the repository reads `update_data.status` on a dict, also failing. |

## Common partial-update data-loss bug

`DynamicRelationalDAO.update()` converts a Pydantic update model using `data.__dict__`. Pydantic includes every optional field with a `None` default. The DAO merges that full dictionary over the stored record, then rewrites all scalar fields and replaces all child rows. Thus a request intended to update one property clears all omitted optional properties and child collections.

Affected live storage collections and tables:

| Routes using this path | Parent table | Child tables that may be replaced/cleared |
| --- | --- | --- |
| activity logging | `sj_activities` | `sj_activity_meta` |
| notification writes/read state | `sj_notifications` | `sj_notification_data` |
| return creation/status/valet updates | `sj_return_requests` | `sj_return_request_items`, `sj_return_valet_declines` |
| schemes | `sj_schemes` | `sj_scheme_roles` |
| contacts | `sj_contacts` | `sj_contact_addresses`, `sj_contact_phones` |
| device/push subscriptions | `sj_device_subscriptions` | `sj_device_keys`, `sj_device_sub_data` |
| collections | `sj_collections` | `sj_collection_pages`, `sj_collection_segments`, `sj_collection_rules`, `sj_collection_products` |
| search tags | `sj_search_tags` | all six `sj_search_tag_*` tables |
| delivery charges | `sj_delivery_charges` | `sj_delivery_charge_tiers` |
| default delivery charges | `sj_delivery_charge_defaults` | `sj_delivery_charge_def_tiers` |
| delivery zones | `sj_delivery_zones` | `sj_delivery_zone_pincodes` |

This affects direct Pydantic update endpoints such as collections, contacts, zones and delivery charges. Dict-based updates are safer only when they include the intended changed keys; they still replace child tables when called.

## Accepted-but-dropped or malformed values

| Endpoint/table | Accepted client value(s) | Outcome |
| --- | --- | --- |
| Contacts / `sj_contacts` | `socialMedia` | Present in `ContactCreate`/`ContactUpdate` and response schema, but absent from both the repository payload and table/child mappings. It is silently dropped on create and update. |
| Collections / `sj_collection_rules` | Structured `visibilityRules` | The persistence configuration declares a single text `rule` column, and the shared DAO converts the rule object to `str(...)`. On read it returns a string, not a rule object. The collection filtering code expects `pageType` and `pageIds`, while the request model defines `type` and `value`. Rule content cannot round-trip or drive visibility as intended. |
| Banners / `sj_banner_visibility_rules` | Structured `visibilityRules` | Rules are stringified on insert. Reads return strings while `BannerResponse` expects `VisibilityRuleSnippet` objects. The repository also looks for `pageType` in a model that declares `type`; position defaults to `homepage` and the submitted rule semantics are lost. |
| Categories / `sj_categories` | `showInMobileHomepage` | The API model accepts it, but category insert/update SQL never writes the existing `show_in_mobile_homepage` column and the row mapper never reads it. It always falls back to false. |
| Products / `sj_products` | `isExclusive`, `collection`, `catalogSellerIds`, `rating`, `reviews`, `sellers`, `mrpPerCase`, `quantityPerCase`, `brand` (after the create crash is repaired) | They are not consistently forwarded by `ProductRepository.create()` to `ProductInternalCreate`, and the product parent SQL does not store `isExclusive` or `collection`. `ProductUpdate` additionally accepts `isExclusive`, `collection`, and `variations`, but the repository puts unsupported names into a strict internal model, causing validation failure rather than a save. |
| Product variants / `sj_product_variants`, `sj_product_variant_combo_attrs` | Each variant's `sku`, `price`, `pricePerCase`, `stock`, `attributes` | DAO child writing uses dict membership/subscript operations against `VariantOption` Pydantic models. Membership evaluates false, so variants are written with null/zero values and no attributes (or fail for a model shape). |
| Cart / `sj_cart_items` | `variantAttributes` | Accepted and used for in-memory matching, but the table write contains only product, quantity, sell-as-case, bundle ID/name. Variant attributes are never persisted or reloaded. A variant cart item becomes indistinguishable after a request. |
| Cart `PUT /api/cart/{item_id}` and repeat add | `quantity` | The handlers index Pydantic cart items as dictionaries (`items[i]["quantity"]`). This raises instead of updating the existing item. |
| Wishlist / `sj_wishlist_items` | Item `quantity`, item ID, added timestamp | Only `product_id` exists in the DAO mapping and is reloaded as a raw string. Quantity and item metadata are discarded even if the wishlist add failure is fixed. |
| Delivery charge `POST /api/delivery-charges` | All body fields: pincode, state, city, district, amount, serviceability, tiers, etc. | The repository tests Pydantic models using `"field" in charge_data`, which is false. It constructs and stores an almost blank/default charge; the router's correct validation does not survive the repository boundary. |
| Default charge `POST /api/delivery-charges/default` | `tiers`, GST flags, urgent charge | The same membership check sees no tiers and rejects the payload. Even with a dict caller, the configured parent table maps only role flags/active status, not `deliveryChargeGst`, `deliveryChargeGstPercentage`, or `urgentDeliveryCharge`; tier mapping expects `min`/`max` but the public model sends `maxAmount`. |
| Delivery charge tables | `urgentDeliveryAvailable`, `urgentDeliveryCharge` | The delivery-charge public schema accepts them. The repository deliberately forces `urgentDeliveryAvailable=False`; the active scalar map has neither field, so neither is persisted. |
| `GET /api/delivery-zones/for-pincode` | `pincode` | The query joins `sj_delivery_zone_pincodes` using nonexistent `p.sj_delivery_zones_id`; the schema uses `parent_id`. The lookup fails at SQL level. |
| User create/update / `sj_users` | `alternatePhone`, `gstin`, `preferredLanguage`, `locationLink`, `deviceId`, `msg91Token`, `effectiveRole`; create also discards supplied role/approval in registration | The user table/DAO has no mapping for most of these values. `upiId`/`qrCodeUrl` columns are written but omitted from the returned `User` mapper. Registration explicitly forces role and approval, which is appropriate for security but must be documented as intentional override. |
| Support tickets / `sj_support_tickets` | `assignedTo` | Accepted by the status request model but never copied into `SupportTicketInternalUpdate`; it is ignored even if the dict/attribute crash is fixed. |

## Table and route coverage notes

* The direct MySQL tables for users, orders, products, brands, carts, wishlists, payments, categories, banners, bundles, sessions, seller records, and feature flags were traced through their active storage factory selection.
* The generated relational storage path was traced for activities, notifications, returns, schemes, contacts, device subscriptions, collections, search tags, delivery charges/defaults, and delivery zones. Its update bug is shared across all of those active groups.
* `coupons`, `deliverySlots`, and `events` use dedicated DAOs despite stale generated configurations; this was accounted for when assigning impact.
* Unknown request keys are rejected only by models that explicitly configure `extra='forbid'`. Many route-facing `BaseModel` classes leave Pydantic's default `extra='ignore'`; unknown client keys can therefore be silently removed before the repository layer. This includes the main product, contact, category, brand, banner, cart, wishlist, and several user request models.

## Evidence

* App import failure: `app/models/product.py:35,60`; second blocker: `app/models/tracking.py:54`.
* Order creation failure: `app/db/mysql_order_dao.py:347-358` inside `create()`.
* User update failure: `app/db/mysql_user_dao.py:263,282,313-314`.
* Shared destructive update: `app/db/mysql_generated_daos.py:195-201`; child deletion/replacement starts at line 104.
* Product create mismatch: `app/repositories/product_repository.py:978-989`.
* Brand mismatch: `app/db/mysql_brand_dao.py:112,156-157`.
* Wishlist dict/attribute mismatch: `app/repositories/wishlist_repository.py:24-30`.
* Search tag model-unpack failure: `app/repositories/search_tag_repository.py:91`.
* Support-ticket failures: `app/routers/support_tickets.py:176`, `app/repositories/support_ticket_repository.py:75-84`.
* Pincode join mismatch: `app/routers/delivery_zones.py:99` vs `schema.sql:646-652`.

## Recommended remediation order

1. Fix the two startup exceptions, then add an application-import test to CI.
2. Repair order creation and the user, product, brand, wishlist, search-tag, and ticket write paths; cover each with one create and one partial-update integration test.
3. Change `DynamicRelationalDAO.update()` to use `model_dump(exclude_unset=True, by_alias=True)` (or `model_fields_set`) and replace child data only when that child field was explicitly supplied.
4. Make every route-facing request model `extra='forbid'`, except deliberately extensible analytics payloads. Return a 422 rather than silently dropping unknown keys.
5. Define one canonical DTO and field naming scheme per resource. Update the database mapping and response mapper together, including structured JSON child values such as visibility rules and variants.

The above content shows the entire, complete file contents of the requested file.
