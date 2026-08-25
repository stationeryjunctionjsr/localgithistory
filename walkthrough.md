# UI/UX Improvements Walkthrough

All changes made across desktop browser, mobile browser, and mobile app (Expo).
No visual redesigns -- only bug fixes, code quality improvements, and missing feature sync.

---

## Phase 1: Banner Sync (Desktop to Mobile App)

### 1. Created shared `BannerCarousel` component
**File:** `frontend/mobile/src/components/BannerCarousel.tsx` (NEW)
- Reusable banner carousel with horizontal FlatList, auto-advance (4s), dot indicators
- `onPress` navigates via `router.push(banner.linkUrl)` when a link URL exists
- Configurable `height`, `autoPlayInterval`, `horizontalPadding` props
- Styles extracted from home.tsx banner code (exact match)

### 2. Fixed home banner tap-through
**File:** `frontend/mobile/app/(tabs)/home.tsx`
- Added `linkUrl` and `link` fields to the `Banner` interface
- Replaced inline banner FlatList + dots + auto-scroll with `<BannerCarousel>` component
- Removed redundant code: `BANNER_WIDTH`, `BANNER_HEIGHT` constants, `currentBannerIndex` state, `bannerRef` ref, auto-scroll `useEffect`, `renderBannerItem` function, 8 unused style definitions
- Removed stale comment about expo-linear-gradient not being installed

### 3. Fixed categories tab banner
**File:** `frontend/mobile/app/(tabs)/categories.tsx`
- Changed `pageType` from `'Category'` to `'all_categories'` to match desktop API pattern
- Replaced single static `Image` with `<BannerCarousel>` (now supports multiple banners + tap-through)
- Added `BannerCarousel` import

### 4. Added banners to brands tab
**File:** `frontend/mobile/app/(tabs)/brands.tsx`
- Added `useAuth` hook and `banners` state
- Added banner fetch (`position: 'all_brands_mobile'`, `pageType: 'all_brands'`) in existing `Promise.all`
- Renders `<BannerCarousel>` between header and brand grid

### 5. Added banners to ProductsList
**File:** `frontend/mobile/app/products/index.tsx`
- Added `banners?: any[]` to `ProductsListProps`
- Added self-fetch for standalone `/products` route (`position: 'products_mobile'`, `pageType: 'all_products'`)
- `renderScrollableHeader` shows `BannerCarousel` when banners available, falls back to entity image or text header

### 6. Added banners to category detail
**File:** `frontend/mobile/app/categories/[slug].tsx`
- Fetches banners with `pageType: 'Category'`, `pageId: slug` (matches desktop)
- Passes `banners` prop to `ProductsList`

### 7. Added banners to brand detail
**File:** `frontend/mobile/app/brands/[slug].tsx`
- Fetches banners with `pageType: 'Brand'`, `pageId: slug` (matches desktop)
- Passes `banners` prop to `ProductsList`

### 8. Added banners to collection detail
**File:** `frontend/mobile/app/collections/[slug].tsx`
- Fetches banners with `pageType: 'Collection'`, `pageId: slug` (matches desktop)
- Passes `banners` prop to `ProductsList`

---

## Phase 2: P0 Bug Fixes

### 9. Fixed mobile search deep linking
**File:** `frontend/mobile/app/products/index.tsx`
- Added `initialSearch` that reads both `search` and `searchTerm` URL params
- Initialized `search` state with `initialSearch` (was hardcoded to `''`)
- Search from home/search overlay now works when navigating to `/products?search=...`

### 10. Fixed mobile checkout UPI copy
**File:** `frontend/mobile/app/checkout.tsx`
- Replaced fake `Alert.alert('Copied')` with actual `Clipboard.setStringAsync(upiDetails.upiId)`
- Installed `expo-clipboard` package

### 11. Fixed desktop ProductCatalog popularity filter duplicate
**File:** `frontend/src/components/ProductCatalog.tsx`
- Removed duplicate `params.append('popularity', filters.popularity)` (was appended twice)

### 12. Fixed desktop orders infinite loading
**File:** `frontend/src/app/customer/orders/page.tsx`
- Added `else if (!loading) { setLoading(false) }` when `user` is null
- Previously, if user was never set, `loading` stayed `true` forever with no UI

### 13. Fixed desktop search param mismatch
**File:** `frontend/src/components/MobileComponents/MobileHeader.tsx`
- Changed search URL from `?search=` to `?searchTerm=` to match what `ProductCatalog` reads
- Mobile browser search now correctly triggers product listing filtering

### 14. Fixed mobile cart error state
**File:** `frontend/mobile/app/(tabs)/cart.tsx`
- Added `fetchError` state tracking
- On API failure, shows "Could not load cart" with retry button instead of misleading empty cart

### 15. Fixed mobile orders error state + pull-to-refresh
**File:** `frontend/mobile/app/orders/index.tsx`
- Added `fetchError` state tracking
- On API failure, shows "Could not load orders" with retry button instead of empty "No orders yet"
- Added `RefreshControl` to FlatList for pull-to-refresh

### 16. Fixed mobile wishlist error state
**File:** `frontend/mobile/app/wishlist.tsx`
- Added `fetchError` state tracking
- On API failure, shows "Could not load wishlist" with retry button instead of misleading empty list

