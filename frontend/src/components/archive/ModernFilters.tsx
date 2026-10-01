'use client';

import React, { useState, useEffect } from 'react';
import { useTheme } from '@/context/ThemeContext';
import styles from './ModernFilters.module.css';

interface FilterOption {
  id: string;
  name: string;
  count?: number;
}

interface FilterSection {
  id: string;
  title: string;
  type: 'checkbox' | 'radio' | 'range' | 'search';
  options?: FilterOption[];
  min?: number;
  max?: number;
  unit?: string;
}

interface ModernFiltersProps {
  filters: FilterSection[];
  activeFilters: Record<string, any>;
  onFilterChange: (filterId: string, value: any) => void;
  onClearAll: () => void;
  className?: string;
}

export default function ModernFilters({
  filters,
  activeFilters,
  onFilterChange,
  onClearAll,
  className = '',
}: ModernFiltersProps) {
  const { theme } = useTheme();
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const [searchTerms, setSearchTerms] = useState<Record<string, string>>({});
  // eslint-disable-next-line unused-imports/no-unused-vars
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [priceRange, setPriceRange] = useState({ min: 0, max: 10000 });

  useEffect(() => {
    // Expand first few sections by default
    const defaultExpanded = new Set(filters.slice(0, 3).map((f) => f.id));
    setExpandedSections(defaultExpanded);
  }, [filters]);

  const toggleSection = (sectionId: string) => {
    setExpandedSections((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId);
      } else {
        newSet.add(sectionId);
      }
      return newSet;
    });
  };

  const handleSearchChange = (sectionId: string, value: string) => {
    setSearchTerms((prev) => ({ ...prev, [sectionId]: value }));
  };

  const getFilteredOptions = (section: FilterSection) => {
    if (!section.options) return [];
    const searchTerm = searchTerms[section.id] || '';
    return section.options.filter((option) =>
      option.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  const getActiveCount = () => {
    return Object.keys(activeFilters).filter((key) => {
      const value = activeFilters[key];
      if (Array.isArray(value)) return value.length > 0;
      return value !== undefined && value !== '' && value !== 'all';
    }).length;
  };

  const hasActiveFilters = getActiveCount() > 0;

  return (
    <div className={`${styles.modernFilters} ${className}`}>
      {/* Header */}
      <div className={styles.filtersHeader}>
        <h2 className={styles.filtersTitle}>FILTERS</h2>
        {hasActiveFilters && (
          <button
            className={styles.clearAllBtn}
            onClick={onClearAll}
            style={{ color: theme.primary }}
          >
            Clear all
          </button>
        )}
      </div>

      {/* Active Filters Count */}
      {hasActiveFilters && (
        <div className={styles.activeFiltersCount}>
          {getActiveCount()} filter{getActiveCount() !== 1 ? 's' : ''} applied
        </div>
      )}

      {/* Filter Sections */}
      <div className={styles.filterSections}>
        {filters.map((section) => {
          const isExpanded = expandedSections.has(section.id);
          const filteredOptions = getFilteredOptions(section);
          const hasMore = filteredOptions.length > 5 && !isExpanded;

          return (
            <div key={section.id} className={styles.filterSection}>
              <div className={styles.sectionHeader} onClick={() => toggleSection(section.id)}>
                <h3 className={styles.sectionTitle}>{section.title}</h3>
                <div className={`${styles.expandIcon} ${isExpanded ? styles.expanded : ''}`}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path
                      d="M6 9L12 15L18 9"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
              </div>

              {isExpanded && (
                <div className={styles.sectionContent}>
                  {/* Search within filter */}
                  {section.type === 'checkbox' &&
                    section.options &&
                    section.options.length > 10 && (
                      <div className={styles.filterSearch}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                          <circle
                            cx="11"
                            cy="11"
                            r="8"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                          <path
                            d="M21 21L16.65 16.65"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                        <input
                          type="text"
                          placeholder={`Search ${section.title.toLowerCase()}`}
                          value={searchTerms[section.id] || ''}
                          onChange={(e) => handleSearchChange(section.id, e.target.value)}
                          className={styles.searchInput}
                        />
                      </div>
                    )}

                  {/* Checkbox/Radio Options */}
                  {(section.type === 'checkbox' || section.type === 'radio') && (
                    <div className={styles.optionsList}>
                      {filteredOptions.slice(0, isExpanded ? undefined : 5).map((option) => {
                        const isActive =
                          section.type === 'checkbox'
                            ? activeFilters[section.id]?.includes(option.id)
                            : activeFilters[section.id] === option.id;

                        return (
                          <label key={option.id} className={styles.optionLabel}>
                            <input
                              type={section.type}
                              name={section.id}
                              value={option.id}
                              checked={isActive}
                              onChange={(e) => {
                                if (section.type === 'checkbox') {
                                  const currentValues = activeFilters[section.id] || [];
                                  const newValues = e.target.checked
                                    ? [...currentValues, option.id]
                                    : currentValues.filter((id: string) => id !== option.id);
                                  onFilterChange(section.id, newValues);
                                } else {
                                  onFilterChange(section.id, e.target.value);
                                }
                              }}
                              className={styles.optionInput}
                            />
                            <span className={styles.optionText}>{option.name}</span>
                            {option.count !== undefined && (
                              <span className={styles.optionCount}>({option.count})</span>
                            )}
                          </label>
                        );
                      })}

                      {hasMore && (
                        <button
                          className={styles.showMoreBtn}
                          onClick={() => toggleSection(section.id)}
                          style={{ color: theme.primary }}
                        >
                          + {filteredOptions.length - 5} more
                        </button>
                      )}
                    </div>
                  )}

                  {/* Price Range */}
                  {section.type === 'range' && (
                    <div className={styles.priceRange}>
                      <div className={styles.priceInputs}>
                        <div className={styles.priceInput}>
                          <input
                            type="number"
                            placeholder="Min"
                            value={activeFilters[section.id]?.min || ''}
                            onChange={(e) => {
                              const currentRange = activeFilters[section.id] || {
                                min: 0,
                                max: 10000,
                              };
                              onFilterChange(section.id, {
                                ...currentRange,
                                min: Number(e.target.value) || 0,
                              });
                            }}
                            className={styles.priceNumberInput}
                          />
                          <span className={styles.priceUnit}>{section.unit || '₹'}</span>
                        </div>
                        <span className={styles.priceSeparator}>-</span>
                        <div className={styles.priceInput}>
                          <input
                            type="number"
                            placeholder="Max"
                            value={activeFilters[section.id]?.max || ''}
                            onChange={(e) => {
                              const currentRange = activeFilters[section.id] || {
                                min: 0,
                                max: 10000,
                              };
                              onFilterChange(section.id, {
                                ...currentRange,
                                max: Number(e.target.value) || 10000,
                              });
                            }}
                            className={styles.priceNumberInput}
                          />
                          <span className={styles.priceUnit}>{section.unit || '₹'}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Search Filter */}
                  {section.type === 'search' && (
                    <div className={styles.searchFilter}>
                      <div className={styles.filterSearch}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                          <circle
                            cx="11"
                            cy="11"
                            r="8"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                          <path
                            d="M21 21L16.65 16.65"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                        <input
                          type="text"
                          placeholder={`Search ${section.title.toLowerCase()}`}
                          value={activeFilters[section.id] || ''}
                          onChange={(e) => onFilterChange(section.id, e.target.value)}
                          className={styles.searchInput}
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
