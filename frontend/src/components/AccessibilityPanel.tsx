'use client';

import React, { useId } from 'react';
import { useAccessibility } from '@/context/AccessibilityContext';
import { useTheme } from '@/context/ThemeContext';

const fontSizeLabels: Record<string, string> = {
  normal: 'A',
  large: 'A+',
  xl: 'A++',
};

export default function AccessibilityPanel() {
  const { config, toggleHighContrast, toggleReducedMotion, toggleFocusVisible, toggleDyslexiaFont, cycleFontSize } =
    useAccessibility();
  const { theme } = useTheme();

  const hcId = useId();
  const rmId = useId();
  const fvId = useId();
  const dfId = useId();

  return (
    <div
      style={{
        padding: '10px 20px 6px',
        borderTop: '1px solid #f3f4f6',
      }}
      role="group"
      aria-label="Accessibility settings"
    >
      {/* Section header */}
      <p
        style={{
          fontSize: '10px',
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.1em',
          color: theme.primary,
          margin: '0 0 8px 0',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
        }}
      >
        <svg
          width="13"
          height="13"
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
        Accessibility
      </p>

      {/* High Contrast */}
      <div className="a11y-panel-toggle-row">
        <span id={hcId} style={{ fontSize: '12px', color: '#374151' }}>
          High Contrast
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
          Reduce Motion
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
          Focus Rings
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
          Dyslexia Font
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
        <span style={{ fontSize: '12px', color: '#374151' }}>Text Size</span>
        <button
          className="a11y-font-badge"
          onClick={cycleFontSize}
          aria-label={`Text size: ${config.fontSize}. Click to cycle`}
          style={{ background: theme.primary }}
        >
          {fontSizeLabels[config.fontSize]}
        </button>
      </div>
    </div>
  );
}
