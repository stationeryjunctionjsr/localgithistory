'use client';

import React, { useId } from 'react';
import { useAccessibility } from '@/context/AccessibilityContext';
import { useTheme } from '@/context/ThemeContext';
import { useLanguage } from '@/context/LanguageContext';

const fontSizeLabels: Record<string, string> = {
  normal: 'A',
  large: 'A+',
  xl: 'A++',
};

export default function AccessibilityPanel() {
  const { config, toggleHighContrast, toggleReducedMotion, toggleFocusVisible, toggleDyslexiaFont, cycleFontSize } =
    useAccessibility();
  const { theme } = useTheme();
  const { t, locale } = useLanguage();

  const hcId = useId();
  const rmId = useId();
  const fvId = useId();
  const dfId = useId();
  const langId = useId();

  // Native language name label for the current locale
  const langLabel = t(`lang.${locale}`, locale.toUpperCase());

  return (
    <div
      style={{
        padding: '0',
      }}
      role="group"
      aria-label={t('accessibility.settings', 'Accessibility settings')}
    >
      {/* Section header */}
      <h3
        style={{
          fontSize: '20px',
          fontWeight: 800,
          color: theme.primary,
          margin: '0 0 20px 0',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}
      >
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
          focusable="false"
        >
          <circle cx="12" cy="12" r="10" />
          <path d="M12 8v4M12 16h.01" />
        </svg>
        {t('accessibility.title', 'Accessibility Options')}
      </h3>

      {/* High Contrast */}
      <div className="a11y-panel-toggle-row">
        <span id={hcId} style={{ fontSize: '12px', color: '#374151' }}>
          {t('accessibility.highContrast', 'High Contrast')}
        </span>
        <label className="a11y-toggle-switch" aria-labelledby={hcId}>
          <input
            type="checkbox"
            checked={config.highContrast}
            onChange={toggleHighContrast}
            aria-checked={config.highContrast}
          />
          <span className="a11y-toggle-slider" />
        </label>
      </div>

      {/* Reduced Motion */}
      <div className="a11y-panel-toggle-row">
        <span id={rmId} style={{ fontSize: '12px', color: '#374151' }}>
          {t('accessibility.reduceMotion', 'Reduce Motion')}
        </span>
        <label className="a11y-toggle-switch" aria-labelledby={rmId}>
          <input
            type="checkbox"
            checked={config.reducedMotion}
            onChange={toggleReducedMotion}
            aria-checked={config.reducedMotion}
          />
          <span className="a11y-toggle-slider" />
        </label>
      </div>

      {/* Focus Rings */}
      <div className="a11y-panel-toggle-row">
        <span id={fvId} style={{ fontSize: '12px', color: '#374151' }}>
          {t('accessibility.focusRings', 'Focus Rings')}
        </span>
        <label className="a11y-toggle-switch" aria-labelledby={fvId}>
          <input
            type="checkbox"
            checked={config.focusVisible}
            onChange={toggleFocusVisible}
            aria-checked={config.focusVisible}
          />
          <span className="a11y-toggle-slider" />
        </label>
      </div>

      {/* Dyslexia Font */}
      <div className="a11y-panel-toggle-row">
        <span id={dfId} style={{ fontSize: '12px', color: '#374151' }}>
          {t('accessibility.dyslexiaFont', 'Dyslexia Font')}
        </span>
        <label className="a11y-toggle-switch" aria-labelledby={dfId}>
          <input
            type="checkbox"
            checked={config.dyslexiaFont}
            onChange={toggleDyslexiaFont}
            aria-checked={config.dyslexiaFont}
          />
          <span className="a11y-toggle-slider" />
        </label>
      </div>

      {/* Text Size */}
      <div className="a11y-panel-toggle-row">
        <span style={{ fontSize: '12px', color: '#374151' }}>{t('accessibility.textSize', 'Text Size')}</span>
        <button
          className="a11y-font-badge"
          onClick={cycleFontSize}
          aria-label={`${t('accessibility.textSize', 'Text size')}: ${config.fontSize}. ${t('common.retry', 'Click to cycle')}`}
          style={{ background: theme.primary }}
        >
          {fontSizeLabels[config.fontSize]}
        </button>
      </div>

      {/* Language — links to the LanguageSwitcher floating button */}
      <div className="a11y-panel-toggle-row">
        <span id={langId} style={{ fontSize: '12px', color: '#374151' }}>
          {t('accessibility.language', 'Language')}
        </span>
        <span
          aria-labelledby={langId}
          lang={locale}
          style={{
            fontSize: '13px',
            fontWeight: '600',
            color: theme.primary,
            background: '#f0fdf4',
            borderRadius: '9999px',
            padding: '4px 10px',
          }}
          title={t('lang.changeLanguage', 'Use the Language Switcher button in the bottom-right corner')}
        >
          🌐 {langLabel}
        </span>
      </div>
    </div>
  );
}
