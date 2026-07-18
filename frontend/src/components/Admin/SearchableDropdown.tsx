'use client';

import { useState, useRef, useEffect } from 'react';

interface Option {
  _id: string;
  name: string;
}

interface SearchableDropdownProps {
  options: Option[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

export default function SearchableDropdown({
  options,
  value,
  onChange,
  placeholder = 'Search...',
  className = '',
}: SearchableDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  const selectedOption = options.find((opt) => opt._id === value || opt.name === value);

  const filteredOptions = options.filter((opt) =>
    opt.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchTerm('');
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <div className="relative flex items-center">
        <input
          type="text"
          className="min-h-[42px] w-full cursor-pointer rounded border bg-white px-3 py-2 pr-10 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500"
          placeholder={selectedOption ? selectedOption.name : placeholder}
          value={isOpen ? searchTerm : selectedOption ? selectedOption.name : ''}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            if (!isOpen) setIsOpen(true);
          }}
          onClick={() => setIsOpen(!isOpen)}
          readOnly={!isOpen && !!selectedOption && searchTerm === ''}
        />
        <div
          className="pointer-events-none absolute right-3 cursor-pointer"
          onClick={() => setIsOpen(!isOpen)}
        >
          <svg
            className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {isOpen && (
        <div className="absolute z-[150] mt-1 max-h-60 w-full overflow-y-auto rounded border bg-white shadow-lg">
          {filteredOptions.length > 0 ? (
            filteredOptions.map((opt) => (
              <div
                key={opt._id}
                className={`cursor-pointer px-3 py-2 text-sm hover:bg-indigo-50 ${value === opt._id || value === opt.name ? 'bg-indigo-100 font-medium' : ''}`}
                onClick={() => {
                  onChange(opt.name || opt._id);
                  setIsOpen(false);
                  setSearchTerm('');
                }}
              >
                {opt.name}
              </div>
            ))
          ) : (
            <div className="px-3 py-2 text-sm italic text-gray-500">No results found</div>
          )}
        </div>
      )}
    </div>
  );
}
