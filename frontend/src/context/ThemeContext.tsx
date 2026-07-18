'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

export const themes = {
  red: {
    name: 'Red Theme',
    primary: '#d63031',
    primaryDark: '#c0392b',
    primaryLight: '#e74c3c',
    gradient: 'linear-gradient(135deg, #c0392b 0%, #d63031 100%)',
    hoverGradient: 'linear-gradient(135deg, #c0392b 0%, #d63031 100%)',
    categoryGradient: 'linear-gradient(135deg, #d63031 0%, #ff3f6c 50%, #ff3f6c 100%)',
    border: '#d63031',
    shadow: 'rgba(214, 48, 49, 0.4)',
  },
  blue: {
    name: 'Blue Theme',
    primary: '#0984e3',
    primaryDark: '#0652dd',
    primaryLight: '#74b9ff',
    gradient: 'linear-gradient(135deg, #0652dd 0%, #0984e3 100%)',
    hoverGradient: 'linear-gradient(135deg, #0652dd 0%, #0984e3 100%)',
    categoryGradient: 'linear-gradient(135deg, #0984e3 0%, #00b8ff 50%, #00b8ff 100%)',
    border: '#0984e3',
    shadow: 'rgba(9, 132, 227, 0.4)',
  },
  green: {
    name: 'Green Theme',
    primary: '#00b894',
    primaryDark: '#00a085',
    primaryLight: '#55efc4',
    gradient: 'linear-gradient(135deg, #00a085 0%, #00b894 100%)',
    hoverGradient: 'linear-gradient(135deg, #00a085 0%, #00b894 100%)',
    categoryGradient: 'linear-gradient(135deg, #00b894 0%, #00ffa8 50%, #00ffa8 100%)',
    border: '#00b894',
    shadow: 'rgba(0, 184, 148, 0.4)',
  },
  purple: {
    name: 'Purple Theme',
    primary: '#6c5ce7',
    primaryDark: '#5f3dc4',
    primaryLight: '#a29bfe',
    gradient: 'linear-gradient(135deg, #5f3dc4 0%, #6c5ce7 100%)',
    hoverGradient: 'linear-gradient(135deg, #5f3dc4 0%, #6c5ce7 100%)',
    categoryGradient: 'linear-gradient(135deg, #6c5ce7 0%, #a29bfe 50%, #a29bfe 100%)',
    border: '#6c5ce7',
    shadow: 'rgba(108, 92, 231, 0.4)',
  },
  orange: {
    name: 'Orange Theme',
    primary: '#e17055',
    primaryDark: '#d63031',
    primaryLight: '#fdcb6e',
    gradient: 'linear-gradient(135deg, #d63031 0%, #e17055 100%)',
    hoverGradient: 'linear-gradient(135deg, #d63031 0%, #e17055 100%)',
    categoryGradient: 'linear-gradient(135deg, #e17055 0%, #ff7675 50%, #ff7675 100%)',
    border: '#e17055',
    shadow: 'rgba(225, 112, 85, 0.4)',
  },
  teal: {
    name: 'Teal Theme',
    primary: '#008080',
    primaryDark: '#006666',
    primaryLight: '#00a3a3',
    gradient: 'linear-gradient(135deg, #006666 0%, #008080 100%)',
    hoverGradient: 'linear-gradient(135deg, #006666 0%, #008080 100%)',
    categoryGradient: 'linear-gradient(135deg, #008080 0%, #009999 50%, #009999 100%)',
    border: '#008080',
    shadow: 'rgba(0, 128, 128, 0.4)',
  },
  pink: {
    name: 'Pink Theme',
    primary: '#fd79a8',
    primaryDark: '#e84393',
    primaryLight: '#fdcb6e',
    gradient: 'linear-gradient(135deg, #e84393 0%, #fd79a8 100%)',
    hoverGradient: 'linear-gradient(135deg, #e84393 0%, #fd79a8 100%)',
    categoryGradient: 'linear-gradient(135deg, #fd79a8 0%, #ffeaa7 50%, #ffeaa7 100%)',
    border: '#fd79a8',
    shadow: 'rgba(253, 121, 168, 0.4)',
  },
  indigo: {
    name: 'Indigo Theme',
    primary: '#4834d4',
    primaryDark: '#2f3542',
    primaryLight: '#686de0',
    gradient: 'linear-gradient(135deg, #2f3542 0%, #4834d4 100%)',
    hoverGradient: 'linear-gradient(135deg, #2f3542 0%, #4834d4 100%)',
    categoryGradient: 'linear-gradient(135deg, #4834d4 0%, #686de0 50%, #686de0 100%)',
    border: '#4834d4',
    shadow: 'rgba(72, 52, 212, 0.4)',
  },
  black: {
    name: 'Black Theme',
    primary: '#000000',
    primaryDark: '#1a1a1a',
    primaryLight: '#333333',
    gradient: 'linear-gradient(135deg, #1a1a1a 0%, #000000 100%)',
    hoverGradient: 'linear-gradient(135deg, #1a1a1a 0%, #000000 100%)',
    categoryGradient: 'linear-gradient(135deg, #000000 0%, #2d2d2d 50%, #2d2d2d 100%)',
    border: '#000000',
    shadow: 'rgba(0, 0, 0, 0.4)',
  },
  mustard: {
    name: 'Mustard Yellow Theme',
    primary: '#daa520',
    primaryDark: '#b8860b',
    primaryLight: '#ffdb58',
    gradient: 'linear-gradient(135deg, #b8860b 0%, #daa520 100%)',
    hoverGradient: 'linear-gradient(135deg, #b8860b 0%, #daa520 100%)',
    categoryGradient: 'linear-gradient(135deg, #daa520 0%, #ffdb58 50%, #ffdb58 100%)',
    border: '#daa520',
    shadow: 'rgba(218, 165, 32, 0.4)',
  },
  darkGreen: {
    name: 'Dark Green Theme',
    primary: '#1a4d33',
    primaryDark: '#143b27',
    primaryLight: '#2a6b4a',
    gradient: 'linear-gradient(135deg, #143b27 0%, #1a4d33 100%)',
    hoverGradient: 'linear-gradient(135deg, #143b27 0%, #1a4d33 100%)',
    categoryGradient: 'linear-gradient(135deg, #1a4d33 0%, #2a6b4a 50%, #2a6b4a 100%)',
    border: '#1a4d33',
    shadow: 'rgba(26, 77, 51, 0.4)',
  },
  babyBlue: {
    name: 'Baby Blue Theme',
    primary: '#89CFF0',
    primaryDark: '#5fb8e0',
    primaryLight: '#B0E0E6',
    gradient: 'linear-gradient(135deg, #5fb8e0 0%, #89CFF0 100%)',
    hoverGradient: 'linear-gradient(135deg, #5fb8e0 0%, #89CFF0 100%)',
    categoryGradient: 'linear-gradient(135deg, #89CFF0 0%, #B0E0E6 50%, #B0E0E6 100%)',
    border: '#89CFF0',
    shadow: 'rgba(137, 207, 240, 0.4)',
  },
  sage: {
    name: 'Sage Theme',
    primary: '#A8CBB7',
    primaryDark: '#8DAF9C',
    primaryLight: '#C3E2D1',
    gradient: 'linear-gradient(135deg, #8DAF9C 0%, #A8CBB7 100%)',
    hoverGradient: 'linear-gradient(135deg, #8DAF9C 0%, #A8CBB7 100%)',
    categoryGradient: 'linear-gradient(135deg, #A8CBB7 0%, #C3E2D1 100%)',
    border: '#A8CBB7',
    shadow: 'rgba(168, 203, 183, 0.4)',
  },
  mintPastel: {
    name: 'Mint Pastel Theme',
    primary: '#CFE8D5',
    primaryDark: '#B4CDBA',
    primaryLight: '#EAFDF0',
    gradient: 'linear-gradient(135deg, #B4CDBA 0%, #CFE8D5 100%)',
    hoverGradient: 'linear-gradient(135deg, #B4CDBA 0%, #CFE8D5 100%)',
    categoryGradient: 'linear-gradient(135deg, #CFE8D5 0%, #EAFDF0 100%)',
    border: '#CFE8D5',
    shadow: 'rgba(207, 232, 213, 0.4)',
  },
  sand: {
    name: 'Sand Theme',
    primary: '#F6F1EB',
    primaryDark: '#DED6CB',
    primaryLight: '#FFFFFF',
    gradient: 'linear-gradient(135deg, #DED6CB 0%, #F6F1EB 100%)',
    hoverGradient: 'linear-gradient(135deg, #DED6CB 0%, #F6F1EB 100%)',
    categoryGradient: 'linear-gradient(135deg, #F6F1EB 0%, #FFFFFF 100%)',
    border: '#F6F1EB',
    shadow: 'rgba(246, 241, 235, 0.4)',
  },
  beige: {
    name: 'Beige Theme',
    primary: '#EFE7DC',
    primaryDark: '#D4CABB',
    primaryLight: '#FFF9F2',
    gradient: 'linear-gradient(135deg, #D4CABB 0%, #EFE7DC 100%)',
    hoverGradient: 'linear-gradient(135deg, #D4CABB 0%, #EFE7DC 100%)',
    categoryGradient: 'linear-gradient(135deg, #EFE7DC 0%, #FFF9F2 100%)',
    border: '#EFE7DC',
    shadow: 'rgba(239, 231, 220, 0.4)',
  },
  steel: {
    name: 'Steel Theme',
    primary: '#5C7C99',
    primaryDark: '#455E74',
    primaryLight: '#7AA1C5',
    gradient: 'linear-gradient(135deg, #455E74 0%, #5C7C99 100%)',
    hoverGradient: 'linear-gradient(135deg, #455E74 0%, #5C7C99 100%)',
    categoryGradient: 'linear-gradient(135deg, #5C7C99 0%, #7AA1C5 100%)',
    border: '#5C7C99',
    shadow: 'rgba(92, 124, 153, 0.4)',
  },
  slate: {
    name: 'Slate Theme',
    primary: '#6B8BA4',
    primaryDark: '#526D81',
    primaryLight: '#8BB0C9',
    gradient: 'linear-gradient(135deg, #526D81 0%, #6B8BA4 100%)',
    hoverGradient: 'linear-gradient(135deg, #526D81 0%, #6B8BA4 100%)',
    categoryGradient: 'linear-gradient(135deg, #6B8BA4 0%, #8BB0C9 100%)',
    border: '#6B8BA4',
    shadow: 'rgba(107, 139, 164, 0.4)',
  },
  peach: {
    name: 'Peach Theme',
    primary: '#F4C7B9',
    primaryDark: '#D8A598',
    primaryLight: '#FFE3D9',
    gradient: 'linear-gradient(135deg, #D8A598 0%, #F4C7B9 100%)',
    hoverGradient: 'linear-gradient(135deg, #D8A598 0%, #F4C7B9 100%)',
    categoryGradient: 'linear-gradient(135deg, #F4C7B9 0%, #FFE3D9 100%)',
    border: '#F4C7B9',
    shadow: 'rgba(244, 199, 185, 0.4)',
  },
  coral: {
    name: 'Coral Theme',
    primary: '#FFD6C9',
    primaryDark: '#EBB6A8',
    primaryLight: '#FFF1EE',
    gradient: 'linear-gradient(135deg, #EBB6A8 0%, #FFD6C9 100%)',
    hoverGradient: 'linear-gradient(135deg, #EBB6A8 0%, #FFD6C9 100%)',
    categoryGradient: 'linear-gradient(135deg, #FFD6C9 0%, #FFF1EE 100%)',
    border: '#FFD6C9',
    shadow: 'rgba(255, 214, 201, 0.4)',
  },
  charcoal: {
    name: 'Charcoal Theme',
    primary: '#2E2E2E',
    primaryDark: '#1A1A1A',
    primaryLight: '#4A4A4A',
    gradient: 'linear-gradient(135deg, #1A1A1A 0%, #2E2E2E 100%)',
    hoverGradient: 'linear-gradient(135deg, #1A1A1A 0%, #2E2E2E 100%)',
    categoryGradient: 'linear-gradient(135deg, #2E2E2E 0%, #4A4A4A 100%)',
    border: '#2E2E2E',
    shadow: 'rgba(46, 46, 46, 0.4)',
  },
};

