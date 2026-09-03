/**
 * @sj/i18n — Shared locale data for Stationery Junction web and mobile.
 * Zero-dependency: just plain JSON, re-exported as typed objects.
 */

import en from './locales/en/common.json';
import hi from './locales/hi/common.json';
import bn from './locales/bn/common.json';
import te from './locales/te/common.json';
import mr from './locales/mr/common.json';
import ta from './locales/ta/common.json';
import gu from './locales/gu/common.json';
import kn from './locales/kn/common.json';
import ml from './locales/ml/common.json';
import pa from './locales/pa/common.json';
import or from './locales/or/common.json';
import ur from './locales/ur/common.json';

export type LocaleCode = 'en' | 'hi' | 'bn' | 'te' | 'mr' | 'ta' | 'gu' | 'kn' | 'ml' | 'pa' | 'or' | 'ur';

export const SUPPORTED_LOCALES: LocaleCode[] = [
  'en', 'hi', 'bn', 'te', 'mr', 'ta', 'gu', 'kn', 'ml', 'pa', 'or', 'ur',
];

/** True for right-to-left locales */
export const RTL_LOCALES: Set<LocaleCode> = new Set<LocaleCode>(['ur']);

export const locales: Record<LocaleCode, typeof en> = {
  en, hi, bn, te, mr, ta, gu, kn, ml, pa, or, ur,
};

export type Translations = typeof en;
