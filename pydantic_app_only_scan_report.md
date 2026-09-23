# Pydantic Anti-Pattern Scan Report (app/ only)

## hasattr (2 hits)
`
db\mysql_flat_daos.py:1119: if hasattr(data, k) and getattr(data, k) is not None:
db\mysql_generated_daos.py:183: if hasattr(data, api_k) and getattr(data, api_k) is not None:
`

## getattr (6 hits)
`
db\mysql_flat_base_dao.py:115: val = getattr(data, api_key, None) if not isinstance(data, dict) else data.get(api_key)
db\mysql_flat_daos.py:1119: if hasattr(data, k) and getattr(data, k) is not None:
db\mysql_flat_daos.py:1120: kwargs[k] = getattr(data, k)
db\mysql_flat_daos.py:1122: kwargs[k] = getattr(existing, k)
db\mysql_generated_daos.py:183: if hasattr(data, api_k) and getattr(data, api_k) is not None:
db\mysql_generated_daos.py:185: params[f"s_{api_k}"] = getattr(data, api_k)
`

## dict_usage (0 hits)

## dot_get (345 hits)
`
main.py:504: @app.get("/")
db\mysql_activities_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
db\mysql_activities_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
db\mysql_categoryTags_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
db\mysql_categoryTags_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
db\mysql_coachMarks_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
db\mysql_coachMarks_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
db\mysql_collections_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
db\mysql_collections_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
db\mysql_contacts_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
db\mysql_contacts_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
db\mysql_coupons_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
db\mysql_coupons_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
db\mysql_customer_segment_dao.py:45: if out.get(k) is not None:
db\mysql_customer_segment_dao.py:114: "min_avg_order_value": filters.get("minAverageOrderValue"),
db\mysql_customer_segment_dao.py:115: "max_avg_order_value": filters.get("maxAverageOrderValue"),
db\mysql_customer_segment_dao.py:116: "start_date": filters.get("startDate"),
db\mysql_customer_segment_dao.py:117: "end_date": filters.get("endDate"),
db\mysql_customer_segment_dao.py:118: "min_order_freq": filters.get("minOrderFrequency"),
db\mysql_customer_segment_dao.py:119: "max_order_freq": filters.get("maxOrderFrequency"),
db\mysql_customer_segment_dao.py:120: "state": filters.get("state"),
db\mysql_customer_segment_dao.py:121: "district": filters.get("district"),
db\mysql_customer_segment_dao.py:122: "app_user": filters.get("appUser"),
db\mysql_customer_segment_dao.py:123: "behavior": filters.get("behavior"),
db\mysql_customer_segment_dao.py:124: "role": filters.get("role"),
db\mysql_deliveryChargeDefaults_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
db\mysql_deliveryChargeDefaults_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
db\mysql_deliveryCharges_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
db\mysql_deliveryCharges_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
db\mysql_deliverySlots_dao.py:45: db_col = query_map.get(k, k)
db\mysql_deliverySlots_dao.py:57: return self._map_to_schema(row, children_map.get(int(row.id), {}))
db\mysql_deliverySlots_dao.py:72: db_col = query_map.get(k, k)
db\mysql_deliverySlots_dao.py:87: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
db\mysql_deliveryZones_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
db\mysql_deliveryZones_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
db\mysql_deviceSubscriptions_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
db\mysql_deviceSubscriptions_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
db\mysql_flat_base_dao.py:115: val = getattr(data, api_key, None) if not isinstance(data, dict) else data.get(api_key)
db\mysql_notifications_dao.py:55: return self._map_to_schema(row, children_map.get(int(row.id), {}))
db\mysql_notifications_dao.py:85: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
db\mysql_orderFeedback_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
db\mysql_orderFeedback_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
db\mysql_promoStrips_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
db\mysql_promoStrips_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
db\mysql_pushNotifications_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
db\mysql_pushNotifications_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
db\mysql_returnRequests_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
db\mysql_returnRequests_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
db\mysql_returnSettings_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
db\mysql_returnSettings_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
db\mysql_schemes_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
db\mysql_schemes_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
db\mysql_searchTags_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
db\mysql_searchTags_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
db\mysql_supportTickets_dao.py:56: return self._map_to_schema(row, children_map.get(int(row.id), {}))
db\mysql_supportTickets_dao.py:86: return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]
repositories\collection_repository.py:19: user_role = query.get("userRole", "guest")
repositories\collection_repository.py:20: target_page_type = query.get("pageType") or query.get("visiblePage")
repositories\collection_repository.py:21: target_page_id = query.get("pageId")
repositories\collection_repository.py:51: rule_pg = rule.get("pageType", "")
repositories\collection_repository.py:59: page_ids = rule.get("pageIds", [])
repositories\content_repository.py:22: existing = await self.get()
repositories\content_repository.py:60: existing = await self.get()
repositories\google_review_repository.py:42: response = await client.get(url, headers=headers)
repositories\google_review_repository.py:45: rating = data.get('rating')
repositories\google_review_repository.py:46: count = data.get('userRatingCount')
repositories\google_review_repository.py:58: rating_val = res.get("rating", 5.0)
repositories\google_review_repository.py:59: count_val = res.get("user_ratings_total", "421")
repositories\google_review_repository.py:87: response = await client.get(self.url, headers=headers)
repositories\payment_repository.py:179: entryId=e.get("entryId"),
repositories\payment_repository.py:180: amount=e.get("amount", 0),
repositories\payment_repository.py:181: paymentMethod=e.get("paymentMethod"),
repositories\payment_repository.py:182: paidAt=e.get("paidAt"),
repositories\payment_repository.py:183: image=e.get("image"),
repositories\payment_repository.py:184: notes=e.get("notes"),
repositories\payment_repository.py:185: verified=e.get("verified", False),
repositories\payment_repository.py:186: createdAt=e.get("createdAt")
repositories\payment_repository.py:243: entryId=e.get("entryId"),
repositories\payment_repository.py:244: amount=e.get("amount", 0),
repositories\payment_repository.py:245: paymentMethod=e.get("paymentMethod"),
repositories\payment_repository.py:246: paidAt=e.get("paidAt"),
repositories\payment_repository.py:247: image=e.get("image"),
repositories\payment_repository.py:248: notes=e.get("notes"),
repositories\payment_repository.py:249: verified=e.get("verified", False),
repositories\payment_repository.py:250: createdAt=e.get("createdAt")
routers\ads.py:23: @router.get("/summary", response_model=AdSummaryResponse)
routers\ads.py:44: @router.get("/", response_model=List[Ad])
routers\analytics.py:342: @router.get("/kpi", response_model=KPIMetricsResponse)
routers\analytics.py:358: @router.get("/dashboard-data", response_model=DashboardDataResponse)
routers\analytics.py:373: @router.get("/reports/bundle-performance", response_model=List[UserOrderStatsResponse])
routers\analytics.py:385: @router.get("/sales-over-time", response_model=List[SalesOverTimeResponse])
routers\analytics.py:403: @router.get("/sales-breakdown", response_model=SalesBreakdownResponse)
routers\analytics.py:419: @router.get("/average-order-value", response_model=List[AverageOrderValueResponse])
routers\analytics.py:436: @router.get("/sales-by-channel", response_model=List[ItemsByUserTypeResponse])
routers\analytics.py:452: @router.get("/sales-by-product", response_model=List[SalesByProductResponse])
routers\analytics.py:470: @router.get("/conversion-rate", response_model=ConversionRateResponse)
routers\analytics.py:487: @router.get("/conversion-breakdown", response_model=ConversionRateResponse)
routers\analytics.py:503: @router.get("/checkout-funnel", response_model=CheckoutFunnelResponse)
routers\analytics.py:519: @router.get("/sessions-by-device", response_model=List[SessionsByDeviceResponse])
routers\analytics.py:535: @router.get("/sessions-by-location", response_model=List[SessionsByLocationResponse])
routers\analytics.py:551: @router.get("/all-user-engagement", response_model=AllUserEngagementResponse)
routers\analytics.py:565: @router.get("/products-sell-through", response_model=List[ProductsSellThroughResponse])
routers\analytics.py:583: @router.get("/customer-cohort", response_model=List[CustomerCohortResponse])
routers\analytics.py:599: @router.get("/sessions-by-landing-page", response_model=List[SessionsByLandingPageResponse])
routers\analytics.py:615: @router.get("/user-engagement", response_model=UserEngagementResponse)
routers\analytics.py:631: @router.get("/user-engagement/{user_id}", response_model=UserEngagementResponse)
routers\analytics.py:651: @router.get("/reports/top-users", response_model=List[TopUsersReportResponse])
routers\analytics.py:664: @router.get("/reports/user-order-stats", response_model=List[UserOrderStatsResponse])
routers\analytics.py:676: @router.get("/reports/items-by-user-type", response_model=List[ItemsByUserTypeResponse])
routers\analytics.py:687: @router.get("/reports/summary", response_model=AllReportsSummaryResponse)
routers\analytics.py:698: @router.get("/reports/returns", response_model=List[ReturnsReportResponse])
routers\analytics.py:715: @router.get("/reports/payment-methods", response_model=List[PaymentMethodsReportResponse])
routers\analytics.py:732: @router.get("/reports/revenue-by-category", response_model=List[PaymentMethodsReportResponse])
routers\analytics.py:750: @router.get("/reports/inventory-alerts", response_model=List[RevenueByCategoryResponse])
routers\analytics.py:764: @router.get("/reports/fulfillment-time", response_model=List[InventoryAlertResponse])
routers\analytics.py:781: @router.get("/reports/coupon-usage", response_model=List[FulfillmentTimeReportResponse])
routers\analytics.py:798: @router.get("/reports/sales-by-location", response_model=List[CouponUsageReportResponse])
routers\analytics.py:816: @router.get("/reports/new-vs-returning", response_model=List[SalesByLocationReportResponse])
routers\analytics.py:832: @router.get("/reports/items-bought-together", response_model=List[NewVsReturningCustomerSalesResponse])
routers\analytics.py:849: @router.get("/reports/sales-by-device", response_model=List[ItemsBoughtTogetherResponse])
routers\analytics.py:865: @router.get("/reports/top-returned-products", response_model=List[SalesByDeviceReportResponse])
routers\analytics.py:883: @router.get("/reports/inventory-value-by-category", response_model=List[TopReturnedProductsResponse])
routers\analytics.py:898: @router.get("/reports/sessions-over-time", response_model=List[InventoryValueByCategoryResponse])
routers\analytics.py:914: @router.get("/reports/visitors-now", response_model=List[SessionsOverTimeResponse])
routers\analytics.py:926: @router.get("/reports/searches-no-clicks", response_model=List[VisitorsNowResponse])
routers\analytics.py:942: @router.get("/reports/search-conversion", response_model=List[SearchesNoClicksResponse])
routers\analytics.py:958: @router.get("/reports/bounce-rate", response_model=List[SearchConversionResponse])
routers\analytics.py:974: @router.get("/reports/rfm-segments", response_model=List[BounceRateResponse])
routers\analytics.py:990: @router.get("/reports/customer-frequency", response_model=List[RFMSegmentsResponse])
routers\analytics.py:1008: @router.get("/reports/net-sales", response_model=List[CustomerFrequencyResponse])
routers\analytics.py:1026: @router.get("/reports/sales-heatmap", response_model=List[NetSalesResponse])
routers\analytics.py:1044: @router.get("/reports/inventory-runway", response_model=List[SalesHeatmapResponse])
routers\analytics.py:1064: @router.get("/reports/sales-by-channel-detailed", response_model=List[InventoryRunwayResponse])
routers\analytics.py:1080: @router.get("/reports/discounts-audit", response_model=List[DiscountsAuditResponse])
routers\analytics.py:1098: @router.get("/reports/products-pct-sold", response_model=List[DiscountsAuditResponse])
routers\auth.py:577: @router.get("/me", response_model=UserResponse)
routers\availability_requests.py:79: @router.get("", response_model=AvailabilityRequestListResponse)
routers\availability_requests.py:80: @router.get("/", response_model=AvailabilityRequestListResponse)
routers\banners.py:16: @router.get("/public", response_model=List[BannerResponse])
routers\banners.py:58: @router.get("", response_model=List[BannerResponse])
routers\banners.py:59: @router.get("/", response_model=List[BannerResponse])
routers\banners.py:111: @router.get("/{banner_id}", response_model=BannerResponse)
routers\brands.py:16: @router.get("/public", response_model=List[BrandResponse])
routers\brands.py:36: @router.get("", response_model=List[BrandResponse])
routers\brands.py:37: @router.get("/", response_model=List[BrandResponse])
routers\bundles.py:175: @router.get("/search", response_model=BundlesListResponse)
routers\bundles.py:270: @router.get("", response_model=BundlesListResponse)
routers\bundles.py:271: @router.get("/", response_model=BundlesListResponse)
routers\bundles.py:289: @router.get("/product/{product_id}", response_model=List[BundleResponse])
routers\bundles.py:302: enriched.sort(key=lambda x: x.get("salesCount", 0), reverse=True)
routers\bundles.py:309: @router.get("/admin/all", response_model=BundlesListResponse)
routers\bundles.py:327: @router.get("/{bundle_id}", response_model=BundleResponse)
routers\cart.py:33: @router.get("", response_model=CartResponse)
routers\cart.py:34: @router.get("/", response_model=CartResponse)
routers\cart.py:369: @router.get("/saved-for-later", response_model=SavedForLaterResponse)
routers\categories.py:107: @router.get("/available", response_model=List[Category])
routers\categories.py:126: @router.get("/public", response_model=List[Category])
routers\categories.py:152: @router.get("/public/tags/{tag_name}/categories", response_model=List[Category])
routers\categories.py:179: @router.get("/public/tags/{tag_name}/brands", response_model=List[Any])
routers\categories.py:235: @router.get("", response_model=List[Category])
routers\categories.py:236: @router.get("/", response_model=List[Category])
routers\categories.py:264: @router.get("/{category_id}", response_model=Category)
routers\category_tags.py:34: @router.get("", response_model=List[CategoryTagResponse])
routers\category_tags.py:35: @router.get("/")
routers\category_tags.py:46: @router.get("/active", response_model=List[CategoryTagResponse])
routers\coach_marks.py:16: @router.get("", response_model=List[CoachMarkResponse])
routers\coach_marks.py:17: @router.get("/", response_model=List[CoachMarkResponse])
routers\coach_marks.py:23: @router.get("/{id}", response_model=CoachMarkResponse)
routers\collections.py:39: @router.get("/public", response_model=List[CollectionResponse])
routers\collections.py:53: @router.get("", response_model=List[CollectionResponse])
routers\collections.py:54: @router.get("/", response_model=List[CollectionResponse])
routers\collections.py:61: @router.get("/{collection_id}/products", response_model=List[ProductResponse])
routers\collections.py:74: @router.get("/{collection_id}", response_model=CollectionResponse)
routers\commission.py:232: @router.get("/tiers", response_model=TiersResponse)
routers\commission.py:297: @router.get("/sellers", response_model=List[SellerCommissionInfo])
routers\commission.py:378: @router.get("/calculate", response_model=CommissionPreviewResponse)
routers\contacts.py:16: @router.get("", response_model=List[ContactResponse])
routers\contacts.py:17: @router.get("/", response_model=List[ContactResponse])
routers\contacts.py:28: @router.get("/public", response_model=List[ContactResponse])
routers\contacts.py:36: @router.get("/{contact_id}", response_model=ContactResponse)
routers\content_pages.py:100: @router.get("/faq/public", response_model=List[FAQSectionResponse])
routers\content_pages.py:106: @router.get("/faq", response_model=List[FAQSectionResponse])
routers\content_pages.py:137: @router.get("/about/public", response_model=AboutUsResponse)
routers\content_pages.py:140: doc = await about_repository.get()
routers\content_pages.py:144: @router.get("/about", response_model=AboutUsResponse)
routers\content_pages.py:146: doc = await about_repository.get()
routers\content_pages.py:160: @router.get("/privacy/public", response_model=PrivacyPolicyResponse)
routers\content_pages.py:163: doc = await privacy_repository.get()
routers\content_pages.py:167: @router.get("/privacy", response_model=PrivacyPolicyResponse)
routers\content_pages.py:169: doc = await privacy_repository.get()
routers\content_pages.py:185: @router.get("/privacy/history", response_model=List[PrivacyPolicyResponse])
routers\content_pages.py:188: doc = await privacy_repository.get()
routers\coupons.py:16: @router.get("", response_model=List[CouponResponse])
routers\coupons.py:17: @router.get("/", response_model=List[CouponResponse])
routers\coupons.py:27: @router.get("/validate/{code}", response_model=CouponValidationResponse)
routers\coupons.py:88: @router.get("/{coupon_id}", response_model=CouponResponse)
routers\customer_segments.py:50: @router.get("", response_model=List[CustomerSegmentResponse])
routers\customer_segments.py:51: @router.get("/", response_model=List[CustomerSegmentResponse])
routers\customer_segments.py:57: @router.get("/{segment_id}", response_model=CustomerSegmentResponse)
routers\delivery_charges.py:75: @router.get("", response_model=List[DeliveryChargeResponse])
routers\delivery_charges.py:76: @router.get("/", response_model=List[DeliveryChargeResponse])
routers\delivery_charges.py:82: @router.get("/default", response_model=DefaultDeliveryChargeResponse)
routers\delivery_charges.py:90: @router.get("/location", response_model=LocationChargeResponse)
routers\delivery_charges.py:124: @router.get("/serviceable-pincodes", response_model=List[str])
routers\delivery_charges.py:137: @router.get("/check-serviceability", response_model=ServiceabilityResponse)
routers\delivery_charges.py:274: @router.get("/{charge_id}", response_model=DeliveryChargeResponse)
routers\delivery_slots.py:133: @router.get("", response_model=List[DeliverySlotConfigResponse])
routers\delivery_slots.py:134: @router.get("/", response_model=List[DeliverySlotConfigResponse])
routers\delivery_slots.py:153: @router.get("/available", response_model=List[AvailableSlotItem])
routers\delivery_slots.py:238: @router.get("/dates-with-slots", response_model=DatesWithSlotsResponse)
routers\delivery_zones.py:85: @router.get("/for-pincode", response_model=DeliveryZoneResponse)
routers\delivery_zones.py:125: @router.get("", response_model=List[DeliveryZoneResponse])
routers\delivery_zones.py:126: @router.get("/", response_model=List[DeliveryZoneResponse])
routers\delivery_zones.py:156: @router.get("/{zone_id}", response_model=DeliveryZoneResponse)
routers\feature_flags.py:43: @router.get("", response_model=List[FeatureFlagItem])
routers\feature_flags.py:44: @router.get("/", response_model=List[FeatureFlagItem])
routers\feature_flags.py:55: @router.get("/enabled", response_model=List[FeatureFlagItem])
routers\feature_flags.py:67: @router.get("/{flag_id}", response_model=FeatureFlagItem)
routers\feature_flags.py:82: @router.get("/check/{flag_id}", response_model=FeatureFlagItem)
routers\google_reviews.py:22: @router.get("/rating", response_model=GoogleReviewResponse)
routers\health.py:38: @router.get("/health/live", response_model=LivenessResponse)
routers\health.py:44: @router.get("/health", response_model=HealthResponse)
routers\health.py:45: @router.get("/health/ready", response_model=HealthResponse)
routers\media.py:39: @router.get("/media", response_class=RedirectResponse)
routers\notifications.py:32: @router.get("", response_model=List[NotificationResponse])
routers\notifications.py:33: @router.get("/")
routers\notifications.py:64: @router.get("/unread-count", response_model=UnreadCountResponse)
routers\orders.py:387: @router.get("", response_model=PaginatedOrdersResponse)
routers\orders.py:388: @router.get("/", response_model=PaginatedOrdersResponse)
routers\orders.py:439: @router.get("/{order_id}", response_model=PopulatedOrderResponse)
routers\orders.py:2467: @router.get("/valet/pending", response_model=List[Order])
routers\orders.py:3092: @router.get("/{order_id}/invoice", response_class=FileResponse)
routers\orders.py:3135: @router.get("/seller-orders", response_model=PaginatedSubOrdersResponse)
routers\orders.py:3158: @router.get("/seller-orders/{sub_order_id}", response_model=SubOrder)
routers\orders.py:3225: @router.get("/admin/sub-orders", response_model=PaginatedSubOrdersResponse)
routers\order_feedback.py:55: @router.get("/eligible", response_model=EligibleFeedbackResponse)
routers\order_feedback.py:110: @router.get("/order/{order_id}", response_model=OrderFeedbackResponse)
routers\order_feedback.py:127: @router.get("", response_model=List[OrderFeedbackResponse])
routers\order_feedback.py:128: @router.get("/", response_model=List[OrderFeedbackResponse])
routers\page_info.py:44: @router.get("/{page_id}", response_model=PageInfoResponse)
routers\page_info.py:71: @router.get("", response_model=List[PageInfoResponse])
routers\page_info.py:72: @router.get("/", response_model=List[PageInfoResponse])
routers\payments.py:51: @router.get("/dues", response_model=DuesResponse)
routers\payments.py:214: @router.get("", response_model=List[PaymentResponse])
routers\payments.py:215: @router.get("/", response_model=List[PaymentResponse])
routers\payments.py:254: @router.get("/{payment_id}", response_model=PaymentResponse)
routers\pincodes.py:27: @router.get("/states", response_model=List[str])
routers\pincodes.py:35: @router.get("/districts", response_model=List[str])
routers\pincodes.py:45: @router.get("/pincodes", response_model=List[str])
routers\pincodes.py:58: @router.get("/{pincode}", response_model=Dict[str, str])
routers\pincode_searches.py:14: @router.get("", response_model=List[PincodeSearchResponse])
routers\pincode_searches.py:15: @router.get("/", response_model=List[PincodeSearchResponse])
routers\pincode_searches.py:36: @router.get("/stats", response_model=PincodeSearchStatsResponse)
routers\products.py:294: @router.get("/export-csv", response_class=StreamingResponse)
routers\products.py:413: @router.get("/suggest", response_model=SearchSuggestResponse)
routers\products.py:615: @router.get("/public", response_model=PaginatedProductResponse)
routers\products.py:732: @router.get("/public/{product_id}", response_model=ProductResponse)
routers\products.py:761: @router.get("", response_model=PaginatedProductResponse)
routers\products.py:762: @router.get("/", response_model=PaginatedProductResponse)
routers\products.py:888: @router.get("/{product_id}", response_model=ProductResponse)
routers\products.py:1051: @router.get("/{product_id}/search-tags", response_model=List[str])
routers\promo_strips.py:27: @router.get("", response_model=List[PromoStripResponse])
routers\promo_strips.py:28: @router.get("/", response_model=List[PromoStripResponse])
routers\promo_strips.py:34: @router.get("/active", response_model=List[PromoStripResponse])
routers\push_notifications.py:20: @router.get("", response_model=List[PushNotificationResponse])
routers\push_notifications.py:21: @router.get("/")
routers\push_notifications.py:190: @router.get("/{notification_id}/analytics", response_model=PushAnalyticsResponse)
routers\push_notifications.py:212: @router.get("/inbox", response_model=List[PushNotificationResponse])
routers\push_notifications.py:268: @router.get("/vapid-public-key", response_model=VapidKeyResponse)
routers\push_notifications.py:288: @router.get("/{notification_id}", response_model=PushNotificationResponse)
routers\recommendations.py:55: @router.get("", response_model=List[Product])
routers\recommendations.py:56: @router.get("/", response_model=List[Product])
routers\recommendations.py:138: @router.get("/favourites")
routers\recommendations.py:267: @router.get("/metrics")
routers\referrals.py:18: @router.get("/settings", response_model=ReferralSettingsResponse)
routers\referrals.py:33: @router.get("/check-eligibility", response_model=ReferralEligibilityResponse)
routers\referrals.py:105: @router.get("/scheme", response_model=ReferralPublicSchemeResponse)
routers\returns.py:71: @router.get("/my-returns", response_model=List[ReturnRequestResponse])
routers\returns.py:81: @router.get("/admin/all", response_model=List[ReturnRequestResponse])
routers\returns.py:91: @router.get("/valet/assigned", response_model=List[ReturnRequestResponse])
routers\returns.py:103: @router.get("/order/{order_id}/eligibility", response_model=ReturnEligibilityResponse)
routers\returns.py:432: @router.get("/valet/pending", response_model=List[ReturnRequestResponse])
routers\return_settings.py:11: @router.get("", response_model=ReturnSettingsResponse)
routers\return_settings.py:12: @router.get("/", response_model=ReturnSettingsResponse)
routers\reviews.py:101: @router.get("/product/{product_id}", response_model=List[ProductReviewResponse])
routers\reviews.py:112: @router.get("/classifications", response_model=List[ClassificationTagResponse])
routers\reviews.py:122: @router.get("/admin/list", response_model=List[ProductReviewResponse])
routers\reviews.py:187: @router.get("/admin/classifications", response_model=List[ClassificationTagResponse])
routers\schemes.py:19: @router.get("", response_model=List[CouponResponse])
routers\schemes.py:20: @router.get("/", response_model=List[CouponResponse])
routers\schemes.py:59: @router.get("/applicable/{product_id}", response_model=List[dict])
routers\schemes.py:113: @router.get("/applicable/bundle/{bundle_id}", response_model=List[dict])
routers\search_tags.py:16: @router.get("", response_model=List[SearchTagResponse])
routers\search_tags.py:17: @router.get("/", response_model=List[SearchTagResponse])
routers\seller_availability.py:226: @router.get("/my", response_model=List[SellerAvailabilityResponse])
routers\seller_availability.py:243: @router.get("", response_model=List[SellerAvailabilityResponse])
routers\seller_availability.py:244: @router.get("/", response_model=List[SellerAvailabilityResponse])
routers\seller_payouts.py:79: @router.get("", response_model=List[SellerPayoutResponse])
routers\seller_payouts.py:80: @router.get("/", response_model=List[SellerPayoutResponse])
routers\seller_payouts.py:191: @router.get("/my-summary", response_model=SellerPayoutSummaryResponse)
routers\seller_payouts.py:201: @router.get("/summary/{seller_id}", response_model=SellerPayoutSummaryResponse)
routers\seller_payouts.py:210: @router.get("/summaries", response_model=List[SellerPayoutSummaryResponse])
routers\seller_requests.py:78: @router.get("", response_model=List[SellerRequestResponse])
routers\seller_requests.py:79: @router.get("/", response_model=List[SellerRequestResponse])
routers\seller_requests.py:99: @router.get("/{request_id}", response_model=SellerRequestResponse)
routers\support_tickets.py:108: @router.get("", response_model=List[SupportTicketResponse])
routers\support_tickets.py:109: @router.get("/", response_model=List[SupportTicketResponse])
routers\support_tickets.py:129: @router.get("/{ticket_id}", response_model=SupportTicketResponse)
routers\system_settings.py:33: @router.get("", response_model=SystemSettingsResponse)
routers\system_settings.py:34: @router.get("/", response_model=SystemSettingsResponse)
routers\tracking.py:323: @router.get("/recent", response_model=List[str])
routers\tracking.py:345: @router.get("/suggestions", response_model=SearchSuggestionsResponse)
routers\tracking.py:362: @router.get("/most-searched", response_model=List[MostSearchedResponse])
routers\tracking.py:375: @router.get("/zero-result-searches", response_model=List[ZeroResultSearchResponse])
routers\tracking.py:388: @router.get("/most-viewed", response_model=List[MostViewedResponse])
routers\tracking.py:401: @router.get("/returning-users", response_model=List[ReturningUserResponse])
routers\tracking.py:413: @router.get("/drop-off-points", response_model=List[DropOffPointResponse])
routers\tracking.py:426: @router.get("/cart-abandonments", response_model=List[CartAbandonmentResponse])
routers\tracking.py:439: @router.get("/most-abandoned-products", response_model=List[MostAbandonedProductResponse])
routers\upi.py:22: @router.get("/details", response_model=UPIDetailsResponse)
routers\users.py:17: @router.get("", response_model=PaginatedUsersResponse)
routers\users.py:18: @router.get("/", response_model=PaginatedUsersResponse)
routers\users.py:63: @router.get("/pending-approvals", response_model=List[UserResponse])
routers\users.py:70: @router.get("/me", response_model=UserResponse)
routers\users.py:71: @router.get("/profile", response_model=UserResponse)
routers\users.py:149: @router.get("/valets/available", response_model=List[UserResponse])
routers\users.py:297: @router.get("/seller-delivery-settings", response_model=UserResponse)
routers\users.py:352: @router.get("/{user_id}", response_model=UserResponse)
routers\valet_availability.py:152: @router.get("/my", response_model=ValetAvailabilityResponse)
routers\valet_availability.py:168: @router.get("", response_model=ValetAvailabilityResponse)
routers\valet_availability.py:169: @router.get("/", response_model=ValetAvailabilityResponse)
routers\valet_payout.py:74: @router.get("/settings", response_model=ValetPayoutSettingsResponse)
routers\valet_payout.py:164: @router.get("/earnings/me", response_model=ValetEarningsResponse)
routers\valet_payout.py:180: @router.get("/earnings/{valet_id}", response_model=ValetEarningsResponse)
routers\version.py:27: @router.get("/version", response_model=VersionResponse)
routers\version.py:46: @router.get("/maintenance", response_model=MaintenanceResponse)
routers\wishlist.py:37: @router.get("", response_model=List[Product])
routers\wishlist.py:38: @router.get("/", response_model=List[Product])
services\push_notification_service.py:204: expo_tokens = [d.get("expoToken") for d in targeted_devices if d.get("expoToken")]
services\push_notification_service.py:224: web_devices = [d for d in devices if d.get("endpoint") and d.get("keys")]
services\push_notification_service.py:237: subscription_info={"endpoint": device.get("endpoint"), "keys": device.get("keys", {})},
services\push_notification_service.py:244: logger.error("Failed to send to web device %s: %s", device.get("_id"), str(e))
services\push_notification_service.py:246: await push_notification_repository.removeDeviceSubscription(device.get("_id"))
services\push_notification_service.py:249: expo_tokens = [d.get("expoToken") for d in devices if d.get("expoToken")]
utils\otp.py:87: response = requests.get(url, timeout=10)
`

