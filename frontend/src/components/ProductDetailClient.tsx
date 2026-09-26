'use client';

import { useState, useEffect, useMemo } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import api from '@/utils/api';
import {
  recordEvent,
  trackEcommerceEvent,
  trackAddToWishlist,
  trackRemoveFromWishlist,
  trackBackendProductView,
  getSessionId,
} from '@/utils/analytics';
import { useAuth } from '@/context/AuthContext';
import { useWishlist } from '@/context/WishlistContext';
import { useCart } from '@/context/CartContext';
import { useTheme } from '@/context/ThemeContext';
import { getImageUrlWithFallback } from '@/utils/imageUrl';
import { getMinimumQuantity } from '@/utils/priceCalculator';
import { useShare } from '@/hooks/useShare';
import Header from '@/components/Header';
import ProductCarousel from '@/components/ProductCarousel';
import styles from '@/app/customer/product/[id]/ProductDetail.module.css';
import { toast } from 'react-toastify';
import AuthModal from '@/components/AuthModal';
import { usePincode } from '@/context/PincodeContext';
import { logger } from '@/utils/logger';
import { useSellerAvailability, formatUnavailableUntil } from '@/hooks/useSellerAvailability';


// Icons
const StarIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
  </svg>
);

const HeartIcon = () => (
  <svg
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
  </svg>
);

const ShareIcon = () => (
  <svg
    width="20"
    height="20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <circle cx="18" cy="5" r="3" />
    <circle cx="6" cy="12" r="3" />
    <circle cx="18" cy="19" r="3" />
    <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
    <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
  </svg>
);

export interface ProductDetailClientProps {
  initialProduct?: any;
  searchParams?: { [key: string]: string | string[] | undefined };
}

