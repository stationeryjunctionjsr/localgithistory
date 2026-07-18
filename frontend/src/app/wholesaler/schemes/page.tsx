'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import Header from '@/components/Header';

interface SchemeData {
  _id: string;
  code: string | null;
  method: string;
  discountType: string;
  discountValue: number;
  typeOfDiscount: string;
  appliesToType: string;
  appliesToValueIds: string[];
  validUntil: string;
  buyXGetYCustomerGetsQuantity?: number;
  buyXGetYCustomerGetsAppliesToType?: string;
  buyXGetYCustomerGetsAppliesToValueIds?: string[];
  buyXGetYCustomerGetsDiscountType?: string;
  buyXGetYCustomerGetsDiscountValue?: number;
  minRequirementType?: string;
  minQuantityOfEligibleItems?: number;
  minPurchaseAmount?: number;
  isActive: boolean;
  createdAt: string;
}

export default function SchemesPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [schemes, setSchemes] = useState<SchemeData[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [brands, setBrands] = useState<any[]>([]);
  const [collections, setCollections] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);

  useEffect(() => {
    if (authLoading) return;
    const userRole = user?.effectiveRole || user?.role;
    if (userRole !== 'wholesaler') {
      router.push('/');
      return;
    }
    fetchData();
  }, [user, authLoading, router]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setFetchError(false);
      const [schemesRes, catsRes, brandsRes, collectionsRes] = await Promise.all([
        api.get('/schemes'),
        api.get('/categories/public'),
        api.get('/brands/public'),
        api.get('/collections/public'),
      ]);

      setSchemes(schemesRes.data || []);
      setCategories(catsRes.data?.categories || catsRes.data || []);
      setBrands(brandsRes.data?.brands || brandsRes.data || []);
      setCollections(collectionsRes.data || []);
    } catch (err) {
      console.error('Error fetching schemes:', err);
      setFetchError(true);
    } finally {
      setLoading(false);
    }
  };

  const resolveNames = (type: string, ids: string[]) => {
    if (!ids || ids.length === 0) return [];
    if (type === 'categories') {
      return ids
        .map((id) => {
          const cat = categories.find((c: any) => c._id === id);
          return cat ? cat.name : null;
        })
        .filter(Boolean);
    }
    if (type === 'brands') {
      return ids
        .map((id) => {
          const brand = brands.find((b: any) => b._id === id);
          return brand ? brand.name : null;
        })
        .filter(Boolean);
    }
    if (type === 'collections') {
      return ids
        .map((id) => {
          const col = collections.find((c: any) => c._id === id);
          return col ? col.name : null;
        })
        .filter(Boolean);
    }
    return [];
  };

  const handleSchemeClick = (scheme: SchemeData) => {
    // Determine redirect based on appliesToType
    const type = scheme.appliesToType;
    const ids = scheme.appliesToValueIds || [];

    if (type === 'all') {
      router.push('/wholesaler');
    } else if (type === 'categories' && ids.length > 0) {
      const catNames = resolveNames('categories', ids);
      if (catNames.length > 0) {
        router.push(`/wholesaler?category=${encodeURIComponent(catNames[0])}`);
      }
    } else if (type === 'brands' && ids.length > 0) {
      const brandNames = resolveNames('brands', ids);
      if (brandNames.length > 0) {
        router.push(`/wholesaler?brand=${encodeURIComponent(brandNames[0])}`);
      }
    } else if (type === 'collections' && ids.length > 0) {
      router.push(`/wholesaler?collection=${encodeURIComponent(ids[0])}`);
    } else if (type === 'specific_products' && ids.length > 0) {
      router.push(`/wholesaler/product/${ids[0]}`);
    }
  };

  const formatOfferName = (scheme: SchemeData) => {
    if (scheme.typeOfDiscount === 'buy_x_get_y') {
      const getQty = scheme.buyXGetYCustomerGetsQuantity || 1;

      let getDesc = 'Free';
      if (scheme.buyXGetYCustomerGetsDiscountType === 'percentage') {
        getDesc = `${scheme.buyXGetYCustomerGetsDiscountValue}% off`;
      } else if (scheme.buyXGetYCustomerGetsDiscountType === 'amount_off') {
        getDesc = `₹${scheme.buyXGetYCustomerGetsDiscountValue} off`;
      }

      const buyPart =
        scheme.minRequirementType === 'min_quantity'
          ? `Buy ${scheme.minQuantityOfEligibleItems}`
          : 'Buy';

      return `${buyPart} Get ${getQty} ${getDesc}`;
    } else {
      // Amount off products
      if (scheme.discountType === 'percentage') {
        return `${scheme.discountValue}% off`;
      } else {
        return `₹${scheme.discountValue} off`;
      }
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-gray-200 border-t-[#1a4d33]"></div>
      </div>
    );
  }

  if (fetchError) {
    return (
      <div className="flex min-h-screen flex-col bg-gray-50">
        <Header />
        <div className="flex flex-1 flex-col items-center justify-center px-4 py-20 text-center">
          <p className="mb-4 text-gray-600">Could not load schemes. Please check your connection and try again.</p>
          <button
            onClick={fetchData}
            className="rounded-xl bg-[#1a4d33] px-6 py-2 font-semibold text-white hover:bg-[#15402a]"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      <Header />

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-10 md:px-8">
        <div className="mb-10">
          <h1 className="mb-2 text-3xl font-bold tracking-tight text-gray-900 md:text-4xl">
            Active Schemes
          </h1>
          <p className="text-sm text-gray-500 md:text-base">
            Discover all exclusive discounts and offers added for your business.
          </p>
        </div>

        {schemes.length === 0 ? (
          <div className="rounded-2xl border border-gray-100 bg-white p-12 text-center shadow-sm">
            <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-gray-100">
              <svg
                className="h-10 w-10 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                />
              </svg>
            </div>
            <h2 className="mb-2 text-xl font-bold text-gray-900">No Active Schemes</h2>
            <p className="text-gray-500">
              There are no discount schemes available at the moment. Please check back later.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {schemes.map((scheme) => {
              const offerName = formatOfferName(scheme);
              const expiryDate = new Date(scheme.validUntil).toLocaleDateString('en-IN', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
              });

              let applicableText = 'Applicable on all products';
              if (scheme.appliesToType !== 'all') {
                const names = resolveNames(scheme.appliesToType, scheme.appliesToValueIds);
                if (names.length > 0) {
                  const typeLabel =
                    scheme.appliesToType.charAt(0).toUpperCase() +
                    scheme.appliesToType.slice(1, -1);
                  applicableText = `Applicable on ${typeLabel}: ${names.join(', ')}`;
                }
              }

              return (
                <button
                  key={scheme._id}
                  onClick={() => handleSchemeClick(scheme)}
                  className="group flex h-full w-full transform cursor-pointer flex-col overflow-hidden rounded-2xl border border-gray-100 bg-white text-left shadow-sm transition-all hover:-translate-y-1 hover:shadow-lg"
                >
                  <div className="relative overflow-hidden bg-gradient-to-r from-[#1a4d33] to-[#2a7a52] p-6 text-white">
                    <div className="absolute -right-6 -top-6 h-32 w-32 rounded-full bg-white/10 blur-2xl"></div>
                    <div className="relative z-10 mb-2 flex items-start justify-between">
                      <h3 className="max-w-[70%] text-2xl font-black leading-tight">{offerName}</h3>
                      <div className="text-right">
                        <span className="mb-1 block text-[10px] font-bold uppercase tracking-widest opacity-80">
                          Expires
                        </span>
                        <span className="line-clamp-1 rounded bg-white/20 px-2 py-1 text-sm font-semibold">
                          {expiryDate}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-1 flex-col justify-between p-6">
                    <div>
                      <p className="mb-4 border-l-2 border-[#1a4d33] pl-3 text-sm font-medium leading-relaxed text-gray-700">
                        {applicableText}
                      </p>

                      {scheme.minRequirementType === 'min_amount' && (
                        <div className="mb-2 flex items-center gap-2 rounded bg-gray-50 p-2 text-xs text-gray-500">
                          <svg
                            className="h-4 w-4 text-emerald-600"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                          </svg>
                          Min. purchase: ₹{scheme.minPurchaseAmount}
                        </div>
                      )}

                      {scheme.method === 'discount_code' && scheme.code && (
                        <div className="relative mt-4 overflow-hidden rounded-lg border border-dashed border-gray-300 bg-gray-50 p-3 text-center">
                          <span className="mb-1 block cursor-default text-xs font-bold uppercase tracking-wider text-gray-400">
                            Use Code
                          </span>
                          <span className="font-mono text-lg font-bold tracking-widest text-gray-800">
                            {scheme.code}
                          </span>
                        </div>
                      )}
                      {scheme.method === 'automatic' && (
                        <div className="mt-4 flex items-center justify-center gap-2 rounded-lg border border-emerald-100 bg-emerald-50 p-3 text-center text-emerald-700">
                          <svg
                            className="h-4 w-4"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                          <span className="cursor-default text-sm font-bold uppercase">
                            Applied Automatically
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-gray-50 py-3 font-bold text-[#1a4d33] transition-colors group-hover:bg-[#1a4d33] group-hover:text-white">
                      Shop Now
                      <svg
                        className="h-4 w-4 transform transition-transform group-hover:translate-x-1"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M17 8l4 4m0 0l-4 4m4-4H3"
                        />
                      </svg>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
