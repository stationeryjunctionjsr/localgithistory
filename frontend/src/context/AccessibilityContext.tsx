'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

interface AccessibilityConfig {
  highContrast: boolean;
  reducedMotion: boolean;
  fontSize: 'normal' | 'large' | 'xl';
  focusVisible: boolean;
  dyslexiaFont: boolean;
}

interface AccessibilityContextType {
  config: AccessibilityConfig;
  updateConfig: (updates: Partial<AccessibilityConfig>) => void;
  toggleHighContrast: () => void;
  toggleReducedMotion: () => void;
  toggleFocusVisible: () => void;
  toggleDyslexiaFont: () => void;
  cycleFontSize: () => void;
}

const defaultConfig: AccessibilityConfig = {
  highContrast: false,
  reducedMotion: false,
  fontSize: 'normal',
  focusVisible: false,
  dyslexiaFont: false,
};

const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined);

export const AccessibilityProvider = ({ children }: { children: React.ReactNode }) => {
  const [config, setConfig] = useState<AccessibilityConfig>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('a11yConfig');
      if (saved) {
        try {
          return { ...defaultConfig, ...JSON.parse(saved) };
        } catch {
          return defaultConfig;
        }
      }
    }
    return defaultConfig;
  });

  const updateConfig = (updates: Partial<AccessibilityConfig>) => {
    const newConfig = { ...config, ...updates };
    setConfig(newConfig);
    if (typeof window !== 'undefined') {
      localStorage.setItem('a11yConfig', JSON.stringify(newConfig));
    }
  };

  const toggleHighContrast = () => updateConfig({ highContrast: !config.highContrast });
  const toggleReducedMotion = () => updateConfig({ reducedMotion: !config.reducedMotion });
  const toggleFocusVisible = () => updateConfig({ focusVisible: !config.focusVisible });
  const toggleDyslexiaFont = () => updateConfig({ dyslexiaFont: !config.dyslexiaFont });

  const cycleFontSize = () => {
    const sizes: AccessibilityConfig['fontSize'][] = ['normal', 'large', 'xl'];
    const currentIndex = sizes.indexOf(config.fontSize);
    const nextSize = sizes[(currentIndex + 1) % sizes.length];
    updateConfig({ fontSize: nextSize });
  };

  // Apply CSS classes to <html> whenever config changes
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const html = document.documentElement;

    // High contrast
    html.classList.toggle('a11y-high-contrast', config.highContrast);

    // Reduced motion
    html.classList.toggle('a11y-reduced-motion', config.reducedMotion);

    // Font size
    html.classList.remove('a11y-font-large', 'a11y-font-xl');
    if (config.fontSize === 'large') html.classList.add('a11y-font-large');
    if (config.fontSize === 'xl') html.classList.add('a11y-font-xl');

    // Always-on focus rings
    html.classList.toggle('a11y-focus-visible', config.focusVisible);

    // Dyslexia font - load Lexend if needed
    if (config.dyslexiaFont) {
      const linkId = 'a11y-lexend-font';
      if (!document.getElementById(linkId)) {
        const link = document.createElement('link');
        link.id = linkId;
        link.rel = 'stylesheet';
        link.href =
          'https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;500;600;700&display=swap';
        document.head.appendChild(link);
      }
      html.classList.add('a11y-dyslexia-font');
    } else {
      html.classList.remove('a11y-dyslexia-font');
    }
  }, [config]);

  return (
    <AccessibilityContext.Provider
      value={{
        config,
        updateConfig,
        toggleHighContrast,
        toggleReducedMotion,
        toggleFocusVisible,
        toggleDyslexiaFont,
        cycleFontSize,
      }}
    >
      {children}
    </AccessibilityContext.Provider>
  );
};

export const useAccessibility = () => {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider');
  }
  return context;
};
