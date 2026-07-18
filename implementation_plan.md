# Buy X Get Y (BXGY) Logic and Conflict Resolution (Updated)

This plan outlines the design and implementation details for the Buy X Get Y (BXGY) discount engine and admin conflict prevention. It details the allocation process, comparative discount application, and validation rules to prevent active deal overlaps, modified to support case-based pricing and standard conflict resolution workflows.

## User Review Required

> [!IMPORTANT]
> - **Case-Wise Calculations**: When `applicableItemType == "cases"`, calculations are performed on a per-case basis. Cart items bought as cases (`sellAsCase = True`) are treated as cases, with each case having a price equal to the case price (`mrpPerCase`). Sorting and allocation to BX/GY are done on cases rather than individual pieces.
> - **Standard Conflict Resolution**: Overlapping active BXGY deals will trigger a `409 Conflict` containing the conflict details. The admin can choose to:
>   - **Overwrite**: Exclude the overlapping products from the earlier deal.
>   - **Retain**: Exclude the overlapping products from the new deal.
>   - **Go Back and Edit**: Manually edit the deal products.

## Alignment with Original Requirements

1. **A product can appear in only 1 active BXGY deal at a time — across BX side, GY side, or both**: Handled by the updated `check_discount_overlap` which checks the union of BX and GY products against all other active BXGY deals.
2. **Same product can appear on both BX and GY sides of the same deal**: Handled by processing a unified list of elements for allocation.
3. **Deal applies once per order only**: The allocation algorithm (`_calculate_bxgy_discount`) runs once per deal, allocating exactly $X$ items to BX and exactly $Y$ items to GY per order.
4. **BXGY only applies if its effective unit price is better than amount-off for that product**: The helper calculates the effective price and compares it against the best automatic product discount before applying.
5. **Sort all BX list items in descending order of price**: Elements are sorted by price (descending) before BX allocation.
6. **Most expensive units are allocated to meet BX threshold first**: We select the top $X$ elements from the sorted BX list.
7. **Allocated BX units are locked and excluded from GY consideration**: The top $X$ elements are removed from the candidate pool for GY allocation.
8. **From remaining cart items on GY list, sort in descending order of price**: Remaining elements are filtered and sorted again by price.
9. **Top Y items get the GY discount applied per unit**: We select the top $Y$ elements for the GY discount.
10. **If user has added more than Y items from GY list, only the most expensive Y are discounted**: Selecting the top $\min(Y, \text{remaining})$ ensures this.
11. **Remaining items outside BXGY get amount-off each product discount applied if applicable**: Any elements not allocated to BX or GY (or elements where amount-off was better) receive the automatic product discount.
12. **Extra items are naturally the cheapest ones**: Guaranteed by the descending order sorting logic.
13. **If a product already exists in an active BXGY deal, it cannot be added to another active BXGY deal**: Enforced by the `check_discount_overlap` logic for BXGY deals.
14. **Alert the admin with the count of conflicting products**: The backend will return a `409 Conflict` with the overlap count and details, which the frontend displays.
15. **Admin must explicitly resolve the conflict**: Supported via the standard "Overwrite" and "Retain" workflows in the UI, which updates the `excludedProductIds` in the DB.

## Proposed Changes

---

### Backend Components

#### [MODIFY] [coupon_repository.py](file:///c:/Ecommerce%20app/backend/app/repositories/coupon_repository.py)

