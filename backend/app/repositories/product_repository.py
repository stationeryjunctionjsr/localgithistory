from app.models.product import Product
from typing import Any
import asyncio
import time as time_module
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.db.storage_factory import get_storage


class ProductRepository:
    def __init__(self):
        self.storage = get_storage("products")
        self._search_tags_cache = None
        self._search_tags_cache_time = None
        self._collections_cache = None
        self._collections_cache_time = None
        self._cat_gst_map: Optional[Dict[str, float]] = None
        self._cat_gst_map_exp: float = 0.0
        # Lock prevents thundering herd: only one coroutine rebuilds the
        # lightweight search catalog at a time; all others wait then serve from cache.
        self._light_catalog_lock = asyncio.Lock()
        self._light_catalog_cache: Dict = {}

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            # Handle 'Z' or other offsets
            clean_str = date_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_str)
            # Ensure it's aware
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError, AttributeError):
            return None

    # --- Weighted search scoring ---
    SEARCH_WEIGHTS = {
        "name": 10,
        "sku": 8,
        "searchTags": 7,
        "category": 5,
        "subCategory": 4,
        "collections": 4,
        "brand": 3,
        "variantAttributes": 3,
        "price": 6,
        "description": 1,
    }

    def _get_variant_search_text(self, product: Any) -> str:
        """Flatten variant attributes and combination values into searchable text."""
        parts = []
        for attr in product.variantAttributes or []:
            parts.append(str(attr).lower())
        for combo in product.variantCombinations or []:
            attrs = combo.attributes or {}
            for k, v in attrs.items():
                parts.append(str(k).lower())
                parts.append(str(v).lower())
            price = combo.price
            if price is not None:
                p_val = float(price)
                parts.append(str(p_val))
                parts.append(str(int(p_val)))
        return " ".join(parts)

    def _extract_price_text(self, product: Any) -> str:
        """Collect text representations of all prices for a product (MRP, case MRP, variant prices)."""
        parts = []
        if product.mrp is not None:
            try:
                fmrp = float(product.mrp)
                parts.extend([str(fmrp), str(int(fmrp)), f"rs {int(fmrp)}", f"₹{int(fmrp)}", f"rs.{int(fmrp)}"])
            except ValueError:
                pass
        if product.mrpPerCase is not None:
            try:
                fmrp_case = float(product.mrpPerCase)
                parts.extend([str(fmrp_case), str(int(fmrp_case))])
            except ValueError:
                pass
        return " ".join(parts).lower()

    def _score_product(self, product: Any, tokens: List[str]) -> float:
        """Score a product against search tokens using weighted field matching.
        Supports text matching, price matching, and price range expression matching."""
        score = 0.0
        price_text = self._extract_price_text(product)
            
        fields = {
            "name": (product.name or "").lower(),
            "sku": (product.sku or "").lower(),
            "searchTags": " ".join(product.searchTags or []).lower(),
            "category": (product.category or "").lower(),
            "categoryTag": (product.categoryTag or "").lower(),
            "subCategory": (product.subCategory or "").lower(),
            "collections": " ".join(product.resolvedCollectionNames or []).lower(),
            "brand": (product.brand or "").lower(),
            "variantAttributes": self._get_variant_search_text(product),
            "price": price_text,
            "description": (product.description or "").lower(),
        }

        # Check price range expression patterns across raw query tokens (e.g. 'under 500', 'below 300', '100-500')
        import re

        full_query = " ".join(tokens).lower()
        prod_mrp = float(product.mrp)

        price_expr_matched = False
        # Pattern 1: under/below/less than X or <=X
        match_under = re.search(r"(?:under|below|less\s+than|<=)\s*₹?\s*(\d+(?:\.\d+)?)", full_query)
        if match_under:
            limit_val = float(match_under.group(1))
            if prod_mrp > 0 and prod_mrp <= limit_val:
                score += self.SEARCH_WEIGHTS["price"] * 2.0
                price_expr_matched = True

        # Pattern 2: above/over/more than X or >=X
        match_above = re.search(r"(?:above|over|more\s+than|>=)\s*₹?\s*(\d+(?:\.\d+)?)", full_query)
        if match_above:
            limit_val = float(match_above.group(1))
            if prod_mrp >= limit_val:
                score += self.SEARCH_WEIGHTS["price"] * 2.0
                price_expr_matched = True

        # Pattern 3: X to Y or X-Y
        match_range = re.search(r"(\d+(?:\.\d+)?)\s*(?:to|-)\s*(\d+(?:\.\d+)?)", full_query)
        if match_range:
            low_val, high_val = float(match_range.group(1)), float(match_range.group(2))
            if prod_mrp >= low_val and prod_mrp <= high_val:
                score += self.SEARCH_WEIGHTS["price"] * 2.0
                price_expr_matched = True

        price_expr_keywords = {"under", "below", "less", "than", "above", "over", "more", "to"}

        for token in tokens:
            # Clean currency symbols from token (e.g. '₹500' -> '500', 'rs500' -> '500')
            clean_token = re.sub(r"^(?:rs\.?|₹)", "", token).strip()
            if not clean_token:
                clean_token = token

            token_matched = False
            for field_name, field_value in fields.items():
                if clean_token in field_value or token in field_value:
                    score += self.SEARCH_WEIGHTS[field_name]
                    token_matched = True

            # If token is part of a price expression keyword/value and price expression matched, count token as matched
            if not token_matched and (price_expr_matched or token in price_expr_keywords):
                if price_expr_matched:
                    token_matched = True

            if not token_matched:
                return 0.0  # AND logic: all tokens must match somewhere
        return score

    async def _weighted_search(self, products: List[Dict], search_query: str) -> Dict:
        """Filter and rank products using multi-word tokenized search with weighted relevance scoring.
        Falls back to fuzzy matching if exact search yields fewer than 5 results.
        The CPU-heavy fuzzy search is offloaded to a thread pool to avoid blocking the event loop."""
        tokens = [t.lower() for t in search_query.split() if t.strip()]
        if not tokens:
            return {"products": products, "usedFuzzy": False, "suggestedQuery": None}

        scored = []
        for p in products:
            score = self._score_product(p, tokens)
            if score > 0:
                p._searchScore = score
                scored.append(p)

        used_fuzzy = False
        suggested_query = None

        # Fuzzy fallback if too few exact results — run in thread pool to avoid blocking the event loop
        if len(scored) < 5:
            already_matched = {p.id for p in scored}
            loop = asyncio.get_event_loop()
            fuzzy_results, suggested_query = await loop.run_in_executor(
                None, self._fuzzy_search, products, tokens, already_matched
            )
            if fuzzy_results:
                scored.extend(fuzzy_results)
                used_fuzzy = True

        # Sort by score descending (higher score = more relevant)
        scored.sort(key=lambda p: (p._searchScore if p._searchScore is not None else 0), reverse=True)

        # Clean up internal score field
        for p in scored:
            p.pop("_searchScore", None)

        return {"products": scored, "usedFuzzy": used_fuzzy, "suggestedQuery": suggested_query}

    def _fuzzy_search(
        self, products: List[Dict], tokens: List[str], already_matched: set
    ) -> tuple[List[Dict], Optional[str]]:
        """Fuzzy matching fallback using difflib for typo tolerance."""
        from difflib import SequenceMatcher

        FUZZY_THRESHOLD = 0.7
        fuzzy_results = []
        best_token_suggestions = {token: {"word": token, "ratio": 1.0} for token in tokens}

        for p in products:
            if p.id in already_matched:
                continue

            fields_text = {
                "name": (p.name or "").lower(),
                "searchTags": " ".join(p.searchTags or []).lower(),
                "category": (p.category or "").lower(),
                "collections": " ".join(p.resolvedCollectionNames or []).lower(),
                "brand": (p.brand or "").lower(),
                "variantAttributes": self._get_variant_search_text(p),
            }

            total_score = 0.0
            all_tokens_fuzzy_match = True
            product_token_suggestions = {}

            for token in tokens:
                best_ratio = 0.0
                best_field = None
                best_word = None
                for field_name, field_value in fields_text.items():
                    # Check each word in the field
                    for word in field_value.split():
                        clean_word = word.strip(".,;:!?()[]\"'")
                        ratio = SequenceMatcher(None, token, clean_word).ratio()
                        if ratio > best_ratio:
                            best_ratio = ratio
                            best_field = field_name
                            best_word = clean_word

                if best_ratio >= FUZZY_THRESHOLD and best_field:
                    total_score += self.SEARCH_WEIGHTS[best_field] if best_field in self.SEARCH_WEIGHTS else 1 * best_ratio
                    product_token_suggestions[token] = {"word": best_word, "ratio": best_ratio}
                else:
                    all_tokens_fuzzy_match = False
                    break

            if all_tokens_fuzzy_match and total_score > 0:
                p._searchScore = total_score * 0.8  # Slightly lower than exact matches
                fuzzy_results.append(p)
                for token, sugg in product_token_suggestions.items():
                    if (
                        sugg["ratio"] > best_token_suggestions[token]["ratio"]
                        or best_token_suggestions[token]["ratio"] == 1.0
                    ):
                        if (
                            best_token_suggestions[token]["ratio"] < 1.0
                            or sugg["ratio"] > best_token_suggestions[token]["ratio"]
                        ):
                            best_token_suggestions[token] = sugg
                    if best_token_suggestions[token]["ratio"] == 1.0:
                        best_token_suggestions[token] = sugg

        has_fuzzy = False
        suggested_words = []
        for token in tokens:
            sugg = best_token_suggestions[token] if token in best_token_suggestions else None
            if sugg and sugg["ratio"] < 1.0 and sugg["ratio"] >= FUZZY_THRESHOLD:
                has_fuzzy = True
                suggested_words.append(sugg["word"])
            else:
                suggested_words.append(token)

        suggested_query = " ".join(suggested_words) if has_fuzzy else None
        return fuzzy_results, suggested_query

    async def _get_lightweight_search_catalog(self, role: str, user_id: Optional[str]) -> List[Product]:
        _TTL = 300.0
        now_m = time_module.monotonic()
        effective_role = "wholesaler" if role == "wholesaler" else "customer"

        # Fast path: serve from warm cache without acquiring the lock
        entry = self._light_catalog_cache[effective_role] if effective_role in self._light_catalog_cache else None
        if entry and now_m < entry["exp"]:
            return entry["data"]

        # Slow path: cache is cold or expired — acquire lock so only ONE
        # coroutine rebuilds it while all others wait, then serve from cache.
        async with self._light_catalog_lock:
            # Double-check: another coroutine may have built the cache
            # while we were waiting for the lock.
            entry = self._light_catalog_cache[effective_role] if effective_role in self._light_catalog_cache else None
            if entry and now_m < entry["exp"]:
                return entry["data"]

            # We are genuinely the first — build the cache now.
            raw_products = await self.storage.findAll({"isActive": True})

            products = await self._attach_category_gst(raw_products)
            products = await self.add_dynamic_tags(products, effective_role, None)
            products = await self.resolve_search_tags(products)

            light_products = [
                {
                    "_id": p.id,
                    "name": p.name,
                    "sku": p.sku,
                    "searchTags": p.searchTags,
                    "category": p.category,
                    "categoryTag": p.categoryTag,
                    "subCategory": p.sub_category,
                    "resolvedCollectionNames": p.resolvedCollectionNames,
                    "brand": p.brand,
                    "variantAttributes": p.variant_attributes,
                    "variantCombinations": p.variantCombinations,
                    "description": p.description,
                    # Seller IDs for pincode-based availability filtering in autocomplete
                    "sellerIds": [
                        str(s.sellerId)
                        for s in (p.sellers or [])
                        if s.isActive
                        and (s.stock or 0) > 0
                        and (s.requestStatus if s.requestStatus is not None else "approved") == "approved"
                    ],
                    # Seller IDs for catalogue filtering (mega menu, brands, collections).
                    # Includes out-of-stock items so they still appear in navigation.
                    "catalogSellerIds": [
                        str(s.sellerId)
                        for s in (p.sellers or [])
                        if s.isActive
                        and (s.requestStatus if s.requestStatus is not None else "approved") == "approved"
                    ],
                }
                for p in products
            ]

            self._light_catalog_cache[effective_role] = {
                "data": light_products,
                "exp": time_module.monotonic() + _TTL,
            }
            return light_products

    async def _attach_category_gst(self, products: List[Dict]) -> List[Product]:
        if not products:
            return products
        from app.repositories.category_repository import category_repository

        now_m = time_module.monotonic()
        if self._cat_gst_map is not None and now_m < self._cat_gst_map_exp:
            cat_gst_map = self._cat_gst_map
        else:
            categories = await category_repository.findAll()
            cat_gst_map = {cat.name: (cat.gst if cat.gst is not None else 0) for cat in categories}
            self._cat_gst_map = cat_gst_map
            self._cat_gst_map_exp = now_m + 60.0
        for p in products:
            p.gst = float(cat_gst_map[p.category] if p.category in cat_gst_map else 0)
        return products

    async def findAll(self, query: Optional[Dict] = None):
        products = await self.storage.findAll(query)
        products = await self._attach_category_gst(products)

        query = query or {}

        # Apply filters
        if query["category"] if "category" in query else None:
            products = [p for p in products if p.category == query["category"]]

        # Filter by multiple categories (comma-separated)
        if query["categories"] if "categories" in query else None:
            category_list = [c.strip() for c in query["categories"].split(",")]
            products = [p for p in products if p.category in category_list]

        if query["subCategory"] if "subCategory" in query else None:
            products = [p for p in products if p.sub_category == query["subCategory"]]

        if query["brand"] if "brand" in query else None:
            # Support multiple brands (comma-separated)
            brand_list = [b.strip().lower() for b in query["brand"].split(",")]
            products = [p for p in products if (p.brand if p.brand is not None else "").lower() in brand_list]

        if query["minPrice"] if "minPrice" in query else None:
            min_price = float(query["minPrice"])
            role = query["role"] if "role" in query else "customer"
            products = [p for p in products if self.getPriceForRole(p, role) >= min_price]

        if query["maxPrice"] if "maxPrice" in query else None:
            max_price = float(query["maxPrice"])
            role = query["role"] if "role" in query else "customer"
            products = [p for p in products if self.getPriceForRole(p, role) <= max_price]

        # Defer search to after tag resolution for weighted scoring
        search_query = (query["search"] if "search" in query else "").strip()

        # categoryTag filtering will be handled after dynamic tags

        # Filter active products
        is_active = query["isActive"] if "isActive" in query else None
        include_inactive = query["includeInactive"] if "includeInactive" in query else False
        if is_active is True:
            products = [p for p in products if (p.is_active if p.is_active is not None else True)]
        elif is_active is False:
            products = [p for p in products if not (p.is_active if p.is_active is not None else True)]
        elif not include_inactive:
            products = [p for p in products if (p.is_active if p.is_active is not None else True)]

        # Add dynamic tags (best selling, new)
        role = query["role"] if "role" in query else "customer"
        user_id = query["user_id"] if "user_id" in query else None
        products = await self.add_dynamic_tags(products, role, user_id)

        # Resolve search tags based on association rules
        products = await self.resolve_search_tags(products)

        # Apply weighted search AFTER tag resolution
        if search_query:
            search_res = await self._weighted_search(products, search_query)
            products = search_res["products"]

        # Apply popularity filter (new, best_selling, trending; exclusive → Collections)
        if query["popularity"] if "popularity" in query else None:
            pop = query["popularity"].lower()
            if pop == "new":
                products = [p for p in products if "new" in [t.lower() for t in (p.tags if p.tags is not None else [])]]
            elif pop == "best_selling":
                products = [
                    p
                    for p in products
                    if "best_selling" in [t.lower() for t in (p.tags if p.tags is not None else [])]
                    or any("best_selling_" in t.lower() for t in (p.tags if p.tags is not None else []))
                ]
            elif pop == "trending":
                products = [p for p in products if "trending" in [t.lower() for t in (p.tags if p.tags is not None else [])]]

        # Apply minDiscount filter
        if query["minDiscount"] if "minDiscount" in query else None:
            min_disc = float(query["minDiscount"])
            products_filtered = []
            for p in products:
                price = self.getPriceForRole(p, role)
                mrp = float(p.mrp)
                if mrp > 0 and price < mrp:
                    if not mrp:
                        raise ValueError("Cannot calculate discount: MRP is zero or None")
                    disc = ((mrp - price) / mrp) * 100
                    if disc >= min_disc:
                        products_filtered.append(p)
            products = products_filtered

        # Final filter by categoryTag if present
        if query["categoryTag"] if "categoryTag" in query else None:
            target_tag = query["categoryTag"].lower()
            # Get matching categories from static config
            from app.repositories.category_repository import category_repository

            categories = await category_repository.findAll()
            matching_cats = [c.name for c in categories if (c.categoryTag or "").lower() == target_tag]

            # Filter products that either have a matching category OR have the tag in their dynamic tags
            products = [
                p
                for p in products
                if p.category in matching_cats or any(t.lower() == target_tag for t in (p.tags if p.tags is not None else []))
            ]

        # Filter by collection if present
        if query["collection"] if "collection" in query else None:
            collection_id = query["collection"]
            from app.repositories.collection_repository import collection_repository

            collection = await collection_repository.findById(collection_id)
            if collection:
                allowed_ids = collection["productIds"] if "productIds" in collection else []
                products = [p for p in products if p.id in allowed_ids]
            else:
                # If collection not found, return empty results for safety
                products = []

        # Apply availability filter: when set, only show available or only stock out
        def _is_in_stock(p: Any) -> bool:
            stock = p.stock
            if stock is None:
                return False
            try:
                return int(stock) > 0
            except (TypeError, ValueError):
                return False

        availability = (query["availability"] if "availability" in query else None or "").strip().lower()
        if availability == "available":
            products = [p for p in products if _is_in_stock(p)]
        elif availability == "stock_out":
            products = [p for p in products if not _is_in_stock(p)]

        # Apply sorting — default to relevance when searching, newest otherwise
        sort_by = query["sort"] if "sort" in query else ("relevance" if search_query else "newest")

        if sort_by == "relevance" and search_query:
            pass  # Already sorted by relevance score from _weighted_search
        elif sort_by == "price_asc":
            products.sort(key=lambda p: self.getPriceForRole(p, role))
        elif sort_by == "price_desc":
            products.sort(key=lambda p: self.getPriceForRole(p, role), reverse=True)
        elif sort_by == "name_asc":
            products.sort(key=lambda p: (p.name if p.name is not None else "").lower())
        elif sort_by == "name_desc":
            products.sort(key=lambda p: (p.name if p.name is not None else "").lower(), reverse=True)
        elif sort_by == "popular":
            products.sort(
                key=lambda p: (
                    -1 if any("best_selling" in t for t in (p.tags if p.tags is not None else [])) else 0,
                    self._parse_date((p.created_at if p.created_at is not None else "2000-01-01")).timestamp()
                    if self._parse_date(p.created_at)
                    else 0,
                ),
                reverse=True,
            )
        else:  # newest
            products.sort(
                key=lambda p: (
                    self._parse_date((p.created_at if p.created_at is not None else "2000-01-01")).timestamp()
                    if self._parse_date(p.created_at)
                    else 0
                ),
                reverse=True,
            )

        # When no availability filter: show available first (sorted), then stock out (sorted)
        if not availability:
            available_list = [p for p in products if _is_in_stock(p)]
            stock_out_list = [p for p in products if not _is_in_stock(p)]
            products = available_list + stock_out_list

        return products

    async def get_catalog(
        self, query: Any, skip: int = 0, limit: int = 50, sort: str = "newest", include_facets: bool = True
    ):
        """Orchestrates server-side pagination by calling the DAO."""
        dao_query = query.copy()
        role = query["role"] if "role" in query else "customer"
        user_id = query["user_id"] if "user_id" in query else None

        allowed_ids_sets = []

        # Handle Popularity
        if query["popularity"] if "popularity" in query else None:
            pop = query["popularity"].lower()
            from app.repositories.recommendation_repository import recommendation_repository as _rec_repo

            segment = "wholesaler" if role == "wholesaler" else "customer"

            if pop == "best_selling":
                if role == "wholesaler":
                    bf_ids = await _rec_repo.get_business_favourites_product_ids()
                    allowed_ids_sets.append(set(bf_ids))
                else:
                    cf_ids = await _rec_repo.get_customer_favourites_product_ids()
                    allowed_ids_sets.append(set(cf_ids))
            elif pop == "trending":
                trending_ids = await _rec_repo.get_trending_product_ids(segment)
                allowed_ids_sets.append(set(trending_ids))

        # Handle Collection
        if query["collection"] if "collection" in query else None:
            from app.repositories.collection_repository import collection_repository

            collection = await collection_repository.findById(query["collection"])
            if collection:
                allowed_ids_sets.append(set(str(pid) for pid in (collection["productIds"] if "productIds" in collection else [])))
            else:
                allowed_ids_sets.append(set())

        # Handle CategoryTag
        if query["categoryTag"] if "categoryTag" in query else None:
            target_tag = query["categoryTag"].lower()
            from app.repositories.category_repository import category_repository

            categories = await category_repository.findAll()
            matching_cats = [c.name for c in categories if (c.categoryTag or "").lower() == target_tag]

            if matching_cats:
                # Merge into existing categories filter if any
                existing = dao_query["categories"] if "categories" in dao_query else ""
                if existing:
                    dao_query["categories"] = existing + "," + ",".join(matching_cats)
                else:
                    dao_query["categories"] = ",".join(matching_cats)
            else:
                allowed_ids_sets.append(set())

        # Handle Serviceable Sellers (Hyperlocal Pincode)
        if "allowed_seller_ids" in query:
            dao_query["seller_ids"] = query["allowed_seller_ids"]

        if allowed_ids_sets:
            final_allowed = allowed_ids_sets[0]
            for s in allowed_ids_sets[1:]:
                final_allowed = final_allowed.intersection(s)
            dao_query["allowed_ids"] = list(final_allowed)

        if True:
            paginated_products, total_count = await self.storage.find_paginated(
                dao_query, skip=skip, limit=limit, sort=sort
            )

            search_query = dao_query["search"] if "search" in dao_query else "".strip()
            used_fuzzy = False
            suggested_query = None

            if search_query and total_count < 5:
                # 1. Fetch lightweight in-memory catalog
                candidate_products = await self._get_lightweight_search_catalog(role, user_id)

                # 2. Apply python-side fuzzy search
                search_res = await self._weighted_search(candidate_products, search_query)
                matched_products = search_res["products"]
                used_fuzzy = search_res["usedFuzzy"]
                suggested_query = search_res["suggestedQuery"]

                matched_ids = [p.id for p in matched_products]

                if matched_ids:
                    # 3. Create a new query bypassing the DB string search but enforcing all other filters
                    fuzzy_dao_query = dao_query.copy()
                    fuzzy_dao_query.pop("search", None)

                    if "allowed_ids" in fuzzy_dao_query:
                        existing_set = set(fuzzy_dao_query["allowed_ids"])
                        new_allowed = list(existing_set.intersection(set(matched_ids)))
                    else:
                        new_allowed = matched_ids

                    fuzzy_dao_query["allowed_ids"] = new_allowed

                    if new_allowed:
                        fuzzy_dao_query["limit"] = 1000  # fetch all matching to sort in python
                        full_products = await self.storage.findAll(fuzzy_dao_query)

                        full_products = await self._attach_category_gst(full_products)
                        full_products = await self.add_dynamic_tags(full_products, role, user_id)
                        full_products = await self.resolve_search_tags(full_products)

                        sort_by = sort or dao_query["sort"] if "sort" in dao_query else "relevance"
                        if sort_by == "relevance":
                            order_map = {str(p.id): idx for idx, p in enumerate(matched_products)}
                            full_products.sort(key=lambda p: order_map[str(p.id)] if str(p.id) in order_map else 9999)
                        elif sort_by == "price_asc":
                            full_products.sort(key=lambda p: self.getPriceForRole(p, role))
                        elif sort_by == "price_desc":
                            full_products.sort(key=lambda p: self.getPriceForRole(p, role), reverse=True)
                        elif sort_by == "name_asc":
                            full_products.sort(key=lambda p: (p.name if p.name is not None else "").lower())
                        elif sort_by == "name_desc":
                            full_products.sort(key=lambda p: (p.name if p.name is not None else "").lower(), reverse=True)

                        total_count = len(full_products)
                        paginated_products = full_products[skip : skip + limit]
                    else:
                        paginated_products = []
                        total_count = 0
                else:
                    paginated_products = []
                    total_count = 0
            else:
                # Post-process items returned from DB
                paginated_products = await self._attach_category_gst(paginated_products)
                paginated_products = await self.add_dynamic_tags(paginated_products, role, user_id)
                paginated_products = await self.resolve_search_tags(paginated_products)

            if include_facets:
                facets = await self.storage.get_facets(dao_query)
                # Collections Facet (Simple fallback: return all non-empty collections)
                from app.repositories.collection_repository import collection_repository

                all_collections = await collection_repository.findAll()
                available_collections = [col["name"] if "name" in col else None for col in all_collections if (col["productIds"] if "productIds" in col else None)]
                facets["collections"] = sorted(list(set(available_collections)))
            else:
                facets = {"brands": [], "categories": [], "subCategories": [], "collections": []}

            return paginated_products, total_count, facets, used_fuzzy, suggested_query
        # FileStorage Fallback — disabled: Oracle is the only supported backend.
        # else:
        #     fallback_query = query.copy()
        #     fallback_query.pop("search", None)
        #     all_products = await self.findAll(fallback_query)
        #
        #     used_fuzzy = False
        #     suggested_query = None
        #     search_query = (query["search"] if "search" in query else "").strip()
        #     if search_query:
        #         search_res = self._weighted_search(all_products, search_query)
        #         all_products = search_res["products"]
        #         used_fuzzy = search_res["usedFuzzy"]
        #         suggested_query = search_res["suggestedQuery"]
        #
        #     total_count = len(all_products)
        #
        #     sort_by = sort or query["sort"] if "sort" in query else "newest"
        #
        #     paginated_products = all_products[skip:skip+limit]
        #
        #     facets = {
        #         "brands": sorted(list(set(p.brand for p in all_products if p.brand))),
        #         "categories": sorted(list(set(p.category for p in all_products if p.category))),
        #         "subCategories": sorted(list(set(p.sub_category for p in all_products if p.sub_category)))
        #     }
        #     from app.repositories.collection_repository import collection_repository
        #     all_collections = await collection_repository.findAll()
        #     all_pids = set(str(p.id) for p in all_products)
        #     available_collections = []
        #     for col in all_collections:
        #         col_pids = set(str(pid) for pid in col["productIds"] if "productIds" in col else [])
        #         if all_pids.intersection(col_pids):
        #             available_collections.append(col["name"] if "name" in col else None)
        #     facets["collections"] = sorted(list(set(available_collections)))
        #
        #     return paginated_products, total_count, facets, used_fuzzy, suggested_query

    async def add_dynamic_tags(
        self, products: List[Dict], role: str = "customer", user_id: Optional[str] = None
    ) -> List[Product]:
        """Add refined dynamic tags: segmented best sellers and user-specific new arrivals"""
        import time as _t

        user_ordered_pids = set()
        if user_id:
            from app.repositories.order_repository import order_repository

            # Only fetch orders for this specific user
            user_orders = await order_repository.findAll({"user": user_id})
            for o in user_orders:
                for item in o["items"] if "items" in o else []:
                    if item.product:
                        user_ordered_pids.add(str(item.product))

        # Calculate thresholds (Aware)
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)

        # Tags: new, best_selling_customer (Customer Favourites), best_selling_wholesaler (Business Favourites), trending
        # Use a short-lived per-repository cache to avoid 3 separate file reads per product listing request.
        from app.repositories.recommendation_repository import recommendation_repository as _rec_repo

        _TAG_TTL = 30.0
        try:
            self._dyn_tag_cache
        except AttributeError:
            self._dyn_tag_cache: dict = {}
        cache_key = f"dyn_{role}"
        entry = self._dyn_tag_cache[cache_key] if cache_key in self._dyn_tag_cache else None
        _now_m = _t.monotonic()

        if entry and _now_m < entry["exp"]:
            trending_ids_set = entry["trending"]
            cf_ids_set = entry["cf"]
            bf_ids_set = entry["bf"]
        else:
            segment = "wholesaler" if role == "wholesaler" else "customer"
            trending_ids_set, cf_ids_set = await asyncio.gather(
                _rec_repo.get_trending_product_ids(segment),
                _rec_repo.get_customer_favourites_product_ids(),
            )
            bf_ids_set = await _rec_repo.get_business_favourites_product_ids() if role == "wholesaler" else set()
            self._dyn_tag_cache[cache_key] = {
                "trending": trending_ids_set,
                "cf": cf_ids_set,
                "bf": bf_ids_set,
                "exp": _now_m + _TAG_TTL,
            }

        trending_ids = {"customer": trending_ids_set, "wholesaler": trending_ids_set}

        for p in products:
            pid = p.id
            created_date = self._parse_date(p.created_at)
            is_new = created_date and created_date >= thirty_days_ago and str(pid) not in user_ordered_pids
            final_tags = []
            if is_new:
                final_tags.append("new")
            if role in ["customer", "guest"] and pid in cf_ids_set:
                final_tags.append("best_selling_customer")
            if role == "wholesaler" and pid in bf_ids_set:
                final_tags.append("best_selling_wholesaler")
            if role == "wholesaler" and pid in trending_ids["wholesaler"]:
                final_tags.append("trending")
            elif role in ["customer", "guest"] and pid in trending_ids["customer"]:
                final_tags.append("trending")
            p.tags = final_tags
            # Mark products the logged-in user has previously bought (all-time, not time-limited)
            p.previouslyBought = bool(user_id and str(pid) in user_ordered_pids)

        return products

    async def _get_active_search_tags(self) -> List[Product]:
        """Get all active search tags with short caching"""
        now = datetime.now(timezone.utc)
        if (
            self._search_tags_cache is not None
            and self._search_tags_cache_time
            and (now - self._search_tags_cache_time).total_seconds() < 10
        ):
            return self._search_tags_cache
        from app.repositories.search_tag_repository import search_tag_repository

        tags = await search_tag_repository.findAllActive()
        self._search_tags_cache = tags
        self._search_tags_cache_time = now
        return tags

    async def _get_collections(self) -> List[Product]:
        """Get all collections with short caching"""
        now = datetime.now(timezone.utc)
        if (
            self._collections_cache is not None
            and self._collections_cache_time
            and (now - self._collections_cache_time).total_seconds() < 10
        ):
            return self._collections_cache
        from app.repositories.collection_repository import collection_repository

        collections = await collection_repository.findAll()
        self._collections_cache = collections
        self._collections_cache_time = now
        return collections

    async def resolve_search_tags(self, products: List[Dict]) -> List[Product]:
        """Resolve which search tags apply to each product based on association rules"""
        search_tags = await self._get_active_search_tags()

        # Build collection -> productIds mapping and product -> collection names (used for search scoring)
        collections = await self._get_collections()
        collection_product_map: Dict[str, List[str]] = {}
        product_collection_names: Dict[str, List[str]] = {}
        for col in collections:
            col_id = str(col["_id"] if "_id" in col else "")
            col_name = col["name"] if "name" in col else ""
            col_product_ids = col["productIds"] if "productIds" in col else []
            if col_id:
                collection_product_map[col_id] = col_product_ids
            for pid in col_product_ids:
                pid_str = str(pid)
                if pid_str not in product_collection_names:
                    product_collection_names[pid_str] = []
                if col_name and col_name not in product_collection_names[pid_str]:
                    product_collection_names[pid_str].append(col_name)

        for p in products:
            pid = str((p.id if p.id is not None else ""))
            p_category = (p.category if p.category is not None else "")
            p_sub_category = (p.sub_category if p.sub_category is not None else "")
            p_brand = (p.brand if p.brand is not None else "")
            p_collection = (p.collection if p.collection is not None else "")

            matched_tags = []
            for tag in search_tags:
                # Check exclusion first
                excluded_ids = (tag.excludedProductIds if tag.excludedProductIds is not None else [])
                if pid in excluded_ids:
                    continue

                matched = False

                # Check direct product assignment
                tag_product_ids = (tag.productIds if tag.productIds is not None else [])
                if pid in tag_product_ids:
                    matched = True

                # Check category match
                if not matched and p_category:
                    tag_categories = (tag.categories if tag.categories is not None else [])
                    if tag_categories and p_category in tag_categories:
                        matched = True

                # Check subcategory match
                if not matched and p_sub_category:
                    tag_sub_categories = (tag.subCategories if tag.subCategories is not None else [])
                    if tag_sub_categories and p_sub_category in tag_sub_categories:
                        matched = True

                # Check brand match
                if not matched and p_brand:
                    tag_brands = (tag.brands if tag.brands is not None else [])
                    if tag_brands and p_brand in tag_brands:
                        matched = True

                # Check collection match
                if not matched:
                    tag_collections = (tag.collections if tag.collections is not None else [])
                    if tag_collections:
                        for col_id in tag_collections:
                            col_pids = collection_product_map[col_id] if col_id in collection_product_map else []
                            if pid in col_pids:
                                matched = True
                                break
                        # Also check the product's own collection field
                        if not matched and p_collection and p_collection in tag_collections:
                            matched = True

                if matched:
                    matched_tags.append((tag.name if tag.name is not None else ""))

            p.searchTags = matched_tags
            p.resolvedCollectionNames = product_collection_names[pid] if pid in product_collection_names else []

        return products

    async def findById(self, id: str):
        p = await self.storage.findById(id)
        if p:
            p = (await self._attach_category_gst([p]))[0]
        return p

    async def findBySku(self, sku: str):
        p = await self.storage.findOne({"sku": sku})
        if p:
            p = (await self._attach_category_gst([p]))[0]
        return p

    async def findByCollection(self, collection_id: str) -> List[Product]:
        from app.repositories.collection_repository import collection_repository

        collection = await collection_repository.findById(collection_id)
        if not collection:
            return []
        product_ids = collection["productIds"] if "productIds" in collection else []
        if not product_ids:
            return []
        str_ids = [str(pid) for pid in product_ids]
        products = await self.storage.findAll({"allowed_ids": str_ids, "isActive": True})
        return await self._attach_category_gst(products)

    async def create(self, product_data: Any) -> Product:
        from app.models.daos import ProductInternalCreate
        if isinstance(product_data, dict):
            product_data.setdefault("mrp", 0.0)
            product_data.setdefault("price", 0.0)
            product_data.setdefault("category", "Uncategorized")
            product_data = ProductInternalCreate(**product_data)
        # Use DB-native MAX(id) instead of loading all products into memory
        try:
            factory_fn = self.storage._factory()
        except AttributeError:
            factory_fn = None
        if factory_fn:
            from sqlalchemy import text as _text

            async with factory_fn() as _session:
                row = (await _session.execute(_text(f"SELECT MAX(id) FROM {self.storage.TABLE}"))).fetchone()
                max_id = int(row[0]) if row and row[0] is not None else 0
        else:
            all_products = await self.storage.findAll()
            max_id = max(
                ((p.product_id if p.product_id is not None else 0) for p in all_products if isinstance(p.product_id, int)), default=0
            )
        product_id = max_id + 1
        product_id_formatted = f"PDT-{product_id}"

        from app.models.daos import ProductInternalCreate
        
        sku_val = product_data.sku
        if not sku_val or str(sku_val).strip() == "":
            sku_val = f"SKU-{product_id_formatted}"

        existing = await self.findBySku(sku_val)
        if existing:
            raise ValueError("Product with this SKU already exists")

        internal_create = ProductInternalCreate(
            productId=product_id,
            productIdFormatted=product_id_formatted,
            name=product_data.name,
            description=product_data.description if product_data.description is not None else "",
            sku=sku_val,
            categoryId=product_data.categoryId,
            subCategory=product_data.subCategory,
            brandId=product_data.brandId,
            price=float(product_data.price if product_data.price is not None else 0),
            mrp=float(product_data.mrp if product_data.mrp is not None else 0),
            stock=int(product_data.stock if product_data.stock is not None else 0),
            unit=product_data.unit if product_data.unit is not None else "pc",
            isActive=product_data.isActive if product_data.isActive is not None else True,
            tags=product_data.tags if product_data.tags is not None else [],
            images=product_data.images if product_data.images is not None else [],
            videos=getattr(product_data, "videos", []),
            thumbnail=product_data.thumbnail,
            variants=getattr(product_data, "variants", []),
            variantAttributes=getattr(product_data, "variantAttributes", []),

            details=product_data.details if product_data.details is not None else {},
        )

        if internal_create.variants:
            existing_skus = set()
            for combo in internal_create.variants:
                combo_sku = combo.sku
                combo_attrs = combo.attributes if combo.attributes is not None else {}
                if not combo_sku:
                    combo_sku = (
                        f"{sku_val}-{'-'.join(str(v).replace(' ', '') for v in combo_attrs.values())}"
                    )
                    combo.sku = combo_sku
                if combo_sku in existing_skus:
                    raise ValueError(f"Duplicate variant SKU generated or provided: {combo_sku}")
                existing_skus.add(combo_sku)

        created = await self.storage.create(internal_create)
        return (await self._attach_category_gst([created]))[0]

    async def update(self, id: str, update_data: Any) -> Optional[Product]:
        from app.models.daos import ProductInternalUpdate
        
        # Zero Data Stripping: Do not use model_dump or dictionary methods!
        update_fields = {}
        for field_name in update_data.model_fields_set:
            val = None
            if field_name == "sellers": val = update_data.sellers
            elif field_name == "sku": val = update_data.sku
            elif field_name == "category": val = update_data.category
            elif field_name == "subCategory": val = update_data.subCategory
            elif field_name == "brand": val = update_data.brand
            elif field_name == "mrpPerCase": val = update_data.mrpPerCase
            elif field_name == "quantityPerCase": val = update_data.quantityPerCase
            elif field_name == "stock": val = update_data.stock
            elif field_name == "rating": val = update_data.rating
            elif field_name == "reviews": val = update_data.reviews
            elif field_name == "videos": val = update_data.videos
            elif field_name == "tags": val = update_data.tags
            elif field_name == "variantAttributes": val = update_data.variantAttributes
            elif field_name == "variants": val = update_data.variants
            elif field_name == "details": val = update_data.details
            elif field_name == "name": val = update_data.name
            elif field_name == "description": val = update_data.description
            elif field_name == "price": val = update_data.price
            elif field_name == "mrp": val = update_data.mrp
            elif field_name == "categoryId": val = update_data.categoryId
            elif field_name == "brandId": val = update_data.brandId
            elif field_name == "images": val = update_data.images
            elif field_name == "isActive": val = update_data.isActive
            elif field_name == "sellerId": val = update_data.sellerId

            if field_name in ["mrp", "mrpPerCase"] and val is not None:
                val = float(val)
            elif field_name in ["quantityPerCase", "stock"] and val is not None:
                val = int(val)
            update_fields[field_name] = val

        if "sku" in update_fields:
            existing = await self.findBySku(update_fields["sku"])
            if existing and str(existing.id) != str(id):
                raise ValueError("SKU already in use")

        if "variantCombinations" in update_fields:
            existing_product = await self.storage.findById(id)
            sku_val = update_fields["sku"] if "sku" in update_fields else existing_product.sku
            for combo in update_fields['variantCombinations']:
                combo_sku = combo.sku
                combo_attrs = combo.attributes if combo.attributes is not None else {}
                if not combo_sku or combo_sku.startswith("NEW-"):
                    combo_sku = (
                        f"{sku_val}-{'-'.join(str(v).replace(' ', '') for v in combo_attrs.values())}"
                    )
                    combo.sku = combo_sku
        
        internal_update = ProductInternalUpdate(**update_fields)
        updated = await self.storage.update(id, internal_update)
        return (await self._attach_category_gst([updated]))[0] if updated else None

    async def delete(self, id: str):
        return await self.storage.update(id, {"isActive": False})

    def getPriceForRole(
        self,
        product: Any,
        role: str,
        quantity: int = 1,
        selected_attributes: Optional[Dict] = None,
        sell_as_case: bool = False,
        user_id: Optional[str] = None,
        ignore_auto_discount: bool = False,
    ) -> float:
        """Price per unit, or price per case when sell_as_case=True and role is business."""
        if not product:
            return 0.0

        # Business (wholesaler) buying by case: calculate total using case MRP
        if sell_as_case and role == "wholesaler":
            qty_per_case = product.quantityPerCase or 0
            mrp_case = product.mrpPerCase
            if qty_per_case and mrp_case is not None:
                return round(float(mrp_case), 2)

        # Base MRP (per unit)
        mrp = float(product.mrp)

        # Check for variant-specific pricing if attributes are selected
        if selected_attributes and product.variantCombinations:
            for combo in product.variantCombinations:
                match = True
                combo_attrs = combo.attributes if combo.attributes is not None else {}
                for k, v in selected_attributes.items():
                    if k not in combo_attrs or combo_attrs[k] != v:
                        match = False
                        break
                if match:
                    if combo.price is not None:
                        mrp = float(combo.price)
                    break

        if mrp <= 0:
            return 0.0

        # Apply automatic product discount if cached and not ignored
        from app.repositories.coupon_repository import coupon_repository

        active_discounts = coupon_repository._active_automatic_discounts_cache
        if active_discounts and not ignore_auto_discount:
            auto_discount_pct = 0.0
            auto_discount_value = 0.0
            auto_discount_type = "percentage"
            pid = str((product.id if product.id is not None else ""))
            for c in active_discounts:
                # Match role
                if role not in (c.applicableRoles if c.applicableRoles is not None else []):
                    continue
                # Match user_id
                applicable_user_ids = c.applicableUserIds or []
                if applicable_user_ids:
                    if not user_id or str(user_id) not in [str(x) for x in applicable_user_ids]:
                        continue
                # Match product eligibility using pre-calculated set
                affected = c._affected_product_ids or set()
                if pid in affected:
                    if c.minRequirementType == "quantity_based" and c.quantityTiers:
                        # Evaluate quantity tiers
                        qty_to_use = quantity
                        if role == "wholesaler" and sell_as_case:
                            if c.applicableItemType == "cases" and product.quantityPerCase:
                                qty_to_use = quantity // product.quantityPerCase

                        sorted_tiers = sorted(c.quantityTiers, key=lambda x: x["quantity"] if "quantity" in x else 0, reverse=True)
                        matched_pct = 0.0
                        for tier in sorted_tiers:
                            if qty_to_use >= tier["quantity"] if "quantity" in tier else 0:
                                matched_pct = float(tier["discount"] if "discount" in tier else 0)
                                break
                        pct = matched_pct
                        val = matched_pct
                        c_discount_type = "percentage"
                    else:
                        pct = 0.0
                        val = float(c.discountValue or 0)
                        c_discount_type = c.discountType
                        if c_discount_type == "percentage":
                            pct = val
                        elif c_discount_type == "fixed":
                            if mrp > 0:
                                if not mrp:
                                    raise ValueError("Cannot calculate discount: MRP is zero or None")
                                pct = (val / mrp) * 100

                    if pct > auto_discount_pct:
                        auto_discount_pct = pct
                        auto_discount_value = val
                        auto_discount_type = c_discount_type
            if auto_discount_pct > 0:
                if auto_discount_type == "percentage":
                    mrp = mrp * (1 - auto_discount_value / 100)
                elif auto_discount_type == "fixed":
                    mrp = max(0.0, mrp - auto_discount_value)

        return round(mrp, 2)

    def calculateTotalPrice(
        self,
        product: Any,
        role: str,
        quantity: int,
        selected_attributes: Optional[Dict] = None,
        sell_as_case: bool = False,
        user_id: Optional[str] = None,
        ignore_auto_discount: bool = False,
    ) -> float:
        """Total price for quantity (units). If sell_as_case, quantity is in units and price = cases * mrpPerCase."""
        if sell_as_case and role == "wholesaler":
            qty_per_case = int(product.quantityPerCase or 0)
            mrp_case = product.mrpPerCase
            if qty_per_case and mrp_case is not None and quantity >= qty_per_case:
                cases = quantity // qty_per_case
                return round(float(mrp_case) * cases, 2)
        price_per_piece = self.getPriceForRole(
            product,
            role,
            quantity,
            selected_attributes,
            sell_as_case,
            user_id=user_id,
            ignore_auto_discount=ignore_auto_discount,
        )
        return round(price_per_piece * quantity, 2)

    async def get_available_stock(self, product_id: str, exclude_user_id: Optional[str] = None) -> int:
        """Returns stock minus active reservations of other users."""
        product = await self.findById(product_id)
        if not product:
            return 0
        actual_stock = int((product.stock if product.stock is not None else 0))
        from app.repositories.stock_reservation_repository import stock_reservation_repository

        reserved = await stock_reservation_repository.get_reserved_quantity(product_id, exclude_user_id=exclude_user_id)
        return max(0, actual_stock - reserved)

    async def decrement_stock_atomic(
        self, product_id: str, quantity: int, variant_combinations: list = None, role: str = None
    ):
        from sqlalchemy import text
        from app.config.database import get_async_session_factory
        factory = get_async_session_factory()
        if not factory:
            return None
        async with factory() as session:
            # Lock the parent product row — serialises concurrent decrements across all
            # VMs/workers sharing the same MySQL instance (FOR UPDATE is DB-level).
            result = await session.execute(
                text(f"SELECT id, stock FROM {self.storage.TABLE} WHERE id = :id FOR UPDATE"),
                {"id": product_id},
            )
            row = result.fetchone()
            if not row:
                return None
            if row.stock < quantity:
                raise ValueError(f"Insufficient stock for product {product_id}")
            new_stock = row.stock - quantity
            await session.execute(
                text(f"UPDATE {self.storage.TABLE} SET stock = :stock, updated_at = UTC_TIMESTAMP() WHERE id = :rid"),
                {"stock": new_stock, "rid": row.id},
            )

            # Decrement variant-level stock when the order specifies variant attributes.
            # Previously variant_combinations was accepted but silently dropped.
            if variant_combinations:
                # Lock all variant rows for this product in the same transaction.
                v_result = await session.execute(
                    text("SELECT id, stock, sku FROM sj_product_variants WHERE product_id = :pid FOR UPDATE"),
                    {"pid": row.id},
                )
                all_variants = v_result.fetchall()

                if all_variants:
                    variant_ids = [v.id for v in all_variants]
                    placeholders = ", ".join([f":vid_{i}" for i in range(len(variant_ids))])
                    attr_params = {f"vid_{i}": vid for i, vid in enumerate(variant_ids)}

                    # Fetch combo attributes for attribute-based matching
                    attr_result = await session.execute(
                        text(
                            f"SELECT variant_id, attr_name, attr_value "
                            f"FROM sj_product_variant_combo_attrs "
                            f"WHERE variant_id IN ({placeholders})"
                        ),
                        attr_params,
                    )
                    variant_attrs: dict = {v.id: {} for v in all_variants}
                    for ar in attr_result.fetchall():
                        variant_attrs[ar.variant_id][ar.attr_name] = ar.attr_value

                    for vc in variant_combinations:
                        req_attrs = vc["attributes"] if "attributes" in vc else None or {}
                        vc_qty = int(vc["quantity"] if "quantity" in vc else quantity)
                        matched = False
                        for v_row in all_variants:
                            v_id = v_row.id
                            if req_attrs and v_id in variant_attrs and variant_attrs[v_id] == req_attrs:
                                if (v_row.stock or 0) < vc_qty:
                                    raise ValueError(f"Insufficient stock for variant of product {product_id}")
                                new_v_stock = (v_row.stock or 0) - vc_qty
                                await session.execute(
                                    text(
                                        "UPDATE sj_product_variants "
                                        "SET stock = :stock WHERE id = :vid"
                                    ),
                                    {"stock": new_v_stock, "vid": v_id},
                                )
                                matched = True
                                break
                        if not matched and req_attrs:
                            from app.utils.logger import logger as _log
                            _log.warning(
                                "[decrement_stock_atomic] No variant matched attrs %s for product %s — "
                                "global stock decremented but variant stock unchanged.",
                                req_attrs, product_id,
                            )

            await session.commit()
        return new_stock


