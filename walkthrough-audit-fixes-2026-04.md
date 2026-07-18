# Audit bug fixes — walkthrough (April 2026)

This is a **new** walkthrough document for the “Fix all audit bugs” work (P0 / P1 / P2). The older `walkthrough.md` in this repo was **not** modified for this pass.

---

## Scope

- **Backend:** FastAPI (`backend/app/`)
- **Web:** Next.js (`frontend/src/`)
- **Mobile:** Expo (`frontend/mobile/`)

Source plan (Cursor): `fix_all_audit_bugs_3bd0711c.plan.md` (path under your user’s `.cursor/plans/`).

---

## P0 — status: **complete**

All 13 P0 items from the plan are implemented in code (force-update store links, honest ratings / reviews UX, external banner links, cart variants + API, wholesaler query navigation, wishlist + cart endpoint, activity body contract, optional bearer on device register, collections products route, guest orders loading, etc.). Details live in git history and the plan checklist.

---

## P1 — status: **mostly complete** (see “Remaining” below)

| ID | Topic | What was done |
|----|--------|----------------|
| P1-1 | Orders `alert` → toast | `frontend/src/app/customer/orders/page.tsx` — `react-toastify`; fetch error banner + retry |
| P1-2 | Cart `alert` → toast | `frontend/src/app/customer/cart/page.tsx` |
| P1-3 / P1-8 | Product detail alerts + wishlist errors | `frontend/src/components/ProductDetailClient.tsx` |
| P1-4 | Admin users | `frontend/src/app/admin/users/page.tsx` |
| P1-5 | Admin profile | `frontend/src/app/admin/profile/page.tsx` |
| P1-6 | Orders + support errors | Orders: inline error + retry. **Support:** `frontend/src/app/support/page.tsx` — toasts + banners + retry for contacts/tickets (this continuation) |
| P1-7 | Wholesaler schemes fetch | `frontend/src/app/wholesaler/schemes/page.tsx` — `fetchError` + retry screen |
| P1-9 | Dashboard silent fetches | **Partial** — SSR pages still swallow network failures with `.catch(() => null)`; client secondary fetches mostly `console.error` only |
| P1-10 | Product not found | `customer/product/[id]/page.tsx`, `wholesaler/product/[id]/page.tsx` — message + link home |
| P1-11 | Schemes nested controls | Schemes cards: single outer `<button>`, inner CTA is `<div>` |
| P1-12 | Wishlist hardcoded green | `customer/wishlist/page.tsx` — Tailwind `emerald-800` / `emerald-900` |
| P1-13 | Mobile silent catches | **Partial** — e.g. wishlist remove, cart qty/remove now surface `Alert` on failure |
| P1-14 | Order detail back | `frontend/mobile/app/orders/[id].tsx` — header + `router.back()` |
| P1-15 | Share URL fallback | `frontend/mobile/app/products/[id].tsx` — production web origin default |
| P1-16 | Edit profile auth | `frontend/mobile/app/edit-profile.tsx` — redirect to login if no user |
| P1-17 | Search overlay | Hardcoded category chips removed; “Search tips” when empty. **Clear recent** still UI-only (no API clear yet) |
| P1-18 | Coach marks | `frontend/mobile/app/(tabs)/home.tsx` — ref so auto-start runs once per mount |
| P1-19 | Password change | `backend/app/routers/users.py` — non–super-admin must send `currentPassword` and verify |
| P1-20 | Coach marks writes | `backend/app/routers/coach_marks.py` — `require_super_admin` on create/update/delete |
| P1-21 | Recommendations metrics | `backend/app/routers/recommendations.py` — `/metrics` requires super admin |
| P1-22 | Mark read | `backend/app/routers/push_notifications.py` — **`Depends(get_current_user)`** (Bearer required) |
| P1-23 | Webhook secret logging | `backend/app/routers/auth.py` — no logged secret value |
| P1-24 | CSV upload response | `backend/app/routers/products.py` — `successCount` / `errorCount` + single `errors` list |
| P1-25 | Feature flags body | `backend/app/routers/feature_flags.py` — Pydantic create/update models |
| P1-26 | UPI env in production | `backend/app/config/upi.py` — warnings when `APP_ENV=production` and vars missing |

---

## P2 — status: **partial**

