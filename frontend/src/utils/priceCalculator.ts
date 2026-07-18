/**
 * Calculate product price based on user role, quantity, and product discounts
 */
export const calculatePrice = (
  product: any,
  quantity: number = 1,
  userRole: string = 'customer'
): number => {
  if (!product || !product.mrp) return 0;

  const mrp = parseFloat(product.mrp || 0);
  if (mrp <= 0) return 0;

  // Base role discounts removed. Only quantity discounts (for customers) or promotions apply.
  let discount = 0;

  // Find applicable quantity discount from quantityTiers
  const quantityTiers = product.quantityTiers || [];
  let additionalDiscount = 0;
  if (quantityTiers.length > 0) {
    let qtyToUse = quantity;
    if (userRole === 'wholesaler' && product.quantityItemType === 'cases' && product.quantityPerCase) {
      qtyToUse = Math.floor(quantity / product.quantityPerCase);
    }
    const sorted = [...quantityTiers].sort(
      (a: any, b: any) => (b.quantity || 0) - (a.quantity || 0)
    );
    for (const qd of sorted) {
      if (qtyToUse >= (qd.quantity || 0)) {
        additionalDiscount = parseFloat(qd.discount || 0);
        break;
      }
    }
  }

  const totalDiscount = discount + additionalDiscount;
  return mrp * (1 - totalDiscount / 100);
};

/**
 * Get the minimum quantity required for a user role
 */
// eslint-disable-next-line unused-imports/no-unused-vars
// eslint-disable-next-line unused-imports/no-unused-vars
export const getMinimumQuantity = (product: any, userRole: string): number => {
  return 1;
};

/**
 * Get display price for product listing (uses minimum quantity for role)
 */
export const getDisplayPrice = (product: any, userRole: string = 'customer'): number => {
  if (!product || !product.mrp) return 0;

  const minQty = getMinimumQuantity(product, userRole);
  return calculatePrice(product, minQty, userRole);
};

/**
 * Get the discount type being applied based on role and quantity
 * @returns Discount type: 'wholesaler' or 'customer'
 */
export const getDiscountType = (
  product: any,
  // eslint-disable-next-line unused-imports/no-unused-vars
  quantity: number = 1,
  // eslint-disable-next-line unused-imports/no-unused-vars
  userRole: string = 'customer'
): string => {
  return 'customer';
};