# ── MULTI-VM STOCK DECREMENT (commented out — already handled by DB-level lock) ──
#
# The active decrement_stock_atomic() above uses SELECT … FOR UPDATE on sj_products
# (and sj_product_variants when variant_combinations is provided).  These are
# MySQL row locks that work identically whether requests come from 1 worker or
# N workers across M VMs — all share the same MySQL instance.
#
# HOW SINGLE-VM WORKS (active):
#   With uvicorn --workers 4 on one VM, all 4 workers share one event loop per
#   process.  MySQL's FOR UPDATE serialises concurrent order-completion requests
#   for the same product at the DB level.  No in-process asyncio.Lock is needed
#   because the lock scope must cross process boundaries.
#
# IF PRE-DB LOAD SHEDDING IS EVER NEEDED (flash-sale, extreme RPS):
#
# # async def decrement_stock_atomic_redis_gated(
# #     self, product_id: str, quantity: int,
# #     variant_combinations: list = None, role: str = None
# # ):
# #     """Like decrement_stock_atomic but gates via a Redis distributed lock.
# #     Prevents DB pool saturation on high-concurrency product flash-sales.
# #     """
# #     import aioredis, os
# #     redis = aioredis.from_url(os.environ["REDIS_URL"])
# #     lock_key = f"sj:stock:{product_id}"
# #     async with redis.lock(lock_key, timeout=10, blocking_timeout=8):
# #         return await self.decrement_stock_atomic(
# #             product_id, quantity, variant_combinations, role
# #         )
#
# TO ACTIVATE:
#   1. pip install aioredis
#   2. Add REDIS_URL to .env
#   3. Replace decrement_stock_atomic calls in orders.py with decrement_stock_atomic_redis_gated.
#
# ─────────────────────────────────────────────────────────────────────────────────

    async def increment_stock_atomic(self, product_id: str, quantity: int) -> int:
        from sqlalchemy import text
        from app.config.database import get_async_session_factory
        factory = get_async_session_factory()
        if not factory:
            return -1
        async with factory() as session:
            result = await session.execute(
                text(f"SELECT id, stock FROM {self.storage.TABLE} WHERE id = :id FOR UPDATE"),
                {"id": product_id},
            )
            row = result.fetchone()
            if not row:
                return -1
            new_stock = row.stock + quantity
            await session.execute(
                text(f"UPDATE {self.storage.TABLE} SET stock = :stock, updated_at = UTC_TIMESTAMP() WHERE id = :rid"),
                {"stock": new_stock, "rid": row.id},
            )
            await session.commit()
        return new_stock


product_repository = ProductRepository()







