'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

export const fonts = [
  { name: 'Inter', category: 'Sans Serif' },
  { name: 'Outfit', category: 'Sans Serif' },
  { name: 'Roboto', category: 'Sans Serif' },
  { name: 'Montserrat', category: 'Sans Serif' },
  { name: 'Poppins', category: 'Sans Serif' },
  { name: 'Playfair Display', category: 'Serif' },
  { name: 'Merriweather', category: 'Serif' },
  { name: 'Lora', category: 'Serif' },
  { name: 'Space Grotesk', category: 'Display' },
  { name: 'Syncopate', category: 'Display' },
  { name: 'JetBrains Mono', category: 'Monospace' },
];

export const fontWeights = [
  { value: '300', label: 'Light' },
  { value: '400', label: 'Regular' },
  { value: '500', label: 'Medium' },
  { value: '600', label: 'Semi Bold' },
  { value: '700', label: 'Bold' },
  { value: '800', label: 'Extra Bold' },
  { value: '900', label: 'Black' },
];

interface FontConfig {
  family: string;
  weight: string;
  headingWeight: string;
}

interface FontContextType {
  config: FontConfig;
  updateConfig: (updates: Partial<FontConfig>) => void;
  fonts: typeof fonts;
  fontWeights: typeof fontWeights;
}

const FontContext = createContext<FontContextType | undefined>(undefined);

export const FontProvider = ({ children }: { children: React.ReactNode }) => {
  const [config, setConfig] = useState<FontConfig>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('appFontConfig');
      return saved ? JSON.parse(saved) : { family: 'Inter', weight: '400', headingWeight: '900' };
    }
    return { family: 'Inter', weight: '400', headingWeight: '900' };
  });

  const updateConfig = (updates: Partial<FontConfig>) => {
    const newConfig = { ...config, ...updates };
    setConfig(newConfig);
    if (typeof window !== 'undefined') {
      localStorage.setItem('appFontConfig', JSON.stringify(newConfig));
    }
  };

  useEffect(() => {
    if (typeof window !== 'undefined') {
      // Create or update Google Fonts link tag
      const linkId = 'dynamic-google-fonts';
      let link = document.getElementById(linkId) as HTMLLinkElement;

      if (!link) {
        link = document.createElement('link');
        link.id = linkId;
        link.rel = 'stylesheet';
        document.head.appendChild(link);
      }

      const familyParam = config.family.replace(/ /g, '+');
      const weights = Array.from(
        new Set([config.weight, config.headingWeight, '400', '700', '900'])
      ).sort();
      link.href = `https://fonts.googleapis.com/css2?family=${familyParam
}:wght@${weights.join(';')}&display=swap`;

      // Apply to root
      const root = document.documentElement;
      root.style.setProperty('--app-font-family', `'${config.family}', sans-serif`);
      root.style.setProperty('--app-font-weight', config.weight);
      root.style.setProperty('--app-heading-weight', config.headingWeight);
    }
  }, [config]);

  return (
    <FontContext.Provider value={{ config, updateConfig, fonts, fontWeights }}>
      {children}
    </FontContext.Provider>
  );
};

export const useFont = () => {
  const context = useContext(FontContext);
  if (!context) {
    throw new Error('useFont must be used within a FontProvider');
  }
  return context;
};
