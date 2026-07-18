interface GuestCartItem {
  productId: string;
  name: string;
  price: number;
  quantity: number;
  images: string[];
  addedAt: string;
}

export const guestCartService = {
  getCart: (): GuestCartItem[] => {
    if (typeof window !== 'undefined') {
      const cart = localStorage.getItem('guestCart');
      return cart ? JSON.parse(cart) : [];
    }
    return [];
  },

  addToCart: (item: Omit<GuestCartItem, 'addedAt'>) => {
    if (typeof window !== 'undefined') {
      const cart = guestCartService.getCart();
      const existingItem = cart.find((cartItem) => cartItem.productId === item.productId);

      if (existingItem) {
        existingItem.quantity += item.quantity;
      } else {
        cart.push({
          ...item,
          addedAt: new Date().toISOString(),
        });
      }

      localStorage.setItem('guestCart', JSON.stringify(cart));
    }
  },

  removeFromCart: (productId: string) => {
    if (typeof window !== 'undefined') {
      const cart = guestCartService.getCart();
      const filteredCart = cart.filter((item) => item.productId !== productId);
      localStorage.setItem('guestCart', JSON.stringify(filteredCart));
    }
  },

  updateQuantity: (productId: string, quantity: number) => {
    if (typeof window !== 'undefined') {
      const cart = guestCartService.getCart();
      const item = cart.find((cartItem) => cartItem.productId === productId);

      if (item) {
        if (quantity <= 0) {
          guestCartService.removeFromCart(productId);
        } else {
          item.quantity = quantity;
          localStorage.setItem('guestCart', JSON.stringify(cart));
        }
      }
    }
  },

  clearCart: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('guestCart');
    }
  },

  getCartTotal: (): number => {
    const cart = guestCartService.getCart();
    return cart.reduce((total, item) => total + item.price * item.quantity, 0);
  },

  getCartCount: (): number => {
    const cart = guestCartService.getCart();
    return cart.reduce((total, item) => total + item.quantity, 0);
  },
};
