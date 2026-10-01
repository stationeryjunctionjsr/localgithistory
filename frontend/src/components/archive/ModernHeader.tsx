'use client';

import React, { useState, useRef, useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
// import { useWishlist } from '@/context/WishlistContext';
import { useWishlistStore } from '@/store/wishlistStore';
import Link from 'next/link';
import { guestCartService } from '@/utils/guestCart';
import ThemeSwitcher from '../ThemeSwitcher';
import { SearchIcon, ProfileIcon, CloseIcon } from '../Icons/HeaderIcons';
import { MyCartIcon, WishlistIcon } from '../Icons/CartWishlistIcons';
import api from '@/utils/api';
import styles from './ModernHeader.module.css';
import { logger } from '@/utils/logger';

interface Category {
  id: string;
  name: string;
  subcategories?: {
    id: string;
    name: string;
    items?: string[];
  }[];
}

const categories: Category[] = [
  {
    id: 'men',
    name: 'MEN',
    subcategories: [
      {
        id: 'clothing',
        name: 'Clothing',
        items: ['T-Shirts', 'Shirts', 'Jeans', 'Trousers', 'Shorts', 'Kurtas', 'Ethnic Wear'],
      },
      {
        id: 'footwear',
        name: 'Footwear',
        items: ['Sports Shoes', 'Casual Shoes', 'Formal Shoes', 'Sandals', 'Flip Flops'],
      },
      {
        id: 'accessories',
        name: 'Accessories',
        items: ['Watches', 'Belts', 'Wallets', 'Sunglasses', 'Bags', 'Backpacks'],
      },
    ],
  },
  {
    id: 'women',
    name: 'WOMEN',
    subcategories: [
      {
        id: 'clothing',
        name: 'Clothing',
        items: [
          'Kurtis',
          'Sarees',
          'Dresses',
          'Tops',
          'T-Shirts',
          'Jeans',
          'Leggings',
          'Salwar Suits',
        ],
      },
      {
        id: 'footwear',
        name: 'Footwear',
        items: ['Heels', 'Flats', 'Sandals', 'Sports Shoes', 'Boots', 'Slippers'],
      },
      {
        id: 'accessories',
        name: 'Accessories',
        items: ['Handbags', 'Clutches', 'Wallets', 'Jewelry', 'Watches', 'Sunglasses'],
      },
    ],
  },
  {
    id: 'kids',
    name: 'KIDS',
    subcategories: [
      {
        id: 'boys-clothing',
        name: 'Boys Clothing',
        items: ['T-Shirts', 'Shirts', 'Shorts', 'Jeans', 'Trousers', 'Ethnic Wear'],
      },
      {
        id: 'girls-clothing',
        name: 'Girls Clothing',
        items: ['Tops', 'Dresses', 'Skirts', 'Shorts', 'Jeans', 'Ethnic Wear'],
      },
      {
        id: 'footwear',
        name: 'Footwear',
        items: ['Sports Shoes', 'Casual Shoes', 'Sandals', 'Boots', 'School Shoes'],
      },
      {
        id: 'infants',
        name: 'Infants',
        items: ['Bodysuits', 'Onesies', 'Sleepwear', 'Accessories'],
      },
    ],
  },
  {
    id: 'home',
    name: 'HOME',
    subcategories: [
      {
        id: 'bed-linen',
        name: 'Bed Linen',
        items: ['Bedsheets', 'Pillow Covers', 'Blankets', 'Quilts', 'Mattresses'],
      },
      {
        id: 'bath',
        name: 'Bath',
        items: ['Towels', 'Bath Robes', 'Slippers', 'Bathroom Accessories'],
      },
      {
        id: 'kitchen',
        name: 'Kitchen',
        items: ['Cookware', 'Dinnerware', 'Storage', 'Appliances', 'Utensils'],
      },
    ],
  },
  {
    id: 'beauty',
    name: 'BEAUTY',
    subcategories: [
      {
        id: 'makeup',
        name: 'Makeup',
        items: ['Lipstick', 'Foundation', 'Eyeliner', 'Mascara', 'Nail Polish'],
      },
      {
        id: 'skincare',
        name: 'Skincare',
        items: ['Face Wash', 'Moisturizer', 'Sunscreen', 'Serum', 'Face Masks'],
      },
      {
        id: 'haircare',
        name: 'Haircare',
        items: ['Shampoo', 'Conditioner', 'Hair Oil', 'Hair Color', 'Styling'],
      },
    ],
  },
  {
    id: 'stationery',
    name: 'STATIONERY',
    subcategories: [
      {
        id: 'office',
        name: 'Office Supplies',
        items: ['Notebooks', 'Pens', 'Files', 'Folders', 'Desk Accessories'],
      },
      {
        id: 'art',
        name: 'Art & Craft',
        items: ['Colors', 'Brushes', 'Canvas', 'DIY Kits', 'Craft Papers'],
      },
      {
        id: 'school',
        name: 'School Supplies',
        items: ['Backpacks', 'Lunch Boxes', 'Water Bottles', 'Geometry Sets'],
      },
    ],
  },
];

export default function ModernHeader() {
  const { user, logout } = useAuth();
  const { theme } = useTheme();
  // const { items: wishlistItems } = useWishlist();
  const wishlistItems = useWishlistStore((s) => s.items);
  // eslint-disable-next-line unused-imports/no-unused-vars
  const pathname = usePathname();
  const router = useRouter();

  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);
  const [cartCount, setCartCount] = useState(0);
  const [searchSuggestions, setSearchSuggestions] = useState<string[]>([]);
  const [showSearchSuggestions, setShowSearchSuggestions] = useState(false);

  const searchRef = useRef<HTMLDivElement>(null);
  const profileDropdownRef = useRef<HTMLDivElement>(null);
  const megaMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchCartCount();
    const interval = setInterval(fetchCartCount, 5000);
    return () => clearInterval(interval);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  useEffect(() => {
    // Cleanup on unmount
    return () => {
      setShowProfileDropdown(false);
      setShowSearchSuggestions(false);
      setActiveCategory(null);
    };
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        profileDropdownRef.current &&
        !profileDropdownRef.current.contains(event.target as Node)
      ) {
        setShowProfileDropdown(false);
      }
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowSearchSuggestions(false);
      }
      if (megaMenuRef.current && !megaMenuRef.current.contains(event.target as Node)) {
        setActiveCategory(null);
      }
    };

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setShowProfileDropdown(false);
        setShowSearchSuggestions(false);
        setActiveCategory(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, []);

  const fetchCartCount = async () => {
    try {
      if (user) {
        const response = await api.get('/cart');
        const cartItems = response.data.items || [];
        const totalQuantity = cartItems.reduce(
          (sum: number, item: any) => sum + (item.quantity || 0),
          0
        );
        setCartCount(totalQuantity);
      } else {
        const guestCart = guestCartService.getCart();
        const totalQuantity = guestCart.reduce((sum: number, item: any) => sum + item.quantity, 0);
        setCartCount(totalQuantity);
      }
    } catch (error) {
      logger.error('Error fetching cart count:', error);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      const basePath = getUserBasePath();
      router.push(`${basePath}/search?q=${encodeURIComponent(searchQuery.trim())}`);
      setShowSearchSuggestions(false);
    }
  };

  const searchTimerRef = useRef<NodeJS.Timeout | null>(null);

  const handleSearchInputChange = (value: string) => {
    setSearchQuery(value);
    if (value.length > 2) {
      // Debounced API call for real suggestions
      if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
      searchTimerRef.current = setTimeout(async () => {
        try {
          const res = await api.get(`/products/suggest?q=${encodeURIComponent(value)}&limit=6`);
          const suggestions: string[] = res.data?.suggestions || [];
          setSearchSuggestions(suggestions);
          setShowSearchSuggestions(suggestions.length > 0);
        } catch (error) {
          logger.error('Suggest API failed:', error);
          setShowSearchSuggestions(false);
        }
      }, 300);
    } else {
      setShowSearchSuggestions(false);
    }
  };

  const getUserBasePath = () => {
    if (!user) return '/';
    if (user.role === 'customer') return '/customer';
    if (user.role === 'wholesaler') return '/wholesaler';
    if (user.role === 'valet') return '/valet';
    return '/';
  };

  const handleCategoryClick = (category: string) => {
    const basePath = getUserBasePath();
    router.push(`${basePath}/category/${category}`);
    setActiveCategory(null);
  };

  const handleSubcategoryClick = (category: string, subcategory: string) => {
    const basePath = getUserBasePath();
    router.push(`${basePath}/category/${category}/${subcategory}`);
    setActiveCategory(null);
  };

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <header className={styles.modernHeader}>
      {/* Top Banner */}
      <div className={styles.topBanner}>
        <div className={styles.bannerContent}>
          <span>🎉 UPTO ₹300 OFF on selected items</span>
        </div>
      </div>

      {/* Main Header */}
      <div className={styles.mainHeader}>
        <div className={styles.headerContainer}>
          {/* Logo */}
          <Link href="/landingpage" className={styles.logo}>
            <h1
              className="font-serif"
              style={{
                color: theme.primary,
                fontSize: '1.6rem',
                whiteSpace: 'nowrap',
                fontWeight: 'bold',
              }}
            >
              Stationery Junction
            </h1>
          </Link>

          {/* Main Navigation */}
          <nav className={styles.mainNav} ref={megaMenuRef}>
            {categories.map((category) => (
              <div
                key={category.id}
                className={`${styles.navItem} ${activeCategory === category.id ? styles.active : ''}`}
                onMouseEnter={() => setActiveCategory(category.id)}
                onMouseLeave={() => setActiveCategory(null)}
              >
                <button className={styles.navLink}>{category.name}</button>

                {/* Mega Menu */}
                {activeCategory === category.id && (
                  <div className={styles.megaMenu}>
                    <div className={styles.megaMenuContent}>
                      {category.subcategories?.map((subcategory) => (
                        <div key={subcategory.id} className={styles.megaMenuColumn}>
                          <h4
                            className={styles.subcategoryTitle}
                            onClick={() => handleCategoryClick(category.id)}
                          >
                            {subcategory.name}
                          </h4>
                          <ul className={styles.subcategoryList}>
                            {subcategory.items?.map((item) => (
                              <li key={item}>
                                <button
                                  className={styles.subcategoryItem}
                                  onClick={() =>
                                    handleSubcategoryClick(category.id, subcategory.id)
                                  }
                                >
                                  {item}
                                </button>
                              </li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </nav>

          {/* Search Bar */}
          <div className={styles.searchContainer} ref={searchRef}>
            <form onSubmit={handleSearch} className={styles.searchForm}>
              <div className={styles.searchInputWrapper}>
                <SearchIcon />
                <input
                  type="text"
                  placeholder="Search for products, brands and more"
                  value={searchQuery}
                  onChange={(e) => handleSearchInputChange(e.target.value)}
                  onFocus={() => searchQuery.length > 2 && setShowSearchSuggestions(true)}
                  className={styles.searchInput}
                />
                {searchQuery && (
                  <button
                    type="button"
                    onClick={() => {
                      setSearchQuery('');
                      setShowSearchSuggestions(false);
                    }}
                    className={styles.clearSearch}
                  >
                    <CloseIcon />
                  </button>
                )}
              </div>
            </form>

            {/* Search Suggestions */}
            {showSearchSuggestions && (
              <div className={styles.searchSuggestions}>
                {searchSuggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    className={styles.suggestionItem}
                    onClick={() => {
                      setSearchQuery(suggestion);
                      setShowSearchSuggestions(false);
                      handleSearch({ preventDefault: () => {} } as React.FormEvent);
                    }}
                  >
                    <SearchIcon />
                    {suggestion}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Right Icons */}
          <div className={styles.headerIcons}>
            {/* Theme Switcher */}
            <ThemeSwitcher />

            {/* Profile */}
            <div className={styles.profileWrapper} ref={profileDropdownRef}>
              <button
                className={styles.iconButton}
                onClick={() => setShowProfileDropdown(!showProfileDropdown)}
              >
                <ProfileIcon />
                <span>Profile</span>
              </button>

              {showProfileDropdown && (
                <div className={styles.profileDropdown}>
                  {user ? (
                    <>
                      <div className={styles.userInfo}>
                        <span className={styles.userName}>{user.name}</span>
                        <span className={styles.userEmail}>{user.email}</span>
                      </div>
                      <div className={styles.dropdownDivider} />
                      <button
                        className={styles.dropdownItem}
                        onClick={() => {
                          setShowProfileDropdown(false);
                          router.push(`${getUserBasePath()}/profile`);
                        }}
                      >
                        My Profile
                      </button>
                      <button
                        className={styles.dropdownItem}
                        onClick={() => {
                          setShowProfileDropdown(false);
                          router.push(`${getUserBasePath()}/orders`);
                        }}
                      >
                        My Orders
                      </button>
                      <button
                        className={styles.dropdownItem}
                        onClick={() => {
                          setShowProfileDropdown(false);
                          router.push(`${getUserBasePath()}/wishlist`);
                        }}
                      >
                        Wishlist
                      </button>
                      {user?.role === 'super_admin' && (
                        <button
                          className={styles.dropdownItem}
                          onClick={() => {
                            setShowProfileDropdown(false);
                            router.push('/admin');
                          }}
                        >
                          Admin Panel
                        </button>
                      )}
                      <div className={styles.dropdownDivider} />
                      <button
                        className={styles.dropdownItem}
                        onClick={() => {
                          setShowProfileDropdown(false);
                          handleLogout();
                        }}
                      >
                        Logout
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        className={styles.dropdownItem}
                        onClick={() => {
                          setShowProfileDropdown(false);
                          router.push('/login');
                        }}
                      >
                        Login
                      </button>
                      <button
                        className={styles.dropdownItem}
                        onClick={() => {
                          setShowProfileDropdown(false);
                          router.push('/register');
                        }}
                      >
                        Register
                      </button>
                    </>
                  )}
                </div>
              )}
            </div>

            {/* Wishlist */}
            <button
              className={styles.iconButton}
              onClick={() => router.push(`${getUserBasePath()}/wishlist`)}
            >
              <WishlistIcon count={wishlistItems.length} />
              <span>Wishlist</span>
            </button>

            {/* Cart */}
            <button
              className={styles.iconButton}
              onClick={() => router.push(`${getUserBasePath()}/cart`)}
            >
              <MyCartIcon cartCount={cartCount} />
              <span>Bag</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
