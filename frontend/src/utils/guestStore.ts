const GUEST_CART_KEY = 'guest_cart';
const GUEST_WISHLIST_KEY = 'guest_wishlist';

// ─── Types ───────────────────────────────────────────────────────────
export interface GuestCartItem {
  productId: string;
  quantity: number;
  product?: any; // snapshot for display
}

export interface GuestWishlistItem {
  productId: string;
  product?: any;
}

// ─── Cart ────────────────────────────────────────────────────────────
export function getGuestCart(): GuestCartItem[] {
  try {
    const raw = localStorage.getItem(GUEST_CART_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function addGuestCartItem(
  productId: string,
  quantity: number = 1,
  product?: any
): GuestCartItem[] {
  const cart = getGuestCart();
  const idx = cart.findIndex((i) => i.productId === productId);
  if (idx >= 0) {
    cart[idx].quantity += quantity;
    if (product) cart[idx].product = product;
  } else {
    cart.push({ productId, quantity, product });
  }
  localStorage.setItem(GUEST_CART_KEY, JSON.stringify(cart));
  removeGuestWishlistItem(productId);
  return cart;
}

export function updateGuestCartQty(productId: string, quantity: number): GuestCartItem[] {
  let cart = getGuestCart();
  if (quantity <= 0) {
    cart = cart.filter((i) => i.productId !== productId);
  } else {
    const idx = cart.findIndex((i) => i.productId === productId);
    if (idx >= 0) cart[idx].quantity = quantity;
  }
  localStorage.setItem(GUEST_CART_KEY, JSON.stringify(cart));
  return cart;
}

export function removeGuestCartItem(productId: string): GuestCartItem[] {
  const cart = getGuestCart().filter((i) => i.productId !== productId);
  localStorage.setItem(GUEST_CART_KEY, JSON.stringify(cart));
  return cart;
}

export function saveGuestCart(cart: GuestCartItem[]): void {
  localStorage.setItem(GUEST_CART_KEY, JSON.stringify(cart));
}

export function clearGuestCart(): void {
  localStorage.removeItem(GUEST_CART_KEY);
}

export function getGuestCartCount(): number {
  return getGuestCart().reduce((sum, i) => sum + i.quantity, 0);
}

// ─── Wishlist ────────────────────────────────────────────────────────
export function getGuestWishlist(): GuestWishlistItem[] {
  try {
    const raw = localStorage.getItem(GUEST_WISHLIST_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function addGuestWishlistItem(productId: string, product?: any): GuestWishlistItem[] {
  const list = getGuestWishlist();
  if (list.some((i) => i.productId === productId)) return list;
  list.push({ productId, product });
  localStorage.setItem(GUEST_WISHLIST_KEY, JSON.stringify(list));
  return list;
}

export function removeGuestWishlistItem(productId: string): GuestWishlistItem[] {
  const list = getGuestWishlist().filter((i) => i.productId !== productId);
  localStorage.setItem(GUEST_WISHLIST_KEY, JSON.stringify(list));
  return list;
}

export function isInGuestWishlist(productId: string): boolean {
  return getGuestWishlist().some((i) => i.productId === productId);
}

export function clearGuestWishlist(): void {
  localStorage.removeItem(GUEST_WISHLIST_KEY);
}
