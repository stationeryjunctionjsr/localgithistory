# Stationery Junction - Exhaustive Technical & Functional Walkthrough

This document serves as the absolute source of truth for all workflows, backend rules, and algorithms running the Stationery Junction e-commerce platform. It is designed for Administrators to understand the precise logic powering the platform.

---

## 1. User Roles, Access, and Restrictions (Deep Dive)

The system enforces strict role-based access control (RBAC) across all endpoints.

### Customer (Retail / B2C)
- **Pricing:** Billed at the standard `price` per unit. The `sellAsCase` flag is ignored for retail.
- **Cart & Stock Reservation:**
  - When an item is added to the cart, the stock is reserved for **10 minutes** using the `stock_reservation_repository`.
  - A countdown timer uses the `expiresAt` field to notify the frontend.
- **Payments:** 
  - Eligible for Cash on Delivery (COD) and UPI. 
  - Credit is strictly forbidden.
- **Referrals:** 
  - Eligible for a referral discount *only* on their very first order (`order_count == 0`).
  - Cannot refer themselves.
  - The discount is proportionally distributed across all items in the cart for fair refunding.
- **Deactivation:** Customers can self-deactivate their accounts (`isActive = False`), but they cannot delete them (unless using the strict GDPR Right-to-Erasure endpoint).

### Wholesaler (Business / B2B)
- **Approval Flow:** 
  - Wholesalers register with an `approvalStatus` of `pending`.
  - Super Admins must verify their **Company Name** and **Address** (both are mandatory) before approving.
- **Pricing & Constraints:** 
  - Access to `mrpPerCase` and B2B specific discounts.
  - Cart addition strictly enforces that the quantity added must be a multiple of `quantityPerCase` if they opt for case pricing.
- **Cart & Stock Reservation:** 
  - Stock is reserved for **30 minutes** to accommodate complex bulk orders.
- **Payments:** 
  - Eligible for COD, UPI, and **Credit**.
- **Credit Limit & Blocking Logic:**
  - Admins assign `paymentTerms` (default 30 days).
  - During checkout (`orders.py`), the backend scans all previous credit payments. It calculates the `effective_due = totalAmount - verified_paid`.
  - If any `effective_due > 0` and the order date is older than `paymentTerms` days, a `HTTP 400` error is thrown: *"You have overdue bills. Please clear your pending dues to continue placing orders."*

### Seller Admin (Vendor / Marketplace Merchant)
- **Capabilities:** 
  - Manage individual vendor store profiles, brand identity, and service area pincodes.
  - Create and manage their own product listings and stock inventories.
  - Review and dispatch incoming sub-orders (`/orders/{id}/dispatch`) belonging to their store.
  - Configure seller-level delivery options (e.g., toggling urgent delivery permissions via `sellerPermissions`).
  - View commission breakdowns, unrealized vs. realized earnings, and payout statements.

### Valet (Delivery Agent)
- **Capabilities:** 
  - Schedule pre-shift availability up to 7 days in advance (`full_day` or `custom` time slots).
  - Toggle live on-duty status (`isOnDuty`) and define serviceable delivery pincodes (`serviceAreaPincodes`).
  - Receive real-time push notifications for assigned delivery requests with automated acceptance windows (5 min for Urgent, 20 min for Standard).
  - Accept or decline assigned orders (`/valet-response`), triggering automated cascading on decline or timeout.
  - Update delivery fulfillment status (e.g., "Out for Delivery", "Delivered") and execute physical return collections from customers.

### Super Admin
- **Capabilities:** Full control over product catalogs, seller approvals and commission tiers, category mapping, coupon generation, delivery rules, user approval, payment verification, dynamic content, and system-wide overrides.

---

## 2. Recommendations Engine

The recommendation engine structures products into specific targeted sections based on user roles and history.
*(Note: The `epsilon-greedy` Multi-Armed Bandit algorithm for dynamically sorting these sections is currently disabled by request. Sections are now served in a static, predefined order: New Arrivals, Customer Favourites, Trending Now, Explore, Business Favourites).*

### Event Tracking & Analytics
- The `tracking_repository` still logs two critical actions for reporting and future tuning:
  - `recommendation_product_view`: Clicked a recommended product.
  - `recommendation_add_to_cart`: Added a recommended product to the cart.

### Role-Specific Slot Contents & Fallbacks

#### A. New Arrivals
- **Criteria:** Fetches all products **and bundles** created within the last 30 days, sorted by newest first.
- **Retail Exclusions:** If a retail user is logged in, the system scans their entire order history and automatically hides products they have already purchased, ensuring the section only shows *unbought* new items.
- **Cart Exclusions:** Products currently in the user's active cart are also excluded from this section.
- **Limit:** The backend returns up to 24 items. The frontend applies responsive section visibility and expansion rules — see **UI Expansion** below.