export default function ProductDetailClient({ initialProduct, searchParams }: ProductDetailClientProps) {
  const { id } = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const { theme } = useTheme();
  const { addToWishlist, removeFromWishlist, isInWishlist } = useWishlist();
  const { cart, addToCart, updateQuantity, removeFromCart, fetchCart, openCart } = useCart();
  const { pincode, serviceableSellers } = usePincode();
  const { share } = useShare();
  const { sellerAvailability } = useSellerAvailability();
  const [product, setProduct] = useState<any>(initialProduct || null);
  const [loading, setLoading] = useState(!initialProduct);
  const [quantity, setQuantity] = useState(1);
  const [hasInteractedWithQuantity, setHasInteractedWithQuantity] = useState(false);
  const [selectedVariants, setSelectedVariants] = useState<Record<string, string>>({});
  const [currentCombination, setCurrentCombination] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [reviewsList, setReviewsList] = useState<any[]>([]);
  const [bundles, setBundles] = useState<any[]>([]);
  // Pincode availability state
  const [requestAdded, setRequestAdded] = useState(false);
  const [notifyAdded, setNotifyAdded] = useState(false);
  const [pincodeActionLoading, setPincodeActionLoading] = useState<'request' | 'notify' | null>(null);

  // Seller time-off state — derived from the zone-status map each render
  // (product state may be null on first render; defaults to "available")
  const productSellerId: string | undefined = product?.sellers?.[0]?.sellerId;
  const sellerTimeOffUntil: string | undefined =
    productSellerId ? sellerAvailability[productSellerId] : undefined;
  const isSellerTimeOff = !!sellerTimeOffUntil;


  // Computes how many full copies of a bundle are currently in the cart.
  // Each bundle item is tagged with bundleId; we find the minimum ratio of
  // (cart item quantity / bundle item quantity) across all bundle items.
  const getBundleCartCount = (bundle: any): number => {
    if (!cart?.items?.length || !bundle?.items?.length) return 0;
    const counts = bundle.items.map((bItem: any) => {
      const cartItem = cart.items.find(
        (i: any) => i.bundleId === bundle.id && (i.product?.id || i.product) === bItem.productId
      );
      if (!cartItem) return 0;
      return Math.floor(cartItem.quantity / bItem.quantity);
    });
    return Math.min(...counts);
  };

  // Decrements one full copy of the bundle from the cart.
  const handleBundleDecrement = async (bundle: any) => {
    try {
      for (const bItem of bundle.items) {
        const cartItem = cart?.items?.find(
          (i: any) => i.bundleId === bundle.id && (i.product?.id || i.product) === bItem.productId
        );
        if (!cartItem) continue;
        const newQty = cartItem.quantity - bItem.quantity;
        if (newQty <= 0) {
          await removeFromCart(cartItem.id);
        } else {
          await updateQuantity(cartItem.id, newQty);
        }
      }
      await fetchCart();
    } catch (e) { logger.warn("Silent catch block:", e); /* silent — fetchCart will re-sync state */ }
  };
  const [selectedClassification, setSelectedClassification] = useState<string>('All');
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [pendingWishlistAction, setPendingWishlistAction] = useState(false);

  const classificationsWithReviews = useMemo(() => {
    const classes = new Set<string>();
    reviewsList.forEach((r: any) => {
      if (r.classification) {
        classes.add(r.classification);
      }
    });
    return Array.from(classes);
  }, [reviewsList]);

  const filteredReviewsList = useMemo(() => {
    if (selectedClassification === 'All') {
      return reviewsList;
    }
    return reviewsList.filter((r: any) => r.classification === selectedClassification);
  }, [reviewsList, selectedClassification]);

  // Initialize selected variants from initialProduct if it exists
  useEffect(() => {
    if (
      initialProduct?.variantAttributes &&
      initialProduct?.variantAttributes.length > 0 &&
      initialProduct?.variantCombinations?.length > 0
    ) {
      const firstCombo = initialProduct.variantCombinations[0];
      setSelectedVariants(firstCombo.attributes);
      setCurrentCombination(firstCombo);
    }
  }, [initialProduct]);

  useEffect(() => {
    if (id) {
      // If user is logged in, or there is no initial product, fetch the product for potentially private details
      if (user || !initialProduct) {
        fetchProduct();
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, user]);

  useEffect(() => {
    if (product?.id) {
      trackEcommerceEvent('view_item', {
        value: product.price,
        items: [
          {
            item_id: product.id,
            item_name: product.name,
            price: product.price,
            item_brand: product.brand,
            item_category: product.category,
            quantity: 1,
          },
        ],
      });
      recordEvent({
        type: 'product_view',
        payload: { productId: product.id, name: product.name },
      });
      trackBackendProductView(product.id, product.name);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [product?.id]);

  const cartItem = useMemo(() => {
    return cart?.items?.find((item: any) => {
      const isSameProduct = item.product?.id === product?.id || item.id === product?.id;
      if (!isSameProduct) return false;
      
      if (product?.variantAttributes?.length > 0) {
        const itemVariants = item.variantAttributes || {};
        const currentVariants = selectedVariants || {};
        return Object.keys(currentVariants).every(
          (key) => itemVariants[key] === currentVariants[key]
        );
      }
      return true;
    });
  }, [cart, product, selectedVariants]);

  const isSameAsCart = cartItem && quantity === cartItem.quantity;

  useEffect(() => {
    if (cartItem && !hasInteractedWithQuantity) {
      setQuantity(cartItem.quantity);
    } else if (!hasInteractedWithQuantity) {
      const role = user?.effectiveRole || user?.role || 'customer';
      const minQty = product ? getMinimumQuantity(product, role) : 1;
      setQuantity(minQty);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cartItem?.quantity, currentCombination, product, user]);

  useEffect(() => {
    const fetchRecommendations = async () => {
      if (!product?.category) return;
      try {
        const endpoint = user ? '/products' : '/products/public';
        const params: any = {
          category: product.category,
          sort: 'popular',
          limit: 10
        };
        if (product.subCategory) {
          params.subCategory = product.subCategory;
        }
        const response = await api.get(endpoint, { params });
        let prods = response.data.products || [];
        prods = prods.filter((p: any) => p.id !== product.id);
        // Exclude products from sellers currently in a time-off window
        prods = prods.filter((p: any) => {
          const sid = p.sellers?.[0]?.sellerId;
          return !sid || !sellerAvailability[sid];
        });
        const mapped = prods.map((p: any) => ({
          id: p.id,
          name: p.name,
          displayImage: p.images?.[0],
          displayPrice: p.price,
          displayStock: p.stock
        }));
        setRecommendations(mapped);

      } catch (error) {
        logger.error('Failed to fetch recommendations', error);
      }
    };

    fetchRecommendations();
  }, [product?.id, product?.category, product?.subCategory, user]);

  useEffect(() => {
    const fetchBundles = async () => {
      if (!id) return;
      try {
        const response = await api.get(`/bundles/product/${id}`);
        setBundles(response.data.bundles || []);
      } catch (error) {
        logger.error('Failed to fetch bundles for product', error);
      }
    };

    fetchBundles();
  }, [id]);

  const fetchReviews = async () => {
    if (!id) return;
    try {
      const res = await api.get(`/reviews/product/${id}`);
      setReviewsList(res.data || []);
    } catch (err) {
      logger.error('Failed to fetch reviews', err);
    }
  };

  useEffect(() => {
    if (id) {
      fetchReviews();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const fetchProduct = async () => {
    try {
      // Use public endpoint for unauthenticated users, private endpoint for authenticated
      const endpoint = user ? `/products/${id}` : `/products/public/${id}`;
      const response = await api.get(endpoint);
      const productData = response.data;
      setProduct(productData);

      // Initialize selected variants with first available combination if possible
      if (
        productData.variantAttributes &&
        productData.variantAttributes.length > 0 &&
        productData.variantCombinations?.length > 0
      ) {
        const firstCombo = productData.variantCombinations[0];
        setSelectedVariants(firstCombo.attributes);
        setCurrentCombination(firstCombo);
      }

      setLoading(false);
    } catch (error) {
      logger.error('Product not found', error);
      toast.error('Product could not be loaded. Please try again.');
      router.push('/customer');
      setLoading(false);
    }
  };

  const handleAddToCart = async () => {
    try {
      await addToCart(id as string, quantity, product, selectedVariants);
      trackEcommerceEvent('add_to_cart', {
        value: activePrice * quantity,
        items: [
          {
            item_id: product.id,
            item_name: product.name,
            price: activePrice,
            item_brand: product.brand,
            item_category: product.category,
            variant: Object.values(selectedVariants).join(' / '),
            quantity: quantity,
          },
        ],
      });
      recordEvent({
        type: 'add_to_cart',
        payload: { productId: id, quantity, page: 'pdp', variants: selectedVariants },
      });
      toast.success('Product added to cart');
      setHasInteractedWithQuantity(false);
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to add to cart');
    }
  };

  const handleUpdateCart = async () => {
    if (!cartItem) return;
    try {
      await updateQuantity(cartItem.id, quantity);
      toast.success('Cart updated');
      setHasInteractedWithQuantity(false);
      openCart();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to update cart');
    }
  };

  const handleWishlistToggle = async () => {
    if (!product?.id) return;
    try {
      if (isInWishlist(product.id)) {
        trackRemoveFromWishlist({
          productId: product.id,
          productName: product.name,
          source: 'product_detail',
        });
        await removeFromWishlist(product.id);
      } else {
        if (!user) {
          setPendingWishlistAction(true);
          setShowAuthModal(true);
          return;
        }
        trackAddToWishlist({
          productId: product.id,
          productName: product.name,
          source: 'product_detail',
        });
        await addToWishlist(product.id, getSessionId());
      }
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (e) {
      toast.error('Could not update wishlist. Please try again.');
    }
  };

  const activePrice = useMemo(() => {
    if (currentCombination) return currentCombination.price;
    return product?.price || 0;
  }, [product, currentCombination]);

  const activeMrp = useMemo(() => {
    if (currentCombination) return currentCombination.price; // For now use same unless combo has mrp
    return product?.mrp || 0;
  }, [product, currentCombination]);

  const discountPercentage = useMemo(() => {
    const p = activePrice;
    const m = activeMrp;
    if (!m || p >= m) return 0;
    return Math.round(((m - p) / m) * 100);
  }, [activePrice, activeMrp]);

  const isOutOfStock = useMemo(() => {
    if (product?.variantAttributes?.length > 0) {
      return !currentCombination || currentCombination.stock <= 0;
    }
    return !product?.stock || product?.stock <= 0;
  }, [product, currentCombination]);

  // Hyperlocal availability check: is this product available at user's pincode?
  // True when: no pincode set (can't check), OR at least one of the product's
  // active+stocked sellers serves the user's pincode.
  const isAvailableAtPincode = useMemo(() => {
    if (!pincode) return true; // No pincode set — optimistic
    if (!serviceableSellers || serviceableSellers.length === 0) return false;
    const productSellers: any[] = product?.sellers || [];
    if (productSellers.length === 0) return true; // No seller restriction info — optimistic
    const serviceableIds = new Set(serviceableSellers.map((s: any) => String(s.id)));
    return productSellers.some(
      (s: any) =>
        s.isActive &&
        (s.stock ?? 0) > 0 &&
        (s.requestStatus === 'approved' || !s.requestStatus) &&
        serviceableIds.has(String(s.sellerId))
    );
  }, [pincode, serviceableSellers, product, user]);

  const handleVariantSelect = (attr: string, value: string) => {
    const newSelections = { ...selectedVariants, [attr]: value };
    setSelectedVariants(newSelections);
    setHasInteractedWithQuantity(false);

    // Find matching combination
    if (product.variantCombinations) {
      const match = product.variantCombinations.find((combo: any) =>
        Object.entries(newSelections).every(([k, v]) => combo.attributes[k] === v)
      );
      setCurrentCombination(match || null);
    }
  };

  // Check if a specific value for an attribute is "Sold Out" given current selections
  const isOptionSoldOut = (attr: string, value: string) => {
    if (!product.variantCombinations) return false;

    // Create a temporary selection with this value
    const tempSelections = { ...selectedVariants, [attr]: value };

    // Check if any combination matches this selection AND has stock
    // If the product has multiple axes, we need to check if ANY combination exists with this value and current other selections
    const possibleCombo = product.variantCombinations.find((combo: any) =>
      Object.entries(tempSelections).every(([k, v]) => combo.attributes[k] === v)
    );

    return !possibleCombo || possibleCombo.stock <= 0;
  };

  if (loading) {
    return (
      <>
        <Header />
        <div className={styles.container}>
          <div className="flex animate-pulse flex-col gap-8">
            <div className="h-8 w-1/4 rounded bg-gray-200"></div>
            <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
              <div className="h-[600px] rounded bg-gray-200"></div>
              <div className="flex flex-col gap-4">
                <div className="h-10 w-3/4 rounded bg-gray-200"></div>
                <div className="h-6 w-1/2 rounded bg-gray-200"></div>
                <div className="h-24 rounded bg-gray-200"></div>
                <div className="h-14 rounded bg-gray-200"></div>
              </div>
            </div>
          </div>
        </div>
      </>
    );
  }

  if (!product) {
    return (
      <>
        <Header />
        <div className={styles.container}>Product not found</div>
      </>
    );
  }

  // Get role-based home path
  const getHomePath = () => {
    if (!user) return '/';
    switch (user.role) {
      case 'customer':
        return '/customer';
      case 'wholesaler':
        return '/wholesaler';
      default:
        return '/';
    }
  };

  // Get role-based product listing path
  const getListingPath = () => {
    if (!user) return '/customer';
    switch (user.role) {
      case 'wholesaler':
        return '/wholesaler';
      default:
        return '/customer';
    }
  };

  // Build breadcrumb parts dynamically based on where the user came from
  const breadcrumbParts: { label: string; href?: string }[] = [
    { label: 'Home', href: getHomePath() },
  ];

  const refBrand = searchParams?.refBrand as string | undefined;
  const refCollection = searchParams?.refCollection as string | undefined;

  if (refBrand) {
    // If they came from a Brand page or filtered by Brand
    breadcrumbParts.push({
      label: 'Brands',
      href: '/brands',
    });
    breadcrumbParts.push({
      label: refBrand,
      href: `/brands/${encodeURIComponent(refBrand)}`,
    });
  } else if (refCollection) {
    // If they came from a Collection
    breadcrumbParts.push({
      label: 'Collections',
      href: '/collections', // if we had a collections page, otherwise maybe just list it
    });
    breadcrumbParts.push({
      label: refCollection,
      href: `/collections/${encodeURIComponent(refCollection)}`,
    });
  } else {
    // Default category fallback
    if (product.category) {
      breadcrumbParts.push({
        label: product.category,
        href: `${getListingPath()}?category=${encodeURIComponent(product.category)}`,
      });
    }
    if (product.subCategory) {
      breadcrumbParts.push({
        label: product.subCategory,
        href: `${getListingPath()}?category=${encodeURIComponent(product.category)}&subCategory=${encodeURIComponent(product.subCategory)}`,
      });
    }
  }

  // Add product name as active page (no href)
  breadcrumbParts.push({
    label: product.name,
  });

  return (
    <>
      <Header />
      <div className="w-full max-w-full overflow-x-hidden">
        {/* Breadcrumbs - Consistent with product listing page */}
        <div className="border-b border-gray-100 bg-white px-4 py-3 text-xs font-medium tracking-wide text-gray-500 md:px-6">
          <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-1.5">
            {breadcrumbParts.map((part, index) => (
              <span key={index} className="flex items-center gap-1.5">
                {index === 0 && (
                  <svg
                    className="h-3.5 w-3.5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
                    />
                  </svg>
                )}
                {index > 0 && (
                  <svg
                    className="h-3 w-3 text-gray-300"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                )}
                {part.href ? (
                  <Link href={part.href} className="transition-colors hover:text-gray-900">
                    {part.label}
                  </Link>
                ) : (
                  <span className="text-gray-600">{part.label}</span>
                )}
              </span>
            ))}
          </div>
        </div>

        <div className={styles.container}>
          <div className={styles.productWrapper}>
            {/* Left: Image Gallery */}
            <div className={styles.imageGallery}>
              {product.images && product.images.length > 0 ? (
                product.images.map((img: string, idx: number) => (
                  <div key={idx} className={styles.productImageItem}>
                    <Image
                      src={getImageUrlWithFallback(img)}
                      alt={`${product.name} view ${idx + 1}`}
                      width={600}
                      height={800}
                      priority={idx === 0}
                      style={{ objectFit: 'cover', width: '100%', height: 'auto' }}
                    />
                  </div>
                ))
              ) : (
                <div className={styles.productImageItem}>
                  <div className="flex h-full w-full items-center justify-center text-gray-400">
                    No Image Available
                  </div>
                </div>
              )}
            </div>

            {/* Right: Sticky Details */}
            <div className={styles.productDetails}>
              <p className={styles.brandName}>{product.brand || 'Stationery Junction'}</p>
              <h1 className={styles.productName}>{product.name}</h1>

              {/* Social Proof Rating */}
              {product.rating && (
                <div className={styles.ratingBadge}>
                  <span>{product.rating.toFixed(1)}</span>
                  <span className={styles.starIcon}>
                    <StarIcon />
                  </span>
                  <span className={styles.ratingDivider}>|</span>
                  <span className={styles.reviewText}>{product.reviews || 0} Ratings</span>
                </div>
              )}

              <div className={styles.priceSection}>
                <div className={styles.priceRow}>
                  <span className={styles.currentPrice}>₹{activePrice?.toFixed(0)}</span>
                  {discountPercentage > 0 && (
                    <>
                      <span className={styles.mrpLabel}>
                        MRP <span className={styles.originalPrice}>₹{activeMrp?.toFixed(0)}</span>
                      </span>
                      <span className={styles.discount}>({discountPercentage}% OFF)</span>
                    </>
                  )}
                </div>
                <p className={styles.taxInfo}>inclusive of all taxes</p>
              </div>

              {/* Available Offers Section */}
              {product.applicableDiscounts && product.applicableDiscounts.length > 0 && (
                <div className="mb-6 rounded-lg border border-dashed border-[#ff3f6c]/30 bg-[#ff3f6c]/5 p-4 transition-all">
                  <h3 className="mb-3 text-xs font-bold uppercase tracking-wider text-[#ff3f6c]">
                    Available Offers & Discounts
                  </h3>
                  <div className="flex flex-col gap-2.5">
                    {product.applicableDiscounts.map((disc: any, index: number) => (
                      <div key={index} className="flex items-start gap-2.5 text-xs text-gray-700">
                        <span className="mt-0.5 inline-flex items-center justify-center rounded-full bg-[#ff3f6c]/10 p-1 text-[#ff3f6c]">
                          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5a2 2 0 10-2 2h2zm0 0h4m-4 0h-4m0 0v13m0 13h8" />
                          </svg>
                        </span>
                        <div className="flex-1">
                          <p className="font-semibold text-gray-800">{disc.description}</p>
                          {disc.code && (
                            <span className="mt-1 inline-block rounded bg-white border border-[#ff3f6c]/20 px-1.5 py-0.5 font-mono text-[10px] font-bold text-[#ff3f6c] uppercase">
                              Code: {disc.code}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* New Multi-Axis Variants Selector */}
              {product.variantAttributes && product.variantAttributes.length > 0 && (
                <div className="mb-8 flex flex-col gap-6">
                  {product.variantAttributes.map((attr: string) => {
                    // Determine unique values for this attribute axis
                    const uniqueValues = Array.from(
                      new Set(product.variantCombinations.map((c: any) => c.attributes[attr]))
                    ).filter(Boolean) as string[];

                    return (
                      <div key={attr} className="flex flex-col gap-3">
                        <span className="text-xs font-bold uppercase tracking-widest text-gray-800">
                          {attr}
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {uniqueValues.map((val: string) => {
                            const isSelected = selectedVariants[attr] === val;
                            const soldOut = isOptionSoldOut(attr, val);

                            return (
                              <button
                                key={val}
                                onClick={() => handleVariantSelect(attr, val)}
                                className={`relative overflow-hidden border-2 px-4 py-1.5 text-xs font-bold transition-all ${
                                  isSelected
                                    ? 'border-[#ff3f6c] bg-[#ff3f6c]/5 text-[#ff3f6c]'
                                    : 'border-gray-200 text-gray-700 hover:border-gray-300'
                                } ${soldOut ? 'text-gray-400 opacity-60' : ''} rounded-md`}
                              >
                                {val}
                                {soldOut && (
                                  <div className="pointer-events-none absolute inset-0">
                                    <div className="absolute left-0 top-1/2 h-[1px] w-full translate-y-[-50%] -rotate-12 bg-gray-400"></div>
                                  </div>
                                )}
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Quantity Selector */}
              <div className="mb-6 flex flex-col gap-2">
                <div className="flex items-center gap-4">
                  <span className="text-sm font-bold uppercase tracking-widest text-gray-800">
                    Select Quantity
                  </span>
                  <div className="flex items-center overflow-hidden rounded border border-gray-300">
                    <button
                      onClick={() => { setQuantity((q) => Math.max(1, q - 1)); setHasInteractedWithQuantity(true); }}
                      className="border-r px-3 py-1 hover:bg-gray-100"
                    >
                      -
                    </button>
                    <input
                      type="number"
                      value={quantity}
                      onChange={(e) => { setQuantity(Math.max(1, parseInt(e.target.value) || 1)); setHasInteractedWithQuantity(true); }}
                      className="w-12 py-1 text-center font-bold outline-none"
                    />
                    <button
                      onClick={() => { setQuantity((q) => q + 1); setHasInteractedWithQuantity(true); }}
                      className="border-l px-3 py-1 hover:bg-gray-100"
                    >
                      +
                    </button>
                  </div>
                </div>
                {user &&
                  (() => {
                    const role = user.effectiveRole || user.role;
                    const minQty = getMinimumQuantity(product, role);
                    if (minQty > 1) {
                      return (
                        <p className="text-xs font-bold text-red-500">
                          Minimum order: {minQty} units
                        </p>
                      );
                    }
                  })()}
                
                {/* Quantity Discounts Tier Indicator Strip */}
                {product.quantityTiers && product.quantityTiers.length > 0 && (
                  <div className="mt-4 rounded-xl border border-rose-100 bg-rose-50/30 p-3.5 transition-all">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-rose-500 block mb-2">
                      📊 Tiered Quantity Discounts ({product.quantityItemType || 'units'})
                    </span>
                    <div className="flex flex-col gap-1.5">
                      {(() => {
                        const qtyToUse = (user && (user.effectiveRole || user.role) === 'wholesaler' && product.quantityItemType === 'cases' && product.quantityPerCase)
                          ? Math.floor(quantity / product.quantityPerCase)
                          : quantity;
                        const sortedTiers = [...product.quantityTiers].sort((a: any, b: any) => a.quantity - b.quantity);
                        const activeTier = [...sortedTiers].reverse().find((t: any) => qtyToUse >= t.quantity);
                        
                        return sortedTiers.map((tier: any, index: number) => {
                          const isActive = activeTier && activeTier.quantity === tier.quantity;
                          const label = product.quantityItemType === 'cases' ? 'cases' : 'units';
                          return (
                            <div
                              key={index}
                              className={`flex items-center justify-between rounded-lg px-3 py-2 text-xs font-semibold border transition-all ${
                                isActive
                                  ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-700'
                                  : 'bg-white border-gray-100 text-gray-600'
                              }`}
                            >
                              <div className="flex items-center gap-2">
                                {isActive ? (
                                  <svg className="h-4 w-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                  </svg>
                                ) : (
                                  <span className="h-1.5 w-1.5 rounded-full bg-gray-300" />
                                )}
                                <span>Buy {tier.quantity}+ {label}</span>
                              </div>
                              <span className={isActive ? 'text-emerald-700 font-bold' : 'text-gray-500 font-bold'}>
                                {tier.discount}% off {isActive && '✓ ACTIVE'}
                              </span>
                            </div>
                          );
                        });
                      })()}
                    </div>
                  </div>
                )}
              </div>

              {/* Seller Time-Off Banner */}
              {isSellerTimeOff && (
                <div className="mb-4 rounded-xl border border-orange-200 bg-orange-50 dark:bg-orange-900/20 dark:border-orange-700 p-4">
                  <div className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-orange-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-orange-800 dark:text-orange-300">
                        Product currently unavailable
                      </p>
                      <p className="text-xs text-orange-700 dark:text-orange-400 mt-0.5">
                        This product will be back by{' '}
                        <span className="font-semibold">{formatUnavailableUntil(sellerTimeOffUntil!)}</span>.
                        You can save it to your wishlist and check back then.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Pincode Unavailability Banner */}
              {pincode && !isAvailableAtPincode && (

                <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 dark:bg-amber-900/20 dark:border-amber-700 p-4">
                  <div className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-amber-800 dark:text-amber-300">
                        {(user?.role === 'wholesaler' || user?.effectiveRole === 'wholesaler') 
                          ? 'Not eligible for your account' 
                          : `Not available at your pincode (${pincode})`}
                      </p>
                      <p className="text-xs text-amber-700 dark:text-amber-400 mt-0.5">
                        {(user?.role === 'wholesaler' || user?.effectiveRole === 'wholesaler') 
                          ? 'This product is not serviced for business accounts.' 
                          : 'This product is currently not delivered to your area.'}
                      </p>
                      <div className="flex flex-wrap gap-2 mt-3">
                        <button
                          onClick={async () => {
                            if (requestAdded || pincodeActionLoading) return;
                            setPincodeActionLoading('request');
                            try {
                              await api.post('/availability-requests', {
                                productId: product.id || product.id,
                                productName: product.name,
                                pincode,
                              });
                              setRequestAdded(true);
                              toast.success('Request submitted! We\'ll work on bringing this to your pincode.');
                            } catch {
                              toast.error('Failed to submit request. Please try again.');
                            } finally {
                              setPincodeActionLoading(null);
                            }
                          }}
                          disabled={requestAdded || pincodeActionLoading !== null}
                          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold bg-amber-600 hover:bg-amber-700 text-white disabled:opacity-60 disabled:cursor-not-allowed transition-all"
                        >
                          {pincodeActionLoading === 'request' ? (
                            <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          ) : requestAdded ? '✓ Requested' : '+ Request Addition'}
                        </button>
                        <button
                          onClick={async () => {
                            if (notifyAdded || pincodeActionLoading) return;
                            setPincodeActionLoading('notify');
                            try {
                              await api.post('/tracking/notify-pincode', {
                                productId: product.id || product.id,
                                productName: product.name,
                                pincode,
                              });
                              setNotifyAdded(true);
                              toast.success('We\'ll notify you when this product is available at your pincode!');
                            } catch {
                              toast.error('Failed to set notification. Please try again.');
                            } finally {
                              setPincodeActionLoading(null);
                            }
                          }}
                          disabled={notifyAdded || pincodeActionLoading !== null}
                          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold border border-amber-600 text-amber-700 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-900/30 disabled:opacity-60 disabled:cursor-not-allowed transition-all"
                        >
                          {pincodeActionLoading === 'notify' ? (
                            <span className="w-4 h-4 border-2 border-amber-600 border-t-transparent rounded-full animate-spin" />
                          ) : notifyAdded ? '✓ Notified' : (
                            <>
                              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                              </svg>
                              Notify Me
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className={styles.actionGroup}>
                {isOutOfStock ? (
                  <div className="flex-1 min-w-[200px]">
                    {user?.email ? (
                      <button
                        onClick={async () => {
                          try {
                            await api.post(`/products/${id}/notify-me`, {});
                            toast.success(`We will notify you at ${user.email} once restocked!`);
                          } catch (err: any) {
                            toast.error(err.response?.data?.detail || 'Failed to register notification');
                          }
                        }}
                        className="w-full flex items-center justify-center gap-2 rounded bg-[#ff3f6c] py-3.5 text-sm font-bold uppercase tracking-wider text-white hover:bg-[#e0355f] transition-all"
                      >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                        </svg>
                        Notify Me
                      </button>
                    ) : (
                      <div className="flex gap-2 w-full">
                        <input
                          type="email"
                          placeholder="Email for restock alert"
                          id="notify-email-input"
                          className="flex-1 rounded border border-gray-300 px-3 py-2 text-xs outline-none focus:border-[#ff3f6c] bg-white text-gray-800"
                        />
                        <button
                          onClick={async () => {
                            const input = document.getElementById('notify-email-input') as HTMLInputElement;
                            const email = input?.value?.trim() || '';
                            if (!email || !email.includes('@')) {
                              toast.error('Please enter a valid email address.');
                              return;
                            }
                            try {
                              await api.post(`/products/${id}/notify-me`, { email });
                              toast.success(`We will notify you at ${email} once restocked!`);
                              if (input) input.value = '';
                            } catch (err: any) {
                              toast.error(err.response?.data?.detail || 'Failed to register notification');
                            }
                          }}
                          className="rounded bg-[#ff3f6c] px-4 py-2.5 text-xs font-bold uppercase text-white hover:bg-[#e0355f] transition-all"
                        >
                          Notify
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  <button
                    onClick={isSameAsCart ? () => openCart() : (cartItem ? handleUpdateCart : handleAddToCart)}
                    disabled={(isOutOfStock || !isAvailableAtPincode || isSellerTimeOff) && !isSameAsCart}
                    className={`${styles.addToCartBtn} ${((isOutOfStock || !isAvailableAtPincode || isSellerTimeOff) && !isSameAsCart) ? 'cursor-not-allowed opacity-50' : ''}`}
                    style={{ background: ((isOutOfStock || !isAvailableAtPincode || isSellerTimeOff) && !isSameAsCart) ? '#a0a0a0' : theme.primary }}
                  >

                    <svg
                      width="20"
                      height="20"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      {isSameAsCart ? (
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13 5l7 7-7 7M5 12h14" />
                      ) : (
                        <>
                          <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" />
                          <line x1="3" y1="6" x2="21" y2="6" />
                          <path d="M16 10a4 4 0 0 1-8 0" />
                        </>
                      )}
                    </svg>
                    {isSameAsCart ? 'GO TO CART' : (!isAvailableAtPincode ? ((user?.role === 'wholesaler' || user?.effectiveRole === 'wholesaler') ? 'NOT ELIGIBLE' : 'UNAVAILABLE AT PINCODE') : (cartItem ? 'UPDATE CART' : 'ADD TO CART'))}
                  </button>
                )}
                <button
                  type="button"
                  className={styles.wishlistBtn}
                  onClick={handleWishlistToggle}
                  aria-pressed={product?.id ? isInWishlist(product.id) : false}
                >
                  <HeartIcon />
                  {product?.id && isInWishlist(product.id) ? ' SAVED' : ' WISHLIST'}
                </button>
                <button
                  type="button"
                  className={styles.shareBtn}
                  onClick={() => {
                    const productDetailUrl =
                      typeof window !== 'undefined'
                        ? `${window.location.origin}/customer/product/${id}`
                        : `/customer/product/${id}`;
                    share({
                      title: product?.name,
                      text: `${product?.name} - ₹${activePrice?.toFixed(0)}`,
                      url: productDetailUrl,
                    });
                  }}
                  aria-label="Share product"
                >
                  <ShareIcon />
                  SHARE
                </button>
              </div>

              {/* Trust Markers */}
              <div className="mb-8 rounded border border-gray-100 bg-gray-50 p-4">
                <div className="mb-2 flex items-center gap-3">
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#282c3f"
                    strokeWidth="2"
                  >
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                    <polyline points="22 4 12 14.01 9 11.01" />
                  </svg>
                  <span className="text-sm font-bold">100% Original Products</span>
                </div>
                <div className="flex items-center gap-3">
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#282c3f"
                    strokeWidth="2"
                  >
                    <rect x="1" y="3" width="15" height="13" />
                    <polygon points="16 8 20 8 23 11 23 16 16 16 16 8" />
                    <circle cx="5.5" cy="18.5" r="2.5" />
                    <circle cx="18.5" cy="18.5" r="2.5" />
                  </svg>
                  <span className="text-sm font-bold">Fast Delivery Available</span>
                </div>
              </div>

              {/* Description & Specs */}
              <div className={styles.productDescription}>
                <h3 className={styles.sectionTitle}>Product Details</h3>
                <p className={styles.descriptionText}>{product.description}</p>

                <div className={styles.specList}>
                  <div className={styles.specItem}>
                    <span className={styles.specLabel}>Category</span>
                    <span className={styles.specValue}>{product.category}</span>
                  </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Reviews & Ratings Section */}
            <div className="mt-12 border-t border-gray-200 pt-8 px-4 md:px-6 max-w-7xl mx-auto w-full">
              <h2 className="text-xl font-bold text-gray-900 mb-6">Customer Reviews & Ratings</h2>
              
              {reviewsList.length === 0 ? (
                <div className="rounded-lg bg-gray-50 p-6 text-center text-gray-500">
                  No reviews yet. Be the first to buy and review this product!
                </div>
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  {/* Rating Summary */}
                  <div className="lg:col-span-1 bg-gray-50 rounded-xl p-6 flex flex-col justify-between">
                    <div>
                      <div className="flex items-baseline gap-2 mb-2">
                        <span className="text-5xl font-extrabold text-gray-900">
                          {(reviewsList.reduce((acc, r) => acc + r.rating, 0) / reviewsList.length).toFixed(1)}
                        </span>
                        <span className="text-gray-500 text-lg">/ 5</span>
                      </div>
                      <div className="flex items-center gap-1 mb-2">
                        {Array.from({ length: 5 }).map((_, i) => {
                          const avg = reviewsList.reduce((acc, r) => acc + r.rating, 0) / reviewsList.length;
                          return (
                            <svg
                              key={i}
                              className={`h-6 w-6 ${i < Math.round(avg) ? 'text-yellow-400 fill-current' : 'text-gray-300'}`}
                              viewBox="0 0 24 24"
                            >
                              <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                            </svg>
                          );
                        })}
                      </div>
                      <p className="text-sm font-semibold text-gray-600">
                        Based on {reviewsList.length} verified review{reviewsList.length !== 1 ? 's' : ''}
                      </p>
                    </div>

                    {/* Classification Stats */}
                    {classificationsWithReviews.length > 0 && (
                      <div className="mt-6 border-t border-gray-200 pt-4">
                        <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wider mb-3">Reviews By Classification</h4>
                        <div className="space-y-2">
                          {classificationsWithReviews.map((cls) => {
                            const count = reviewsList.filter((r) => r.classification === cls).length;
                            const pct = Math.round((count / reviewsList.length) * 100);
                            return (
                              <div key={cls} className="flex items-center text-xs">
                                <span className="w-20 text-gray-600 truncate">{cls}</span>
                                <div className="flex-1 mx-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                                  <div className="h-full bg-[#ff3f6c] rounded-full" style={{ width: `${pct}%` }}></div>
                                </div>
                                <span className="w-8 text-right font-medium text-gray-700">{count}</span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Reviews List & Filters */}
                  <div className="lg:col-span-2">
                    {/* Classification Pills Filter */}
                    {classificationsWithReviews.length > 0 && (
                      <div className="flex flex-wrap gap-2 mb-6">
                        <button
                          onClick={() => setSelectedClassification('All')}
                          className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all border ${
                            selectedClassification === 'All'
                              ? 'bg-gray-900 border-gray-900 text-white'
                              : 'bg-white border-gray-200 text-gray-700 hover:border-gray-300'
                          }`}
                        >
                          All ({reviewsList.length})
                        </button>
                        {classificationsWithReviews.map((cls) => {
                          const count = reviewsList.filter((r) => r.classification === cls).length;
                          return (
                            <button
                              key={cls}
                              onClick={() => setSelectedClassification(cls)}
                              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all border ${
                                selectedClassification === cls
                                  ? 'bg-[#ff3f6c] border-[#ff3f6c] text-white'
                                  : 'bg-white border-gray-200 text-gray-700 hover:border-gray-300'
                              }`}
                            >
                              {cls} ({count})
                            </button>
                          );
                        })}
                      </div>
                    )}

                    {/* Reviews List */}
                    <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
                      {filteredReviewsList.map((review: any) => (
                        <div key={review.id} className="border border-gray-100 rounded-xl p-4 shadow-sm bg-white">
                          <div className="flex justify-between items-start mb-2">
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-bold text-sm text-gray-800">{review.userName || 'Verified Buyer'}</span>
                                <span className="inline-flex items-center px-1.5 py-0.5 rounded bg-green-50 text-[10px] font-bold text-green-700">
                                  <svg className="h-3 w-3 mr-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                  </svg>
                                  Verified Purchase
                                </span>
                              </div>
                              <div className="flex items-center gap-1 mt-1">
                                {Array.from({ length: 5 }).map((_, idx) => (
                                  <svg
                                    key={idx}
                                    className={`h-4 w-4 ${idx < review.rating ? 'text-yellow-400 fill-current' : 'text-gray-200'}`}
                                    viewBox="0 0 24 24"
                                  >
                                    <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                                  </svg>
                                ))}
                              </div>
                            </div>
                            <span className="text-xs text-gray-400 font-medium">
                              {new Date(review.createdAt || Date.now()).toLocaleDateString('en-IN', {
                                day: '2-digit',
                                month: 'short',
                                year: 'numeric'
                              })}
                            </span>
                          </div>
                          
                          {/* Comment */}
                          <p className="text-sm text-gray-700 leading-relaxed my-2.5">
                            {review.comment}
                          </p>

                          {/* Classification Badge */}
                          {review.classification && (
                            <span className="inline-block text-[10px] font-bold tracking-wider text-[#ff3f6c] bg-[#ff3f6c]/5 border border-[#ff3f6c]/10 rounded-full px-2.5 py-0.5 uppercase">
                              {review.classification}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

          {/* Recommendations Section */}
          {recommendations.length > 0 && (
            <div className="mt-12 w-full border-t border-gray-100 pt-8 pb-12">
              <h2 className="mb-6 px-4 text-xl font-bold text-gray-900 md:px-6">Similar Products</h2>
              <ProductCarousel 
                products={recommendations} 
                basePath={getListingPath()} 
                onProductClick={(p) => router.push(`${getListingPath()}/product/${p.id}`)}
              />
            </div>
          )}

          {/* Bundles Section */}
          {bundles.length > 0 && (
            <div className="mt-12 w-full border-t border-gray-100 pt-8 pb-12">
              <h2 className="mb-6 px-4 text-xl font-bold text-gray-900 md:px-6">Available in Promo Bundles</h2>
              <div className="grid grid-cols-1 gap-6 px-4 sm:grid-cols-2 lg:grid-cols-3 md:px-6 max-w-7xl mx-auto">
                {bundles.map((bundle) => (
                  <div key={bundle.id} className="relative flex flex-col justify-between overflow-hidden rounded-2xl border border-gray-100 bg-white p-6 shadow-sm transition-all hover:shadow-md">
                    <div>
                      {/* Bundle Savings Badge */}
                      <div className="absolute top-4 right-4 rounded-full bg-violet-100 px-3 py-1 text-xs font-bold text-violet-700">
                        Save {bundle.savingsPercent}%
                      </div>
                      
                      {/* Bundle Name & Description */}
                      <h3 className="mb-2 pr-16 text-lg font-bold text-gray-900 leading-snug">{bundle.name}</h3>
                      <p className="mb-4 text-sm text-gray-500 line-clamp-2">{bundle.description || 'Exclusive bundle pack'}</p>
                      
                      {/* Included Items */}
                      <div className="mb-6 space-y-2 border-t border-gray-50 border-dashed pt-4">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400">Included Items</span>
                        <div className="max-h-[120px] overflow-y-auto pr-1 space-y-1.5">
                          {bundle.items.map((bItem: any, idx: number) => (
                            <div key={idx} className="flex items-center justify-between text-xs text-gray-700">
                              <span className="truncate pr-4">• {bItem.product?.name || 'Product'}</span>
                              <span className="font-semibold text-gray-500 shrink-0">x{bItem.quantity}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Price and Action */}
                    <div className="border-t border-gray-50 pt-4 mt-auto">
                      <div className="mb-4 flex items-baseline justify-between">
                        <div>
                          <span className="text-2xl font-black text-gray-900">₹{bundle.price}</span>
                          <span className="ml-2 text-sm text-gray-400 line-through">₹{bundle.totalMrp}</span>
                        </div>
                        <span className="text-xs font-bold text-green-600">Save ₹{bundle.savings}</span>
                      </div>
                      
                      {(() => {
                        const bundleCount = getBundleCartCount(bundle);
                        if (!bundle.isAvailable) {
                          return (
                            <button
                              disabled
                              className="w-full rounded-xl py-3 text-center text-sm font-bold text-white bg-gray-300 cursor-not-allowed"
                            >
                              Out of Stock
                            </button>
                          );
                        }
                        if (bundleCount > 0) {
                          return (
                            <div className="flex items-center overflow-hidden rounded-xl border-2 border-gray-900 bg-white">
                              <button
                                onClick={() => handleBundleDecrement(bundle)}
                                className="flex-1 py-3 text-lg font-bold text-gray-900 transition-colors hover:bg-gray-100 active:scale-95"
                              >
                                −
                              </button>
                              <div className="border-x-2 border-gray-900 px-5 py-3 text-sm font-bold text-gray-900">
                                {bundleCount}
                              </div>
                              <button
                                onClick={async () => {
                                  if (!user) { setPendingWishlistAction(false); setShowAuthModal(true); return; }
                                  try {
                                    await api.post(`/bundles/${bundle.id}/add-to-cart`);
                                    await fetchCart();
                                  } catch (err: any) {
                                    toast.error(err.response?.data?.detail || 'Failed to add bundle to cart');
                                  }
                                }}
                                className="flex-1 py-3 text-lg font-bold text-gray-900 transition-colors hover:bg-gray-100 active:scale-95"
                              >
                                +
                              </button>
                            </div>
                          );
                        }
                        return (
                          <button
                            onClick={async () => {
                              if (!user) {
                                setPendingWishlistAction(false);
                                setShowAuthModal(true);
                                return;
                              }
                              try {
                                await api.post(`/bundles/${bundle.id}/add-to-cart`);
                                toast.success(`"${bundle.name}" added to cart!`);
                                await fetchCart();
                                openCart();
                              } catch (err: any) {
                                const msg = err.response?.data?.detail || 'Failed to add bundle to cart';
                                toast.error(msg);
                              }
                            }}
                            className="w-full rounded-xl py-3 text-center text-sm font-bold text-white transition-all shadow-sm bg-gray-900 hover:bg-gray-800 active:scale-95"
                          >
                            Add to Cart
                          </button>
                        );
                      })()}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => {
          setShowAuthModal(false);
          setPendingWishlistAction(false);
        }}
        redirectOnSuccess={false}
        onSuccess={async () => {
          if (pendingWishlistAction && product?.id) {
            try {
              await api.post('/wishlist', { productId: product.id, sessionId: getSessionId() });
              trackAddToWishlist({
                productId: product.id,
                productName: product.name,
                source: 'product_detail',
              });
              toast.success('Added to wishlist');
              // Will be auto-refetched by WishlistContext when user changes
            // eslint-disable-next-line unused-imports/no-unused-vars
            } catch (e) {
              toast.error('Failed to add to wishlist');
            }
          }
        }}
      />
    </>
  );
}
