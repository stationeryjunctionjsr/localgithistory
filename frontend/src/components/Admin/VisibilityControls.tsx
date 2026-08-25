'use client';

import { useState, useEffect } from 'react';
import api from '@/utils/api';
import SearchableDropdown from './SearchableDropdown';
import { logger } from '@/utils/logger';

interface VisibilityRule {
  pageType: string;
  pageIds: string[];
}

interface VisibilityControlsProps {
  userSegments: string[];
  visibilityRules: VisibilityRule[];
  linkUrl?: string;
  onLinkChange?: (url: string) => void;
  onChange: (data: { userSegments: string[]; visibilityRules: VisibilityRule[] }) => void;
}

const PAGE_TYPES = [
  { value: 'homepage_web', label: 'Home Page (Web)' },
  { value: 'homepage_mobile', label: 'Home Page (Mobile)' },
  { value: 'all_categories', label: 'All Categories Page' },
  { value: 'category', label: 'Specific Category Page' },
  { value: 'all_brands', label: 'All Brands Page' },
  { value: 'brand', label: 'Specific Brand Page' },
  { value: 'collection', label: 'Collection Page' },
  { value: 'launch_modal', label: 'Launch Modal (Popup)' },
];

const getIdealSize = (pos: string) => {
  switch (pos) {
    case 'homepage_web':
      return '1920 x 600 px (Web)';
    case 'homepage_mobile':
      return '800 x 1200 px (Mobile App)';
    case 'category':
      return '1600 x 400 px';
    case 'search':
      return '1200 x 300 px';
    case 'launch_modal':
      return '600 x 800 px (Mobile Bottom Sheet)';
    case 'new_arrivals':
    case 'trending':
    case 'customer_favourites':
    case 'business_favourites':
      return '1200 x 400 px';
    default:
      return 'No recommendation';
  }
};

const ROLES = [
  { value: 'all', label: 'All Users' },
  { value: 'guest', label: 'Guest Users' },
  { value: 'customer', label: 'Retail Customers' },
  { value: 'wholesaler', label: 'Business Customers' },
];