#### B. Trending Now (Conversion Based)
Calculated via a dynamic percentile-based journey mapping: `Conversion Rate = Converted Sales Count / Search Count`.
- Every product with at least **1 search** in the last 7 days is scored.
- A "Converted Sale" only counts if the exact same user/session searched for the product *and then bought it* within the window.
- **Dynamic Cutoff:** Computes the 70th-percentile (top 30%) cutoff score dynamically across all scored products. The bar rises when many products convert well and falls when traffic is thin.
- Products below the cutoff are discarded. The remainder is sorted descending by score and capped at the requested limit (e.g. 24). Subcategory limits have been removed — all products compete in a global pool.
- **Bundles in Trending:** Bundles are scored using `salesCount / max_salesCount` normalised to [0, 1] and must pass the same top-30% cutoff. See Section F for why `salesCount` is the proxy.
- **For Retail/Guest:** Uses only retail orders.
- **For Wholesalers:** Uses only wholesaler orders (`ORDER-WH-` prefix).
- **Exclusions:** Automatically excludes items already in the user's cart, purchased in the last 60 days, or shown in the *Customer Favourites* section.
- **UI Expansion:** Follows the responsive row tiering rules — see below.

#### C. Customer Favourites (Weighted Score)
- **Formula:** `(0.7 * Order Frequency) + (0.3 * Total Quantity Sold)`.
- Pulls from Retail Orders (`ORDER-RT-` prefix) over the last 60 days.
- Picks the single best product (Rank 1) per subcategory.
- **Bundles in Customer Favourites:** Qualifying bundles (`salesCount > 0`) are appended after products, ranked by `salesCount` descending.
- **Exclusions:** Automatically excludes items already in the user's cart or purchased in the last 60 days.
- **UI Expansion:** Follows the responsive row tiering rules — see below. (A dedicated "View All" page is also available to Wholesalers to view the un-capped list).
- Highly cached (TTL based) due to heavy calculation.

#### D. Business Favourites
- Same formula as Customer Favourites, but strictly calculates using Wholesaler orders (`ORDER-WH-` prefix).
- Displayed only to Wholesalers.
- **Bundles in Business Favourites:** Same scoring as Customer Favourites — qualifying bundles not already in Customer Favourites are appended, ranked by `salesCount` descending.
- **Exclusions:** Also automatically excludes items already in the user's cart or purchased in the last 60 days. Products already shown in Customer Favourites are also removed from this section.
- **UI Expansion:** Follows the responsive row tiering rules — see below (with a dedicated "View All" page for the un-capped list).

#### E. Explore (User-Centric Discovery)
Explore is fully dynamic — it adapts both the number of subcategories and the number of products per subcategory to the individual user's purchase breadth.

**Algorithm (step by step):**
1. Scan the logged-in user's orders from the **last 60 days**. Count total units purchased per `subCategory` (falls back to `category` if a product has no subCategory) → yields **n** distinct subcategories.
2. If `n = 0` (brand-new user with no history), the Explore section is hidden entirely.
3. **Neglected count** = `max(1, round(n / 3))` — picks the bottom third of the user's subcategories (those with the fewest purchases).
4. **Products per subcategory** = `max(1, round(24 / neglected_count))` — dynamically sized so the total stays close to 24.
5. For each neglected subcategory, pick the top `products_per_subcat` **best-selling products all-time** (by total quantity sold across all orders) not in the exclude set.
   - Explore stays strictly within the `n/3` neglected subcategories — no refill from other subcategories.

**Exclusions — what is filtered out before Explore picks:**
- Products in the user's **cart**
- Products purchased by the user in the **last 60 days**
- Products **already placed in New Arrivals, Trending Now, Customer Favourites, or Business Favourites** for this same API response (true cross-section deduplication — no product appears in two sections)

**Example:** A user who bought from 9 subcategories → neglected_count = 3, products_per_subcat = 8 → up to 24 unique products, all from their 3 least-explored subcategories.

- **UI Expansion:** Follows the responsive row tiering rules — see below.

#### F. Bundles in Recommendations
Bundles are treated as **first-class items** in every recommendation section. They are fetched once as product-like dicts (`isBundle=True`), merged into the shared product map, and scored against the same criteria as regular products. **No hardcoded caps, no artificial slots** — a bundle either qualifies or it doesn't.

> [!NOTE]
> **Why `salesCount` is used as the scoring proxy for bundles:** When a user adds a bundle to the cart, it is unpacked into its individual component products (each tagged with a `bundleId`). This means the bundle's own ID **never appears in order line items** — only the component product IDs do. As a result, the standard order-based scoring (conversion rate, weighted frequency/quantity) cannot be computed for a bundle directly. `salesCount` — which is incremented by the backend each time a bundle is successfully ordered — is the only reliable all-time purchase signal available at the bundle level.