---

## Phase 3: Code Quality and Consistency Fixes

### 17. Fixed desktop orders payment status chip
**File:** `frontend/src/app/customer/orders/page.tsx`
- Payment status chip was always yellow regardless of status
- Now shows green for 'paid', red for 'failed', yellow for 'pending'/other

### 18. Fixed inconsistent add-to-cart feedback
**File:** `frontend/src/components/ProductCatalog.tsx`
- Replaced `alert()` calls with `toast.success()` / `toast.error()` (react-toastify)
- Matches feedback pattern used in cart and other pages

### 19. Fixed BottomNav hardcoded accent color
**File:** `frontend/src/components/MobileComponents/BottomNav.tsx`
- Replaced hardcoded `const MOBILE_ACCENT = '#1a4d33'` with `theme.primary` from `useTheme()`
- Now stays in sync if theme changes (matches MobileHeader which already uses `theme.primary`)

### 20. Fixed mobile profile guest modal re-showing
**File:** `frontend/mobile/app/(tabs)/profile.tsx`
- Removed `useFocusEffect` that reset `showMenu` to `true` on every tab focus
- Added `guestDismissed` state -- once user taps "Maybe later", backdrop, or back, modal stays dismissed for the session

### 21. Fixed ProductCatalog breadcrumb
**File:** `frontend/src/components/ProductCatalog.tsx`
- Guest "Home" breadcrumb linked to `/landingpage` instead of `/`
- Changed to `/` to match the actual app home route

### 22. Fixed product detail image alt typo
**File:** `frontend/src/components/ProductDetailClient.tsx`
- Changed `"vision"` to `"view"` in image alt text

### 23. Cleaned up dead code in LandingPageClient
**File:** `frontend/src/components/LandingPageClient.tsx`
- Removed `currentBannerIndex` state + its `useEffect` interval (HeroCarousel manages its own state)
- Removed 7 never-called fetch functions: `fetchGoogleRating`, `fetchProducts`, `fetchRecommendations`, `fetchBrands`, `fetchCategoryTags`, `fetchCategories`, `fetchCollections`

### 24. Cleaned up unused import in wishlist
**File:** `frontend/src/app/customer/wishlist/page.tsx`
- Removed unused `useRouter` import and `router` variable

---

## Skipped Items (Would Change Page Appearance)

- **Mobile profile stubbed actions** (edit profile, payments, notifications, settings): Requires new screens
- **Guest cart badge on mobile browser**: Requires integrating guestCartService into MobileHeader/BottomNav

---

## New Dependencies

- `expo-clipboard` added to `frontend/mobile/package.json` (for UPI copy fix)

---

## Files Changed Summary

| # | File | Type |
|---|------|------|
| 1 | `frontend/mobile/src/components/BannerCarousel.tsx` | NEW |
| 2 | `frontend/mobile/app/(tabs)/home.tsx` | EDIT |
| 3 | `frontend/mobile/app/(tabs)/categories.tsx` | EDIT |
| 4 | `frontend/mobile/app/(tabs)/brands.tsx` | EDIT |
| 5 | `frontend/mobile/app/products/index.tsx` | EDIT |
| 6 | `frontend/mobile/app/categories/[slug].tsx` | EDIT |
| 7 | `frontend/mobile/app/brands/[slug].tsx` | EDIT |
| 8 | `frontend/mobile/app/collections/[slug].tsx` | EDIT |
| 9 | `frontend/mobile/app/checkout.tsx` | EDIT |
| 10 | `frontend/mobile/app/(tabs)/cart.tsx` | EDIT |
| 11 | `frontend/mobile/app/orders/index.tsx` | EDIT |
| 12 | `frontend/mobile/app/wishlist.tsx` | EDIT |
| 13 | `frontend/mobile/app/(tabs)/profile.tsx` | EDIT |
| 14 | `frontend/src/components/ProductCatalog.tsx` | EDIT |
| 15 | `frontend/src/components/MobileComponents/MobileHeader.tsx` | EDIT |
| 16 | `frontend/src/components/MobileComponents/BottomNav.tsx` | EDIT |
| 17 | `frontend/src/app/customer/orders/page.tsx` | EDIT |
| 18 | `frontend/src/app/customer/wishlist/page.tsx` | EDIT |
| 19 | `frontend/src/app/support/page.tsx` | NOT CHANGED (AuthModal left as-is, removing would need testing) |
| 20 | `frontend/src/components/LandingPageClient.tsx` | EDIT |
| 21 | `frontend/src/components/ProductDetailClient.tsx` | EDIT |
| 22 | `frontend/mobile/package.json` | EDIT (expo-clipboard added) |

---

## Phase 4: Profile Menu Cleanup & New Screens

### 25. Profile menu cleanup
**File:** `frontend/mobile/app/(tabs)/profile.tsx`
- Removed "Payments" quick action button (payments are accessed through orders)
- Removed "Settings" menu item (no settings functionality exists)
- Removed "Notifications" menu item (no notification system exists)
- Added "FAQs", "About Us", and "Privacy Policy" menu items to **both** logged-in and guest profile menus
- Wired edit button (pencil icon) on user card to `/edit-profile`
- Wired guest "FAQs" and "About Us" buttons (were `onPress={() => {}}`)
- Removed unused imports: `useFocusEffect`, `useCallback`, `useEffect`