| ID | Topic | Done / notes |
|----|--------|----------------|
| P2-1 | Localhost in frontend | Product metadata image base uses `NEXT_PUBLIC_API_URL` (see customer/wholesaler product pages). Other files may still default localhost in dev. |
| P2-2 | Unstable list keys | `mobile/app/products/index.tsx`, `mobile/app/(tabs)/brands.tsx` — stable `keyExtractor` |
| P2-3 | SessionAnalytics storage | `mobile/src/components/SessionAnalytics.tsx` — AsyncStorage for returning-user flag |
| P2-4 | Mobile theme colors | **Not** done as a full-app sweep |
| P2-5 | Admin analytics debug line | `frontend/src/app/admin/analytics/page.tsx` — API URL line removed from loading UI |
| P2-6 | `print` → logger | **Partial** — e.g. `push_notifications.py`, `orders.py`, `payments.py` (this continuation). Other `app/` modules may still use `print`. |
| P2-7 | Bare `except` / swallow | **Not** systematically audited; intentional patterns (e.g. cache) left as-is |
| P2-8 | Dead code / unused imports | **Not** done |
| P2-9 | Placeholder images | `frontend/src/utils/imageUrl.ts` default fallback is inline SVG; some components may still pass old `via.placeholder.com` URLs |
| P2-10 | Social URLs configurable | **Not** done |
| P2-11 | Auth boilerplate consolidation | **Not** done |
| P2-12 | Guard `console.*` with `__DEV__` | **Not** done |

---

## Remaining work (priority suggestions)

1. **P1-9:** Optional error boundary or “partial load” banner on `customer/page.tsx` / `wholesaler/page.tsx` when SSR `fetch` returns null.
2. **P1-13 / P1-17:** Finish mobile catch + search-history clear per original audit counts.
3. **P2-4 / P2-9 / P2-10 / P2-11 / P2-12:** Theme sweep, remove remaining placeholder URLs, env-driven social links, shared auth deps, dev-only logging.
4. **P2-6:** Ripgrep `print(` under `backend/app/` (exclude `scripts/`) and switch to `logger`.
5. **Mobile clients:** If anything still calls `POST .../mark-read` without a token, add the header or handle 401.

---

## How to verify quickly

- **Web:** Log in as customer → Orders / Cart / Support (simulate API failure with wrong `NEXT_PUBLIC_API_URL`).
- **Admin:** Users + Profile flows should show toasts, not `alert`.
- **API:** `PUT /users/{id}/password` as non–super-admin without `currentPassword` → 400.
- **API:** `GET /recommendations/metrics` without super-admin token → 403.
- **API:** `POST /push-notifications/{id}/mark-read` without `Authorization` → 401.

---

## Files touched in this “continue” session

- `frontend/src/app/support/page.tsx` — contact/ticket error state, toasts, retry UI  
- `backend/app/routers/push_notifications.py` — `mark_notification_read` now requires `get_current_user`  
- `backend/app/routers/payments.py` — one `print` → `logger.error`  
- **This file** — `walkthrough-audit-fixes-2026-04.md` (new; `walkthrough.md` unchanged)

---

## Verification pass (checklist vs tree)

The following were confirmed in code and **fixed in a follow-up pass**:

| Item | Change |
|------|--------|
| Orders UPI Copy `alert` | `customer/orders/page.tsx` → `toast.success` |
| Valet / retailer product `alert()` | Both pages → `toast` + default `getImageUrlWithFallback` (no `via.placeholder`) |
| `imageUrl.ts` default host | `http://localhost:8000` when `NEXT_PUBLIC_API_URL` unset; export `IMAGE_PLACEHOLDER_DATA_URI` |
| `upi.py` / `auth.py` `print` | `logger` / `logger.warning` |
| Wishlist `#1a4d33` “View” link | Tailwind `text-emerald-800` |
| `via.placeholder.com` on web | Removed from HeroCarousel, InfiniteCarousel, LandingPageClient, CustomerClient, ProductCarousel `onError`, admin banners `onError`, valet/retailer PDP |
| MSG91 webhook success log | `auth.py` — log key names + status field only, not full JSON body |
| Home coach auto-start | `mobile/app/(tabs)/home.tsx` — removed `setTimeout(startTour)`; tour can be wired to a manual entry point |
| Mobile silent `catch` | `privacy-policy`, `about`, `products/index`, `checkout`, `CoachMark`, `SessionAnalytics` — `__DEV__` warnings |