## isinstance_dict (76 hits)
`
main.py:497: if isinstance(e, HTTPException) and isinstance(e.detail, dict) and (e.detail["code"] if "code" in e.detail else None) == ERR_SESSION_REVOKED:
db\mysql_flat_base_dao.py:115: val = getattr(data, api_key, None) if not isinstance(data, dict) else data.get(api_key)
db\mysql_flat_base_dao.py:240: if isinstance(update_data, dict):
db\mysql_flat_daos.py:76: if isinstance(data, dict):
db\mysql_flat_daos.py:103: if isinstance(data, dict):
db\mysql_flat_daos.py:221: if isinstance(data, dict):
db\mysql_flat_daos.py:272: if isinstance(data, dict):
db\mysql_flat_daos.py:385: if isinstance(data, dict):
db\mysql_flat_daos.py:416: if isinstance(data, dict):
db\mysql_flat_daos.py:553: if isinstance(data, dict):
db\mysql_flat_daos.py:620: if isinstance(data, dict):
db\mysql_flat_daos.py:764: if isinstance(data, dict):
db\mysql_flat_daos.py:811: if isinstance(data, dict):
db\mysql_flat_daos.py:928: if isinstance(data, dict):
db\mysql_flat_daos.py:963: if isinstance(data, dict):
db\mysql_flat_daos.py:1073: if isinstance(data, dict):
db\mysql_flat_daos.py:1112: if isinstance(data, dict):
db\mysql_flat_daos.py:1224: if isinstance(data, dict):
db\mysql_flat_daos.py:1403: if isinstance(data, dict):
db\mysql_flat_daos.py:1446: if isinstance(data, dict):
db\mysql_flat_daos.py:1568: if isinstance(data, dict):
db\mysql_flat_daos.py:1611: if isinstance(data, dict):
db\mysql_flat_daos.py:1720: if isinstance(data, dict):
db\mysql_flat_daos.py:1751: if isinstance(data, dict):
db\mysql_flat_daos.py:1860: if isinstance(data, dict):
db\mysql_flat_daos.py:1899: if isinstance(data, dict):
db\mysql_flat_daos.py:2014: if isinstance(data, dict):
db\mysql_flat_daos.py:2053: if isinstance(data, dict):
db\mysql_flat_daos.py:2168: if isinstance(data, dict):
db\mysql_flat_daos.py:2207: if isinstance(data, dict):
db\mysql_flat_daos.py:2326: if isinstance(data, dict):
db\mysql_flat_daos.py:2369: if isinstance(data, dict):
db\mysql_flat_daos.py:2487: if isinstance(data, dict):
db\mysql_flat_daos.py:2526: if isinstance(data, dict):
db\mysql_flat_daos.py:2645: if isinstance(data, dict):
db\mysql_flat_daos.py:2688: if isinstance(data, dict):
db\mysql_flat_daos.py:2798: if isinstance(data, dict):
db\mysql_flat_daos.py:2829: if isinstance(data, dict):
db\mysql_generated_daos.py:113: if isinstance(data, dict):
db\mysql_generated_daos.py:136: if isinstance(item, dict):
db\mysql_generated_daos.py:178: if isinstance(data, dict):
db\mysql_generated_daos.py:203: existing_dict = existing if isinstance(existing, dict) else existing.__dict__
db\mysql_generated_daos.py:204: data_dict = data if isinstance(data, dict) else data.__dict__
db\mysql_seller_availability_dao.py:87: if isinstance(v, dict) and "$in" in v:
db\mysql_sub_order_dao.py:194: if isinstance(v, dict):
db\mysql_wishlist_dao.py:54: pid = item.product if isinstance(item, dict) else item
jobs\valet_timeout_job.py:99: if isinstance(entry, dict):
jobs\valet_timeout_job.py:194: if isinstance(entry, dict):
jobs\valet_timeout_job.py:314: if not any((isinstance(d, dict) and (d['valetId'] if 'valetId' in d else None) == pending_valet_id for d in history)):
jobs\valet_timeout_job.py:338: if not any((isinstance(d, dict) and (d['valetId'] if 'valetId' in d else None) == pending_valet_id for d in history)):
repositories\activity_repository.py:31: if device and isinstance(device, dict):
repositories\notification_repository.py:51: return [NotificationInternal(**n) if isinstance(n, dict) else NotificationInternal.model_validate(n, from_attributes=True) for n in sorted_notifs]
repositories\notification_repository.py:56: return NotificationInternal(**result) if isinstance(result, dict) else NotificationInternal.model_validate(result, from_attributes=True)
repositories\notification_repository.py:64: return NotificationInternal(**result) if isinstance(result, dict) else NotificationInternal.model_validate(result, from_attributes=True)
repositories\notification_repository.py:69: return NotificationInternal(**result) if isinstance(result, dict) else NotificationInternal.model_validate(result, from_attributes=True)
repositories\payment_repository.py:102: if isinstance(update_data, dict):
repositories\payment_repository.py:177: if isinstance(e, dict):
repositories\payment_repository.py:241: if isinstance(e, dict):
repositories\product_repository.py:938: if isinstance(product_data, dict):
repositories\recommendation_repository.py:1050: sub_cat = sc["name"] if "name" in sc else None if isinstance(sc, dict) else sc
routers\auth.py:411: claims = RefreshTokenClaims(**data) if isinstance(data, dict) else data
routers\commission.py:279: if isinstance(updated, dict):
routers\delivery_charges.py:376: # and then checked isinstance(update_dict, dict) which was always False, so
routers\delivery_slots.py:114: zone_id = zone_data.id or (zone_data["_id"] if isinstance(zone_data, dict) and "_id" in zone_data else zone_data["id"] if isinstance(zone_data, dict) and "id" in zone_data else None) if zone_data else None
routers\products.py:718: f = ProductFacets(**facets) if isinstance(facets, dict) else (facets if isinstance(facets, ProductFacets) else ProductFacets())
routers\products.py:874: f = ProductFacets(**facets) if isinstance(facets, dict) else (facets if isinstance(facets, ProductFacets) else ProductFacets())
routers\push_notifications.py:313: request.subscription["endpoint"] if isinstance(request.subscription, dict) and "endpoint" in request.subscription else None
routers\recommendations.py:367: section_weights = (section_wise[body.slot] if isinstance(section_wise, dict) and body.slot in section_wise else None) or engagement or {}
routers\recommendations.py:369: weight = section_weights["add_to_cart"] if isinstance(section_weights, dict) and "add_to_cart" in section_weights else 3
routers\recommendations.py:371: weight = section_weights["product_view"] if isinstance(section_weights, dict) and "product_view" in section_weights else 1
routers\valet_availability.py:225: enriched.sort(key=lambda d: d.date if not isinstance(d, dict) else (d["date"] if "date" in d and d["date"] is not None else ""))
routers\wishlist.py:55: if isinstance(it, dict):
utils\email_otp.py:126: if not isinstance((record["devices"] if "devices" in record else None), dict):
utils\otp.py:133: if isinstance(value, dict):
utils\otp.py:289: if not isinstance((record["devices"] if "devices" in record else None), dict):
utils\otp.py:437: if not user_record or not isinstance((user_record["devices"] if "devices" in user_record else None), dict):
`

## model_dump (0 hits)

## dot_dict (0 hits)