### 26. Created Edit Profile screen
**File:** `frontend/mobile/app/edit-profile.tsx` (NEW)
- Mirrors desktop profile edit functionality (`PUT /users/:id`)
- Sections: Personal Details (name, email, phone locked), Business Details (wholesaler only: company name, GSTIN, location link), Address (full address form)
- Change Password section with collapsible toggle (`PUT /users/:id/password`)
- Save button disabled until changes are detected (deep comparison)
- Keyboard-avoiding scroll view for form usability

### 27. Created FAQ page
**File:** `frontend/mobile/app/faq.tsx` (NEW)
- 5 sections: Orders & Delivery, Payments, Account, Wholesaler Accounts, Returns & Refunds
- Accordion-style expandable Q&A items with smooth layout animation
- "Still have questions?" banner linking to Customer Support
- Accessible from both logged-in and guest profile menus

### 28. Created About Us page
**File:** `frontend/mobile/app/about.tsx` (NEW)
- Brand section with app name and tagline
- Our Mission and What We Offer sections
- Contact info with tappable links (website, email, support)
- Quick links to Privacy Policy and FAQs
- App version footer

### 29. Created Privacy Policy page
**File:** `frontend/mobile/app/privacy-policy.tsx` (NEW)
- 8 sections covering data collection, usage, sharing, security, rights, analytics, changes, and contact
- Clean typographic layout with bullet lists
- Linked from profile menu and About Us page

---

## Updated Files Changed Summary

| # | File | Type |
|---|------|------|
| 1 | `frontend/mobile/src/components/BannerCarousel.tsx` | NEW |
| 2 | `frontend/mobile/app/(tabs)/home.tsx` | EDIT |
| 3 | `frontend/mobile/app/(tabs)/categories.tsx` | EDIT |
| 4 | `frontend/mobile/app/(tabs)/brands.tsx` | EDIT |
| 5 | `frontend/mobile/app/products/index.tsx` | EDIT |
| 6 | `frontend/mobile/app/categories/[slug].tsx` | EDIT |
| 7 | `frontend/mobile/app/brands/[slug].tsx` | EDIT |
| 8 | `frontend/mobile/app/collections/[slug].tsx` | EDIT |
| 9 | `frontend/mobile/app/checkout.tsx` | EDIT |
| 10 | `frontend/mobile/app/(tabs)/cart.tsx` | EDIT |
| 11 | `frontend/mobile/app/orders/index.tsx` | EDIT |
| 12 | `frontend/mobile/app/wishlist.tsx` | EDIT |
| 13 | `frontend/mobile/app/(tabs)/profile.tsx` | EDIT |
| 14 | `frontend/mobile/app/edit-profile.tsx` | NEW |
| 15 | `frontend/mobile/app/faq.tsx` | NEW |
| 16 | `frontend/mobile/app/about.tsx` | NEW |
| 17 | `frontend/mobile/app/privacy-policy.tsx` | NEW |
| 18 | `frontend/src/components/ProductCatalog.tsx` | EDIT |
| 19 | `frontend/src/components/MobileComponents/MobileHeader.tsx` | EDIT |
| 20 | `frontend/src/components/MobileComponents/BottomNav.tsx` | EDIT |
| 21 | `frontend/src/app/customer/orders/page.tsx` | EDIT |
| 22 | `frontend/src/app/customer/wishlist/page.tsx` | EDIT |
| 23 | `frontend/src/components/LandingPageClient.tsx` | EDIT |
| 24 | `frontend/src/components/ProductDetailClient.tsx` | EDIT |
| 25 | `frontend/mobile/package.json` | EDIT (expo-clipboard added) |

---

## Phase 5: Admin-Configurable Content Pages (FAQ, About Us, Privacy Policy)

### Backend API

### 30. Content repository
**File:** `backend/app/repositories/content_repository.py` (NEW)
- `ContentRepository` -- generic single-document store for About Us and Privacy Policy (get + upsert)
- `FAQRepository` -- multi-document store for FAQ sections with embedded Q&A items
- Uses `get_storage()` so it works with both FileStorage (JSON) and Oracle DB

### 31. Content pages router
**File:** `backend/app/routers/content_pages.py` (NEW)
- **FAQ**: `GET /api/content/faq/public` (no auth), `GET/POST /api/content/faq` (super_admin), `PUT/DELETE /api/content/faq/:id` (super_admin)
- **About Us**: `GET /api/content/about/public` (no auth), `GET/PUT /api/content/about` (super_admin)
- **Privacy Policy**: `GET /api/content/privacy/public` (no auth), `GET/PUT /api/content/privacy` (super_admin)
- Pydantic models: `FAQSectionCreate`, `FAQSectionUpdate`, `FAQItem`, `AboutUsUpdate`, `PrivacyPolicyUpdate`, `ContentSection`

### 32. Registered router in main.py
**File:** `backend/app/main.py` (EDIT)
- Added `from app.routers import content_pages` and `app.include_router(content_pages.router, prefix="/api/content", tags=["content-pages"])`

### Admin Frontend (Super Admin)