**Still lower priority / not fully swept:** broad `console.*` cleanup (P2-12), social URL env config (P2-10), repository `except` patterns (P2-7), mobile full theme sweep (P2-4), dead code (P2-8), backend `print` in other modules (P2-6 remainder).

---

## Final P2 closure pass (additional)

Additional work completed in this phase:

- **P2-6 (`print` -> logger)**
  - Converted remaining `print()` usage under `backend/app/` to structured logger calls, including:
    - services: `push_notification_service.py`, `email_service.py`, `report_service.py`
    - utils/repositories: `feature_flags.py`, `error_handler.py`, `user_repository.py`, `google_review_repository.py`
    - routers/jobs/scripts: `customer_segments.py`, `search_tags.py`, `returns.py`, job files and migration/data scripts
  - `rg "print\\(" backend/app` now returns no matches.

- **P2-7 (swallowed exceptions)**
  - Removed remaining `except ...: pass` matches in runtime code paths and replaced with safe fallback/continue or warning log where appropriate.

- **P2-10 (social URL configurable)**
  - `frontend/src/app/support/page.tsx`: Instagram URL now uses `NEXT_PUBLIC_INSTAGRAM_URL` with current URL as fallback.

- **P2-11 (auth boilerplate consolidation)**
  - Migrated repeated local auth dependency boilerplate in these routers to shared dependencies from `app.utils.auth`:
    - `upi.py`
    - `payments.py`
    - `push_notifications.py`
    - `orders.py`

- **P2-12 (console guards) — COMPLETE**
  - All mobile `console.*` calls are now wrapped with `__DEV__` guards (no production log leakage):
    - `app/(tabs)/home.tsx`, `app/(tabs)/brands.tsx`, `app/(tabs)/cart.tsx`, `app/support.tsx`, `app/(tabs)/categories.tsx` (previous pass)
    - `src/components/SearchOverlay.tsx`, `src/components/LaunchPopup.tsx`, `src/components/GeneralFeedbackModal.tsx` (this pass)
    - `src/utils/expoPushNotifications.ts` — all 5 `console.log/error` calls guarded (this pass)
    - `src/api/client.ts` — dev-only base URL log (this pass)
  - Web support page errors guarded with `process.env.NODE_ENV !== 'production'`.

- **P2-4 (hardcoded colors) — COMPLETE**
  - Brand primary `#1a4d33` replaced with `colors.primary` (from `src/theme.ts`) in:
    - `app/(tabs)/brands.tsx` — added `colors` import; `ActivityIndicator` color
    - `app/products/index.tsx` — added `colors` import; `ActivityIndicator`, MultiSlider `selectedStyle`/`markerStyle`, `minimumTrackTintColor`/`thumbTintColor`
    - `app/products/[id].tsx` — `ActivityIndicator` color (already imported `colors`)
  - Remaining inline icon/placeholder colors (`#9CA3AF`, `#94A3B8`, etc.) are intentional Tailwind-equivalent neutrals used as Ionicons prop colors — left as-is.

- **P2-8 (dead code / unused imports) — COMPLETE**
  - `backend/app/routers/recommendations.py`: Removed dead local `get_current_user` function, `security = HTTPBearer()`, and `HTTPBearer`/`HTTPAuthorizationCredentials` imports. Replaced local `optional_user` with `get_optional_user` from `app.utils.auth`. Moved `cache` import to top level.
  - `backend/app/routers/products.py`: Removed dead local `get_current_user`, `require_super_admin`, `security`, `verify_token`, `require_roles`, `HTTPBearer`/`HTTPAuthorizationCredentials`, and unused `import random`. Now imports `get_current_user`, `require_super_admin` directly from `app.utils.auth`.
  - `backend/app/routers/users.py`: Removed dead local `get_current_user`, `require_super_admin`, `security`, `verify_token`, `require_roles`, `HTTPBearer`/`HTTPAuthorizationCredentials`, and unused `status` import. Now uses central auth utilities.
  - `backend/app/routers/coach_marks.py`: Removed unused `get_current_user` from import (only `require_super_admin` is used).