| Section | How a bundle qualifies |
|---|---|
| New Arrivals | `createdAt` within the last 30 days, sorted newest first |
| Customer / Business Favourites | `salesCount > 0`, ranked descending by `salesCount` |
| Trending Now | `salesCount / max_salesCount` normalised to [0, 1]; only bundles at or above the same **top-30% percentile cutoff** as products qualify |
| Explore | Bundle's `subCategory` (or `category` fallback) must be one of the user's bottom-third neglected subcategories, ranked by `salesCount` descending |

Bundles that do not meet the section threshold simply do not appear — exactly like any product that fails the score cutoff.

---

### UI Expansion — Responsive Show-More Tiering (all sections)

The number of products shown per row (`R`) adapts to the current viewport:

| Viewport width | Grid columns (R) |
|---|---|
| < 640 px (mobile) | 2 |
| ≥ 640 px (sm) | 3 |
| ≥ 768 px (md) | 4 |
| ≥ 1024 px (lg) | 5 |
| ≥ 1280 px (xl) | 6 |

Once `R` is known, each section applies the following rules based on its product count:

| Product count | Visible initially | "Show more" available? | Expanded shows |
|---|---|---|---|
| < R | Section hidden entirely | — | — |
| R ≤ count < 2R | 1 row (R) | No | — |
| 2R ≤ count < 3R | 1 row (R) | Yes | 2 rows (2R) |
| 3R ≤ count < 4R | 1 row (R) | Yes | 3 rows (3R) |
| count ≥ 4R | 1 row (R) | Yes | 4 rows (4R) |

