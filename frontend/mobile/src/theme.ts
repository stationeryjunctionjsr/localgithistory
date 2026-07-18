// Premium Luxury Theme - Inspired by high-end e-commerce apps
// Modern, clean, and visually stunning

export const colors = {
  // Brand colors - Deep forest green for premium feel
  brand: {
    primary: '#1a4d33', // Deep forest green
    primaryLight: '#2d7a52', // Lighter forest
    primaryDark: '#0f3322', // Darker shade
    accent: '#D4AF37', // Gold accent for luxury
    accentLight: '#F4E4BC', // Light gold
  },

  // Modern neutrals
  neutral: {
    50: '#FAFAFA',
    100: '#F5F5F5',
    200: '#EEEEEE',
    300: '#E0E0E0',
    400: '#BDBDBD',
    500: '#9E9E9E',
    600: '#757575',
    700: '#616161',
    800: '#424242',
    900: '#212121',
  },

  // Core palette
  primary: '#1a4d33',
  accent: '#D4AF37',
  accentLight: '#F4E4BC',

  // Surfaces
  background: '#FAFAFA',
  backgroundAlt: '#FDFBF7',
  surface: '#FFFFFF',
  surfaceMuted: '#F8F8F8',
  border: '#F0F0F0',
  borderMedium: '#E5E5E5',

  // Text hierarchy
  textPrimary: '#1A1A1A',
  textSecondary: '#666666',
  textMuted: '#999999',
  textOnAccent: '#FFFFFF',
  textOnPrimary: '#FFFFFF',

  // Semantic colors
  success: '#34C759',
  warning: '#FF9500',
  error: '#FF3B30',
  info: '#007AFF',

  // Gradient presets
  gradients: {
    premium: ['#1a4d33', '#2d7a52'],
    gold: ['#D4AF37', '#F4E4BC'],
    sunset: ['#FF6B6B', '#FFA07A'],
    ocean: ['#667eea', '#764ba2'],
  },

  // Legacy compatibility
  textOnSuccess: '#FFFFFF',
  textOnWarning: '#FFFFFF',
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
  xxxl: 64,
};

export const typography = {
  // Premium headers
  h1: { fontSize: 32, fontWeight: '700' as const, letterSpacing: -0.5, lineHeight: 40 },
  h2: { fontSize: 24, fontWeight: '600' as const, letterSpacing: -0.3, lineHeight: 32 },
  h3: { fontSize: 20, fontWeight: '600' as const, letterSpacing: 0, lineHeight: 28 },

  // Body
  body: { fontSize: 16, fontWeight: '400' as const, lineHeight: 24 },
  bodySmall: { fontSize: 14, fontWeight: '400' as const, lineHeight: 20 },

  // Labels
  label: {
    fontSize: 12,
    fontWeight: '600' as const,
    letterSpacing: 0.5,
    textTransform: 'uppercase' as const,
  },
  caption: { fontSize: 11, fontWeight: '400' as const, lineHeight: 14 },
  tiny: { fontSize: 10, fontWeight: '500' as const },
};

// Premium shadows with depth
export const shadows = {
  none: {},
  xs: {
    shadowColor: '#000000',
    shadowOpacity: 0.04,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 1 },
    elevation: 1,
  },
  sm: {
    shadowColor: '#000000',
    shadowOpacity: 0.06,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  md: {
    shadowColor: '#000000',
    shadowOpacity: 0.08,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 4 },
    elevation: 4,
  },
  lg: {
    shadowColor: '#000000',
    shadowOpacity: 0.1,
    shadowRadius: 24,
    shadowOffset: { width: 0, height: 8 },
    elevation: 8,
  },
  xl: {
    shadowColor: '#000000',
    shadowOpacity: 0.15,
    shadowRadius: 32,
    shadowOffset: { width: 0, height: 12 },
    elevation: 12,
  },
  // Special shadows for cards
  card: {
    shadowColor: '#1a4d33',
    shadowOpacity: 0.08,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 3,
  },
  // Glow effect for premium elements
  glow: {
    shadowColor: '#D4AF37',
    shadowOpacity: 0.25,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 4 },
    elevation: 4,
  },
};

export const borderRadius = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 28,
  full: 9999,
};

// Animation durations for smooth transitions
export const animation = {
  instant: 100,
  fast: 150,
  normal: 250,
  slow: 350,
  slower: 500,
};

// Premium design tokens
export const premium = {
  // Card styles
  card: {
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    background: colors.surface,
    ...shadows.card,
  },
  // Button styles
  button: {
    primary: {
      background: colors.primary,
      text: colors.textOnPrimary,
      borderRadius: borderRadius.full,
      padding: { vertical: spacing.md, horizontal: spacing.xl },
    },
    secondary: {
      background: 'transparent',
      text: colors.primary,
      borderRadius: borderRadius.full,
      borderWidth: 1.5,
      borderColor: colors.primary,
    },
  },
  // Tab bar dimensions
  tabBar: {
    height: 72,
    iconSize: 24,
    labelSize: 10,
    indicatorWidth: 48,
    indicatorHeight: 3,
  },
};