interface Theme {
  name: string;
  primary: string;
  primaryDark: string;
  primaryLight: string;
  gradient: string;
  hoverGradient: string;
  categoryGradient: string;
  border: string;
  shadow: string;
}

interface ThemeContextType {
  theme: Theme;
  currentTheme: string;
  changeTheme: (themeKey: string) => void;
  themes: Record<string, Theme>;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider = ({ children }: { children: React.ReactNode }) => {
  const [currentTheme, setCurrentTheme] = useState(() => {
    // Get theme from localStorage or default to red
    if (typeof window !== 'undefined') {
      const savedTheme = localStorage.getItem('landingPageTheme');
      return savedTheme && themes[savedTheme as keyof typeof themes] ? savedTheme : 'darkGreen';
    }
    return 'darkGreen';
  });

  const theme = themes[currentTheme as keyof typeof themes];

  const changeTheme = (themeKey: string) => {
    if (themes[themeKey as keyof typeof themes]) {
      setCurrentTheme(themeKey);
      if (typeof window !== 'undefined') {
        localStorage.setItem('landingPageTheme', themeKey);
      }
    }
  };

  // Apply theme CSS variables
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const root = document.documentElement;
      root.style.setProperty('--primary-color', theme.primary);
      root.style.setProperty('--primary-dark', theme.primaryDark);
      root.style.setProperty('--primary-light', theme.primaryLight);
      root.style.setProperty('--theme-gradient', theme.gradient);
      root.style.setProperty('--theme-hover-gradient', theme.hoverGradient);
      root.style.setProperty('--theme-category-gradient', theme.categoryGradient);
      root.style.setProperty('--theme-border', theme.border);
      root.style.setProperty('--theme-shadow', theme.shadow);
    }
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, currentTheme, changeTheme, themes }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