### 33. FAQ Management page
**File:** `frontend/src/app/admin/faq-management/page.tsx` (NEW)
- Full CRUD: create sections with title, icon, display order
- Inline Q&A editor: add/remove/edit questions and answers within each section
- Table-style section listing with question count and edit/delete buttons
- Modal form matching existing admin UI patterns (green gradient buttons, slate cards)

### 34. About Us Management page
**File:** `frontend/src/app/admin/about-management/page.tsx` (NEW)
- Editable fields: brand name, tagline, contact email, website
- Mission statement text area
- Dynamic "What We Offer" list (add/remove offerings)
- Additional custom sections (add/remove/edit title+body)
- Single "Save Changes" button that upserts the entire document

### 35. Privacy Policy Management page
**File:** `frontend/src/app/admin/privacy-management/page.tsx` (NEW)
- "Last Updated" label field
- Dynamic policy sections with title + content textarea
- Reorderable sections (move up/down buttons)
- Single "Save Changes" button

### 36. Admin sidebar updated
**File:** `frontend/src/components/Admin/AdminLayout.tsx` (EDIT)
- Added "Content Pages" group to `menuItems` with children: FAQ, About Us, Privacy Policy
- Added 4 SVG icons to `menuIcons`: `content-pages`, `faq-management`, `about-management`, `privacy-management`

### Mobile App (Dynamic Content)

### 37. FAQ page now fetches from API + search
**File:** `frontend/mobile/app/faq.tsx` (REWRITTEN)
- Fetches from `GET /api/content/faq/public` on mount; falls back to hardcoded sections if API empty
- **Search bar** at top: filters sections by matching question text OR answer text against the search term
- Shows "No results found" empty state when search yields no matches
- Accordion Q&A with smooth LayoutAnimation

### 38. About Us page now fetches from API
**File:** `frontend/mobile/app/about.tsx` (REWRITTEN)
- Fetches from `GET /api/content/about/public`; falls back to hardcoded defaults
- Renders admin-configured brand info, mission, offerings, custom sections, and contact info
- Loading state with ActivityIndicator

### 39. Privacy Policy page now fetches from API
**File:** `frontend/mobile/app/privacy-policy.tsx` (REWRITTEN)
- Fetches from `GET /api/content/privacy/public`; falls back to hardcoded defaults
- Renders admin-configured sections with "Last updated" date
- Loading state with ActivityIndicator

---

## Complete Files Changed Summary

| # | File | Type |
|---|------|------|
| 1 | `frontend/mobile/src/components/BannerCarousel.tsx` | NEW |
| 2 | `frontend/mobile/app/(tabs)/home.tsx` | EDIT |
| 3 | `frontend/mobile/app/(tabs)/categories.tsx` | EDIT |
| 4 | `frontend/mobile/app/(tabs)/brands.tsx` | EDIT |
| 5 | `frontend/mobile/app/products/index.tsx` | EDIT |
| 6 | `frontend/mobile/app/categories/[slug].tsx` | EDIT |
| 7 | `frontend/mobile/app/brands/[slug].tsx` | EDIT |
| 8 | `frontend/mobile/app/collections/[slug].tsx` | EDIT |
| 9 | `frontend/mobile/app/checkout.tsx` | EDIT |
| 10 | `frontend/mobile/app/(tabs)/cart.tsx` | EDIT |
| 11 | `frontend/mobile/app/orders/index.tsx` | EDIT |
| 12 | `frontend/mobile/app/wishlist.tsx` | EDIT |
| 13 | `frontend/mobile/app/(tabs)/profile.tsx` | EDIT |
| 14 | `frontend/mobile/app/edit-profile.tsx` | NEW |
| 15 | `frontend/mobile/app/faq.tsx` | NEW (rewritten for API) |
| 16 | `frontend/mobile/app/about.tsx` | NEW (rewritten for API) |
| 17 | `frontend/mobile/app/privacy-policy.tsx` | NEW (rewritten for API) |
| 18 | `frontend/src/components/ProductCatalog.tsx` | EDIT |
| 19 | `frontend/src/components/MobileComponents/MobileHeader.tsx` | EDIT |
| 20 | `frontend/src/components/MobileComponents/BottomNav.tsx` | EDIT |
| 21 | `frontend/src/app/customer/orders/page.tsx` | EDIT |
| 22 | `frontend/src/app/customer/wishlist/page.tsx` | EDIT |
| 23 | `frontend/src/components/LandingPageClient.tsx` | EDIT |
| 24 | `frontend/src/components/ProductDetailClient.tsx` | EDIT |
| 25 | `frontend/mobile/package.json` | EDIT (expo-clipboard added) |
| 26 | `backend/app/repositories/content_repository.py` | NEW |
| 27 | `backend/app/routers/content_pages.py` | NEW |
| 28 | `backend/app/main.py` | EDIT |
| 29 | `frontend/src/app/admin/faq-management/page.tsx` | NEW |
| 30 | `frontend/src/app/admin/about-management/page.tsx` | NEW |
| 31 | `frontend/src/app/admin/privacy-management/page.tsx` | NEW |
| 32 | `frontend/src/components/Admin/AdminLayout.tsx` | EDIT |

---

## Phase 6: Guest Cart Badge Fix