This logic lives in [`useProductsPerRow.ts`](file:///c:/Ecommerce%20app/frontend/src/hooks/useProductsPerRow.ts) and is shared by both `CustomerClient.tsx` and `WholesalerClient.tsx`. To update the breakpoints, edit only that file.


## 3. The Exhaustive Checkout Pipeline (`orders.py` & `cart.py`)

The order placement API (`POST /orders/`) is the most complex system in the application.

### Step 1: Pre-validation
- Checks if the user is logged in (Valets are blocked).
- Checks Wholesaler overdue credit status.
- Checks Feature Flags (e.g., `retail_enable_cod`, `wholesale_enable_gst`) to ensure the payment method is active.

### Step 2: Subtotal & Tax Calculation (Pre-Coupon)
- Retrieves all cart items and recalculates pricing server-side to prevent client spoofing.
- Validates that reserved stock (`stock_reservation_repository`) is still valid and sufficient. If the reservation expired and the global stock pool ran out, checkout is blocked.

### Step 3: Delivery Charge Computation
- Reads the Shipping Address (State, City, District, Pincode).
- Queries `delivery_charge_repository` for an exact match, falling back to a global default.
- Compares the `minCartValue` against the order subtotal. If the subtotal is higher, shipping is `₹0`.
- Adds `Urgent Delivery` fees if requested and applicable to the Pincode.
- **GST on Shipping:** Computes 18% GST on the final net delivery charge.

### Step 4: Complex Coupon & Discount Engine
Coupons support three modes: Percentage, Amount Off, and Free Shipping.
- **Eligibility Checking:** Coupons can strictly target specific Categories, Subcategories, Brands, Collections, or Users. 
- **Coupon Conflict Avoidance Engine:** When an Admin creates a new coupon (`coupons.py`), the backend automatically scans the database for `OverlapConflictError`. If a new coupon applies to the exact same Subcategory/User demographic during the exact same Active Dates, the system prevents creation to avoid stacking exploits.
- **User Behavior Targeting:** The backend checks the user's order history over the last 90 days. For example, `regular_registered` requires >=12 orders; `downloaded_no_order` checks the `deviceSubscriptions` table to see if the user installed the mobile app but never ordered.
- **Buy X Get Y (BXGY) Algorithm:**
  - Sorts cart items by price descending.
  - Allocates the most expensive eligible items to the "X" requirement.
  - Allocates the next eligible items to the "Y" requirement.
  - Distributes the "Get Y" discount proportionally across all `X + Y` items. This ensures that if a user returns one item, the refund is mathematically fair.

### Step 5: Post-Coupon GST & Referral Distribution
- After the coupon is applied proportionally across eligible items, a Referral Discount (if any) is applied proportionally to the remaining balance.
- **GST (CGST/SGST):** 
  - GST is calculated *after* all discounts are applied.
  - Formula: `Taxable Value = Final Item Price / (1 + (GST% / 100))`. 
  - `CGST = Taxable Value * (GST% / 200)` and `SGST = Taxable Value * (GST% / 200)`.

### Step 6: Finalization & Payment Processing

The final step diverges significantly based on the chosen payment method.

#### 1. Cash on Delivery (COD)
- **Order Creation:** Order is saved with `paymentMethod: "cod"`.
- **Status:** Starts as `Pending`.
- **Fulfillment:** Order is processed by the Admin and assigned to a Valet. The Valet collects the cash upon physical delivery.

#### 2. UPI (Unified Payments Interface)
- **Checkout Requirement:** The user must upload a screenshot of their UPI transaction (`upiPaymentScreenshot` is mandatory in the payload).
- **Order Creation:** Order is saved with `paymentMethod: "upi"`. 
- **Admin Verification:** The order cannot proceed to fulfillment immediately. The Super Admin receives a notification, reviews the uploaded screenshot in the dashboard, and manually marks the payment as `Verified`. Once verified, the order moves forward.

#### 3. Credit (B2B Wholesalers Only)
- **Pre-Flight Check:** The system checks the wholesaler's current `paymentTerms` (e.g., 30 days) and past dues. If *any* past bills are overdue, checkout is completely blocked.
- **Order Creation:** Order is saved with `paymentMethod: "credit"`.
- **Ledger Generation:** A payment ledger entry is created with the `totalAmount` due. The "due date" is mathematically determined by `Order Date + paymentTerms`.
- **Settlement Workflow:** 
  1. The wholesaler logs into their "Dues" dashboard to see pending credit bills.
  2. They pay the due amount via UPI and submit a `Credit Settlement` request, uploading the new UPI screenshot.
  3. The Super Admin reviews the screenshot.
  4. Once verified by the Admin, the payment ledger entry is updated. If the outstanding dues are cleared, any automatic blocks on the wholesaler's account are lifted, allowing them to place new orders.

### Step 7: Post-Checkout Actions & Split-Cart Sub-Order Generation
- Stock reservations (`stock_reservation_repository`) are cleared and permanently deducted from the main product inventory.
- The user's cart is emptied.
- **Split-Cart Sub-Orders:** If the cart contains products from multiple sellers (or a mix of platform products and marketplace vendors), the checkout pipeline creates a master Parent Order and splits it into independent **Sub-Orders** (`sub_order_repository`):
  - Each sub-order receives a distinct identifier (e.g., `ORD-001-A`, `ORD-001-B`) mapped to its respective `sellerId`.
  - Independent delivery charge calculations, urgent delivery flags, and delivery slot bookings (`deliverySlotId`, `deliverySlotDate`) are attached to each sub-order.
  - Sellers independently receive notifications and manage the fulfillment lifecycle of their own sub-orders without interfering with other vendors in the same cart.
- A PDF invoice is dynamically generated (`invoice_generator.py`) and saved to cloud storage (OCI).
- The Super Admin and associated Seller Admins receive instant push notifications regarding the new order.

### Step 8: Order Cancellation & Decline Rules
The system enforces strict rules on when an order can be cancelled by a user or declined by an Admin:
- **Status Restriction:** Orders can *only* be cancelled or declined while they are in the **`pending`** status. Once an Admin accepts an order (moving it to `processing`), the user can no longer cancel it.
- **Payment Method Restriction (The UPI Rule):** 
  - **COD and Credit** orders *can* be cancelled by the user or declined by the Admin.
  - **UPI** orders **cannot be cancelled or declined** by anyone through the standard flow. Because the user has already transferred real money, UPI orders must be manually handled by the Admin for refunds.
- **Post-Cancellation Actions:** If a COD or Credit order is successfully cancelled:
  1. The stock is immediately restored to the global product inventory pool.
  2. If it was a Credit order, the `creditUsed` limit on the Wholesaler's account is instantly refunded.

---

## 4. Product Search & Catalog Engine Logic

The search API (`products.py` & `product_repository.py`) uses a highly optimized hybrid approach for speed and typo-tolerance.

### The Search Algorithm (Tokenized, Weighted & Price-Aware)
1. **Tokenization:** The user's search query is split into individual lowercase words (tokens).
2. **Price Expression Recognition:** The system scans the full query for patterns like `under ₹500`, `above 300`, or `100 to 500`. If a product's price (MRP or case price) mathematically satisfies the expression, the expression tokens are marked as matched and the product receives a **doubled price weight bonus**.
3. **AND Logic Constraint:** Every single token in the search query *must* match at least one field in a product (or be part of a satisfied price expression), otherwise the product is completely discarded (Score = 0).
4. **Relevance Scoring:** If all tokens match, a `_searchScore` is calculated by summing the weights of the matched fields. The fields and their exact weights are:
   - `name`: 10
   - `sku`: 8
   - `searchTags`: 7 (Includes dynamically resolved tags)
   - `price`: 6 (Matches textual representations like "500", "rs 500")
   - `category`: 5
   - `subCategory`: 4
   - `collections`: 4
   - `brand`: 3
   - `variantAttributes`: 3 (Flattens all variant keys, values, and variant prices)
   - `description`: 1
5. **Sorting:** Products are sorted descending by `_searchScore`.
- **Performance:** To prevent thundering herds on concurrent heavy queries, building the lightweight catalog uses an `asyncio.Lock()`.

### Fuzzy Fallback (Typo Tolerance)
If the exact weighted search yields **fewer than 5 results**, the system automatically triggers a Fuzzy Search fallback.
- It uses Python's `difflib.SequenceMatcher` to compare tokens against product fields.
- **Thread Pool Offloading:** Because fuzzy matching is CPU-heavy, it is executed via `loop.run_in_executor` to avoid blocking the async event loop during high loads.
- **Threshold:** A word must have a similarity ratio of at least `0.7` (70%) to be considered a match.
- **Penalty:** If a match is fuzzy rather than exact, its score is multiplied by `0.8`.
- **"Did you mean?":** The system tracks the best fuzzy matches for misspelled words and returns a `suggestedQuery` string to the frontend.

### Dynamic Facets Generation
- When the user searches, the backend dynamically computes aggregations from the resulting product set.
- It returns a unique list of Brands, Categories, and Collections that are present *only* within those search results, alongside minimum and maximum price bounds. This powers the frontend filter sidebar perfectly without hardcoding.

### Real-Time Price Resolution
- Catalog responses strip out backend fields (like cost price).
- The `calculateTotalPrice` function computes the exact user-facing price on the fly depending on if the requester is a Guest, Retail Customer, or Wholesaler.

### Dynamic Product Tags & Previously Bought Indicator
The backend's `add_dynamic_tags()` method enriches every product in catalog responses with contextual signals rendered as visual badges on product cards. This runs for any **authenticated** user across all listing pages (Categories, Collections, Brands, Search, All Products).

| Signal | Badge Colour | Description |
|---|---|---|
| `isNew` | 🟢 Emerald | Product created in the last 30 days and never ordered by this user. |
| `bestSeller` | 🟡 Amber | Top-ranked product in its subcategory by weighted sales score. |
| `previouslyBought` | 🔵 Indigo | The logged-in user has **ever** purchased this product (all-time, no date cutoff). |

**How `previouslyBought` Works:**
1. When an authenticated user hits any product listing endpoint, the backend fetches all order history for that user (all-time).
2. It builds a set of all product IDs the user has ever bought and stamps `previouslyBought: true/false` onto every product in the response via the `ProductResponse` schema.
3. The frontend renders a subtle **"Previously Bought"** indigo pill badge on the product card image — visible in both `ProductCatalog` (grid view) and `HoverProductCard`.

> [!NOTE]
> Unlike recommendation exclusions (which hide purchased products using a 60-day window), `previouslyBought` is purely **informational**. Products still appear in all listings; the badge simply helps users instantly recognise items they have bought before.

---


## 5. Dynamic Content (Headless CMS)

- **Pages Managed:** FAQ, About Us, Privacy Policy, Terms & Conditions.
- **Storage:** Stored in the `content_repository` as JSON blocks.
- **Instant Sync:** Edits made in the Super Admin dashboard instantly invalidate the frontend cache, reflecting immediately on both the Next.js Web Application and the Expo React Native Mobile App.

---

## 6. Order Returns & Refunds Lifecycle

The system supports a complete flow for managing customer returns, overseen by the Super Admin and executed by Valets.

### Return Eligibility & Validation
- **Window:** The user must request the return within the `returnDays` threshold (default is 7 days after the order's `deliveredAt` timestamp).
- **Category Restrictions:** The requested items must belong to a category where `isReturnable` is true.
- **Quantity Constraints:** The system calculates the `maxQuantity` eligible by checking the original ordered amount and subtracting any quantities already returned or pending return in the `return_request_repository`.
- **Payment Method Constraints:** If the return is requested for a UPI order, the user MUST upload a screenshot (`upiPaymentScreenshot`) for verification before the return can be processed.

### The 4-Stage Return Workflow
1. **Pending (`PENDING`):** The customer submits the return request. The backend calculates the return delivery charge based on the customer's pincode and notifies the Super Admin.
2. **Assigned (`ASSIGNED`):** The Super Admin reviews the request and assigns it to a Valet for pickup. 
3. **Collected (`COLLECTED`):** The Valet physically collects the items from the customer and marks the status as Collected in their mobile app. This lets the Super Admin know that the physical items have been successfully retrieved from the customer, but they haven't arrived back at the warehouse yet.
4. **Returned / Completed (`RETURNED`):** The Super Admin receives the items at the warehouse, verifies their condition, and marks the request as Completed. 
   - *Automated Restocking:* Upon completion, the returned quantities are automatically added back to the `product_repository`'s global stock.
   - An email notification is sent to the user confirming the return.
*(Note: Admins can also mark a return as `REJECTED` at any point before completion, adding notes for the user).*

---

## 7. Customer Segmentation Engine

The backend features a dynamic segmentation engine (`customer_segments.py`) used to group users for targeted marketing, push notifications, and analytics. 

### Segmentation Types
- **Retail vs Business:** Segments are strictly split by user role (Customer vs Wholesaler).
- **Custom Segments:** Admins can create manual segments by applying filters.
- **System Segments:** 16 pre-defined, auto-maintained segments generated by the backend based on complex user behavior.

### Filter Criteria & Behavioral Logic
The engine can filter users across a matrix of data points:
- **Geographic:** State, City, District constraints.
- **Financial:** Minimum and maximum Average Order Value (`avg = total / count`).
- **Frequency:** Minimum and maximum Order Frequency.
- **App Usage:** Whether the user has installed the app (checked via the `deviceSubscriptions` table).
- **Date Range:** Orders placed between specific `startDate` and `endDate`.

### The Pre-Defined System Behaviors
The engine automatically buckets users into these actionable cohorts:
- `registered_no_order`: Registered but did not order.
- `registered_one_order`: Registered and ordered exactly once.
- `regular_registered`: Regular users (averaging >= 4 orders/month).
- `registered_irregular`: Irregular users (>1 order but <= 3 orders per month).
- `downloaded_no_order`: Downloaded the app but did not order.
- `downloaded_one_order`: Downloaded the app and ordered once.
- `regular_app_user`: Regular app user (averaging >= 4 orders/month).
- `downloaded_irregular`: App users with irregular frequency.

These segments can be "refreshed" by the Admin, which re-runs the SQL/Mongo aggregations in real-time to update the user list based on the latest purchase data.

---

## 8. Analytics & Event Tracking Engine

The platform includes a robust custom analytics layer (`analytics.py`) that syncs telemetry data from the frontend clients into the database.

### Event Tracking Stream
The client apps push a continuous stream of events to the backend, which are enriched with `userId` and timestamp data and synced to the `tracking_repository`. Captured events include:
- `session_start`, `session_end`, `page_view`
- `product_view` and `product_click` (powers the Multi-Armed Bandit recommendation engine)
- `add_to_cart`, `remove_from_cart`, `add_to_wishlist`
- `search` (capturing the search query and the number of results returned)

### Administrative Reporting
The dashboard queries the backend to generate complex business reports:
- **Conversion Funnel:** Tracks user progression through: `Session Start -> Cart -> Checkout -> Purchase Completed`.
- **Market Basket Analysis:** Computes products most frequently "bought together" (`/reports/items-bought-together`).
- **Cohort Analysis:** Tracks retention of new customers vs returning customers over time.
- **Product Sell-Through Rate:** Tracks inventory velocity (how quickly products sell out compared to their available stock).
- **KPI Metrics:** Sales broken down by Channel (Web vs App), Device Type, Location, and Payment Method.

---

## 9. Push Notifications & Engagement

The notification system (`push_notifications.py`) supports targeted, scheduled messaging to both the mobile app and progressive web app (PWA).

### Device Registration & Delivery
- **Mobile Apps (React Native):** Devices are registered using Expo Push Tokens (`expoToken`).
- **Web App (Next.js PWA):** Browsers are registered using VAPID keys for secure Web Push delivery.

### Audience Targeting
Admins do not need to select individual users. The system hooks directly into the **Customer Segmentation Engine** (Section 7). Notifications can be dispatched targeting specific `userSegment` or `userBehavior` cohorts (e.g., sending a re-engagement coupon specifically to the `downloaded_no_order` segment).

### Security & Idempotency
- When a user interacts with a notification, the frontend calls the `/mark-read` endpoint.
- To prevent spoofing of read metrics, the backend strictly verifies that the authenticated user's ID was mathematically part of the original targeted audience before tracking the interaction.

---

## 10. Product Bundles (Curated Kits)

The application supports Admin-managed custom bundles (`bundles.py`), allowing multiple products to be sold together at a fixed discount price. Bundles now natively store metadata like `category`, `subCategory`, `brand`, and `searchTags`.

### Bundle Search Engine
Bundles can be natively searched via a dedicated endpoint.
- Supports text searching (name, description, tags) as well as the exact same price-expression matching as the product search (e.g. `under 500`).
- **Dynamic Facet Resolution:** If a bundle does not have an admin-set category or brand, the search engine dynamically infers them by aggregating the categories and brands of its component products.

### Bundle Stock Engine
Unlike individual products, bundles do not have their own stock counter in the database. Instead:
- When a user views a bundle, the backend dynamically calculates `isAvailable` by iterating through every product required for the bundle and checking the global `product_repository` and `stock_reservation_repository`.
- If any single component product goes out of stock, the entire bundle automatically marks itself as unavailable.

### Cart Unpacking Logic
When a user adds a bundle to their cart, the system does not add it as a single "Bundle" item. 
- It unpacks the bundle into its constituent products.
- Each product is added to the cart normally, but tagged with a hidden `bundleId`.
- This ensures that stock deduction and returns can be handled at the individual product level while visually grouping them as a bundle in the frontend UI.
- *Note:* Unlike normal cart additions, unpacking a bundle into the cart **no longer removes** those items from the user's wishlist, preserving them for future intent.

---

## 11. Authentication, OTP, & Security Lifecycle

The Authentication system (`auth.py`) is protected by rate limiters and external webhook verification to prevent spam.

### Registration Flow & Phone/Email Verification
- The user submits their phone number or email address. A rate-limited (`5/minute`) endpoint triggers an OTP via the external SMS provider (MSG91) or email system.
- The system can verify the OTP in two ways:
  1. **Direct OTP input:** Validated against the internal database.
  2. **MSG91 Widget Token:** A third-party token is sent to the backend, which verifies it directly with MSG91 servers (`verify_msg91_widget_token`).
- Registration is blocked if the phone/email already exists in the `user_repository`.

### Wholesaler Role Elevation
- A wholesaler can register via the app, but they are initially forced into an `approvalStatus = "pending"`.
- If a deactivated or pending wholesaler logs in, the backend computes their `effectiveRole` as `"customer"`. This allows them to browse the app and buy retail products while they wait for Super Admin approval to access B2B pricing.

### Right-to-Erasure (Data Privacy)
- A highly destructive `/me` endpoint allows authenticated users to permanently delete their account.
- It intercepts their active `sessionId`, revokes it globally in the `session_repository` to destroy any in-flight access tokens, and wipes their identity from the database.

---

## 12. Referral Code Engine

The system supports a referral tracking program designed exclusively to acquire new Retail customers (`referrals.py`).

### Strict Eligibility Rules
1. **Role Restriction:** The user's `effectiveRole` must be `"customer"`. Wholesalers are not eligible for referral discounts.
2. **First Order Only:** The backend queries the `order_repository` to count past orders. If `order_count > 0`, the referral code is rejected.
3. **Anti-Fraud:** The system checks if `str(referrer._id) == str(current_user._id)` to completely block users from entering their own referral code.

### Scheme Tracking
- Admins configure the active global discount (Percentage vs Fixed Amount) in the referral settings.
- If verified successfully during checkout, the referral discount is mathematically distributed proportionally across all items in the cart (just like standard coupons) to ensure partial refunds are calculated fairly.

---

## 13. Customer Support & Helpdesk Workflows

The platform includes a built-in unified ticketing system (`support_tickets.py`) allowing users to escalate issues directly from the app.

### Data Aggregation Layer
- When a user submits a ticket, the backend intercepts their `current_user._id` (if logged in).
- For unauthenticated users (Guests), the backend parses their payload data (`name`, `email`, `phone`, `company`) to map them gracefully. 
- When an Admin fetches a ticket, a "Population Engine" seamlessly maps `user`, `assignedTo`, and `responses` out of raw IDs into fully hydrated user objects.

### Admin Escalation & Responses
- Support tickets contain strict access checks (`user == current_user._id`), meaning customers can only view and update their own tickets.
- Super Admins can assign tickets to specific admin personnel (`assignedTo`).
- When an Admin responds to a thread, the backend forces the `isAdminResponse` boolean to `true`, providing visual distinction on the frontend.

---

## 14. Product Reviews & Rating Engine

The application manages customer feedback through a moderated review workflow (`reviews.py`).

### Review Eligibility (Proof of Purchase)
- To prevent spam and fake reviews, the backend enforces a rigorous "Proof of Purchase" lock.
- Before a review is accepted, the backend queries the `order_repository` searching for `user == current_user._id` and `status == "delivered"`.
- It then scans every single item within those delivered orders. Only if the exact `productId` is found inside a delivered order will the review be permitted.

### The Moderation Pipeline
1. **Pending Status:** All user-submitted reviews enter the database with `status = "pending"`. They are completely hidden from the public product page.
2. **Admin Action:** A Super Admin reviews the text. They can click `Approve` or `Remove`.
3. **Live Recalculation:** If approved, the backend instantly intercepts the action. It recalculates the mathematical average of all approved ratings for that product and strictly updates the `rating` and `reviews` (count) fields on the root `product_repository`.
4. **Classification System:** Admins map reviews into pre-defined tags (e.g., "Quality", "Delivery Speed") stored dynamically in the `review_classification_repository`. Users are forced to choose an active classification tag before submitting their review.

---

## 15. Multi-Vendor Marketplace & Commission Engine

The platform operates a full multi-vendor marketplace model (`commission.py`, `sub_order_repository.py`), allowing third-party merchants to sell alongside platform inventory.

### Multi-Vendor Inventory & Sub-Orders
- Products in the catalog can belong to the platform (`sellerId = None`) or specific third-party vendors (`sellerId = <user_id>`).
- Customers enjoy a unified cart experience. If items from multiple vendors are purchased together, the system automatically creates a parent order and splits it into independent sub-orders for each seller upon checkout.
- Sellers can independently view, accept, pack, and dispatch their assigned sub-orders.
- **Valet Multi-Pickup:** A valet assigned to a multi-vendor order must visit each seller to collect their respective items. The valet triggers `ConfirmPickup` for each sub-order. Only when *all* sibling sub-orders are picked up does the parent order transition to `out_for_delivery`, triggering a notification to the customer.

### Commission Configuration & Hierarchy
The platform computes marketplace commission on every delivered order item:
1. **Seller-Level Override:** Super Admins can configure a fixed commission percentage for a specific seller (`PUT /api/commission/sellers/{id}/override`). If set, this override takes absolute precedence.
2. **Global Value-Based Tiers:** If no seller-level override is defined, the system evaluates global commission tiers (`GET/PUT /api/commission/tiers`) based on the order's subtotal value (e.g., ₹0–₹500: 8%, ₹501–₹2000: 6%, ₹2001+: 4%).
3. **Default Fallback:** If no tier matches, a global default commission rate (default 5.0%) is applied.

### Commission Lifecycle & Realization
To protect against returns and refunds, commission follows a strict two-stage realization lifecycle:
- **`pending` / `processing` / `shipped`:** No commission is recorded yet.
- **`delivered`:** The commission percentage and total commission amount are calculated. The sub-order status is stamped with `commissionStatus = "unrealized"`. The funds are held in escrow.
- **`delivered + returnDays elapsed`:** Once the statutory return window (default 7 days after delivery) closes without a return, the commission status transitions to `commissionStatus = "realized"`. Net seller earnings are then finalized and made available for vendor payout settlement.

---

## 16. Valet Scheduling, Matching & Auto-Cascade Dispatch Engine

The platform features an automated, intelligent logistics engine (`valet_availability.py`, `valet_timeout_job.py`, `orders.py`) to manage local delivery fulfillment.

### 1. Valet Pre-Shift Availability & Duty Status
- **Shift Scheduling:** Valets can schedule their availability up to 7 days in advance via the mobile app (`POST /valet-availability`), choosing either `full_day` or specific time slots (`custom`).
- **Live Duty Status:** Valets toggle `isOnDuty: True/False` in real-time. Only on-duty valets can receive new order dispatches.
- **Service Areas:** Each valet is configured with a list of serviceable pincodes (`serviceAreaPincodes`).

### 2. 4-Step Valet Eligibility Matcher
When an Admin or Seller triggers a dispatch (`PUT /orders/{id}/dispatch`), the backend executes a 4-step eligibility algorithm to select the best delivery agent:
1. **On-Duty Check:** `role == 'valet'` and `isOnDuty == True`.
2. **Pincode Match:** The seller's pickup pincode must be included in the valet's `serviceAreaPincodes`.
3. **Availability & Slot Check:** The valet must have marked availability for the order date and matching time slot.
4. **Capacity Sorting:** Eligible valets are ranked by their active delivery load (ascending). The order is dispatched to the least busy valet.

### 3. Acceptance Window & Auto-Cascade Engine
- **Dispatch Offer (`pending_valet`):** The selected valet receives an instant push notification. The order enters `pending_valet` status with an assigned countdown window:
  - **Urgent Delivery:** **5 minutes** acceptance window.
  - **Standard Delivery:** **20 minutes** acceptance window.
- **Valet Response (`PUT /orders/{id}/valet-response`):**
  - **Accept:** Status moves to **`shipped`**, `assignedValet` is permanently stamped, the seller is notified, and B2B invoices are auto-generated.
  - **Decline:** The valet's ID is appended to `valetDeclineHistory`, `valetCascadeCount` increments, and the system immediately cascades the offer to the next best eligible valet.
- **Background Timeout Watchdog (`valet_timeout_job.py`):**
  - Runs every **1 minute**.
  - Scans all orders in `pending_valet` whose acceptance window has expired without a response.
  - Automatically logs the timeout into `valetDeclineHistory` and cascades the order to the next available valet.
  - **Fallback when all valets are exhausted:** If no eligible valets remain, the order status safely reverts back to **`processing`** (`pendingValetId = None`) and an urgent push notification is dispatched to the Seller/Admin requesting manual reassignment.
  - Note: The exact same 20-minute auto-cascade engine governs Return pickups (using `PENDING_VALET` status), dynamically finding the next eligible valet to collect physical returns.

---

## 17. Delivery Slots Engine

The platform allows customers to select precise fulfillment windows (Delivery Slots) during checkout or when scheduling returns.

### Slot Configuration
- **Platform vs Seller Slots:** Slots can be configured globally by the Super Admin or scoped directly to a specific `sellerId`.
- **Constraint Matrix:** A configuration object (`DeliverySlotConfig`) restricts slots to specific dates, segments (Retail vs B2B), and target `pincodes`.
- **Capacity & Expiry:** Each slot has a strict `capacity` limit. Once `bookedCount >= capacity`, the slot is locked. 
- **Urgent Delivery Rules:** Slots can be marked as `isUrgent` (which triggers the Urgent Delivery surcharge at checkout). They are governed by `cutoffHours` and `urgentCutoffHours`, preventing users from booking a slot if the current time exceeds the configured window.

### Checkout & Return Slot Booking
- During checkout, the customer retrieves available slots. If buying from a specific seller who has defined slots, the engine strictly offers those; otherwise, it gracefully falls back to the Platform-wide slots.
- When an order or return is finalized, the engine automatically increments the `bookedCount` for the chosen `deliverySlotId` within a transaction-safe flow to prevent double booking.
