'use client';

import React, { useState, useRef, useEffect } from 'react';
import { SUPPORTED_LOCALES, RTL_LOCALES } from '@sj/i18n';
import type { LocaleCode } from '@sj/i18n';
import { useLanguage } from '@/context/LanguageContext';

// Native script names for each language — shown on the button and in the list
const LANG_LABELS: Record<LocaleCode, { native: string; english: string }> = {
  en: { native: 'English', english: 'English' },
  hi: { native: 'हिंदी', english: 'Hindi' },
  bn: { native: 'বাংলা', english: 'Bengali' },
  te: { native: 'తెలుగు', english: 'Telugu' },
  mr: { native: 'मराठी', english: 'Marathi' },
  ta: { native: 'தமிழ்', english: 'Tamil' },
  gu: { native: 'ગુજરાતી', english: 'Gujarati' },
  kn: { native: 'ಕನ್ನಡ', english: 'Kannada' },
  ml: { native: 'മലയാളം', english: 'Malayalam' },
  pa: { native: 'ਪੰਜਾਬੀ', english: 'Punjabi' },
  or: { native: 'ଓଡ଼ିଆ', english: 'Odia' },
  ur: { native: 'اردو', english: 'Urdu' },
};

export default function LanguageSwitcher() {
  const { locale, setLocale, t } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    if (!isOpen) return;
    const handleClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsOpen(false);
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [isOpen]);

  const currentLabel = LANG_LABELS[locale] ?? LANG_LABELS.en;

  return (
    <div ref={containerRef} style={{ position: 'fixed', bottom: '160px', right: '16px', zIndex: 9999 }}>
      {/* Toggle button */}
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label={t('lang.changeLanguage', 'Change Language')}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        title={t('lang.changeLanguage', 'Change Language')}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '8px 12px',
          borderRadius: '9999px',
          background: '#1a4d33',
          color: '#fff',
          border: 'none',
          cursor: 'pointer',
          fontSize: '13px',
          fontWeight: '600',
          boxShadow: '0 2px 8px rgba(0,0,0,0.25)',
          whiteSpace: 'nowrap',
        }}
      >
        🌐 <span lang={locale}>{currentLabel.native}</span>
      </button>

      {/* Dropdown */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            onClick={() => setIsOpen(false)}
            style={{
              position: 'fixed', inset: 0, zIndex: -1,
            }}
            aria-hidden="true"
          />
          <div
            role="listbox"
            aria-label={t('lang.chooseLanguage', 'Choose Language')}
            style={{
              position: 'absolute',
              bottom: '48px',
              right: 0,
              background: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '12px',
              boxShadow: '0 8px 32px rgba(0,0,0,0.14)',
              padding: '8px',
              minWidth: '200px',
              maxHeight: '320px',
              overflowY: 'auto',
            }}
          >
            <p
              style={{
                margin: '0 0 6px 8px',
                fontSize: '11px',
                fontWeight: '700',
                color: '#6b7280',
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
              }}
            >
              {t('lang.chooseLanguage', 'Choose Language')}
            </p>

            {SUPPORTED_LOCALES.map((code) => {
              const isActive = code === locale;
              const label = LANG_LABELS[code];
              const isRTL = RTL_LOCALES.has(code);
              return (
                <button
                  key={code}
                  role="option"
                  aria-selected={isActive}
                  onClick={() => {
                    setLocale(code);
                    setIsOpen(false);
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    width: '100%',
                    padding: '9px 12px',
                    borderRadius: '8px',
                    border: 'none',
                    background: isActive ? '#f0fdf4' : 'transparent',
                    cursor: 'pointer',
                    textAlign: 'left',
                    gap: '8px',
                  }}
                  lang={code}
                  dir={isRTL ? 'rtl' : 'ltr'}
                >
                  <span style={{ fontSize: '15px', fontWeight: isActive ? '700' : '400', color: isActive ? '#1a4d33' : '#111827' }}>
                    {label.native}
                  </span>
                  <span style={{ fontSize: '11px', color: '#9ca3af', fontWeight: '400', direction: 'ltr' }}>
                    {label.english}
                  </span>
                  {isActive && (
                    <span style={{ color: '#1a4d33', fontWeight: '700', marginLeft: 'auto' }} aria-hidden="true">
                      ✓
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