### 40. Guest cart badge on mobile browser MobileHeader
**File:** `frontend/src/components/MobileComponents/MobileHeader.tsx` (EDIT)
- Cart count fetch previously skipped entirely for guests (`if (!user) return`)
- Now reads `getGuestCart()` from `@/utils/guestStore` when user is null
- Guest users now see their cart item count badge in the header

### 41. Guest cart badge on mobile browser BottomNav
**File:** `frontend/src/components/MobileComponents/BottomNav.tsx` (EDIT)
- Same fix: reads guest cart from localStorage when user is null
- Cart tab now shows badge count for guest users

---

## Phase 7: G-Series Remaining Items & Audit Cleanup

### 42. G-19: Wishlist toggle in mobile product detail
**File:** `frontend/mobile/app/products/[id].tsx` (EDIT)
- Renamed `addToWishlist` to `toggleWishlist`
- If item is already wishlisted: calls `DELETE /wishlist/{productId}` (auth) or `removeGuestWishlistItem` (guest), sets `addedToWishlist = false`
- If not wishlisted: adds as before
- On mount, now checks wishlist status for both logged-in users (via `GET /wishlist`) and guests (via `isInGuestWishlist`), so heart renders correctly on page load
- Imported `removeGuestWishlistItem` from guestStore

### 43. G-15: Variant price/stock dynamic update in mobile product detail
**File:** `frontend/mobile/app/products/[id].tsx` (EDIT)
- Added `selectedCombination` computed value: finds the matching `variantCombination` when all variant attributes are selected
- `effectivePrice` now resolves from `selectedCombination?.price` first, falling back to `product.price`
- `effectiveMrp` resolves from `selectedCombination?.mrp` first, falling back to `product.mrp`
- `stockCount` resolves from `selectedCombination?.stock` first, falling back to `product.stock`
- Displayed price, MRP strike-through, discount %, and stock badge all update in real time when user taps a variant chip

### 44. G-14: Address add / edit / delete in mobile
**File:** `frontend/mobile/app/addresses.tsx` (REWRITTEN)
- Screen was previously a read-only list; now full CRUD
- "+" button in header opens an "Add Address" modal
- Each address card has edit (pencil) and delete (trash) icon buttons
- Edit pre-fills the form with existing address data
- Delete shows a confirmation alert before removing
- Save calls `PUT /users/{id}` with updated `savedAddresses` array; refreshes Zustand auth store via `setUser(res.data)`
- Required fields: Street, City, State, Pincode -- shows alert if missing
- Form fields: Name, Street, Address Line 2, Landmark, City, District, State, Country, Pincode, Mobile Number

---

## Phase 8: G-20 Skeleton Screens

### 45. Created reusable SkeletonLoader component
**File:** `frontend/mobile/src/components/SkeletonLoader.tsx` (NEW)
- `SkeletonBone` -- single animated bone with left-to-right shimmer using `Animated` + `LinearGradient` (expo-linear-gradient, already installed)
- `HomeScreenSkeleton` -- banner placeholder + two product row grids
- `ProductDetailSkeleton` -- full-height image + brand/name/price/variant chips/description blocks
- `CartScreenSkeleton` -- three cart item rows + summary/checkout box
- `OrdersListSkeleton` -- four order cards with header, status badge, amount, date placeholders

### 46. Home screen skeleton
**File:** `frontend/mobile/app/(tabs)/home.tsx` (EDIT)
- Replaced `ActivityIndicator` spinner with `HomeScreenSkeleton` during initial load

### 47. Product detail skeleton
**File:** `frontend/mobile/app/products/[id].tsx` (EDIT)
- Replaced `ActivityIndicator` spinner with `ProductDetailSkeleton` during load

### 48. Cart screen skeleton
**File:** `frontend/mobile/app/(tabs)/cart.tsx` (EDIT)
- Replaced `ActivityIndicator` spinner with `CartScreenSkeleton` during initial load

### 49. Orders list skeleton
**File:** `frontend/mobile/app/orders/index.tsx` (EDIT)
- Replaced `ActivityIndicator` spinner with `OrdersListSkeleton` during initial load

---

## Phase 9: Order Pagination + Wholesaler Mobile Dashboard

### 50. Order pagination — backend
**File:** `backend/app/routers/orders.py` (EDIT)
- `GET /orders` now accepts optional `page` and `limit` query params
- When both are provided, returns `{ orders, total, page, limit, hasMore }` instead of a plain array
- Backwards compatible: callers that don't pass page/limit still receive a plain array

### 51. Order pagination — mobile
**File:** `frontend/mobile/app/orders/index.tsx` (EDIT)
- Fetches 10 orders per page (`PAGE_SIZE = 10`)
- Infinite scroll: `onEndReached` on `FlatList` automatically fetches the next page
- Spinner footer while loading more; pull-to-refresh resets to page 1
- `isFetchingRef` guard prevents duplicate in-flight requests

### 52. Order pagination — desktop
**File:** `frontend/src/app/customer/orders/page.tsx` (EDIT)
- Shows 10 orders per page; numbered page buttons appear when `totalPages > 1`
- Previous / Next buttons flank numbered buttons; disabled at boundaries
- Date-filter changes reset to page 1 automatically
- Total order count shown next to pagination controls

### 53. Wholesaler mobile home screen
**Files:**
- `frontend/mobile/src/components/WholesalerHomeScreen.tsx` (NEW)
- `frontend/mobile/app/(tabs)/home.tsx` (EDIT)

