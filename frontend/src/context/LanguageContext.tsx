'use client';

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
} from 'react';
import { locales, SUPPORTED_LOCALES, RTL_LOCALES } from '@sj/i18n';
import type { LocaleCode, Translations } from '@sj/i18n';
import api from '@/utils/api';

// ── Types ─────────────────────────────────────────────────────────────────────

interface LanguageContextType {
  locale: LocaleCode;
  setLocale: (code: LocaleCode) => void;
  t: (key: string, fallback?: string) => string;
  isRTL: boolean;
  isLoaded: boolean;
}

// ── Helpers ──────────────────────────────────────────────────────────────────

const STORAGE_KEY = 'sj_locale';

/** Resolve a dot-notation key against a translations object, e.g. "nav.home" */
function resolve(translations: Translations, key: string): string {
  const parts = key.split('.');
  let current: unknown = translations as unknown;
  for (const part of parts) {
    if (current == null || typeof current !== 'object') return key;
    current = (current as Record<string, unknown>)[part];
  }
  return typeof current === 'string' ? current : key;
}

/** Pick the best locale from navigator.languages, falling back to 'en'. */
function detectBrowserLocale(): LocaleCode {
  if (typeof navigator === 'undefined') return 'en';
  const langs = navigator.languages ?? [navigator.language ?? 'en'];
  for (const lang of langs) {
    const code = lang.split('-')[0] as LocaleCode;
    if (SUPPORTED_LOCALES.includes(code)) return code;
  }
  return 'en';
}

function readStoredLocale(): LocaleCode | null {
  if (typeof localStorage === 'undefined') return null;
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored && SUPPORTED_LOCALES.includes(stored as LocaleCode)) {
    return stored as LocaleCode;
  }
  return null;
}

function persistLocale(code: LocaleCode) {
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(STORAGE_KEY, code);
  }
}

// ── Context ───────────────────────────────────────────────────────────────────

const LanguageContext = createContext<LanguageContextType>({
  locale: 'en',
  setLocale: () => {},
  t: (key) => key,
  isRTL: false,
  isLoaded: false,
});

// ── Provider ──────────────────────────────────────────────────────────────────

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<LocaleCode>('en');
  const [isLoaded, setIsLoaded] = useState(false);
  const syncedRef = useRef(false); // prevent duplicate DB syncs on rapid changes

  // ── Initialise from localStorage / browser on mount ──────────────────────
  useEffect(() => {
    const stored = readStoredLocale();
    const initial = stored ?? detectBrowserLocale();
    setLocaleState(initial);
    setIsLoaded(true);
  }, []);

  // ── Apply lang + dir to <html> whenever locale changes ───────────────────
  useEffect(() => {
    if (!isLoaded) return;
    const html = document.documentElement;
    html.setAttribute('lang', locale);
    html.setAttribute('dir', RTL_LOCALES.has(locale) ? 'rtl' : 'ltr');
  }, [locale, isLoaded]);

  // ── Sync from auth user's preferredLanguage on login ─────────────────────
  // We listen for a custom event dispatched by AuthContext after a successful login.
  useEffect(() => {
    const handler = (e: Event) => {
      const preferredLanguage = (e as CustomEvent<string>).detail;
      if (preferredLanguage && SUPPORTED_LOCALES.includes(preferredLanguage as LocaleCode)) {
        const lang = preferredLanguage as LocaleCode;
        setLocaleState(lang);
        persistLocale(lang);
      }
    };
    window.addEventListener('sj:user-login', handler);
    return () => window.removeEventListener('sj:user-login', handler);
  }, []);

  // ── setLocale: update state, persist, and push to DB if logged in ─────────
  const setLocale = useCallback(
    async (code: LocaleCode) => {
      if (!SUPPORTED_LOCALES.includes(code)) return;
      setLocaleState(code);
      persistLocale(code);

      // Push to backend (best-effort; fire-and-forget)
      if (!syncedRef.current) {
        syncedRef.current = true;
        try {
          // Only call if a JWT token exists (user is logged in)
          const token =
            typeof document !== 'undefined'
              ? document.cookie.includes('sj_token') ||
                localStorage.getItem('token')
              : false;
          if (token) {
            await api.patch('/users/me/preferences', { preferredLanguage: code });
          }
        } catch {
          // Non-critical — local preference is already saved
        } finally {
          syncedRef.current = false;
        }
      }
    },
    []
  );

  // ── Translation function ──────────────────────────────────────────────────
  const t = useCallback(
    (key: string, fallback?: string): string => {
      const translations = locales[locale] ?? locales.en;
      const result = resolve(translations, key);
      // If key wasn't found, try English as fallback, then provided fallback
      if (result === key) {
        const enResult = resolve(locales.en, key);
        return enResult !== key ? enResult : (fallback ?? key);
      }
      return result;
    },
    [locale]
  );

  const isRTL = RTL_LOCALES.has(locale);

  return (
    <LanguageContext.Provider value={{ locale, setLocale, t, isRTL, isLoaded }}>
      {children}
    </LanguageContext.Provider>
  );
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useLanguage() {
  return useContext(LanguageContext);
}
