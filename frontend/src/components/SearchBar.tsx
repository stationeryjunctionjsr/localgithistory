'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/utils/api';
import { recordEvent } from '@/utils/analytics';

interface SearchBarProps {
  onSearch?: (searchTerm: string) => void;
  onCategoryChange?: (filters: {
    brand: string;
    priceRange: { min: string; max: string };
    subCategory: string;
  }) => void;
  onSortChange?: (sort: string) => void;
}

export default function SearchBar({ onSearch, onCategoryChange, onSortChange }: SearchBarProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSort, setSelectedSort] = useState('newest');
  const [showFilterPanel, setShowFilterPanel] = useState(false);
  const [selectedBrand, setSelectedBrand] = useState('');
  const [priceRange, setPriceRange] = useState({ min: '', max: '' });
  const [brands, setBrands] = useState<string[]>([]);
  const [subCategories, setSubCategories] = useState<string[]>([]);
  const [subCategory, setSubCategory] = useState('');
  // eslint-disable-next-line unused-imports/no-unused-vars
  const router = useRouter();

  useEffect(() => {
    fetchBrandsAndSubCategories();
  }, []);

  // Debounced search - 300ms delay
  useEffect(() => {
    const timer = setTimeout(() => {
      if (onSearch) {
        onSearch(searchTerm);
      }
      if (searchTerm.trim()) {
        recordEvent({
          type: 'search',
          payload: {
            term: searchTerm,
            brand: selectedBrand,
            subCategory,
            priceRange,
            sort: selectedSort,
          },
        });
      }
    }, 300);
    return () => clearTimeout(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchTerm, onSearch]);

  useEffect(() => {
    if (onSortChange) {
      onSortChange(selectedSort);
    }
  }, [selectedSort, onSortChange]);

  const fetchBrandsAndSubCategories = async () => {
    try {
      const response = await api.get('/products/public');
      const products = response.data.products || response.data || [];
      const uniqueBrands = Array.from(
        new Set(products.map((p: any) => p.brand).filter(Boolean))
      ) as string[];
      const uniqueSubCategories = Array.from(
        new Set(products.map((p: any) => p.subCategory).filter(Boolean))
      ) as string[];
      setBrands(uniqueBrands);
      setSubCategories(uniqueSubCategories);
    } catch (error) {
      console.error('Failed to fetch brands and subcategories', error);
    }
  };

  const handleFilterApply = () => {
    if (onCategoryChange) {
      onCategoryChange({ brand: selectedBrand, priceRange, subCategory });
    }
    setShowFilterPanel(false);
  };

  const handleFilterReset = () => {
    setSelectedBrand('');
    setPriceRange({ min: '', max: '' });
    setSubCategory('');
    setSelectedSort('newest');
    if (onCategoryChange) {
      onCategoryChange({ brand: '', priceRange: { min: '', max: '' }, subCategory: '' });
    }
  };

  return (
    <div className="w-full border-b border-gray-200 bg-white">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-2.5 px-4 py-2">
        <input
          type="text"
          className="w-full max-w-md rounded border border-gray-300 px-4 py-3 text-sm md:max-w-sm md:text-base"
          placeholder="Search products..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <select
          value={selectedSort}
          onChange={(e) => setSelectedSort(e.target.value)}
          className="rounded border border-gray-300 bg-white px-2.5 py-2.5 text-sm text-black md:text-base"
        >
          <option value="newest">Newest First</option>
          <option value="popular">Popular</option>
          <option value="price_asc">Price: Low to High</option>
          <option value="price_desc">Price: High to Low</option>
          <option value="name_asc">Name: A to Z</option>
          <option value="name_desc">Name: Z to A</option>
        </select>
        <button
          onClick={() => setShowFilterPanel(!showFilterPanel)}
          className="cursor-pointer rounded border border-gray-300 bg-white px-4 py-2.5 text-sm text-black transition-all md:px-5 md:text-base"
          onMouseEnter={(e: any) => {
            e.target.style.background = 'linear-gradient(135deg, #c0392b 0%, #d63031 100%)';
            e.target.style.color = 'white';
          }}
          onMouseLeave={(e: any) => {
            e.target.style.background = 'white';
            e.target.style.color = 'black';
          }}
        >
          Filters
        </button>
      </div>

      {/* Filter Panel */}
      {showFilterPanel && (
        <div className="mx-auto max-w-7xl border-t border-gray-200 bg-gray-50 p-3">
          <h3 className="mb-2 mt-0 font-semibold">Filters</h3>
          <div className="mb-2 grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-4">
            <div className="flex flex-col">
              <label className="mb-1 font-semibold">Brand:</label>
              <select
                value={selectedBrand}
                onChange={(e) => setSelectedBrand(e.target.value)}
                className="mt-1 w-full rounded border border-gray-300 p-2"
              >
                <option value="">All Brands</option>
                {brands.map((brand) => (
                  <option key={brand} value={brand}>
                    {brand}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col">
              <label className="mb-1 font-semibold">Min Price:</label>
              <input
                type="number"
                value={priceRange.min}
                onChange={(e) => setPriceRange({ ...priceRange, min: e.target.value })}
                placeholder="Min"
                className="mt-1 w-full rounded border border-gray-300 p-2"
              />
            </div>
            <div className="flex flex-col">
              <label className="mb-1 font-semibold">Max Price:</label>
              <input
                type="number"
                value={priceRange.max}
                onChange={(e) => setPriceRange({ ...priceRange, max: e.target.value })}
                placeholder="Max"
                className="mt-1 w-full rounded border border-gray-300 p-2"
              />
            </div>
            {subCategories.length > 0 && (
              <div className="flex flex-col">
                <label className="mb-1 font-semibold">Sub-Category:</label>
                <select
                  value={subCategory}
                  onChange={(e) => setSubCategory(e.target.value)}
                  className="mt-1 w-full rounded border border-gray-300 p-2"
                >
                  <option value="">All Sub-Categories</option>
                  {subCategories.map((subCat) => (
                    <option key={subCat} value={subCat}>
                      {subCat}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
          <div className="flex gap-2.5">
            <button
              onClick={handleFilterApply}
              className="cursor-pointer rounded border-none bg-gradient-to-r from-red-600 to-red-500 px-5 py-2.5 text-white transition-all hover:from-red-700 hover:to-red-600"
            >
              Apply Filters
            </button>
            <button
              onClick={handleFilterReset}
              className="cursor-pointer rounded border border-gray-300 bg-white px-5 py-2.5 text-black hover:bg-gray-100"
            >
              Reset
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