**Previous state:** Wholesaler users on mobile saw the identical generic customer home screen (no B2B differentiation). Only the Schemes tab was added.

**New state:**
- `home.tsx` detects `user?.role === 'wholesaler'` and renders `WholesalerHomeScreen` instead of the standard customer home
- `WholesalerHomeScreen` features:
  - **Branded gradient header** (deep forest green) with company name, first-name greeting, and a gold "Business Account" badge
  - **Wholesaler-specific banners** (position: `wholesaler`, targetAudience filter); falls back to homepage banners if none are configured
  - **Quick action cards**: Browse Products, My Schemes, My Orders, My Profile
  - **Active Schemes preview** (top 3 with discount badge, see-all link to Schemes tab)
  - **Featured Collections** horizontal scroll
  - **Brand carousel** (logos only, tappable)
  - **Categories** horizontal chip scroll
  - **Browse All Products CTA** button at the bottom
  - Pull-to-refresh reloads all data

---

## Phase 10: Notifications, Coach Marks, Social Media, UI Fixes

### 54. Notifications screen linked from profile
**File:** `frontend/mobile/app/(tabs)/profile.tsx` (EDIT)
- **Previous state:** Notifications menu item had been removed from profile; the `notifications.tsx` screen existed but was unreachable
- **New state:** "Notifications" menu item added back, navigates to `/notifications`, placed above Customer Support

### 55. Coach marks commented out
**File:** `frontend/mobile/app/(tabs)/home.tsx` (EDIT)
- **Previous state:** `useCoachMarks` hook imported and called; two `<CoachMark>` JSX blocks rendered conditionally; auto-start was already disabled but all code was active
- **New state:** Import, `COACH_MARK_IDS` constant, `useCoachMarks` call, and both JSX blocks are commented out with a note "Coach marks deferred — uncomment to re-enable"

### 56. Social media links configurable from admin
**Files:**
- `backend/app/models/schemas.py` (EDIT)
- `frontend/src/app/admin/contacts/page.tsx` (EDIT)
- `frontend/src/app/support/page.tsx` (EDIT)

- **Previous state:** Instagram URL was hardcoded as `process.env.NEXT_PUBLIC_INSTAGRAM_URL || 'https://www.instagram.com/stationeryjunction_jamshedpur'` — no way to change it without a code/env deploy
- **New state:**
  - Backend `ContactBase` schema now includes optional `socialMedia` field (`instagram`, `facebook`, `twitter`, `whatsapp`, `youtube`, `linkedin`)
  - Admin contacts page has a "Social Media Links" section with URL inputs for all 6 platforms
  - Support page reads `contacts.find(c => c.socialMedia?.instagram)?.socialMedia?.instagram` at runtime, with the original URL as fallback

### 57. Desktop wishlist missing Header
**File:** `frontend/src/app/customer/wishlist/page.tsx` (EDIT)
- **Previous state:** Wishlist page had no navigation Header — users had no way to navigate to other pages except using the browser back button; inconsistent with cart, orders, and profile which all have the Header
- **New state:** `Header` component imported and rendered at the top of both the authenticated and unauthenticated states

### 58. Desktop cart UPI modal stuck state
**File:** `frontend/src/app/customer/cart/page.tsx` (EDIT)
- **Previous state:** `fetchUPIDetails` had an empty `catch {}` — if the API failed, `upiDetails` stayed `null`. The modal condition was `showUpiPayment && upiDetails`, so selecting UPI payment rendered absolutely nothing; users were stuck with no feedback
- **New state:**
  - Added `upiDetailsError` state; `fetchUPIDetails` now sets it on failure
  - Modal condition changed from `showUpiPayment && upiDetails` to just `showUpiPayment`
  - When `upiDetails` is null: shows either "Loading UPI details…" or a red error message with a Retry button
  - When `upiDetails` loads: renders the existing QR/UPI ID/screenshot flow unchanged

---

## Deferred Items (Not Implemented)

| Item | Reason |
|---|---|
| Color drift — checkout purple/indigo, register purple branding | Deferred by request |
| Copy scheme code button | Deferred by request |
| B2B minimum quantity enforcement | Deferred — quantity control removed from B2B flow |
| Accessibility pass (ARIA labels, focus traps, keyboard nav) | Deferred unless compliance required |

---

## Final Files Changed Summary

