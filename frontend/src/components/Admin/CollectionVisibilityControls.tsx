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
  onChange: (data: { userSegments: string[]; visibilityRules: VisibilityRule[] }) => void;
}

const PAGE_TYPES = [
  { value: 'homepage', label: 'Home Page' },
  { value: 'all_categories', label: 'All Categories Page' },
  { value: 'category', label: 'Specific Category Page' },
  { value: 'all_brands', label: 'All Brands Page' },
  { value: 'brand', label: 'Specific Brand Page' },
  { value: 'cart', label: 'Cart Page' },
  { value: 'search', label: 'Search Page' },
];

const ROLES = [
  { value: 'all', label: 'All Users' },
  { value: 'guest', label: 'Guest Users' },
  { value: 'customer', label: 'Retail Customers' },
  { value: 'wholesaler', label: 'Business Customers' },
];

export default function CollectionVisibilityControls({
  userSegments,
  visibilityRules,
  onChange,
}: VisibilityControlsProps) {
  const [categories, setCategories] = useState<any[]>([]);
  const [brands, setBrands] = useState<any[]>([]);
  const [collections, setCollections] = useState<any[]>([]);

  useEffect(() => {
    const fetchContextData = async () => {
      try {
        const [catRes, brandRes, collRes] = await Promise.all([
          api.get('/categories/public'),
          api.get('/brands/public'),
          api.get('/collections/public'),
        ]);
        setCategories(catRes.data || []);
        setBrands(brandRes.data || []);
        setCollections(collRes.data || []);
      } catch (error) {
        logger.error('Failed to fetch visibility context data', error);
      }
    };
    fetchContextData();
  }, []);

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
    const newRules = [...visibilityRules, { pageType: 'homepage', pageIds: [] }];
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
        return collections;
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
              className="group relative flex flex-col gap-3 rounded-lg border border-slate-200 bg-slate-50 p-3 shadow-sm"
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

                {['category', 'brand'].includes(rule.pageType.toLowerCase()) && (
                  <div className="flex items-center text-xs text-slate-500">
                    Select specific {rule.pageType.toLowerCase()}s below
                  </div>
                )}
              </div>

              {['category', 'brand'].includes(rule.pageType.toLowerCase()) && (
                <div className="border-t border-slate-100 pt-2">
                  <SearchableDropdown
                    placeholder={`Search ${rule.pageType.toLowerCase()}...`}
                    options={getOptionsForType(rule.pageType)}
                    value=""
                    onChange={(val) => {
                      if (!rule.pageIds.includes(val)) {
                        updateRule(index, { pageIds: [...rule.pageIds, val] });
                      }
                    }}
                    className="w-full"
                  />
                  {rule.pageIds.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {rule.pageIds.map((id) => (
                        <span
                          key={id}
                          className="inline-flex items-center gap-1.5 rounded-full border border-indigo-200 bg-white px-2.5 py-1 text-[10px] font-bold text-indigo-700 shadow-sm"
                        >
                          {id}
                          <button
                            type="button"
                            onClick={() =>
                              updateRule(index, { pageIds: rule.pageIds.filter((i) => i !== id) })
                            }
                            className="-mr-1 flex h-3.5 w-3.5 items-center justify-center rounded-full border border-indigo-200 bg-white hover:text-rose-600"
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