1. **Implement `_calculate_bxgy_discount` private helper**:
   - Accepts the `coupon`, `cart_items`, and product/role context.
   - Pre-evaluates product eligibility for BX and GY sides.
   - Determines the item type mode (`units` vs `cases`) based on `coupon.get("applicableItemType", "units")`.
   - Expands cart items into individual elements (either units or cases):
     - If mode is `units`:
       - If `sellAsCase = True`, quantity is split into individual units, each priced at `mrpPerCase / quantityPerCase`.
       - If `sellAsCase = False`, quantity is processed as units, each priced at `mrp`.
     - If mode is `cases`:
       - Only cart items with `sellAsCase = True` are eligible.
       - The quantity of cases is `quantity // quantityPerCase`.
       - Each case element is priced at `mrpPerCase` (or the case price returned by `getPriceForRole(..., sell_as_case=True)`).
   - Filters elements eligible for BX side, sorts in descending order of price/value, and selects the top `X` (`minQuantityOfEligibleItems`) elements. If fewer than `X` elements are present, the deal is disqualified (discount = 0).
   - Excludes the allocated BX elements. Filters remaining elements for GY side, sorts in descending order, and selects top `Y` (`buyXGetYCustomerGetsQuantity`) elements.
   - For each product in the allocated elements (BX + GY), calculates the effective price under BXGY:
     $$\text{Effective Price} = \frac{(N_{\text{BX}} \times \text{Price}) + (N_{\text{GY}} \times \text{GY Price})}{N_{\text{BX}} + N_{\text{GY}}}$$
     where GY Price has the GY percentage/fixed discount applied.
   - Compares this effective price to the price with the best automatic amount-off/fixed/percentage product-level discount applied.
   - If the effective BXGY price is better (cheaper), applies the BXGY discount. Otherwise, falls back to the automatic product discount for those elements.
   - Applies the best automatic product-level discount to any remaining/leftover elements.
   - Returns the total discount and an `itemDiscounts` mapping of product ID to total discount applied.

2. **Integrate into `validateCoupon` & `find_applicable_automatic_discounts`**:
   - Call `_calculate_bxgy_discount` if `typeOfDiscount == "buy_x_get_y"`.
   - Include the calculated `itemDiscounts` mapping in the return dictionary.

3. **Update Overlap Check (`check_discount_overlap`)**:
   - For BXGY deals, checks if any product in the union of BX side and GY side of the new deal overlaps with the union of BX and GY sides of any other active BXGY deals.
   - Returns a conflict response if any overlapping products are found, strictly enforcing the 1-deal-per-product rule.

4. **Support Overwrite/Retain Resolution in `create` & `update`**:
   - Reuse the existing conflict resolution blocks (`resolution == "overwrite"` and `resolution == "retain"`) which dynamically exclude overlapping products using `excludedProductIds` for both standard and BXGY deals.

---

#### [MODIFY] [orders.py](file:///c:/Ecommerce%20app/backend/app/routers/orders.py)

1. **Incorporate `itemDiscounts` in Order Creation**:
   - Check if the validated/applied coupon response contains `itemDiscounts`.
   - If present, apply the exact discount to each order item using `itemDiscounts` (mapping of product ID to discount amount), resetting the value to prevent duplicate application.
   - Fall back to the proportional distribution ratio only if `itemDiscounts` is not present.

---

### Frontend Components

No changes are required in [DiscountManagement.tsx](file:///c:/Ecommerce%20app/frontend/src/components/Admin/DiscountManagement.tsx) since the existing modal and resolution buttons (Overwrite and Retain) will hook into the updated backend resolution logic out-of-the-box.

---

## Verification Plan

### Automated Tests
- We will create a new test file `tests/test_bxgy_deal_rules.py` covering:
  - Descending order sorting for BX/GY allocation (both units and cases).
  - Multi-product BXGY allocation and locking of BX elements.
  - Comparison of effective unit/case price vs automatic amount-off (qualifying vs falling back).
  - Proper calculation of remaining elements getting amount-off.
  - Overlap check on BX/GY sides across active BXGY deals.
  - Verification of Overwrite and Retain conflict resolution modes for BXGY deals.
- Run the test suite via `pytest tests/test_bxgy_deal_rules.py`.

### Manual Verification
- Log in as admin, create a case-based BXGY deal.
- Create a conflicting BXGY deal and trigger the conflict modal; select Overwrite/Retain and verify the DB exclusions.
- Verify checkout calculations for both unit and case BXGY deals in the cart.