| # | File | Type | Phase |
|---|------|------|-------|
| 1 | `frontend/mobile/src/components/BannerCarousel.tsx` | NEW | 1 |
| 2 | `frontend/mobile/app/(tabs)/home.tsx` | EDIT | 1, 8, 9, 10 |
| 3 | `frontend/mobile/app/(tabs)/categories.tsx` | EDIT | 1 |
| 4 | `frontend/mobile/app/(tabs)/brands.tsx` | EDIT | 1 |
| 5 | `frontend/mobile/app/products/index.tsx` | EDIT | 1, 2 |
| 6 | `frontend/mobile/app/categories/[slug].tsx` | EDIT | 1 |
| 7 | `frontend/mobile/app/brands/[slug].tsx` | EDIT | 1 |
| 8 | `frontend/mobile/app/collections/[slug].tsx` | EDIT | 1 |
| 9 | `frontend/mobile/app/checkout.tsx` | EDIT | 2 |
| 10 | `frontend/mobile/app/(tabs)/cart.tsx` | EDIT | 2, 8 |
| 11 | `frontend/mobile/app/orders/index.tsx` | EDIT | 2, 8, 9 |
| 12 | `frontend/mobile/app/wishlist.tsx` | EDIT | 2 |
| 13 | `frontend/mobile/app/(tabs)/profile.tsx` | EDIT | 3, 4, 10 |
| 14 | `frontend/mobile/app/edit-profile.tsx` | NEW | 4 |
| 15 | `frontend/mobile/app/faq.tsx` | NEW → REWRITTEN | 4, 5 |
| 16 | `frontend/mobile/app/about.tsx` | NEW → REWRITTEN | 4, 5 |
| 17 | `frontend/mobile/app/privacy-policy.tsx` | NEW → REWRITTEN | 4, 5 |
| 18 | `frontend/mobile/app/addresses.tsx` | REWRITTEN | 7 |
| 19 | `frontend/mobile/app/products/[id].tsx` | EDIT | 7, 8 |
| 20 | `frontend/mobile/app/notifications.tsx` | NEW (by user) | 10 |
| 21 | `frontend/mobile/src/components/SkeletonLoader.tsx` | NEW | 8 |
| 22 | `frontend/mobile/src/components/WholesalerHomeScreen.tsx` | NEW | 9 |
| 23 | `frontend/mobile/package.json` | EDIT | 2 |
| 24 | `frontend/src/components/ProductCatalog.tsx` | EDIT | 2, 3 |
| 25 | `frontend/src/components/MobileComponents/MobileHeader.tsx` | EDIT | 2, 6 |
| 26 | `frontend/src/components/MobileComponents/BottomNav.tsx` | EDIT | 3, 6 |
| 27 | `frontend/src/components/ProductDetailClient.tsx` | EDIT | 3 |
| 28 | `frontend/src/components/LandingPageClient.tsx` | EDIT | 3 |
| 29 | `frontend/src/components/Admin/AdminLayout.tsx` | EDIT | 5 |
| 30 | `frontend/src/app/customer/orders/page.tsx` | EDIT | 2, 3, 9 |
| 31 | `frontend/src/app/customer/wishlist/page.tsx` | EDIT | 3, 10 |
| 32 | `frontend/src/app/customer/cart/page.tsx` | EDIT | 10 |
| 33 | `frontend/src/app/support/page.tsx` | EDIT | 10 |
| 34 | `frontend/src/app/admin/faq-management/page.tsx` | NEW | 5 |
| 35 | `frontend/src/app/admin/about-management/page.tsx` | NEW | 5 |
| 36 | `frontend/src/app/admin/privacy-management/page.tsx` | NEW | 5 |
| 37 | `frontend/src/app/admin/contacts/page.tsx` | EDIT | 10 |
| 38 | `backend/app/repositories/content_repository.py` | NEW | 5 |
| 39 | `backend/app/routers/content_pages.py` | NEW | 5 |
| 40 | `backend/app/routers/orders.py` | EDIT | 9 |
| 41 | `backend/app/models/schemas.py` | EDIT | 10 |
| 42 | `backend/app/main.py` | EDIT | 5 |

---

## Phase 11: Real-Time Admin Cache Invalidation

