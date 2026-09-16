from app.models.user import User
from app.models.schemas import MessageResponse, BundleResponse, BundlesListResponse
from typing import Dict, Any, List
from pydantic import BaseModel



"""
Product Bundle Router
---------------------
Admin-managed bundles. Each bundle has:
  - A fixed bundle price (cheaper than sum of individual MRPs)
  - A list of items [{productId, quantity}]
  - Stock uses each individual product's own stock; no separate bundle stock counter.

Endpoints:
  Public / Customer:
    GET  /api/bundles                        – list active bundles (with product details)
    GET  /api/bundles/{bundle_id}            – get single bundle with full product details
    POST /api/bundles/{bundle_id}/add-to-cart – add all bundle items to the user's cart

  Admin only:
    POST   /api/bundles/admin               – create bundle
    PUT    /api/bundles/admin/{bundle_id}   – update bundle
    DELETE /api/bundles/admin/{bundle_id}   – delete bundle
    GET    /api/bundles/admin/all           – list all bundles including inactive
"""

import uuid
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.repositories.bundle_repository import bundle_repository
from app.repositories.product_repository import product_repository
from app.utils.auth import get_current_user, require_super_admin
from app.utils.cache import cache
from app.utils.logger import logger

router = APIRouter()


# ─── Pydantic schemas ─────────────────────────────────────────────────────────


class BundleItemSchema(BaseModel):
    productId: str
    quantity: int  # quantity of that product included in one bundle


