'use client';

import { useState, useEffect } from 'react';
import { useProductsPerRow, getSectionDisplayConfig } from '@/hooks/useProductsPerRow';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import { toast } from 'react-toastify';
import api from '@/utils/api';
import ProductCatalog from '@/components/ProductCatalog';
import InfiniteCarousel from '@/components/InfiniteCarousel';
import ThemeSwitcher from '@/components/ThemeSwitcher';
import Header from '@/components/Header';
import HeroBanner from '@/components/HeroBanner';
import HeroCarousel from '@/components/HeroCarousel';
import StatsCounter from '@/components/StatsCounter';
import HoverProductCard from '@/components/HoverProductCard';
import { getImageUrl, getImageUrlWithFallback } from '@/utils/imageUrl';
import { useRecommendationSectionView } from '@/hooks/useRecommendationSectionView';
import { usePincode } from '@/context/PincodeContext';
import UnserviceableLocationBanner from '@/components/UnserviceableLocationBanner';
import { logger } from '@/utils/logger';

export interface WholesalerClientProps {
  initialCategories?: any[];
  initialCollections?: any[];
  initialBanners?: any[];
  initialBrands?: any[];
  initialStats?: any;
}

export default function WholesalerClient({
  initialCategories,
  initialCollections,
  initialBanners,
  initialBrands,
  initialStats,
}: WholesalerClientProps) {
  const { user, loading: authLoading, logout } = useAuth();
  const { isServiceable, pincode } = usePincode();
  // eslint-disable-next-line unused-imports/no-unused-vars
  const { theme } = useTheme();
  const router = useRouter();
  const searchParams = useSearchParams();
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [showHamburger, setShowHamburger] = useState(false);
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [showCategories, setShowCategories] = useState(false);
  // eslint-disable-next-line unused-imports/no-unused-vars
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);
  const [banners, setBanners] = useState<any[]>(initialBanners || []);
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [currentBannerIndex, setCurrentBannerIndex] = useState(0);
  const [categories, setCategories] = useState<any[]>(initialCategories || []);
  const [brands, setBrands] = useState<any[]>(initialBrands || []);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedCategoryTag, setSelectedCategoryTag] = useState<string | null>(null);
  const [recNewArrivals, setRecNewArrivals] = useState<any[]>([]);
  const [recCustomerFavourites, setRecCustomerFavourites] = useState<any[]>([]);
  const [recTrendingNow, setRecTrendingNow] = useState<any[]>([]);
  const [recExplore, setRecExplore] = useState<any[]>([]);
  const [recBusinessFavourites, setRecBusinessFavourites] = useState<any[]>([]);
  const [recCityName, setRecCityName] = useState<string>('');
  const [recSectionOrder, setRecSectionOrder] = useState<string[]>([
    'new_arrivals',
    'customer_favourites',
    'trending_now',
    'explore',
    'business_favourites',
  ]);

  const [searchTerm, setSearchTerm] = useState('');
  // eslint-disable-next-line unused-imports/no-unused-vars
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [categoryTags, setCategoryTags] = useState<any[]>([]);
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [loading, setLoading] = useState(false); // Start false initially
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});
  const productsPerRow = useProductsPerRow();
  const [googleRating, setGoogleRating] = useState(
    initialStats?.googleRating || { rating: 0, reviewCount: '' }
  );
  const [collections, setCollections] = useState<any[]>(initialCollections || []);
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);
  const [duesInfo, setDuesInfo] = useState<any>(null);
  const [showDuesModal, setShowDuesModal] = useState(false);
  const [selectedBillForSettle, setSelectedBillForSettle] = useState<any>(null);
  const [duesSettleAmount, setDuesSettleAmount] = useState('');
  const [duesSettleImage, setDuesSettleImage] = useState<string | null>(null);
  const [settlingDuesPayment, setSettlingDuesPayment] = useState(false);
  const [upiDetails, setUpiDetails] = useState<any>(null);
  const recNewArrivalsRef = useRecommendationSectionView('new_arrivals');
  const recCustomerFavouritesRef = useRecommendationSectionView('customer_favourites');
  const recTrendingNowRef = useRecommendationSectionView('trending_now');
  const recExploreRef = useRecommendationSectionView('explore');
  const recBusinessFavouritesRef = useRecommendationSectionView('business_favourites');

  useEffect(() => {
    if (authLoading) return;

    const userRole = user?.effectiveRole || user?.role;
    if (userRole !== 'wholesaler') {
      router.push('/');
      return;
    }
    fetchAllData();

    // Check URL params
    const categoryParam = searchParams.get('category');
    const categoryTagParam = searchParams.get('categoryTag');
    const searchTermParam = searchParams.get('searchTerm');
    const collectionParam = searchParams.get('collection');
    const brandParam = searchParams.get('brand');

    if (searchTermParam) {
      setSearchTerm(searchTermParam);
      setSelectedCategory('');
      setSelectedCategoryTag(null);
      setSelectedCollection(null);
    } else if (collectionParam) {
      setSelectedCollection(collectionParam);
      setSelectedCategory('');
      setSelectedCategoryTag(null);
      setSearchTerm('');
    } else if (brandParam) {
      setSearchTerm(brandParam);
      setSelectedCategory('');
      setSelectedCategoryTag(null);
      setSelectedCollection(null);
    } else if (categoryTagParam) {
      setSelectedCategoryTag(categoryTagParam);
      setSelectedCategory('');
    } else if (categoryParam) {
      setSelectedCategory(categoryParam);
      setSelectedCategoryTag(null);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, authLoading, router, searchParams]);

  useEffect(() => {
    if (banners.length > 1) {
      const interval = setInterval(() => {
        setCurrentBannerIndex((prev) => (prev + 1) % banners.length);
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [banners.length]);

  const fetchDues = async () => {
    try {
      const res = await api.get('/payments/dues');
      setDuesInfo(res.data);
    } catch (err) {
      logger.error('Failed to fetch dues info:', err);
    }
  };

  const fetchUPIDetails = async () => {
    try {
      const res = await api.get('/payments/upi-details');
      setUpiDetails(res.data);
    } catch (err) {
      logger.error('Failed to fetch UPI details:', err);
    }
  };

  const handleDuesFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => setDuesSettleImage(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const handleSettleDueBill = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedBillForSettle) return;
    const settleAmt = parseFloat(duesSettleAmount);
    if (isNaN(settleAmt) || settleAmt <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }
    if (!duesSettleImage) {
      toast.error('Please upload your UPI payment screenshot');
      return;
    }
    setSettlingDuesPayment(true);
    try {
      await api.post(`/orders/${selectedBillForSettle.orderId}/settle-credit`, {
        amount: settleAmt,
        paymentImage: duesSettleImage,
        upiPaymentScreenshot: duesSettleImage
      });
      toast.success('Dues payment submitted successfully! Awaiting admin verification.');
      setSelectedBillForSettle(null);
      setDuesSettleAmount('');
      setDuesSettleImage(null);
      fetchDues();
    } catch (err: any) {
      toast.error(err.response?.data?.message || err.response?.data?.detail || 'Failed to submit settlement');
    } finally {
      setSettlingDuesPayment(false);
    }
  };

  const fetchAllData = async () => {
    // Only fetch what isn't already hydrated
    if (!initialBanners || initialBanners.length === 0) fetchBanners();
    if (!initialCategories || initialCategories.length === 0) fetchCategories();
    if (!initialBrands || initialBrands.length === 0) fetchBrands();
    if (!initialCollections || initialCollections.length === 0) fetchCollections();
    fetchRecommendations(); // ALWAYS fetch since it uses personalized user context auth tokens
    fetchDues();
    fetchUPIDetails();
  };

  const fetchBanners = async () => {
    try {
      // Fetch banners for wholesaler page position AND homepage position
      const [wholesalerBanners, homepageBanners] = await Promise.all([
        api.get('/banners/public', { params: { position: 'wholesaler' } }),
        api.get('/banners/public', { params: { position: 'homepage' } }),
      ]);

      const allBanners = [...(wholesalerBanners.data || []), ...(homepageBanners.data || [])];
      const uniqueBanners = allBanners.filter(
        (banner, index, self) => index === self.findIndex((b) => b._id === banner._id)
      );

      const activeBanners = uniqueBanners.filter(
        (b: any) =>
          b.isActive &&
          b.isPublished !== false &&
          (b.targetAudience === 'all' || b.targetAudience === 'wholesaler')
      );
      setBanners(activeBanners);
    } catch (error) {
      logger.error('Failed to fetch banners', error);
    }
  };

  // eslint-disable-next-line unused-imports/no-unused-vars
  const fetchGoogleRating = async () => {
    try {
      const res = await api.get('/google-reviews/rating');
      if (res.data) setGoogleRating(res.data);
    } catch (e) {
      logger.error('Failed to fetch google rating', e);
    }
  };

  const fetchCollections = async () => {
    try {
      const response = await api.get('/collections/public', {
        params: { visiblePage: 'Home', pageType: 'Home' },
      });
      setCollections(response.data || []);
    } catch (error) {
      logger.error('Failed to fetch collections', error);
    }
  };

  const fetchCategories = async () => {
    try {
      try {
        const response = await api.get('/categories/public', { params: { forHomepage: true } });
        const categoryData = response.data || [];
        const activeCategories = categoryData
          .filter((cat: any) => cat.isActive !== false)
          .map((cat: any) => ({
            name: cat.name,
            images: cat.images && cat.images.length > 0 ? cat.images : [],
            description: cat.description || '',
          }));
        setCategories(activeCategories);
      } catch (categoryError) {
        logger.warn('Category API not available, falling back to products', categoryError);
        const response = await api.get('/products/public');
        const products = response.data.products || response.data || [];
        const uniqueCategoryNames: string[] = Array.from(
          new Set(products.map((p: any) => p.category).filter(Boolean))
        );
        setCategories(
          uniqueCategoryNames.map((name: string) => ({
            name,
            images: [] as string[],
            description: '',
          }))
        );
      }
    } catch (error) {
      logger.error('Failed to fetch categories', error);
      setCategories([]);
    }
  };

  const fetchRecommendations = async () => {
    if (!user) return;
    try {
      const response = await api.get('/recommendations');
      const data = response.data || {};
      const group = (arr: any[]) => groupProductsByNameAndType(arr || []);
      setRecNewArrivals(group(data.newArrivals || []));
      setRecCustomerFavourites(group(data.customerFavourites || []));
      setRecTrendingNow(group(data.trendingNow || []));
      setRecExplore(group(data.explore || []));
      setRecBusinessFavourites(group(data.businessFavourites || []));
      setRecCityName((data.cityName || '').trim());
      setRecSectionOrder(
        Array.isArray(data.sectionOrder)
          ? data.sectionOrder
          : [
              'new_arrivals',
              'customer_favourites',
              'trending_now',
              'explore',
              'business_favourites',
            ]
      );
    } catch (error) {
      logger.error('Failed to fetch recommendations', error);
    }
  };

  const fetchBrands = async () => {
    try {
      const response = await api.get('/brands/public');
      setBrands(Array.isArray(response.data) ? response.data : response.data?.brands || []);
    } catch (error) {
      logger.error('Error fetching brands:', error);
    }
  };

  // Group products by name and type
  // If products have same name and type but different values, group them together
  const groupProductsByNameAndType = (allProducts: any[]) => {
    const groupedMap = new Map<string, any>();

    allProducts.forEach((product: any) => {
      // Create a key from name and type (if type exists)
      const hasType = product.type && product.type.trim() !== '';
      const key = hasType
        ? `${product.name.toLowerCase()}_${product.type.toLowerCase()}`
        : product._id;

      if (!groupedMap.has(key)) {
        // First product with this name+type combination
        const groupedProduct = {
          ...product,
          _grouped: hasType, // Flag to indicate this is a grouped product
          _groupedVariants: hasType ? [product] : [], // Store all variants for this group
          displayImage:
            getImageUrl(product.images && product.images.length > 0 ? product.images[0] : null) ||
            undefined,
        };
        groupedMap.set(key, groupedProduct);
      } else {
        // Product with same name+type exists, add as variant if has type
        const existing = groupedMap.get(key)!;
        if (hasType && existing._grouped) {
          existing._groupedVariants.push(product);
          // Use the first product's images, but we'll update on product detail page
        }
      }
    });

    return Array.from(groupedMap.values());
  };

  const handleCategoryClick = (category: string) => {
    setSelectedCategory(category);
    setShowCategories(false);
    setShowHamburger(false);
    router.push(`/wholesaler?category=${encodeURIComponent(category)}`);
  };

  const handleProductClick = (product: any) => {
    if (product._groupedVariants && product._groupedVariants.length > 0) {
      router.push(`/wholesaler/product/${product._groupedVariants[0]._id}`);
    } else if (product._id) {
      router.push(`/wholesaler/product/${product._id}`);
    }
  };

  // eslint-disable-next-line unused-imports/no-unused-vars
  const handleLogout = () => {
    logout();
    router.push('/');
  };

  const handleToggleSection = (sectionKey: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [sectionKey]: !prev[sectionKey],
    }));
  };

  const showHomeSections =
    !selectedCategory && !selectedCategoryTag && !selectedCollection && !searchTerm;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="flex min-h-[400px] items-center justify-center">
          <div className="text-center">
            <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-gray-200 border-t-red-600"></div>
            <p className="text-gray-600">Loading products...</p>
          </div>
        </div>
      </div>
    );
  }

  const userRole = user?.effectiveRole || user?.role;
  if (authLoading || !user || userRole !== 'wholesaler') {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      {isServiceable === false ? (
        <main className="w-full px-4 py-12 md:px-8 xl:px-12">
          {duesInfo && duesInfo.currentOverdue > 0 && (
            <div
              className={`mb-8 p-6 rounded-2xl border transition-all duration-300 ${duesInfo.hasOverdueBills ? 'bg-red-50/95 border-red-200 shadow-[0_4px_20px_rgba(239,68,68,0.1)] text-red-900' : 'bg-blue-50/95 border-blue-200 shadow-[0_4px_20px_rgba(59,130,246,0.1)] text-blue-900'}`}
              style={{
                backdropFilter: 'blur(8px)',
                animation: 'slideDown 0.4s ease-out',
              }}
            >
              <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-xl ${duesInfo.hasOverdueBills ? 'bg-red-500 text-white animate-pulse' : 'bg-blue-500 text-white'}`}>
                    {duesInfo.hasOverdueBills ? (
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <circle cx="12" cy="12" r="10" />
                        <line x1="12" y1="8" x2="12" y2="12" />
                        <line x1="12" y1="16" x2="12.01" y2="16" />
                      </svg>
                    ) : (
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <circle cx="12" cy="12" r="10" />
                        <path d="M12 16v-4" />
                        <path d="M12 8h.01" />
                      </svg>
                    )}
                  </div>
                  <div>
                    <h3 className="font-bold text-lg">
                      Credit Statement Alert
                    </h3>
                    {duesInfo.hasOverdueBills ? (
                      <div className="text-sm mt-1 space-y-0.5">
                        <div>• <strong>Current overdue:</strong> ₹{duesInfo.currentOverdue.toLocaleString('en-IN')}</div>
                        <div>• <strong>Minimum overdue (date has crossed):</strong> ₹{duesInfo.minimumOverdue.toLocaleString('en-IN')}</div>
                        <div className="font-semibold text-red-600 animate-pulse">• Pay the minimum amount to continue placing orders.</div>
                      </div>
                    ) : (
                      <div className="text-sm mt-1 space-y-0.5">
                        <div>• <strong>Current overdue:</strong> ₹{duesInfo.currentOverdue.toLocaleString('en-IN')}</div>
                        <div>• <strong>Minimum overdue (cutoff date is nearest):</strong> ₹{duesInfo.minimumOverdue.toLocaleString('en-IN')}</div>
                        <div>• <strong>Cutoff date:</strong> {new Date(duesInfo.nearestDueDate).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })} (before which minimum overdue has to be paid)</div>
                      </div>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => setShowDuesModal(true)}
                  className={`px-6 py-2.5 rounded-full font-bold text-sm tracking-wide text-white transition-all transform active:scale-95 whitespace-nowrap shadow-sm hover:shadow-md ${duesInfo.hasOverdueBills ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'}`}
                >
                  Clear Dues
                </button>
              </div>
            </div>
          )}
          <UnserviceableLocationBanner />
        </main>
      ) : (
        <>
          {showHomeSections && (
            <>
              <HeroCarousel banners={banners} />
              <StatsCounter productCount={initialStats?.productCount} brandCount={initialStats?.brandCount} />
            </>
          )}

          {/* Main Content */}
          <main className="w-full px-4 py-8 md:px-8 xl:px-12">
        {duesInfo && duesInfo.currentOverdue > 0 && (
          <div
            className={`mb-8 p-6 rounded-2xl border transition-all duration-300 ${duesInfo.hasOverdueBills ? 'bg-red-50/95 border-red-200 shadow-[0_4px_20px_rgba(239,68,68,0.1)] text-red-900' : 'bg-blue-50/95 border-blue-200 shadow-[0_4px_20px_rgba(59,130,246,0.1)] text-blue-900'}`}
            style={{
              backdropFilter: 'blur(8px)',
              animation: 'slideDown 0.4s ease-out',
            }}
          >
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-xl ${duesInfo.hasOverdueBills ? 'bg-red-500 text-white animate-pulse' : 'bg-blue-500 text-white'}`}>
                  {duesInfo.hasOverdueBills ? (
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <circle cx="12" cy="12" r="10" />
                      <line x1="12" y1="8" x2="12" y2="12" />
                      <line x1="12" y1="16" x2="12.01" y2="16" />
                    </svg>
                  ) : (
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <circle cx="12" cy="12" r="10" />
                      <path d="M12 16v-4" />
                      <path d="M12 8h.01" />
                    </svg>
                  )}
                </div>
                <div>
                  <h3 className="font-bold text-lg">
                    Credit Statement Alert
                  </h3>
                  {duesInfo.hasOverdueBills ? (
                    <div className="text-sm mt-1 space-y-0.5">
                      <div>• <strong>Current overdue:</strong> ₹{duesInfo.currentOverdue.toLocaleString('en-IN')}</div>
                      <div>• <strong>Minimum overdue (date has crossed):</strong> ₹{duesInfo.minimumOverdue.toLocaleString('en-IN')}</div>
                      <div className="font-semibold text-red-600 animate-pulse">• Pay the minimum amount to continue placing orders.</div>
                    </div>
                  ) : (
                    <div className="text-sm mt-1 space-y-0.5">
                      <div>• <strong>Current overdue:</strong> ₹{duesInfo.currentOverdue.toLocaleString('en-IN')}</div>
                      <div>• <strong>Minimum overdue (cutoff date is nearest):</strong> ₹{duesInfo.minimumOverdue.toLocaleString('en-IN')}</div>
                      <div>• <strong>Cutoff date:</strong> {new Date(duesInfo.nearestDueDate).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })} (before which minimum overdue has to be paid)</div>
                    </div>
                  )}
                </div>
              </div>
              <button
                onClick={() => setShowDuesModal(true)}
                className={`px-6 py-2.5 rounded-full font-bold text-sm tracking-wide text-white transition-all transform active:scale-95 whitespace-nowrap shadow-sm hover:shadow-md ${duesInfo.hasOverdueBills ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'}`}
              >
                Clear Dues
              </button>
            </div>
          </div>
        )}
        {/* Recommendation sections — new_arrivals always first ("Just Landed"), then bandit-ordered rest */}
        {showHomeSections &&
          (() => {
            const order = recSectionOrder.length
              ? recSectionOrder
              : [
                  'new_arrivals',
                  'customer_favourites',
                  'trending_now',
                  'explore',
                  'business_favourites',
                ];
            const allSections: {
              key: string;
              title: string;
              subtitle: string;
              tag: string;
              items: any[];
              ref: React.RefObject<HTMLDivElement>;
              slot: string;
              color: string;
            }[] = [];
            if (!getSectionDisplayConfig(recNewArrivals.length, productsPerRow).hide)
              allSections.push({
                key: 'new_arrivals',
                title: 'New Arrivals',
                subtitle: 'Check out the latest products added to our wholesaler catalog.',
                tag: 'JUST LANDED',
                items: recNewArrivals,
                ref: recNewArrivalsRef,
                slot: 'new_arrivals',
                color: 'from-[#1a4d33] to-[#D4AF37]',
              });
            if (!getSectionDisplayConfig(recCustomerFavourites.length, productsPerRow).hide)
              allSections.push({
                key: 'customer_favourites',
                title: recCityName ? `Customer Favourites (Popular in ${recCityName})` : 'Customer Favourites',
                subtitle: recCityName
                  ? `Top retail picks delivered to ${recCityName}.`
                  : 'Retail customers love these items for their high turnover.',
                tag: 'RETAIL PICK',
                items: recCustomerFavourites,
                ref: recCustomerFavouritesRef,
                slot: 'customer_favourites',
                color: 'from-emerald-800 to-teal-600',
              });
            if (!getSectionDisplayConfig(recTrendingNow.length, productsPerRow).hide)
              allSections.push({
                key: 'trending_now',
                title: 'Trending Now',
                subtitle: "What's hot in the market right now.",
                tag: 'ON FIRE',
                items: recTrendingNow,
                ref: recTrendingNowRef,
                slot: 'trending_now',
                color: 'from-orange-600 to-red-600',
              });
            if (!getSectionDisplayConfig(recExplore.length, productsPerRow).hide)
              allSections.push({
                key: 'explore',
                title: 'Explore More',
                subtitle: 'Handpicked products from emerging brands.',
                tag: 'DISCOVER',
                items: recExplore,
                ref: recExploreRef,
                slot: 'explore',
                color: 'from-purple-800 to-fuchsia-600',
              });
            if (!getSectionDisplayConfig(recBusinessFavourites.length, productsPerRow).hide)
              allSections.push({
                key: 'business_favourites',
                title: recCityName ? `Business Favourites (Popular in ${recCityName})` : 'Business Favourites',
                subtitle: recCityName
                  ? `High-volume items ordered by businesses in ${recCityName}.`
                  : 'High-margin items recommended for your business.',
                tag: 'PRO CHOICE',
                items: recBusinessFavourites,
                ref: recBusinessFavouritesRef,
                slot: 'business_favourites',
                color: 'from-[#1a4d33] to-[#D4AF37]',
              });

            // new_arrivals always first, rest follow bandit order
            const newArrSec = allSections.find((s) => s.key === 'new_arrivals');
            const banditOrder = order.filter((s) => s !== 'new_arrivals');
            const rest = banditOrder
              .map((s) => allSections.find((sec) => sec.key === s))
              .filter(Boolean) as typeof allSections;
            const ordered = [...(newArrSec ? [newArrSec] : []), ...rest];
            return ordered.map((sec) => (
              <section key={sec.key} ref={sec.ref} className="mb-20">
                <div className="mb-10 flex flex-col items-start justify-between gap-4 md:flex-row md:items-end">
                  <div className="relative">
                    <span
                      className={`mb-2 block text-xs font-semibold uppercase tracking-[0.2em] ${sec.key === 'new_arrivals' ? 'text-[#D4AF37]' : 'text-gray-500'}`}
                    >
                      {sec.tag}
                    </span>
                    <h2 className="text-3xl font-bold tracking-tight text-gray-900 md:text-4xl">
                      {sec.title}
                    </h2>
                    <p className="mt-2 max-w-md text-sm text-gray-500">{sec.subtitle}</p>
                    <div
                      className={`absolute -left-4 bottom-0 top-0 w-1 bg-gradient-to-b ${sec.color} hidden rounded-full md:block`}
                    />
                  </div>
                  {(sec.key === 'customer_favourites' || sec.key === 'business_favourites') && (
                    <button
                      onClick={() =>
                        router.push(
                          sec.key === 'customer_favourites'
                            ? '/wholesaler/customer-favourites'
                            : '/wholesaler/business-favourites'
                        )
                      }
                      className="group inline-flex items-center gap-2 text-sm font-semibold text-gray-900 transition-colors hover:text-emerald-700"
                    >
                      View All
                      <svg
                        className="h-4 w-4 transition-transform group-hover:translate-x-1"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
                      </svg>
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 md:gap-6 lg:grid-cols-5 xl:grid-cols-6">
                  {(() => {
                    const cfg = getSectionDisplayConfig(sec.items.length, productsPerRow);
                    const isExpanded = expandedSections[sec.key];
                    return (
                      <>
                        {sec.items.slice(0, isExpanded ? cfg.expanded : cfg.visible).map((p, index) => (
                          <div
                            key={p._id}
                            className="animate-fade-in-up opacity-0"
                            style={{ animationDelay: `${index * 50}ms`, animationFillMode: 'forwards' }}
                          >
                            <HoverProductCard
                              product={{ ...p, isNew: false, bestSeller: false }}
                              onClick={() => handleProductClick(p)}
                            />
                          </div>
                        ))}

                        {cfg.showButton && (
                          <div className="col-span-full">
                            <div className="relative mt-12 flex justify-center border-t border-gray-100 pt-8">
                              <button
                                onClick={() => handleToggleSection(sec.key)}
                                className="absolute -top-6 flex items-center gap-2 rounded-full border border-gray-200 bg-white px-8 py-3 font-semibold text-gray-900 shadow-sm transition-all hover:shadow-md"
                              >
                                {isExpanded ? (
                                  <>
                                    Show less
                                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                                    </svg>
                                  </>
                                ) : (
                                  <>
                                    Show more
                                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                    </svg>
                                  </>
                                )}
                              </button>
                            </div>
                          </div>
                        )}
                      </>
                    );
                  })()}
                </div>
              </section>
            ));
          })()}
        {/* Collections Section */}
        {collections.length > 0 && showHomeSections && (
          <section className="mb-20">
            <div className="mb-10 flex flex-col items-start justify-between gap-4 md:flex-row md:items-end">
              <div className="relative">
                <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.2em] text-amber-500">
                  Curated For You
                </span>
                <h2 className="text-3xl font-bold tracking-tight text-gray-900 md:text-4xl">
                  Featured Collections
                </h2>
                <p className="mt-2 max-w-md text-sm text-gray-500">
                  Thoughtfully curated sets designed to meet your every stationery need.
                </p>
                <div className="absolute -left-4 bottom-0 top-0 hidden w-1 rounded-full bg-gradient-to-b from-amber-400 to-amber-200 md:block" />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              {collections.map((col: any, index: number) => (
                <div
                  key={col._id}
                  className="animate-fade-in-up group relative aspect-[4/3] cursor-pointer overflow-hidden rounded-2xl opacity-0 shadow-lg"
                  style={{ animationDelay: `${index * 100}ms`, animationFillMode: 'forwards' }}
                  onClick={() =>
                    router.push(`/wholesaler?collection=${encodeURIComponent(col._id)}`)
                  }
                >
                  <img
                    src={getImageUrlWithFallback(
                      col.imageUrl,
                      "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='600' height='450' viewBox='0 0 600 450'%3E%3Crect width='600' height='450' fill='%23f3f4f6'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='18' fill='%239ca3af'%3ENo Image%3C/text%3E%3C/svg%3E"
                    )}
                    alt={col.name}
                    className="absolute inset-0 h-full w-full object-cover transition-transform duration-[8000ms] ease-out group-hover:scale-110"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent opacity-80 transition-opacity duration-500 group-hover:opacity-90" />
                  <div className="absolute inset-0 flex flex-col justify-end p-6 md:p-8">
                    <div className="transform transition-transform duration-500 group-hover:translate-y-[-8px]">
                      <h3 className="mb-2 text-xl font-bold leading-tight text-white md:text-2xl">
                        {col.name}
                      </h3>
                      <p className="mb-4 line-clamp-2 max-w-[90%] text-sm text-white/70">
                        {col.description}
                      </p>
                      <div className="flex translate-y-2 transform items-center gap-2 text-xs font-semibold uppercase tracking-wider text-white opacity-0 transition-all duration-300 group-hover:translate-y-0 group-hover:opacity-100">
                        <span>Explore Collection</span>
                        <svg
                          className="h-4 w-4 transform transition-transform group-hover:translate-x-1"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M17 8l4 4m0 0l-4 4m4-4H3"
                          />
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {categories.length > 0 && showHomeSections && (
          <section className="mb-20">
            <div className="mb-10 flex flex-col items-start justify-between gap-4 md:flex-row md:items-end">
              <div className="relative">
                <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.2em] text-emerald-500">
                  Browse Our Range
                </span>
                <h2 className="text-3xl font-bold tracking-tight text-gray-900 md:text-4xl">
                  Shop by Category
                </h2>
                <p className="mt-2 max-w-md text-sm text-gray-500">
                  Discover premium stationery organized for easy bulk browsing.
                </p>
                <div className="absolute -left-4 bottom-0 top-0 hidden w-1 rounded-full bg-gradient-to-b from-emerald-800 to-emerald-600 md:block" />
              </div>
              <button
                onClick={() => router.push('/categories')}
                className="group inline-flex items-center gap-2 text-sm font-semibold text-gray-900 transition-colors hover:text-emerald-700"
              >
                View All Categories
                <svg
                  className="h-4 w-4 transition-transform group-hover:translate-x-1"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
              </button>
            </div>

            <div className="grid grid-cols-3 gap-4 sm:grid-cols-4 md:grid-cols-6 md:gap-5 lg:grid-cols-8">
              {categories.slice(0, 24).map((cat, index) => (
                <button
                  type="button"
                  key={cat.name}
                  onClick={() => handleCategoryClick(cat.name)}
                  className="animate-fade-in-up group flex flex-col items-center opacity-0 transition-all duration-300"
                  style={{ animationDelay: `${index * 30}ms`, animationFillMode: 'forwards' }}
                >
                  <div className="relative mb-3 h-16 w-16 transform overflow-hidden rounded-full shadow-md ring-2 ring-transparent transition-all duration-300 group-hover:scale-105 group-hover:shadow-xl group-hover:ring-emerald-200 sm:h-20 sm:w-20 md:h-24 md:w-24">
                    {cat.images && cat.images.length > 0 ? (
                      <img
                        src={getImageUrlWithFallback(cat.images[0])}
                        alt={cat.name}
                        className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200">
                        <svg
                          className="h-8 w-8 text-gray-400"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="1.5"
                            d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
                          />
                        </svg>
                      </div>
                    )}
                  </div>
                  <div className="w-full text-center">
                    <h3 className="line-clamp-2 px-1 text-xs font-semibold leading-tight text-gray-800 transition-colors group-hover:text-[#1a4d33] sm:text-sm">
                      {cat.name}
                    </h3>
                  </div>
                </button>
              ))}
            </div>
          </section>
        )}

        {/* Brands Section */}
        {brands.length > 0 && showHomeSections && (
          <section className="mb-20">
            <div className="mb-10 flex flex-col items-start justify-between gap-4 md:flex-row md:items-end">
              <div className="relative">
                <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.2em] text-indigo-500">
                  Trusted Partners
                </span>
                <h2 className="text-3xl font-bold tracking-tight text-gray-900 md:text-4xl">
                  Brand Partners
                </h2>
                <p className="mt-2 max-w-md text-sm text-gray-500">
                  Direct from the best manufacturers in the industry.
                </p>
                <div className="absolute -left-4 bottom-0 top-0 hidden w-1 rounded-full bg-gradient-to-b from-indigo-800 to-indigo-600 md:block" />
              </div>
              <button
                onClick={() => router.push('/brands')}
                className="group inline-flex items-center gap-2 text-sm font-semibold text-gray-900 transition-colors hover:text-indigo-700"
              >
                View All Brands
                <svg
                  className="h-4 w-4 transition-transform group-hover:translate-x-1"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
              </button>
            </div>

            <InfiniteCarousel
              items={brands.map((b) => ({
                id: b._id || b.name,
                title: b.name,
                image: (b.logoUrl ? getImageUrl(b.logoUrl) : undefined) || undefined,
                link: `/wholesaler?brand=${encodeURIComponent(b.name)}`,
                type: 'brand',
              }))}
              speed={60}
            />
          </section>
        )}

        {/* Product Catalog when filtering */}
        {(selectedCategory || selectedCategoryTag || selectedCollection || searchTerm) && (
          <>
            {/* Search Hero Banner - text only, no thumbnail */}
            {searchTerm && (
              <HeroBanner
                title={`"${searchTerm}"`}
                subtitle={`Showing results for your search`}
                breadcrumbs={[{ label: 'Home', href: '/wholesaler' }, { label: 'Search Results' }]}
                hideThumbnail={true}
              />
            )}
            <div className={`w-full ${searchTerm ? 'mt-4' : ''}`}>
              <ProductCatalog
                category={selectedCategory}
                categoryTag={selectedCategoryTag}
                collection={selectedCollection}
                searchTerm={searchTerm}
                showFilters={true}
                hideHeader={!!searchTerm}
              />
            </div>
          </>
        )}

        {googleRating.rating > 0 && showHomeSections && (
          <div className="mb-8 mt-12 w-full px-4 py-4 md:px-12 xl:px-20">
            <div className="flex flex-col items-center justify-between gap-6 rounded-2xl border border-gray-100 bg-white p-6 shadow-sm md:flex-row md:p-8">
              <div className="flex items-center gap-6">
                <div className="rounded-full bg-blue-600 p-3 shadow-md">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="white">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-1 .67-2.26 1.07-3.71 1.07-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                    <path d="M5.84 14.11c-.22-.67-.35-1.39-.35-2.11s.13-1.44.35-2.11V7.05H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.95l3.66-2.84z" />
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.66l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.05l3.66 2.84c.87-2.6 3.3-4.51 6.16-4.51z" />
                  </svg>
                </div>
                <div>
                  <div className="mb-1 flex items-center gap-1.5">
                    {[...Array(5)].map((_, i) => (
                      <svg
                        key={i}
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill={i < Math.floor(googleRating.rating) ? '#fbbf24' : '#e5e7eb'}
                      >
                        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                      </svg>
                    ))}
                    <span className="ml-2 text-xl font-black text-gray-800">
                      {googleRating.rating} / 5
                    </span>
                  </div>
                  <p className="text-sm font-bold uppercase leading-none tracking-widest text-gray-500">
                    Verified by {googleRating.reviewCount} Happy Customers on Google
                  </p>
                </div>
              </div>
              <a
                href="https://share.google/6nwo4Mqy2qMRtztbF"
                target="_blank"
                rel="noopener noreferrer"
                className="whitespace-nowrap rounded-full bg-gray-900 px-8 py-3 text-xs font-black uppercase tracking-widest text-white shadow-md transition-all hover:bg-gray-800 active:scale-95"
              >
                WRITE A REVIEW
              </a>
            </div>
          </div>
        )}
      </main>
        </>
      )}

      {/* Dues Modal */}
      {showDuesModal && duesInfo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={() => setShowDuesModal(false)}>
          <div className="w-full max-w-2xl bg-white rounded-2xl shadow-xl overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <span className="text-lg font-bold text-red-600 flex items-center gap-2">
                ⚠️ Outstanding Credit Dues
              </span>
              <button className="text-gray-400 hover:text-gray-600 text-xl font-bold" onClick={() => setShowDuesModal(false)}>
                ✕
              </button>
            </div>
            <div className="p-6">
              <div className="mb-6 p-4 rounded-xl bg-gray-50 border border-gray-200">
                {duesInfo.hasOverdueBills ? (
                  <div className="text-sm space-y-1 text-gray-700">
                    <div>• <strong>Current overdue:</strong> ₹{duesInfo.currentOverdue.toLocaleString('en-IN')}</div>
                    <div>• <strong>Minimum overdue (date has crossed):</strong> ₹{duesInfo.minimumOverdue.toLocaleString('en-IN')}</div>
                    <div className="font-semibold text-red-600">• Pay the minimum amount to continue placing orders.</div>
                  </div>
                ) : (
                  <div className="text-sm space-y-1 text-gray-700">
                    <div>• <strong>Current overdue:</strong> ₹{duesInfo.currentOverdue.toLocaleString('en-IN')}</div>
                    <div>• <strong>Minimum overdue (cutoff date is nearest):</strong> ₹{duesInfo.minimumOverdue.toLocaleString('en-IN')}</div>
                    <div>• <strong>Cutoff date:</strong> {new Date(duesInfo.nearestDueDate).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })} (before which minimum overdue has to be paid)</div>
                  </div>
                )}
              </div>

              {/* Bill List */}
              <div className="flex flex-col gap-3 max-h-60 overflow-y-auto mb-6">
                {duesInfo.bills && duesInfo.bills.length > 0 ? (
                  duesInfo.bills.map((bill: any) => (
                    <div
                      key={bill.paymentId}
                      className={`flex items-center justify-between p-4 border rounded-xl hover:bg-gray-50/50 transition-colors ${bill.overdue ? 'bg-red-50 border-red-200' : 'bg-gray-50 border-gray-200'}`}
                    >
                      <div>
                        <div className="font-bold text-gray-800 text-sm">
                          Order: #{bill.orderNumber}
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                          Ordered: {new Date(bill.orderDate).toLocaleDateString('en-IN')}
                        </div>
                        <div
                          className={`inline-block text-xs font-semibold px-2.5 py-0.5 rounded-full mt-2 ${bill.overdue ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'}`}
                        >
                          {bill.timeRemaining}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-black text-gray-800">
                          ₹{bill.amountRemaining.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </div>
                        <button
                          onClick={() => {
                            setSelectedBillForSettle(bill);
                            setDuesSettleAmount(bill.amountRemaining.toString());
                            setDuesSettleImage(null);
                          }}
                          className="mt-2.5 px-4 py-1.5 bg-gray-900 text-white rounded-lg font-bold text-xs hover:bg-gray-800 transition-all active:scale-95"
                        >
                          Settle
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    No due bills found!
                  </div>
                )}
              </div>

              {/* Settle Form */}
              {selectedBillForSettle && (
                <div className="border-t border-dashed border-gray-200 pt-6 mt-6">
                  <h4 className="font-bold text-sm text-gray-800 mb-4">
                    Submit Settlement for Order #{selectedBillForSettle.orderNumber}
                  </h4>
                  
                  {/* Bank / UPI info */}
                  {upiDetails && (
                    <div className="bg-emerald-50/50 p-4 rounded-xl border border-emerald-100 mb-6 text-sm text-emerald-800">
                      <div className="font-bold">UPI Account Details:</div>
                      <div className="mt-1">
                        ID: <strong>{upiDetails.upiId}</strong> <br />
                        Name: <strong>{upiDetails.name}</strong>
                      </div>
                    </div>
                  )}

                  <form onSubmit={handleSettleDueBill}>
                    <div className="mb-4">
                      <label className="block text-xs font-bold text-gray-500 uppercase tracking-wide mb-1.5">Amount to Settle (₹) *</label>
                      <input
                        type="number"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition-all"
                        value={duesSettleAmount}
                        onChange={(e) => setDuesSettleAmount(e.target.value)}
                        max={selectedBillForSettle.amountRemaining}
                        required
                      />
                    </div>
                    <div className="mb-4">
                      <label className="block text-xs font-bold text-gray-500 uppercase tracking-wide mb-1.5">Upload Payment Screenshot *</label>
                      <input
                        type="file"
                        accept="image/*"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition-all"
                        onChange={handleDuesFileUpload}
                        required
                      />
                    </div>

                    {duesSettleImage && (
                      <div className="mb-6">
                        <img
                          src={duesSettleImage}
                          alt="Screenshot Preview"
                          className="max-h-36 rounded-lg border border-gray-200"
                        />
                      </div>
                    )}

                    <div className="flex gap-3 justify-end">
                      <button
                        type="button"
                        className="px-5 py-2 border border-gray-200 text-gray-700 rounded-full font-bold text-xs hover:bg-gray-50 transition-all active:scale-95"
                        onClick={() => setSelectedBillForSettle(null)}
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="px-5 py-2 bg-emerald-800 text-white rounded-full font-bold text-xs hover:bg-emerald-900 transition-all active:scale-95"
                        disabled={settlingDuesPayment}
                      >
                        {settlingDuesPayment ? 'Submitting...' : 'Submit Settlement'}
                      </button>
                    </div>
                  </form>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Theme Switcher */}
      <ThemeSwitcher />
    </div>
  );
}

// Export removed
