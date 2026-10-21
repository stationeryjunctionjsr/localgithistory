'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/utils/api';
import { recordEvent } from '@/utils/analytics';
import { logger } from '@/utils/logger';

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
  
  // Voice & Visual Search state
  const [isListening, setIsListening] = useState(false);
  const [isScanningImage, setIsScanningImage] = useState(false);
  const [scanMessage, setScanMessage] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

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
      logger.error('Failed to fetch brands and subcategories', error);
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

  // --------------------------------------------------------------------------
  // FREE Speech-to-Text: Browser Web Speech API
  // --------------------------------------------------------------------------
  const toggleVoiceSearch = () => {
    if (isListening) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsListening(false);
      return;
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert(
        'Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari, or use your keyboard voice dictation.'
      );
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = 'en-US';
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        if (transcript) {
          setSearchTerm(transcript);
          if (onSearch) {
            onSearch(transcript);
          }
        }
      };

      recognition.onerror = (event: any) => {
        logger.error('Voice search error:', event.error);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      logger.error('Failed to start speech recognition', err);
      setIsListening(false);
    }
  };

  // --------------------------------------------------------------------------
  // Image Scanning / Visual Search (OCR & AI Vision)
  // --------------------------------------------------------------------------
  const handleCameraClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleImageFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Reset input so re-uploading the same file triggers change
    e.target.value = '';

    setIsScanningImage(true);
    setScanMessage('Scanning image for product details...');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await api.post('/visual-search/scan', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const data = res.data;
      if (data?.searchQuery) {
        setSearchTerm(data.searchQuery);
        if (onSearch) {
          onSearch(data.searchQuery);
        }
        setScanMessage(`Found: "${data.searchQuery}"`);
      } else {
        setScanMessage('No text detected. Try another photo.');
      }
    } catch (error) {
      logger.error('Visual search failed', error);
      setScanMessage('Could not extract text from image. Try again.');
    } finally {
      setIsScanningImage(false);
      setTimeout(() => setScanMessage(null), 4000);
    }
  };

  return (
    <div className="w-full border-b border-gray-200 bg-white">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-2.5 px-4 py-2">
        {/* Search Input Container with Voice & Camera buttons */}
        <div className="relative w-full max-w-md md:max-w-sm">
          <input
            type="text"
            className={`w-full rounded border py-3 pl-4 pr-20 text-sm md:text-base focus:outline-none ${
              isListening ? 'border-red-500 bg-red-50/30' : 'border-gray-300 focus:border-red-500'
            }`}
            placeholder={
              isListening
                ? 'Listening... Speak now'
                : 'Search products by name, tag, or price...'
            }
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />

          <div className="absolute right-2.5 top-1/2 flex -translate-y-1/2 items-center gap-1.5">
            {/* Visual Search / Camera Button */}
            <button
              type="button"
              onClick={handleCameraClick}
              disabled={isScanningImage}
              title="Scan product image / OCR search"
              className="cursor-pointer rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-gray-800 transition-colors"
              aria-label="Scan image to search"
            >
              {isScanningImage ? (
                <svg className="h-5 w-5 animate-spin text-red-600" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3V4a10 10 0 100 20v-4l-3 3 3 3v-4a8 8 0 01-8-8z" />
                </svg>
              ) : (
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <circle cx="12" cy="13" r="4" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
            </button>

            {/* Voice Search / Mic Button */}
            <button
              type="button"
              onClick={toggleVoiceSearch}
              title={isListening ? 'Stop listening' : 'Voice Search (Speech to Text)'}
              className={`cursor-pointer rounded-full p-1 transition-colors ${
                isListening
                  ? 'bg-red-600 text-white animate-pulse'
                  : 'text-gray-500 hover:bg-gray-100 hover:text-gray-800'
              }`}
              aria-label="Voice Search"
            >
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill={isListening ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
            </button>
          </div>

          {/* Hidden File Input for Image Scanning */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleImageFile}
            accept="image/*"
            capture="environment"
            className="hidden"
          />
        </div>

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

        {/* Status notification toast for scan/voice */}
        {scanMessage && (
          <div className="w-full text-xs font-medium text-gray-700 bg-gray-100 rounded px-3 py-1.5 transition-all">
            {scanMessage}
          </div>
        )}
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
