# OCI Object Storage Integration

Bucket: **sj-prod-assets** (private, Standard, Oracle-managed encryption).

## 1. Object key naming strategy

| Use case | Key pattern | Example |
|----------|-------------|---------|
| Product images (with product id) | `products/{product_id}/images/{filename}` | `products/606d4f42.../images/photo.jpg` |
| Category images (with category id) | `categories/{category_id}/images/{filename}` | `categories/d8df395b.../images/cat.jpg` |
| Temporary / unassociated uploads | `uploads/tmp/{uuid}/{filename}` | `uploads/tmp/a1b2c3d4.../file.png` |
| Banners | `banners/{uuid}/{filename}` | `banners/a1b2c3d4.../banner.png` |
| Brands | `brands/{uuid}/{filename}` | `brands/a1b2c3d4.../logo.png` |
| Collections | `collections/{uuid}/{filename}` | `collections/a1b2c3d4.../cover.png` |
| Push notifications | `push-notifications/{uuid}/{filename}` | `push-notifications/a1b2c3d4.../img.png` |
| UPI QR | `upi/{filename}` | `upi/qr_code.png` |

- **product_id** / **category_id**: entity external_id (e.g. from DB/JSON).
- **uuid**: UUID v4 or similar for uniqueness when entity id is not available at upload time.
- **filename**: safe name (original or generated); avoid path traversal.

When an upload endpoint does not receive an entity id (e.g. product_id), keys use **uploads/tmp/{uuid}/{filename}** or the type-specific pattern with uuid so paths stay predictable and structured.

## 2. Database / store fields (no binary in DB)

Existing fields store **only object keys or path strings** (no binary):

| Entity | Field(s) | Stored value when using OCI |
|--------|----------|-----------------------------|
| Product | `images` (array) | Object keys, e.g. `["products/xxx/images/a.jpg"]` or `["uploads/tmp/uuid/file.jpg"]` |
| Category | `images` (array) | Object keys |
| Banner | `imageUrl` | Single object key |
| Brand | `logoUrl` | Single object key |
| Collection | `imageUrl` | Single object key |
| Push notification | `image` | Object key |
| UPI config | `qrCodeUrl` | Object key |

- **Local fallback:** If OCI is not configured, existing behavior stays: store paths like `/uploads/products/...` and serve from local disk.
- **Display:** For private bucket, the app returns a **path that hits the backend** (e.g. `/api/media?key=...`). The backend redirects to a time-limited PAR (or signed URL). Frontend keeps using the same URL construction (e.g. `getImageUrl(path)`); no API contract change.

## 3. Example flow: upload → store reference → fetch for display

1. **Upload**  
   Client calls existing endpoint (e.g. `POST /api/products/upload-images`) with image file(s).  
   - Backend uploads to OCI with key e.g. `uploads/tmp/{uuid}/{filename}` (or `products/{product_id}/images/{filename}` if id is provided).  
   - Backend returns **same response shape** as today: e.g. `{"images": ["/api/media?key=uploads/tmp/..."]}` so the value is a path the frontend can use as before.

2. **Store reference**  
   Client (e.g. admin) saves product/category with the returned path/key.  
   - Backend stores in DB/JSON only the **object key** (or the `/api/media?key=...` path that encodes it).  
   - No binary data in the database.

3. **Fetch for display**  
   - List/detail APIs return the same field (e.g. `images: ["/api/media?key=..."]`).  
   - Frontend uses existing `getImageUrl(imagePath)` → requests `https://backend/api/media?key=...`.  
   - Backend endpoint **redirects (302)** to a short-lived PAR URL for that object.  
   - Browser loads the image from OCI via the PAR URL (single round-trip: backend → redirect → OCI).

## 4. Configuration

Set in `.env` (or environment):

- `OCI_BUCKET_NAME` – e.g. `sj-prod-assets`
- `OCI_NAMESPACE` – Object Storage namespace (tenancy-specific)
- `OCI_REGION` – e.g. `ap-mumbai-1`
- Auth: either **config file** (e.g. `~/.oci/config`) or **instance principal** (no keys in app). For local/dev, use API key auth via config file or env (see `app/config/oci.py`).

If these are not set, upload and media URLs fall back to local `/uploads` behavior; no infra or extra services required.
