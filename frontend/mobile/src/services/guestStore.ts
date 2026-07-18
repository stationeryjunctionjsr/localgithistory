import AsyncStorage from '@react-native-async-storage/async-storage';

const GUEST_CART_KEY = 'guest_cart';
const GUEST_WISHLIST_KEY = 'guest_wishlist';

// ─── Types ───────────────────────────────────────────────────────────
export interface GuestCartItem {
  productId: string;
  quantity: number;
  product?: any; // snapshot for display (name, price, images, etc.)
}

export interface GuestWishlistItem {
  productId: string;
  product?: any;
}

// ─── Cart ────────────────────────────────────────────────────────────
export async function getGuestCart(): Promise<GuestCartItem[]> {
  try {
    const raw = await AsyncStorage.getItem(GUEST_CART_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export async function addGuestCartItem(
  productId: string,
  quantity: number = 1,
  product?: any
): Promise<GuestCartItem[]> {
  const cart = await getGuestCart();
  const idx = cart.findIndex((i) => i.productId === productId);
  if (idx >= 0) {
    cart[idx].quantity += quantity;
    if (product) cart[idx].product = product;
  } else {
    cart.push({ productId, quantity, product });
  }
  await AsyncStorage.setItem(GUEST_CART_KEY, JSON.stringify(cart));
  return cart;
}

export async function updateGuestCartQty(
  productId: string,
  quantity: number
): Promise<GuestCartItem[]> {
  let cart = await getGuestCart();
  if (quantity <= 0) {
    cart = cart.filter((i) => i.productId !== productId);
  } else {
    const idx = cart.findIndex((i) => i.productId === productId);
    if (idx >= 0) cart[idx].quantity = quantity;
  }
  await AsyncStorage.setItem(GUEST_CART_KEY, JSON.stringify(cart));
  return cart;
}

export async function removeGuestCartItem(productId: string): Promise<GuestCartItem[]> {
  const cart = (await getGuestCart()).filter((i) => i.productId !== productId);
  await AsyncStorage.setItem(GUEST_CART_KEY, JSON.stringify(cart));
  return cart;
}

export async function saveGuestCart(cart: GuestCartItem[]): Promise<void> {
  await AsyncStorage.setItem(GUEST_CART_KEY, JSON.stringify(cart));
}

export async function clearGuestCart(): Promise<void> {
  await AsyncStorage.removeItem(GUEST_CART_KEY);
}

export async function getGuestCartCount(): Promise<number> {
  const cart = await getGuestCart();
  return cart.reduce((sum, i) => sum + i.quantity, 0);
}

// ─── Wishlist ────────────────────────────────────────────────────────
export async function getGuestWishlist(): Promise<GuestWishlistItem[]> {
  try {
    const raw = await AsyncStorage.getItem(GUEST_WISHLIST_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export async function addGuestWishlistItem(
  productId: string,
  product?: any
): Promise<GuestWishlistItem[]> {
  const list = await getGuestWishlist();
  if (list.some((i) => i.productId === productId)) return list;
  list.push({ productId, product });
  await AsyncStorage.setItem(GUEST_WISHLIST_KEY, JSON.stringify(list));
  return list;
}

export async function removeGuestWishlistItem(productId: string): Promise<GuestWishlistItem[]> {
  const list = (await getGuestWishlist()).filter((i) => i.productId !== productId);
  await AsyncStorage.setItem(GUEST_WISHLIST_KEY, JSON.stringify(list));
  return list;
}

export async function isInGuestWishlist(productId: string): Promise<boolean> {
  const list = await getGuestWishlist();
  return list.some((i) => i.productId === productId);
}

export async function clearGuestWishlist(): Promise<void> {
  await AsyncStorage.removeItem(GUEST_WISHLIST_KEY);
}