### 59. Category & Tag Cache Invalidation
**Files:**
- [category_tags.py](file:///c:/Ecommerce%20app/backend/app/routers/category_tags.py) (EDIT)
- [categories.py](file:///c:/Ecommerce%20app/backend/app/routers/categories.py) (EDIT)

- **Issue:** When a super admin added or modified categories/tags, the changes didn't show up on the landing page dropdown/header for up to 5 minutes due to the cached endpoints (`/category-tags/active` and `/categories/public`).
- **Fix:** Added calls to `cache.invalidate()` for `get_active_category_tags`, `get_public_categories`, `get_tag_categories`, and `get_tag_brands` inside all creation, modification, and deletion endpoints for both categories and category tags.

### 60. Product Cache Invalidation
**File:** [products.py](file:///c:/Ecommerce%20app/backend/app/routers/products.py) (EDIT)
- **Fix:** Added `_invalidate_product_caches()` to trigger cache invalidation for `get_public_products` and `get_public_product`, as well as `get_tag_brands` (since brands listing inside category tags depends on product category association), when products are created, updated, deleted, bulk updated, or uploaded via CSV.

### 61. Brand Cache Invalidation
**File:** [brands.py](file:///c:/Ecommerce%20app/backend/app/routers/brands.py) (EDIT)
- **Fix:** Added `_invalidate_brand_caches()` to invalidate the `get_public_brands` and `get_tag_brands` cached routes when brands are created, updated, or deleted.

### 62. Promo Strip, Banner, and Collection Cache Invalidation
**Files:**
- [promo_strips.py](file:///c:/Ecommerce%20app/backend/app/routers/promo_strips.py) (EDIT)
- [banners.py](file:///c:/Ecommerce%20app/backend/app/routers/banners.py) (EDIT)
- [collections.py](file:///c:/Ecommerce%20app/backend/app/routers/collections.py) (EDIT)

- **Fix:** Integrated `cache.invalidate()` calls in the create/update/delete/toggle routes for promo strips, banners, and collections to ensure new configurations show up instantly for customers.

---

## Phase 12: Mobile Hamburger Menu Layout & Touch Fix

### 63. Fixed Mobile Hamburger Menu Drawer Layering & Fall-Through Clicks
**File:** [home.tsx](file:///c:/Ecommerce%20app/frontend/mobile/app/(tabs)/home.tsx) (EDIT)
- **Issue:** On mobile devices (particularly Android), the hamburger menu's `drawerContainer` was positioned relatively inside a flex row. This caused it to render behind the absolutely positioned backdrop modal overlay (`drawerBackdrop`), which made it visually covered and caused any tap inside the drawer to trigger the backdrop's click-to-close handler.
- **Fix:** 
  1. Re-applied z-indexing layout adjustments (`styles.drawerContainer` is absolutely positioned at left) and split close Pressable overlay design (pointerEvents="none" on backdrop, with absolute 15% width close Pressable on the right side) to prevent touch fall-through and layering bugs on Android.
  2. Added ID mapping fallbacks (`tagId = tag._id || tag.id` and `catId = cat._id || cat.id`) for both category tags and categories inside the drawer mapping loop. This ensures that the component resolves and matches primary key identifiers correctly regardless of the backend/database model ID format, restoring full expand/collapse functionality for category sub-lists.
  3. Implemented split-action categories in the drawer menu: tapping the category name text directly navigates the user straight to that category's product list, while tapping the chevron icon on the right toggles the expansion of its subcategories. Added corresponding layout styles (`drawerSubItemRow`, `drawerSubItemTextButton`, `drawerChevronButton`, `drawerChevronPlaceholder`).


---

## Phase 13: Marketplace Bug Fixes & Architectural Hardening

### Architecture Notes — Seller Discount Isolation (`update_coupon`)

#### Q: What are the "dangerous fields" in `update_coupon`, and why strip them?

The `update_coupon` endpoint strips `sellerId` and `discountScope` from any seller's update payload before saving, regardless of what the seller sends.

**Why these two fields:**
- `sellerId` on a coupon = "this coupon applies only to this seller's products in the cart"
- `discountScope` = "this coupon is seller-scoped (not platform-wide)"

If either were changed by the seller:
- `sellerId → null` → discount applies to *any* seller's cart items (seller A discounts seller B's products)
- `discountScope → "platform"` → same effect, discount is no longer isolated

The `.pop()` is **not** because the UI shows these fields — it doesn't. It's server-side defence against raw API calls (curl, Postman, etc. that bypass the UI entirely). The UI is the guard rail; the `.pop()` is the lock on the back door.

#### Q: The seller doesn't select their sellerId — it's auto-set. Shouldn't the UI only show allowed options?

Correct on both counts:

1. **sellerId is auto-injected**: On `create_coupon`, the backend forces `sellerId = current_user._id` — the seller has no input. The `.pop()` on update is purely defensive against raw API callers.

2. **UI already shows only allowed options** (confirmed as of this session):
   - Type dropdown: only `product_discount` and `bxgy` — `total_order_discount`, `shipping_discount`, `referral` removed
   - Method: no dropdown at all — hardcoded to `automatic`, info banner shown
   - Coupon code field: completely removed

The two layers (UI restriction + backend strip/reject) work together. The UI prevents normal users from sending invalid values; the backend rejects them even if someone bypasses the UI.

---

## Phase 14: Database Full Normalization (Option 1)

### Architecture Update
The hybrid storage model (combining native columns with a `doc` JSON blob) was originally designed to emulate a NoSQL Document Store (like MongoDB) in MySQL. We have now fully normalized the `sj_sub_orders` and `sj_seller_availability` tables to strictly adhere to Third Normal Form (3NF) and removed the `doc` columns entirely.

### Changes Implemented
1. **Schema Updates (`backend/scripts/schema_mysql.sql`)**:
   - `sj_seller_availability`: Flattened `reason`, `created_by`, and `cancelled_at` into native columns.
   - `sj_sub_orders`: 
     - Extracted 20+ fields (subtotals, delivery slots, notes, discounts, coupon details) into native scalar columns.
     - Flattened nested address objects (`shippingAddress` and `billingAddress`) into native columns (e.g., `shipping_line1`, `billing_city`).
   - `sj_sub_order_items`: Created a new child table to store the array of items, mapped via foreign key `sub_order_id`.

2. **Data Migration Script (`backend/scripts/migrate_option1.py` & `migrate_option1.sql`)**:
   - Created a standalone SQL migration script to safely add the new scalar columns and the new `sj_sub_order_items` table.
   - Created a Python migration script to execute the SQL DDL, extract existing JSON data, flatten the addresses, iterate over the `items` arrays to populate `sj_sub_order_items`, and finally drop the `doc` columns from both tables.

3. **DAO Rewrites**:
   - `MySQLSellerAvailabilityDAO`: Refactored to operate solely on scalar columns.
   - `MySQLSubOrderDAO`: Completely rewritten. It now performs SQL `JOIN`s against `sj_sub_order_items` during read operations to reconstruct the nested dictionary expected by the Python application layer, ensuring the rest of the codebase continues to function without changes while strictly adhering to 3NF.


