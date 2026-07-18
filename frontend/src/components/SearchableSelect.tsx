'use client';

import { useState, useRef, useEffect } from 'react';

interface SearchableSelectProps {
  options: string[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  className?: string;
  inputClassName?: string;
}

export default function SearchableSelect({
  options,
  value,
  onChange,
  placeholder = 'Select...',
  disabled = false,
  required = false,
  className = '',
  inputClassName = '',
}: SearchableSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const filtered = options.filter((opt) => opt.toLowerCase().includes(searchTerm.toLowerCase()));

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
        setSearchTerm('');
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className={`relative ${className}`} ref={containerRef}>
      {/* Hidden input for form required validation */}
      {required && (
        <input
          type="text"
          value={value}
          required
          onChange={() => {}}
          className="sr-only"
          tabIndex={-1}
          aria-hidden="true"
        />
      )}
      <div className="relative flex items-center">
        <input
          ref={inputRef}
          type="text"
          className={`${
            inputClassName ||
            'min-h-[42px] w-full rounded border px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-purple-400'
          } pr-10 ${
            disabled ? 'cursor-not-allowed bg-gray-100 text-gray-400' : 'cursor-pointer bg-white'
          }`}
          placeholder={value || placeholder}
          value={isOpen ? searchTerm : value || ''}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            if (!isOpen) setIsOpen(true);
          }}
          onClick={() => {
            if (!disabled) {
              setIsOpen(!isOpen);
              if (!isOpen) setSearchTerm('');
            }
          }}
          onFocus={() => {
            if (!disabled && !isOpen) {
              setIsOpen(true);
              setSearchTerm('');
            }
          }}
          readOnly={disabled}
          disabled={disabled}
        />
        <div className="pointer-events-none absolute right-3">
          <svg
            className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke={disabled ? '#9ca3af' : 'currentColor'}
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {isOpen && !disabled && (
        <div className="absolute z-[150] mt-1 max-h-60 w-full overflow-y-auto rounded-lg border bg-white shadow-lg">
          {filtered.length > 0 ? (
            filtered.map((opt) => (
              <div
                key={opt}
                className={`cursor-pointer px-3 py-2 text-sm hover:bg-purple-50 ${
                  opt === value ? 'bg-purple-50 font-medium text-purple-700' : 'text-gray-700'
                }`}
                onClick={() => {
                  onChange(opt);
                  setIsOpen(false);
                  setSearchTerm('');
                }}
              >
                {opt}
              </div>
            ))
          ) : (
            <div className="px-3 py-2 text-sm italic text-gray-400">No results found</div>
          )}
        </div>
      )}
    </div>
  );
}