class CreateBundleRequest(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    items: List[BundleItemSchema]
    imageUrl: Optional[str] = None
    images: Optional[List[str]] = None
    displayImage: Optional[str] = None
    isActive: bool = True
    salesCount: Optional[int] = 0
    category: Optional[str] = None
    subCategory: Optional[str] = None
    brand: Optional[str] = None
    searchTags: Optional[List[str]] = None


class UpdateBundleRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    items: Optional[List[BundleItemSchema]] = None
    imageUrl: Optional[str] = None
    images: Optional[List[str]] = None
    displayImage: Optional[str] = None
    isActive: Optional[bool] = None
    salesCount: Optional[int] = None
    category: Optional[str] = None
    subCategory: Optional[str] = None
    brand: Optional[str] = None
    searchTags: Optional[List[str]] = None


# ─── Helpers ──────────────────────────────────────────────────────────────────


async def _enrich_bundle(bundle: Dict) -> Dict:
    """
    Attach product details to each bundle item and compute:
      - totalMrp  : sum of (item.quantity × product.mrp)
      - savings   : totalMrp − bundle.price
      - availability: True only when every product has sufficient stock
    """
    enriched_items = []
    total_mrp = 0.0
    fully_available = True

    for item in (bundle.items or []):
        p_id = item["productId"] if "productId" in item else (item["product_id"] if "product_id" in item else None) if isinstance(item, dict) else getattr(item, "productId", getattr(item, "product_id", None))
        product = await product_repository.findById(p_id)
        if not product:
            continue
        mrp = product.mrp or 0
        qty = item["quantity"] if "quantity" in item else getattr(item, "quantity", 1) if isinstance(item, dict) else (item.quantity if item.quantity is not None else 1)
        line_mrp = mrp * qty
        total_mrp += line_mrp

        # Available stock (no user to exclude for public endpoint)
        stock = (product.stock if product.stock is not None else 0)
        if stock < qty:
            fully_available = False

        enriched_items.append(
            {
                "productId": item.productId,
                "quantity": qty,
                "product": {
                    "_id": product.id,
                    "name": product.name,
                    "sku": product.sku,
                    "mrp": mrp,
                    "images": (product.images or []),
                    "stock": stock,
                },
                "lineMrp": line_mrp,
            }
        )

    bundle_price = float((bundle.price if bundle.price is not None else 0))
    display_img = (
        getattr(bundle, "displayImage", getattr(bundle, "display_image", getattr(bundle, "imageUrl", getattr(bundle, "image_url", None))))
        or next(
            (item["product"]["images"][0] for item in enriched_items if item["product"] if "product" in item else None and item["product"]["images"] if "images" in item["product"] else None),
            None,
        )
    )
    
    bundle_dict = bundle.model_dump(by_alias=True) if hasattr(bundle, 'model_dump') else (bundle if isinstance(bundle, dict) else {})
    return {
        **bundle_dict,
        "items": enriched_items,
        "totalMrp": round(total_mrp, 2),
        "savings": round(total_mrp - bundle_price, 2),
        "savingsPercent": round((total_mrp - bundle_price) / total_mrp * 100, 1) if total_mrp else 0,
        "isAvailable": fully_available,
        "displayImage": display_img,
    }


async def _validate_bundle_items(items: List[BundleItemSchema]):
    """Raise 400 if any product doesn't exist or has qty < 1."""
    for item in items:
        if item.quantity < 1:
            raise HTTPException(status_code=400, detail=f"Quantity for product {item.productId} must be at least 1")
        p_id = item["productId"] if "productId" in item else (item["product_id"] if "product_id" in item else None) if isinstance(item, dict) else getattr(item, "productId", getattr(item, "product_id", None))
        product = await product_repository.findById(p_id)
        if not product:
            raise HTTPException(status_code=400, detail=f"Product {item.productId} not found")


# ─── Public endpoints ──────────────────────────────────────────────────────────


@router.get("/search", response_model=BundlesListResponse)
async def search_bundles(
    q: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    limit: int = 12,
):
    """
    Search active available bundles by name/description and/or filter by category/brand.
    Public endpoint, no auth required.
    """
    try:
        bundles = await bundle_repository.get_active_bundles()
        # Pre-fetch all products once for category/brand resolution
        from app.db.storage_factory import get_storage as _get_storage
        product_storage = _get_storage("products")
        all_products_list = await product_storage.find({"isActive": True})
        product_map = {str(p.id): p for p in all_products_list if "_id" in p}

        enriched_bundles = []
        for b in bundles:
            try:
                eb = await _enrich_bundle(b)
                if not eb.is_available:
                    continue

                # Filter by search term
                if q:
                    search_term = q.lower()
                    
                    # 1. Check price expressions (e.g. "under 500")
                    price_matched = False
                    price_val = None
                    tokens = search_term.split()
                    if len(tokens) >= 2 and tokens[0] in {"under", "below", "less"}:
                        try:
                            price_val = float(tokens[1])
                            if float((eb.price if eb.price is not None else 0)) <= price_val:
                                price_matched = True
                        except ValueError:
                            pass
                    elif search_term.isdigit():
                        if abs(float((eb.price if eb.price is not None else 0)) - float(search_term)) < 10:
                            price_matched = True

                    # 2. Check text fields
                    name = (eb.name or "").lower()
                    desc = (eb.description or "").lower()
                    tags = [t.lower() for t in (eb.search_tags or [])]
                    
                    text_matched = (
                        search_term in name or 
                        search_term in desc or 
                        any(search_term in t for t in tags)
                    )

                    if not text_matched and not price_matched:
                        continue

                # Resolve effective category & brand
                eff_categories = set()
                eff_brands = set()
                if eb.category:
                    eff_categories.add(eb["category"].lower())
                if eb.brand:
                    eff_brands.add(eb["brand"].lower())

                if not eff_categories or not eff_brands:
                    # Inherit from components
                    for item in (eb.items or []):
                        pid = item.product_id
                        p = (product_map[str(pid)] if str(pid) in product_map else None)
                        if p:
                            c = p.category
                            if c:
                                eff_categories.add((c.name if isinstance(c, dict) else c).lower())
                            b_name = p.brand
                            if b_name:
                                eff_brands.add(b_name.lower())

                if category and category.lower() not in eff_categories:
                    continue
                if brand and brand.lower() not in eff_brands:
                    continue

                enriched_bundles.append(eb)
            except Exception as e:
                logger.warning("Could not enrich bundle %s: %s", b.id, e)

        return {"bundles": enriched_bundles[:limit], "total": len(enriched_bundles[:limit])}
    except Exception as e:
        logger.error("Error searching bundles: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("", response_model=BundlesListResponse)
@router.get("/", response_model=BundlesListResponse)
@cache.ttl_cache(ttl=300.0)
async def list_active_bundles():
    """List all active bundles with enriched product details (public)."""
    try:
        bundles = await bundle_repository.get_active_bundles()
        enriched = []
        for b in bundles:
            try:
                enriched.append(await _enrich_bundle(b))
            except Exception as e:
                logger.warning("Could not enrich bundle %s: %s", b.id, e)
        return {"bundles": enriched, "total": len(enriched)}
    except Exception as e:
        logger.error("Error listing bundles: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/product/{product_id}", response_model=List[BundleResponse])
@cache.ttl_cache(ttl=300.0)
async def list_bundles_for_product(product_id: str):
    """List all active bundles containing a specific product, sorted by salesCount descending."""
    try:
        bundles = await bundle_repository.get_bundles_containing_product(product_id)
        enriched = []
        for b in bundles:
            try:
                enriched.append(await _enrich_bundle(b))
            except Exception as e:
                logger.warning("Could not enrich bundle %s: %s", b.id, e)
        # Sort by salesCount descending
        enriched.sort(key=lambda x: (x["salesCount"] if "salesCount" in x else (x["sales_count"] if "sales_count" in x else 0)) if isinstance(x, dict) else (getattr(x, "salesCount", getattr(x, "sales_count", 0)) or 0), reverse=True)
        return enriched
    except Exception as e:
        logger.error("Error fetching bundles for product %s: %s", product_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/admin/all", response_model=BundlesListResponse)
async def list_all_bundles(current_user: User = Depends(require_super_admin)):
    """List ALL bundles (including inactive) for admin management."""
    try:
        bundles = await bundle_repository.findAll()
        enriched = []
        for b in bundles:
            try:
                enriched.append(await _enrich_bundle(b))
            except Exception as e:
                logger.warning("Could not enrich bundle %s: %s", b.id, e)
                enriched.append(b)
        return {"bundles": enriched, "total": len(enriched)}
    except Exception as e:
        logger.error("Error listing all bundles: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/{bundle_id}", response_model=BundleResponse)
@cache.ttl_cache(ttl=300.0)
async def get_bundle(bundle_id: str):
    """Get a single active bundle with full product details (public)."""
    try:
        bundle = await bundle_repository.findById(bundle_id)
        if not bundle:
            raise HTTPException(status_code=404, detail="Bundle not found")
        if not (getattr(bundle, "isActive", getattr(bundle, "is_active", None)) if getattr(bundle, "isActive", getattr(bundle, "is_active", None)) is not None else True):
            raise HTTPException(status_code=404, detail="Bundle not found")
        return await _enrich_bundle(bundle)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching bundle %s: %s", bundle_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("/{bundle_id}/add-to-cart", response_model=MessageResponse)
async def add_bundle_to_cart(bundle_id: str, current_user: User = Depends(get_current_user)):
    """
    Add all items from a bundle to the user's cart.
    Prices are computed at the individual item level (bundle savings are shown in cart UI).
    Stock is validated per-product.
    """
    try:
        from app.repositories.cart_repository import cart_repository
        from app.repositories.stock_reservation_repository import stock_reservation_repository
        from app.repositories.wishlist_repository import wishlist_repository

        bundle = await bundle_repository.findById(bundle_id)
        if not bundle or not (getattr(bundle, "isActive", getattr(bundle, "is_active", None)) if getattr(bundle, "isActive", getattr(bundle, "is_active", None)) is not None else True):
            raise HTTPException(status_code=404, detail="Bundle not found")

        user_id = current_user.id
        role = current_user.effective_role or (current_user.role if current_user.role is not None else "customer")
        ttl_minutes = 30 if role == "wholesaler" else 10

        # Validate stock before touching the cart
        for item in (bundle.items or []):
            p_id = item["productId"] if "productId" in item else (item["product_id"] if "product_id" in item else None) if isinstance(item, dict) else getattr(item, "productId", getattr(item, "product_id", None))
            product = await product_repository.findById(p_id)
            if not product or not product.is_active:
                raise HTTPException(status_code=400, detail=f"Product {p_id} is no longer available")
            available = await product_repository.get_available_stock(p_id, exclude_user_id=user_id)
            if available < (item["quantity"] if "quantity" in item else getattr(item, "quantity", 1) if isinstance(item, dict) else getattr(item, "quantity", 1)):
                pname = (product.name if product.name is not None else p_id)
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for '{pname}'. Available: {available}, required: {item["quantity"] if "quantity" in item else getattr(item, "quantity", 1) if isinstance(item, dict) else getattr(item, "quantity", 1)}",
                )

        cart = await cart_repository.findByUser(user_id)
        added_product_ids = []

        for item in (bundle.items or []):
            pid = item["productId"] if "productId" in item else (item["product_id"] if "product_id" in item else None) if isinstance(item, dict) else getattr(item, "productId", getattr(item, "product_id", None))
            qty = item["quantity"] if "quantity" in item else getattr(item, "quantity", 1) if isinstance(item, dict) else getattr(item, "quantity", 1)

            new_item = {
                "_id": str(uuid.uuid4()),
                "product": pid,
                "quantity": qty,
                "sellAsCase": False,
                "bundleId": bundle_id,  # tag so cart UI can group bundle items visually
                "bundleName": bundle.name,
            }

            if cart:
                existing = next(
                    (i for i in (cart.items or []) if i.product == pid and i.bundle_id == bundle_id),
                    None,
                )
                if existing:
                    items = (cart.items or [])
                    for i, it in enumerate(items):
                        if it.id == existing.id:
                            if qty is None:
                                raise ValueError("Data Integrity Error: Bundle item missing quantity")
                            items[i]["quantity"] = existing.quantity + qty
                            break
                    await cart_repository.createOrUpdate(user_id, items)
                else:
                    await cart_repository.addItem(user_id, new_item)
            else:
                await cart_repository.addItem(user_id, new_item)
                cart = await cart_repository.findByUser(user_id)

            # Update stock reservation
            updated_cart = await cart_repository.findByUser(user_id)
            final_qty = sum((i.quantity if i.quantity is not None else 0) for i in (updated_cart.items or []) if i.product == pid)
            await stock_reservation_repository.reserve_stock(
                product_id=pid,
                user_id=user_id,
                quantity=final_qty,
                ttl_minutes=ttl_minutes,
            )

            # Remove from wishlist if present
            await wishlist_repository.removeItem(user_id, pid)
            added_product_ids.append(pid)

        return {
            "message": f"Bundle '{bundle.name}' added to cart",
            "addedProducts": added_product_ids,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error adding bundle to cart: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ─── Admin endpoints ───────────────────────────────────────────────────────────


@router.post("/admin", response_model=BundleResponse)
async def create_bundle(payload: CreateBundleRequest, current_user: User = Depends(require_super_admin)):
    """Admin: create a new product bundle."""
    try:
        if payload.price <= 0:
            raise HTTPException(status_code=400, detail="Bundle price must be greater than zero")
        if not payload.items:
            raise HTTPException(status_code=400, detail="Bundle must contain at least one item")

        await _validate_bundle_items(payload.items)

        bundle_data = {
            "_id": str(uuid.uuid4()),
            "name": payload.name.strip(),
            "description": payload.description,
            "price": payload.price,
            "items": [{"productId": i.productId, "quantity": i.quantity} for i in payload.items],
            "imageUrl": payload.imageUrl,
            "isActive": payload.isActive,
            "salesCount": payload.salesCount if payload.salesCount is not None else 0,
            "searchTags": payload.searchTags or [],
        }
        created = await bundle_repository.create(bundle_data)
        return {"message": "Bundle created", "bundle": created}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating bundle: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.put("/admin/{bundle_id}", response_model=BundleResponse)
async def update_bundle(
    bundle_id: str,
    payload: UpdateBundleRequest,
    current_user: User = Depends(require_super_admin),
):
    """Admin: update an existing bundle."""
    try:
        bundle = await bundle_repository.findById(bundle_id)
        if not bundle:
            raise HTTPException(status_code=404, detail="Bundle not found")

        updates: Dict = {}
        if payload.name is not None:
            updates["name"] = payload.name.strip()
        if payload.description is not None:
            updates["description"] = payload.description
        if payload.price is not None:
            if payload.price <= 0:
                raise HTTPException(status_code=400, detail="Bundle price must be greater than zero")
            updates["price"] = payload.price
        if payload.items is not None:
            await _validate_bundle_items(payload.items)
            updates["items"] = [{"productId": i.productId, "quantity": i.quantity} for i in payload.items]
        if payload.imageUrl is not None:
            updates["imageUrl"] = payload.imageUrl
        if payload.isActive is not None:
            updates["isActive"] = payload.isActive
        if payload.salesCount is not None:
            updates["salesCount"] = payload.salesCount
        if payload.searchTags is not None:
            updates["searchTags"] = payload.searchTags

        updated = await bundle_repository.update(bundle_id, updates)
        return {"message": "Bundle updated", "bundle": updated}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating bundle %s: %s", bundle_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.delete("/admin/{bundle_id}", response_model=MessageResponse)
async def delete_bundle(bundle_id: str, current_user: User = Depends(require_super_admin)):
    """Admin: permanently delete a bundle."""
    try:
        bundle = await bundle_repository.findById(bundle_id)
        if not bundle:
            raise HTTPException(status_code=404, detail="Bundle not found")
        await bundle_repository.delete(bundle_id)
        return {"message": "Bundle deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting bundle %s: %s", bundle_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")
