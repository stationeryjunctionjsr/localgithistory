import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from 'react';
import { I18nManager } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { locales, SUPPORTED_LOCALES, RTL_LOCALES } from '@sj/i18n';
import type { LocaleCode } from '@sj/i18n';
import api from '../api/client';
import { useAuthStore } from '../store/authStore';

const LOCALE_STORAGE_KEY = '@sj/locale';
const DEFAULT_LOCALE: LocaleCode = 'en';

// ─── Key resolver ────────────────────────────────────────────────────────────

function resolve(translations: any, key: string): string {
  const parts = key.split('.');
  let current: any = translations;
  for (const part of parts) {
    if (current == null) return key;
    current = current[part];
  }
  return typeof current === 'string' ? current : key;
}

// ─── Context types ───────────────────────────────────────────────────────────

interface LanguageContextValue {
  locale: LocaleCode;
  setLocale: (code: LocaleCode) => Promise<void>;
  t: (key: string, fallback?: string) => string;
  isRTL: boolean;
}

const LanguageContext = createContext<LanguageContextValue | undefined>(undefined);

// ─── Provider ────────────────────────────────────────────────────────────────

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<LocaleCode>(DEFAULT_LOCALE);
  const user = useAuthStore((s) => s.user);

  /** Apply RTL layout direction based on locale */
  const applyRTL = useCallback((code: LocaleCode) => {
    I18nManager.forceRTL(RTL_LOCALES.has(code));
  }, []);

  // On mount: restore persisted locale from AsyncStorage
  useEffect(() => {
    (async () => {
      try {
        const stored = await AsyncStorage.getItem(LOCALE_STORAGE_KEY);
        if (stored && SUPPORTED_LOCALES.includes(stored as LocaleCode)) {
          const code = stored as LocaleCode;
          setLocaleState(code);
          applyRTL(code);
        }
      } catch {
        // fall back to default locale on storage error
      }
    })();
  }, [applyRTL]);

  // When auth user changes (login), override locale from user.preferredLanguage
  useEffect(() => {
    if (user && (user as any).preferredLanguage) {
      const preferred = (user as any).preferredLanguage as string;
      if (SUPPORTED_LOCALES.includes(preferred as LocaleCode)) {
        const code = preferred as LocaleCode;
        setLocaleState(code);
        applyRTL(code);
        // Keep local storage in sync with user preference
        AsyncStorage.setItem(LOCALE_STORAGE_KEY, code).catch(() => {});
      }
    }
  }, [user, applyRTL]);

  /** Change locale: persists locally and syncs to backend if authenticated */
  const setLocale = useCallback(
    async (code: LocaleCode) => {
      if (!SUPPORTED_LOCALES.includes(code)) return;
      setLocaleState(code);
      applyRTL(code);

      try {
        await AsyncStorage.setItem(LOCALE_STORAGE_KEY, code);
      } catch {
        // ignore storage error
      }

      if (user) {
        try {
          await api.patch('/users/me/preferences', { preferredLanguage: code });
        } catch {
          // non-critical — preference will sync on next successful request
        }
      }
    },
    [user, applyRTL]
  );

  /** Translate a dot-notation key, with optional hardcoded fallback */
  const t = useCallback(
    (key: string, fallback?: string): string => {
      const translations = locales[locale] ?? locales[DEFAULT_LOCALE];
      const resolved = resolve(translations, key);
      // If the key wasn't found in the current locale, try the default locale
      if (resolved === key && locale !== DEFAULT_LOCALE) {
        const fromDefault = resolve(locales[DEFAULT_LOCALE], key);
        if (fromDefault !== key) return fromDefault;
      }
      return resolved !== key ? resolved : (fallback ?? key);
    },
    [locale]
  );

  const isRTL = RTL_LOCALES.has(locale);

  return (
    <LanguageContext.Provider value={{ locale, setLocale, t, isRTL }}>
      {children}
    </LanguageContext.Provider>
  );
}

// ─── Hook ────────────────────────────────────────────────────────────────────

export function useLanguage(): LanguageContextValue {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return ctx;
}
