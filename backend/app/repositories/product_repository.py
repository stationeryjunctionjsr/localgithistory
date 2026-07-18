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
        "description": 1,
    }

    def _get_variant_search_text(self, product: Dict) -> str:
        """Flatten variant attributes and combination values into searchable text."""
        parts = []
        for attr in product.get("variantAttributes", []) or []:
            parts.append(str(attr).lower())
        for combo in product.get("variantCombinations", []) or []:
            attrs = combo.get("attributes", {}) or combo
            for k, v in attrs.items() if isinstance(attrs, dict) else []:
                parts.append(str(k).lower())
                parts.append(str(v).lower())
        return " ".join(parts)

    def _score_product(self, product: Dict, tokens: List[str]) -> float:
        """Score a product against search tokens using weighted field matching.
        All tokens must match at least one field (AND logic). Score is the sum of field weights."""
        score = 0.0
        fields = {
            "name": (product.get("name") or "").lower(),
            "sku": (product.get("sku") or "").lower(),
            "searchTags": " ".join(product.get("searchTags") or []).lower(),
            "category": (product.get("category") or "").lower(),
            "categoryTag": (product.get("categoryTag") or "").lower(),
            "subCategory": (product.get("subCategory") or "").lower(),
            "collections": " ".join(product.get("resolvedCollectionNames") or []).lower(),
            "brand": (product.get("brand") or "").lower(),
            "variantAttributes": self._get_variant_search_text(product),
            "description": (product.get("description") or "").lower(),
        }

        for token in tokens:
            token_matched = False
            for field_name, field_value in fields.items():
                if token in field_value:
                    score += self.SEARCH_WEIGHTS[field_name]
                    token_matched = True
            if not token_matched:
                return 0.0  # AND logic: all tokens must match somewhere
        return score

    def _weighted_search(self, products: List[Dict], search_query: str) -> Dict:
        """Filter and rank products using multi-word tokenized search with weighted relevance scoring.
        Falls back to fuzzy matching if exact search yields fewer than 5 results."""
        tokens = [t.lower() for t in search_query.split() if t.strip()]
        if not tokens:
            return {"products": products, "usedFuzzy": False, "suggestedQuery": None}

        scored = []
        for p in products:
            score = self._score_product(p, tokens)
            if score > 0:
                p["_searchScore"] = score
                scored.append(p)

        used_fuzzy = False
        suggested_query = None

        # Fuzzy fallback if too few exact results
        if len(scored) < 5:
            fuzzy_results, suggested_query = self._fuzzy_search(products, tokens, already_matched={p.get("_id") for p in scored})
            if fuzzy_results:
                scored.extend(fuzzy_results)
                used_fuzzy = True

        # Sort by score descending (higher score = more relevant)
        scored.sort(key=lambda p: p.get("_searchScore", 0), reverse=True)

        # Clean up internal score field
        for p in scored:
            p.pop("_searchScore", None)

        return {"products": scored, "usedFuzzy": used_fuzzy, "suggestedQuery": suggested_query}

    def _fuzzy_search(self, products: List[Dict], tokens: List[str], already_matched: set) -> tuple[List[Dict], Optional[str]]:
        """Fuzzy matching fallback using difflib for typo tolerance."""
        from difflib import SequenceMatcher

        FUZZY_THRESHOLD = 0.7
        fuzzy_results = []
        best_token_suggestions = {token: {"word": token, "ratio": 1.0} for token in tokens}

        for p in products:
            if p.get("_id") in already_matched:
                continue

            fields_text = {
                "name": (p.get("name") or "").lower(),
                "searchTags": " ".join(p.get("searchTags") or []).lower(),
                "category": (p.get("category") or "").lower(),
                "collections": " ".join(p.get("resolvedCollectionNames") or []).lower(),
                "brand": (p.get("brand") or "").lower(),
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
                    total_score += self.SEARCH_WEIGHTS.get(best_field, 1) * best_ratio
                    product_token_suggestions[token] = {"word": best_word, "ratio": best_ratio}
                else:
                    all_tokens_fuzzy_match = False
                    break

            if all_tokens_fuzzy_match and total_score > 0:
                p["_searchScore"] = total_score * 0.8  # Slightly lower than exact matches
                fuzzy_results.append(p)
                for token, sugg in product_token_suggestions.items():
                    if sugg["ratio"] > best_token_suggestions[token]["ratio"] or best_token_suggestions[token]["ratio"] == 1.0:
                        if best_token_suggestions[token]["ratio"] < 1.0 or sugg["ratio"] > best_token_suggestions[token]["ratio"]:
                            best_token_suggestions[token] = sugg
                    if best_token_suggestions[token]["ratio"] == 1.0:
                        best_token_suggestions[token] = sugg

        has_fuzzy = False
        suggested_words = []
        for token in tokens:
            sugg = best_token_suggestions.get(token)
            if sugg and sugg["ratio"] < 1.0 and sugg["ratio"] >= FUZZY_THRESHOLD:
                has_fuzzy = True
                suggested_words.append(sugg["word"])
            else:
                suggested_words.append(token)

        suggested_query = " ".join(suggested_words) if has_fuzzy else None
        return fuzzy_results, suggested_query

    async def _get_lightweight_search_catalog(self, role: str, user_id: Optional[str]) -> List[Dict]:
        import time as _t
        
        _TTL = 300.0
        now_m = _t.monotonic()
        effective_role = "wholesaler" if role == "wholesaler" else "customer"
        
        if not hasattr(self, "_light_catalog_cache"):
            self._light_catalog_cache = {}
            
        entry = self._light_catalog_cache.get(effective_role)
        if entry and now_m < entry["exp"]:
            return entry["data"]
            
        raw_products = await self.storage.findAll({"isActive": True})
        
        products = await self._attach_category_gst(raw_products)
        products = await self.add_dynamic_tags(products, effective_role, None)
        products = await self.resolve_search_tags(products)
        
        light_products = []
        for p in products:
            light_products.append({
                "_id": p.get("_id"),
                "name": p.get("name"),
                "sku": p.get("sku"),
                "searchTags": p.get("searchTags"),
                "category": p.get("category"),
                "categoryTag": p.get("categoryTag"),
                "subCategory": p.get("subCategory"),
                "resolvedCollectionNames": p.get("resolvedCollectionNames"),
                "brand": p.get("brand"),
                "variantAttributes": p.get("variantAttributes"),
                "variantCombinations": p.get("variantCombinations"),
                "description": p.get("description"),
            })
            
        self._light_catalog_cache[effective_role] = {
            "data": light_products,
            "exp": now_m + _TTL
        }
        return light_products

    async def _attach_category_gst(self, products: List[Dict]) -> List[Dict]:
        if not products:
            return products
        from app.repositories.category_repository import category_repository

        now_m = time_module.monotonic()
        if self._cat_gst_map is not None and now_m < self._cat_gst_map_exp:
            cat_gst_map = self._cat_gst_map
        else:
            categories = await category_repository.findAll()
            cat_gst_map = {cat.get("name"): cat.get("gst", 0) for cat in categories}
            self._cat_gst_map = cat_gst_map
            self._cat_gst_map_exp = now_m + 60.0
        for p in products:
            p["gst"] = float(cat_gst_map.get(p.get("category"), 0))
        return products

    async def findAll(self, query: Optional[Dict] = None):
        products = await self.storage.findAll(query)
        products = await self._attach_category_gst(products)

        query = query or {}

        # Apply filters
        if query.get("category"):
            products = [p for p in products if p.get("category") == query["category"]]

        # Filter by multiple categories (comma-separated)
        if query.get("categories"):
            category_list = [c.strip() for c in query["categories"].split(",")]
            products = [p for p in products if p.get("category") in category_list]

        if query.get("subCategory"):
            products = [p for p in products if p.get("subCategory") == query["subCategory"]]

        if query.get("brand"):
            # Support multiple brands (comma-separated)
            brand_list = [b.strip().lower() for b in query["brand"].split(",")]
            products = [p for p in products if p.get("brand", "").lower() in brand_list]

        if query.get("minPrice"):
            min_price = float(query["minPrice"])
            role = query.get("role", "customer")
            products = [p for p in products if self.getPriceForRole(p, role) >= min_price]

        if query.get("maxPrice"):
            max_price = float(query["maxPrice"])
            role = query.get("role", "customer")
            products = [p for p in products if self.getPriceForRole(p, role) <= max_price]

        # Defer search to after tag resolution for weighted scoring
        search_query = query.get("search", "").strip()

        # categoryTag filtering will be handled after dynamic tags

        # Filter active products
        is_active = query.get("isActive")
        include_inactive = query.get("includeInactive", False)
        if is_active is True:
            products = [p for p in products if p.get("isActive", True)]
        elif is_active is False:
            products = [p for p in products if not p.get("isActive", True)]
        elif not include_inactive:
            products = [p for p in products if p.get("isActive", True)]

        # Add dynamic tags (best selling, new)
        role = query.get("role", "customer")
        user_id = query.get("user_id")
        products = await self.add_dynamic_tags(products, role, user_id)

        # Resolve search tags based on association rules
        products = await self.resolve_search_tags(products)

        # Apply weighted search AFTER tag resolution
        if search_query:
            search_res = self._weighted_search(products, search_query)
            products = search_res["products"]

        # Apply popularity filter (new, best_selling, trending; exclusive → Collections)
        if query.get("popularity"):
            pop = query["popularity"].lower()
            if pop == "new":
                products = [p for p in products if "new" in [t.lower() for t in p.get("tags", [])]]
            elif pop == "best_selling":
                products = [
                    p
                    for p in products
                    if "best_selling" in [t.lower() for t in p.get("tags", [])]
                    or any("best_selling_" in t.lower() for t in p.get("tags", []))
                ]
            elif pop == "trending":
                products = [p for p in products if "trending" in [t.lower() for t in p.get("tags", [])]]

        # Apply minDiscount filter
        if query.get("minDiscount"):
            min_disc = float(query["minDiscount"])
            products_filtered = []
            for p in products:
                price = self.getPriceForRole(p, role)
                mrp = float(p.get("mrp", 0))
                if mrp > 0 and price < mrp:
                    disc = ((mrp - price) / mrp) * 100
                    if disc >= min_disc:
                        products_filtered.append(p)
            products = products_filtered

        # Final filter by categoryTag if present
        if query.get("categoryTag"):
            target_tag = query["categoryTag"].lower()
            # Get matching categories from static config
            from app.repositories.category_repository import category_repository

            categories = await category_repository.findAll()
            matching_cats = [c["name"] for c in categories if (c.get("categoryTag") or "").lower() == target_tag]

            # Filter products that either have a matching category OR have the tag in their dynamic tags
            products = [
                p
                for p in products
                if p.get("category") in matching_cats or any(t.lower() == target_tag for t in p.get("tags", []))
            ]

        # Filter by collection if present
        if query.get("collection"):
            collection_id = query["collection"]
            from app.repositories.collection_repository import collection_repository

            collection = await collection_repository.findById(collection_id)
            if collection:
                allowed_ids = collection.get("productIds", [])
                products = [p for p in products if p.get("_id") in allowed_ids]
            else:
                # If collection not found, return empty results for safety
                products = []

        # Apply availability filter: when set, only show available or only stock out
        def _is_in_stock(p: Dict) -> bool:
            stock = p.get("stock")
            if stock is None:
                return False
            try:
                return int(stock) > 0
            except (TypeError, ValueError):
                return False

        availability = (query.get("availability") or "").strip().lower()
        if availability == "available":
            products = [p for p in products if _is_in_stock(p)]
        elif availability == "stock_out":
            products = [p for p in products if not _is_in_stock(p)]

        # Apply sorting — default to relevance when searching, newest otherwise
        sort_by = query.get("sort", "relevance" if search_query else "newest")

        if sort_by == "relevance" and search_query:
            pass  # Already sorted by relevance score from _weighted_search
        elif sort_by == "price_asc":
            products.sort(key=lambda p: self.getPriceForRole(p, role))
        elif sort_by == "price_desc":
            products.sort(key=lambda p: self.getPriceForRole(p, role), reverse=True)
        elif sort_by == "name_asc":
            products.sort(key=lambda p: p.get("name", "").lower())
        elif sort_by == "name_desc":
            products.sort(key=lambda p: p.get("name", "").lower(), reverse=True)
        elif sort_by == "popular":
            products.sort(
                key=lambda p: (
                    -1 if any("best_selling" in t for t in p.get("tags", [])) else 0,
                    self._parse_date(p.get("createdAt", "2000-01-01")).timestamp()
                    if self._parse_date(p.get("createdAt"))
                    else 0,
                ),
                reverse=True,
            )
        else:  # newest
            products.sort(
                key=lambda p: (
                    self._parse_date(p.get("createdAt", "2000-01-01")).timestamp()
                    if self._parse_date(p.get("createdAt"))
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

    async def get_catalog(self, query: Dict, skip: int = 0, limit: int = 50, sort: str = "newest", include_facets: bool = True):
        """Orchestrates server-side pagination by calling the DAO."""
        dao_query = query.copy()
        role = query.get("role", "customer")
        user_id = query.get("user_id")
        
        allowed_ids_sets = []
        
        # Handle Popularity
        if query.get("popularity"):
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
        if query.get("collection"):
            from app.repositories.collection_repository import collection_repository
            collection = await collection_repository.findById(query["collection"])
            if collection:
                allowed_ids_sets.append(set(str(pid) for pid in collection.get("productIds", [])))
            else:
                allowed_ids_sets.append(set())
                
        # Handle CategoryTag
        if query.get("categoryTag"):
            target_tag = query["categoryTag"].lower()
            from app.repositories.category_repository import category_repository
            categories = await category_repository.findAll()
            matching_cats = [c["name"] for c in categories if (c.get("categoryTag") or "").lower() == target_tag]
            
            if matching_cats:
                # Merge into existing categories filter if any
                existing = dao_query.get("categories", "")
                if existing:
                    dao_query["categories"] = existing + "," + ",".join(matching_cats)
                else:
                    dao_query["categories"] = ",".join(matching_cats)
            else:
                allowed_ids_sets.append(set())

        if allowed_ids_sets:
            final_allowed = allowed_ids_sets[0]
            for s in allowed_ids_sets[1:]:
                final_allowed = final_allowed.intersection(s)
            dao_query["allowed_ids"] = list(final_allowed)

        if hasattr(self.storage, "find_paginated"):
            paginated_products, total_count = await self.storage.find_paginated(dao_query, skip=skip, limit=limit, sort=sort)
            
            search_query = dao_query.get("search", "").strip()
            used_fuzzy = False
            suggested_query = None
            
            if search_query and total_count < 5:
                # 1. Fetch lightweight in-memory catalog
                candidate_products = await self._get_lightweight_search_catalog(role, user_id)
                
                # 2. Apply python-side fuzzy search
                search_res = self._weighted_search(candidate_products, search_query)
                matched_products = search_res["products"]
                used_fuzzy = search_res["usedFuzzy"]
                suggested_query = search_res["suggestedQuery"]
                
                matched_ids = [p["_id"] for p in matched_products]
                
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
                        
                        sort_by = sort or dao_query.get("sort", "relevance")
                        if sort_by == "relevance":
                            order_map = {str(p["_id"]): idx for idx, p in enumerate(matched_products)}
                            full_products.sort(key=lambda p: order_map.get(str(p["_id"]), 9999))
                        elif sort_by == "price_asc":
                            full_products.sort(key=lambda p: self.getPriceForRole(p, role))
                        elif sort_by == "price_desc":
                            full_products.sort(key=lambda p: self.getPriceForRole(p, role), reverse=True)
                        elif sort_by == "name_asc":
                            full_products.sort(key=lambda p: p.get("name", "").lower())
                        elif sort_by == "name_desc":
                            full_products.sort(key=lambda p: p.get("name", "").lower(), reverse=True)
                        
                        total_count = len(full_products)
                        paginated_products = full_products[skip:skip+limit]
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
                available_collections = [col.get("name") for col in all_collections if col.get("productIds")]
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
        #     search_query = query.get("search", "").strip()
        #     if search_query:
        #         search_res = self._weighted_search(all_products, search_query)
        #         all_products = search_res["products"]
        #         used_fuzzy = search_res["usedFuzzy"]
        #         suggested_query = search_res["suggestedQuery"]
        #
        #     total_count = len(all_products)
        #
        #     sort_by = sort or query.get("sort", "newest")
        #
        #     paginated_products = all_products[skip:skip+limit]
        #
        #     facets = {
        #         "brands": sorted(list(set(p.get("brand") for p in all_products if p.get("brand")))),
        #         "categories": sorted(list(set(p.get("category") for p in all_products if p.get("category")))),
        #         "subCategories": sorted(list(set(p.get("subCategory") for p in all_products if p.get("subCategory"))))
        #     }
        #     from app.repositories.collection_repository import collection_repository
        #     all_collections = await collection_repository.findAll()
        #     all_pids = set(str(p.get("_id")) for p in all_products)
        #     available_collections = []
        #     for col in all_collections:
        #         col_pids = set(str(pid) for pid in col.get("productIds", []))
        #         if all_pids.intersection(col_pids):
        #             available_collections.append(col.get("name"))
        #     facets["collections"] = sorted(list(set(available_collections)))
        #
        #     return paginated_products, total_count, facets, used_fuzzy, suggested_query

    async def add_dynamic_tags(
        self, products: List[Dict], role: str = "customer", user_id: Optional[str] = None
    ) -> List[Dict]:
        """Add refined dynamic tags: segmented best sellers and user-specific new arrivals"""
        import time as _t

        user_ordered_pids = set()
        if user_id:
            from app.repositories.order_repository import order_repository

            # Only fetch orders for this specific user
            user_orders = await order_repository.findAll({"user": user_id})
            for o in user_orders:
                for item in o.get("items", []):
                    if item.get("product"):
                        user_ordered_pids.add(str(item.get("product")))

        # Calculate thresholds (Aware)
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)

        # Tags: new, best_selling_customer (Customer Favourites), best_selling_wholesaler (Business Favourites), trending
        # Use a short-lived per-repository cache to avoid 3 separate file reads per product listing request.
        from app.repositories.recommendation_repository import recommendation_repository as _rec_repo

        _TAG_TTL = 30.0
        if not hasattr(self, "_dyn_tag_cache"):
            self._dyn_tag_cache: dict = {}
        cache_key = f"dyn_{role}"
        entry = self._dyn_tag_cache.get(cache_key)
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
            pid = p["_id"]
            created_date = self._parse_date(p.get("createdAt"))
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
            p["tags"] = final_tags

        return products

    async def _get_active_search_tags(self) -> List[Dict]:
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

    async def _get_collections(self) -> List[Dict]:
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

    async def resolve_search_tags(self, products: List[Dict]) -> List[Dict]:
        """Resolve which search tags apply to each product based on association rules"""
        search_tags = await self._get_active_search_tags()

        # Build collection -> productIds mapping and product -> collection names (used for search scoring)
        collections = await self._get_collections()
        collection_product_map: Dict[str, List[str]] = {}
        product_collection_names: Dict[str, List[str]] = {}
        for col in collections:
            col_id = str(col.get("_id", ""))
            col_name = col.get("name", "")
            col_product_ids = col.get("productIds", [])
            if col_id:
                collection_product_map[col_id] = col_product_ids
            for pid in col_product_ids:
                pid_str = str(pid)
                if pid_str not in product_collection_names:
                    product_collection_names[pid_str] = []
                if col_name and col_name not in product_collection_names[pid_str]:
                    product_collection_names[pid_str].append(col_name)

        for p in products:
            pid = str(p.get("_id", ""))
            p_category = p.get("category", "")
            p_sub_category = p.get("subCategory", "")
            p_brand = p.get("brand", "")
            p_collection = p.get("collection", "")

            matched_tags = []
            for tag in search_tags:
                # Check exclusion first
                excluded_ids = tag.get("excludedProductIds", [])
                if pid in excluded_ids:
                    continue

                matched = False

                # Check direct product assignment
                tag_product_ids = tag.get("productIds", [])
                if pid in tag_product_ids:
                    matched = True

                # Check category match
                if not matched and p_category:
                    tag_categories = tag.get("categories", [])
                    if tag_categories and p_category in tag_categories:
                        matched = True

                # Check subcategory match
                if not matched and p_sub_category:
                    tag_sub_categories = tag.get("subCategories", [])
                    if tag_sub_categories and p_sub_category in tag_sub_categories:
                        matched = True

                # Check brand match
                if not matched and p_brand:
                    tag_brands = tag.get("brands", [])
                    if tag_brands and p_brand in tag_brands:
                        matched = True

                # Check collection match
                if not matched:
                    tag_collections = tag.get("collections", [])
                    if tag_collections:
                        for col_id in tag_collections:
                            col_pids = collection_product_map.get(col_id, [])
                            if pid in col_pids:
                                matched = True
                                break
                        # Also check the product's own collection field
                        if not matched and p_collection and p_collection in tag_collections:
                            matched = True

                if matched:
                    matched_tags.append(tag.get("name", ""))

            p["searchTags"] = matched_tags
            p["resolvedCollectionNames"] = product_collection_names.get(pid, [])

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

    async def findByCollection(self, collection_id: str) -> List[Dict]:
        from app.repositories.collection_repository import collection_repository

        collection = await collection_repository.findById(collection_id)
        if not collection:
            return []
        product_ids = collection.get("productIds", [])
        if not product_ids:
            return []
        all_products = await self.storage.findAll()
        matched = [p for p in all_products if str(p.get("_id")) in [str(pid) for pid in product_ids] and p.get("isActive") is not False]
        return await self._attach_category_gst(matched)

    async def create(self, product_data: Dict):
        # Generate incremental product ID starting from 1
        all_products = await self.storage.findAll()
        max_id = 0
        for p in all_products:
            if p.get("productId") and isinstance(p.get("productId"), int):
                max_id = max(max_id, p.get("productId", 0))
        product_id = max_id + 1
        product_id_formatted = f"PDT-{product_id}"

        sku_val = product_data.get("sku")
        if not sku_val or str(sku_val).strip() == "":
            sku_val = f"SKU-{product_id_formatted}"

        existing = await self.findBySku(sku_val)
        if existing:
            raise ValueError("Product with this SKU already exists")

        product = {
            "productId": product_id,
            "productIdFormatted": product_id_formatted,
            "name": product_data["name"],
            "description": product_data.get("description", ""),
            "sku": sku_val,
            "category": product_data["category"],
            "subCategory": product_data.get("subCategory"),
            "brand": product_data.get("brand", ""),
            "mrp": float(product_data["mrp"]),
            "mrpPerCase": float(product_data["mrpPerCase"]) if product_data.get("mrpPerCase") is not None else None,
            "quantityPerCase": int(product_data["quantityPerCase"])
            if product_data.get("quantityPerCase") is not None
            else None,
            "stock": int(product_data.get("stock", 0)),
            "images": product_data.get("images", []),
            "videos": product_data.get("videos", []),
            "isActive": product_data.get("isActive", True),
            "tags": product_data.get("tags", []),
            "variantAttributes": product_data.get("variantAttributes", []),
            "variantCombinations": product_data.get("variantCombinations", []),
            "details": product_data.get("details", {}),
        }

        # Auto-generate SKUs for variantCombinations if missing or starts with NEW-
        for combo in product.get("variantCombinations", []):
            combo_sku = combo.get("sku", "")
            if not combo_sku or combo_sku.startswith("NEW-"):
                combo["sku"] = (
                    f"{sku_val}-{'-'.join(str(v).replace(' ', '') for v in combo.get('attributes', {}).values())}"
                )

        created = await self.storage.create(product)
        return (await self._attach_category_gst([created]))[0]

    async def update(self, id: str, update_data: Dict):
        if "sku" in update_data:
            existing = await self.findBySku(update_data["sku"])
            if existing and existing.get("_id") != id:
                raise ValueError("SKU already in use")

        numeric_fields = ["mrp", "mrpPerCase"]
        for field in numeric_fields:
            if field in update_data and update_data[field] is not None:
                update_data[field] = float(update_data[field])
        if "quantityPerCase" in update_data and update_data["quantityPerCase"] is not None:
            update_data["quantityPerCase"] = int(update_data["quantityPerCase"])
        if "stock" in update_data:
            update_data["stock"] = int(update_data["stock"])

        if "variantCombinations" in update_data:
            existing_product = await self.storage.findById(id)
            sku_val = update_data.get("sku") or existing_product.get("sku", "")
            for combo in update_data.get("variantCombinations", []):
                combo_sku = combo.get("sku", "")
                if not combo_sku or combo_sku.startswith("NEW-"):
                    combo["sku"] = (
                        f"{sku_val}-{'-'.join(str(v).replace(' ', '') for v in combo.get('attributes', {}).values())}"
                    )

        # Check stock transition before updating
        has_stock_transition = False
        old_product_name = ""
        try:
            if "stock" in update_data or "variantCombinations" in update_data:
                old_product = await self.storage.findById(id)
                if old_product:
                    old_product_name = old_product.get("name", "")
                    if "stock" in update_data:
                        old_stock = int(old_product.get("stock", 0))
                        new_stock = int(update_data["stock"])
                        if old_stock <= 0 and new_stock > 0:
                            has_stock_transition = True
                    if not has_stock_transition and "variantCombinations" in update_data:
                        old_combos = old_product.get("variantCombinations") or []
                        for new_combo in update_data.get("variantCombinations", []):
                            new_stock = int(new_combo.get("stock", 0))
                            new_attrs = new_combo.get("attributes", {})
                            old_combo = next((oc for oc in old_combos if oc.get("attributes") == new_attrs), None)
                            if new_stock > 0 and (not old_combo or int(old_combo.get("stock", 0)) <= 0):
                                has_stock_transition = True
                                break
        except Exception as e:
            logger.error("Error checking stock transition in product repository update: %s", str(e))

        updated = await self.storage.update(id, update_data)
        if updated:
            updated = (await self._attach_category_gst([updated]))[0]
            if has_stock_transition:
                from app.repositories.product_notification_repository import product_notification_repository
                # Trigger restock notifications asynchronously
                asyncio.create_task(
                    product_notification_repository.trigger_restock_notifications(id, old_product_name or updated.get("name", ""))
                )
        return updated

    async def delete(self, id: str):
        return await self.storage.update(id, {"isActive": False})

    def getPriceForRole(
        self,
        product: Dict,
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
            qty_per_case = product.get("quantityPerCase") or 0
            mrp_case = product.get("mrpPerCase")
            if qty_per_case and mrp_case is not None:
                return round(float(mrp_case), 2)

        # Base MRP (per unit)
        mrp = float(product.get("mrp", 0))

        # Check for variant-specific pricing if attributes are selected
        if selected_attributes and product.get("variantCombinations"):
            for combo in product["variantCombinations"]:
                match = True
                combo_attrs = combo.get("attributes", {})
                for k, v in selected_attributes.items():
                    if combo_attrs.get(k) != v:
                        match = False
                        break
                if match:
                    if combo.get("price") is not None:
                        mrp = float(combo["price"])
                    break

        if mrp <= 0:
            return 0.0

        # Apply automatic product discount if cached and not ignored
        from app.repositories.coupon_repository import coupon_repository
        active_discounts = getattr(coupon_repository, "_active_automatic_discounts_cache", None)
        if active_discounts and not ignore_auto_discount:
            auto_discount_pct = 0.0
            auto_discount_value = 0.0
            auto_discount_type = "percentage"
            pid = str(product.get("_id", ""))
            for c in active_discounts:
                # Match role
                if role not in c.get("applicableRoles", []):
                    continue
                # Match user_id
                applicable_user_ids = c.get("applicableUserIds") or []
                if applicable_user_ids:
                    if not user_id or str(user_id) not in [str(x) for x in applicable_user_ids]:
                        continue
                # Match product eligibility using pre-calculated set
                affected = c.get("_affected_product_ids") or set()
                if pid in affected:
                    if c.get("minRequirementType") == "quantity_based" and c.get("quantityTiers"):
                        # Evaluate quantity tiers
                        qty_to_use = quantity
                        if role == "wholesaler" and sell_as_case:
                            if c.get("applicableItemType") == "cases" and product.get("quantityPerCase"):
                                qty_to_use = quantity // product["quantityPerCase"]
                        
                        sorted_tiers = sorted(c["quantityTiers"], key=lambda x: x.get("quantity", 0), reverse=True)
                        matched_pct = 0.0
                        for tier in sorted_tiers:
                            if qty_to_use >= tier.get("quantity", 0):
                                matched_pct = float(tier.get("discount", 0))
                                break
                        pct = matched_pct
                        val = matched_pct
                        c_discount_type = "percentage"
                    else:
                        pct = 0.0
                        val = float(c.get("discountValue") or 0)
                        c_discount_type = c.get("discountType")
                        if c_discount_type == "percentage":
                            pct = val
                        elif c_discount_type == "fixed":
                            if mrp > 0:
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
        product: Dict,
        role: str,
        quantity: int,
        selected_attributes: Optional[Dict] = None,
        sell_as_case: bool = False,
        user_id: Optional[str] = None,
        ignore_auto_discount: bool = False,
    ) -> float:
        """Total price for quantity (units). If sell_as_case, quantity is in units and price = cases * mrpPerCase."""
        if sell_as_case and role == "wholesaler":
            qty_per_case = int(product.get("quantityPerCase") or 0)
            mrp_case = product.get("mrpPerCase")
            if qty_per_case and mrp_case is not None and quantity >= qty_per_case:
                cases = quantity // qty_per_case
                return round(float(mrp_case) * cases, 2)
        price_per_piece = self.getPriceForRole(
            product, role, quantity, selected_attributes, sell_as_case, user_id=user_id, ignore_auto_discount=ignore_auto_discount
        )
        return round(price_per_piece * quantity, 2)

    async def get_available_stock(self, product_id: str, exclude_user_id: Optional[str] = None) -> int:
        """Returns stock minus active reservations of other users."""
        product = await self.findById(product_id)
        if not product:
            return 0
        actual_stock = int(product.get("stock", 0))
        from app.repositories.stock_reservation_repository import stock_reservation_repository
        reserved = await stock_reservation_repository.get_reserved_quantity(product_id, exclude_user_id=exclude_user_id)
        return max(0, actual_stock - reserved)


product_repository = ProductRepository()
