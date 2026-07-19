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

### Valet (Delivery Agent)
- **Capabilities:** Limited to viewing assigned orders (`assignedValet == current_user._id`). Can update order status (e.g., to "Delivered").

### Super Admin
- **Capabilities:** Full control over product catalogs, category mapping, coupon generation, delivery rules, user approval, payment verification, and dynamic content.

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
- **Criteria:** Fetches all products created within the last 30 days, sorted by newest first.
- **Retail Exclusions:** If a retail user is logged in, the system scans their entire order history and automatically hides products they have already purchased, ensuring the section only shows *unbought* new products.
- **Limit:** Displays the top 10 products.

#### B. Trending Now (Conversion Based)
Calculated via a complex journey mapping: `Conversion Rate = Converted Sales Count / Search Count`.
- To qualify, a product must have been searched at least 10 times (`min_search_count = 10`) in the last 7 days.
- A "Converted Sale" only counts if the exact same user/session searched for the product *and then bought it* within those 7 days.
- Takes the top 5 products per subcategory.
- **For Retail/Guest:** Uses only retail orders.
- **For Wholesalers:** Uses only wholesaler orders (`ORDER-WH-` prefix).
- **Exclusions:** Automatically excludes products already in the user's cart, purchased in the last 60 days, or shown in the *Customer Favourites* section.

#### C. Customer Favourites (Weighted Score)
- **Formula:** `(0.7 * Order Frequency) + (0.3 * Total Quantity Sold)`.
- Pulls from Retail Orders (`ORDER-RT-` prefix) over the last 60 days.
- Picks the single best product (Rank 1) per subcategory.
- Highly cached (TTL based) due to heavy calculation.

#### D. Business Favourites
- Same formula as Customer Favourites, but strictly calculates using Wholesaler orders.
- Displayed only to Wholesalers.

#### E. Explore (User-Centric Discovery)
- Looks at the logged-in user's purchase history over the last 60 days.
- Identifies the 5 subcategories the user has bought the *least* from.
- Recommends the #1 best-selling product from each of those neglected subcategories.

---

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

### Step 7: Post-Checkout Actions (All Methods)
- Stock reservations (`stock_reservation_repository`) are cleared and permanently deducted from the main product inventory.
- The user's cart is emptied.
- A PDF invoice is dynamically generated (`invoice_generator.py`) and saved to cloud storage.
- The Super Admin receives an instant push notification via `notification_repository` regarding the new order.

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

### The Search Algorithm (Tokenized & Weighted)
1. **Tokenization:** The user's search query is split into individual lowercase words (tokens).
2. **AND Logic Constraint:** Every single token in the search query *must* match at least one field in a product, otherwise the product is completely discarded (Score = 0).
3. **Relevance Scoring:** If all tokens match, a `_searchScore` is calculated by summing the weights of the matched fields. The fields and their exact weights are:
   - `name`: 10
   - `sku`: 8
   - `searchTags`: 7 (Includes dynamically resolved tags)
   - `category`: 5
   - `subCategory`: 4
   - `collections`: 4
   - `brand`: 3
   - `variantAttributes`: 3 (Flattens all variant keys and values into a searchable string)
   - `description`: 1
4. **Sorting:** Products are sorted descending by `_searchScore`.

### Fuzzy Fallback (Typo Tolerance)
If the exact weighted search yields **fewer than 5 results**, the system automatically triggers a Fuzzy Search fallback.
- It uses Python's `difflib.SequenceMatcher` to compare tokens against product fields.
- **Threshold:** A word must have a similarity ratio of at least `0.7` (70%) to be considered a match.
- **Penalty:** If a match is fuzzy rather than exact, its score is multiplied by `0.8`.
- **"Did you mean?":** The system tracks the best fuzzy matches for misspelled words and returns a `suggestedQuery` string to the frontend.

### Dynamic Facets Generation
- When the user searches, the backend dynamically computes aggregations from the resulting product set.
- It returns a unique list of Brands, Categories, and Collections that are present *only* within those search results, alongside minimum and maximum price bounds. This powers the frontend filter sidebar perfectly without hardcoding.

### Real-Time Price Resolution
- Catalog responses strip out backend fields (like cost price).
- The `calculateTotalPrice` function computes the exact user-facing price on the fly depending on if the requester is a Guest, Retail Customer, or Wholesaler.

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

The application supports Admin-managed custom bundles (`bundles.py`), allowing multiple products to be sold together at a fixed discount price.

### Bundle Stock Engine
Unlike individual products, bundles do not have their own stock counter in the database. Instead:
- When a user views a bundle, the backend dynamically calculates `isAvailable` by iterating through every product required for the bundle and checking the global `product_repository` and `stock_reservation_repository`.
- If any single component product goes out of stock, the entire bundle automatically marks itself as unavailable.

### Cart Unpacking Logic
When a user adds a bundle to their cart, the system does not add it as a single "Bundle" item. 
- It unpacks the bundle into its constituent products.
- Each product is added to the cart normally, but tagged with a hidden `bundleId`.
- This ensures that stock deduction and returns can be handled at the individual product level while visually grouping them as a bundle in the frontend UI.

---

## 11. Authentication, OTP, & Security Lifecycle

The Authentication system (`auth.py`) is protected by rate limiters and external webhook verification to prevent spam.

### Registration Flow & Phone Verification
- The user submits their phone number. A rate-limited (`5/minute`) endpoint triggers an OTP via the external SMS provider (MSG91).
- The system can verify the OTP in two ways:
  1. **Direct OTP input:** Validated against the internal database.
  2. **MSG91 Widget Token:** A third-party token is sent to the backend, which verifies it directly with MSG91 servers (`verify_msg91_widget_token`).
- Registration is blocked if the phone number already exists in the `user_repository`.

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