export default function VisibilityControls({
  userSegments,
  visibilityRules,
  linkUrl,
  onLinkChange,
  onChange,
}: VisibilityControlsProps) {
  const [categories, setCategories] = useState<any[]>([]);
  const [brands, setBrands] = useState<any[]>([]);
  const [collections, setCollections] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);

  useEffect(() => {
    const fetchContextData = async () => {
      try {
        const [catRes, brandRes, collRes, prodRes] = await Promise.all([
          api.get('/categories/public'),
          api.get('/brands/public'),
          api.get('/collections/public'),
          api.get('/products'),
        ]);
        setCategories(catRes.data || []);
        setBrands(brandRes.data || []);
        setCollections(collRes.data || []);
        setProducts(prodRes.data?.products || prodRes.data || []);
      } catch (error) {
        logger.error('Failed to fetch visibility context data', error);
      }
    };
    fetchContextData();
  }, []);

  const getLinkInfo = (url: string) => {
    if (!url) return { type: 'custom', value: '' };
    if (url === '/categories') return { type: 'all_categories', value: '' };
    if (url === '/brands') return { type: 'all_brands', value: '' };
    if (url.startsWith('/categories/'))
      return { type: 'category', value: decodeURIComponent(url.replace('/categories/', '')) };
    if (url.startsWith('/brands/'))
      return { type: 'brand', value: decodeURIComponent(url.replace('/brands/', '')) };
    if (url.startsWith('/collections/'))
      return { type: 'collection', value: decodeURIComponent(url.replace('/collections/', '')) };
    if (url.startsWith('/customer/product/'))
      return { type: 'product', value: decodeURIComponent(url.replace('/customer/product/', '')) };
    return { type: 'custom', value: url };
  };

  const handleSegmentToggle = (role: string) => {
    let newSegments = [...userSegments];
    if (role === 'all') {
      newSegments = ['all'];
    } else {
      newSegments = newSegments.filter((s) => s !== 'all');
      if (newSegments.includes(role)) {
        newSegments = newSegments.filter((s) => s !== role);
        if (newSegments.length === 0) newSegments = ['all'];
      } else {
        newSegments.push(role);
      }
    }
    onChange({ userSegments: newSegments, visibilityRules });
  };

  const addRule = () => {
    const newRules = [...visibilityRules, { pageType: 'homepage_web', pageIds: [] }];
    onChange({ userSegments, visibilityRules: newRules });
  };

  const removeRule = (index: number) => {
    const newRules = visibilityRules.filter((_, i) => i !== index);
    onChange({ userSegments, visibilityRules: newRules });
  };

  const updateRule = (index: number, updates: Partial<VisibilityRule>) => {
    const newRules = visibilityRules.map((rule, i) =>
      i === index ? { ...rule, ...updates } : rule
    );
    onChange({ userSegments, visibilityRules: newRules });
  };

  const getOptionsForType = (type: string) => {
    const t = type.toLowerCase();
    switch (t) {
      case 'category':
        return categories;
      case 'brand':
        return brands;
      case 'collection':
        return collections.map((c) => ({ _id: c._id, name: c.name }));
      case 'product':
        return products.map((p) => ({ _id: p._id, name: p.name }));
      default:
        return [];
    }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <label className="mb-2 block text-sm font-semibold text-slate-700">User Segments</label>
        <div className="flex flex-wrap gap-3">
          {ROLES.map((role) => (
            <label
              key={role.value}
              className="flex cursor-pointer items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 transition-colors hover:border-indigo-300"
            >
              <input
                type="checkbox"
                checked={userSegments.includes(role.value)}
                onChange={() => handleSegmentToggle(role.value)}
                className="h-4 w-4 rounded text-indigo-600 focus:ring-indigo-500"
              />
              <span className="text-sm text-slate-600">{role.label}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <label className="block text-sm font-semibold text-slate-700">Visibility Rules</label>
          <button
            type="button"
            onClick={addRule}
            className="flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800"
          >
            + Add Rule
          </button>
        </div>

        {visibilityRules.length === 0 && (
          <p className="text-xs italic text-slate-400">
            No specific rules defined. Uses legacy visibility settings.
          </p>
        )}

        <div className="space-y-4">
          {visibilityRules.map((rule, index) => (
            <div
              key={index}
              className="group relative flex flex-col gap-3 rounded-lg border border-slate-200 bg-slate-50 p-3"
            >
              <button
                type="button"
                onClick={() => removeRule(index)}
                className="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full border border-rose-200 bg-rose-100 text-sm text-rose-600 opacity-0 transition-opacity group-hover:opacity-100"
              >
                ×
              </button>

              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <select
                  value={rule.pageType}
                  onChange={(e) => updateRule(index, { pageType: e.target.value, pageIds: [] })}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm focus:ring-1 focus:ring-indigo-500"
                >
                  {PAGE_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>

                {['category', 'brand', 'collection'].includes(rule.pageType.toLowerCase()) && (
                  <div className="flex items-center text-xs text-slate-500">
                    Select specific {rule.pageType.toLowerCase()}s below
                  </div>
                )}
              </div>

              <div className="mt-1 rounded border border-blue-100 bg-blue-50 p-2 italic">
                <p className="text-[10px] text-blue-700">
                  ✨ <strong>Ideal Banner Size:</strong> {getIdealSize(rule.pageType)}
                </p>
              </div>

              {['category', 'brand', 'collection'].includes(rule.pageType.toLowerCase()) && (
                <div className="border-t border-slate-100 pt-2">
                  <SearchableDropdown
                    placeholder={`Search ${rule.pageType.toLowerCase()}...`}
                    options={getOptionsForType(rule.pageType)}
                    value={rule.pageIds[0] || ''}
                    onChange={(val) => {
                      updateRule(index, { pageIds: [val] });
                    }}
                    className="w-full"
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {onLinkChange && (
        <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <label className="block text-sm font-semibold text-slate-700">
            Redirection (OnClick Behavior)
          </label>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <select
              className="w-full rounded border bg-white px-3 py-2 text-sm"
              value={getLinkInfo(linkUrl || '').type}
              onChange={(e) => {
                const newType = e.target.value;
                const newUrl =
                  newType === 'custom'
                    ? ''
                    : newType === 'all_categories'
                      ? '/categories'
                      : newType === 'all_brands'
                        ? '/brands'
                        : newType === 'category'
                          ? '/categories/'
                          : newType === 'brand'
                            ? '/brands/'
                            : newType === 'collection'
                              ? '/collections/'
                              : '/customer/product/';
                onLinkChange(newUrl);
              }}
            >
              <option value="custom">Custom URL / None</option>
              <option value="all_categories">All Categories</option>
              <option value="category">Category</option>
              <option value="all_brands">All Brands</option>
              <option value="brand">Brand</option>
              <option value="collection">Collection</option>
              <option value="product">Product</option>
            </select>

            {['all_categories', 'all_brands'].includes(getLinkInfo(linkUrl || '').type) ? (
              <div className="flex items-center rounded border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-500">
                Links to{' '}
                {getLinkInfo(linkUrl || '').type === 'all_categories' ? '/categories' : '/brands'}
              </div>
            ) : getLinkInfo(linkUrl || '').type === 'custom' ? (
              <input
                type="text"
                value={getLinkInfo(linkUrl || '').value}
                onChange={(e) => onLinkChange(e.target.value)}
                placeholder="e.g. /my-path or http..."
                className="w-full rounded border px-3 py-2 text-sm"
              />
            ) : (
              <SearchableDropdown
                placeholder={`Search ${getLinkInfo(linkUrl || '').type}...`}
                options={getOptionsForType(getLinkInfo(linkUrl || '').type)}
                value={getLinkInfo(linkUrl || '').value}
                onChange={(val) => {
                  const type = getLinkInfo(linkUrl || '').type;
                  let newUrl = '';
                  if (!val) {
                    newUrl =
                      type === 'category'
                        ? '/categories/'
                        : type === 'brand'
                          ? '/brands/'
                          : type === 'collection'
                            ? '/collections/'
                            : '/customer/product/';
                  } else {
                    if (type === 'category') newUrl = `/categories/${encodeURIComponent(val)}`;
                    else if (type === 'brand') newUrl = `/brands/${encodeURIComponent(val)}`;
                    else if (type === 'collection')
                      newUrl = `/collections/${encodeURIComponent(val)}`;
                    else if (type === 'product')
                      newUrl = `/customer/product/${encodeURIComponent(val)}`;
                  }
                  onLinkChange(newUrl);
                }}
                className="w-full"
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
