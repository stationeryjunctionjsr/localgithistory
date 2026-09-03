import { Tabs } from 'expo-router';
import { View, Text, Animated, Pressable, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useEffect, useRef, useState, useCallback } from 'react';
import { colors, shadows } from '../../src/theme';
import api from '../../src/api/client';
import { useAuth } from '../../src/hooks/useAuth';
import { getGuestCart } from '../../src/services/guestStore';
import { useFocusEffect } from '@react-navigation/native';
import { useLanguage } from '../../src/context/LanguageContext';

interface TabIconProps {
  name: string;
  focused: boolean;
  activeIcon: keyof typeof Ionicons.glyphMap;
  inactiveIcon: keyof typeof Ionicons.glyphMap;
  badge?: number;
}

function TabIcon({ name, focused, activeIcon, inactiveIcon, badge }: TabIconProps) {
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const iconOpacity = useRef(new Animated.Value(focused ? 1 : 0.6)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.spring(scaleAnim, {
        toValue: focused ? 1.05 : 1, // Subtle scale
        friction: 6,
        tension: 150,
        useNativeDriver: true,
      }),
      Animated.timing(iconOpacity, {
        toValue: 1, // Full opacity for all icons
        duration: 200,
        useNativeDriver: true,
      }),
    ]).start();
  }, [focused]);

  return (
    <View style={styles.tabIconContainer}>
      {/* Active indicator line at top */}
      <View style={[styles.activeIndicator, { opacity: focused ? 1 : 0 }]}>
        <View style={styles.indicatorPill} />
      </View>

      <Animated.View
        style={[
          styles.iconWrapper,
          focused && styles.activeIconWrapper,
          {
            transform: [{ scale: scaleAnim }],
            opacity: 1,
          },
        ]}
      >
        <Ionicons
          name={focused ? activeIcon : inactiveIcon}
          size={26} // Consistently large icons
          color={focused ? colors.primary : colors.neutral[600]} // Darker inactive color
        />

        {/* Badge */}
        {badge !== undefined && badge > 0 && (
          <View style={[styles.badge, focused && { top: -2, right: -2 }]}>
            <Text style={styles.badgeText}>{badge > 99 ? '99+' : badge}</Text>
          </View>
        )}
      </Animated.View>

      <Text
        style={[
          styles.tabLabel,
          {
            color: focused ? colors.primary : colors.neutral[700], // Higher contrast
            fontWeight: '700', // Bold for all states
            fontSize: 11, // Consistently larger
          },
        ]}
      >
        {name}
      </Text>
    </View>
  );
}

export default function TabsLayout() {
  const insets = useSafeAreaInsets();
  const { user } = useAuth();
  const { t } = useLanguage();
  const [cartCount, setCartCount] = useState(0);
  const isFirstRender = useRef(true);

  const fetchCounts = useCallback(async () => {
    try {
      if (user) {
        const cartRes = await api.get('/cart').catch(() => ({ data: [] }));
        setCartCount(Array.isArray(cartRes.data) ? cartRes.data.length : 0);
      } else {
        const guestCart = await getGuestCart();
        setCartCount(guestCart.length);
      }
    } catch {
      setCartCount(0);
    }
  }, [user]);

  useFocusEffect(
    useCallback(() => {
      if (isFirstRender.current) {
        isFirstRender.current = false;
        const timer = setTimeout(() => {
          fetchCounts();
        }, 1500);
        return () => clearTimeout(timer);
      } else {
        fetchCounts();
      }
    }, [fetchCounts])
  );

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopWidth: 0,
          height: 72 + insets.bottom,
          paddingBottom: insets.bottom,
          ...shadows.md,
        },
        tabBarShowLabel: false,
      }}
    >
      <Tabs.Screen
        name="home"
        options={{
          tabBarButton: (props: any) => (
            <Pressable {...props} style={styles.tabButton}>
              <TabIcon
                name={t('nav.home', 'Home')}
                focused={props.accessibilityState?.selected || false}
                activeIcon="home"
                inactiveIcon="home-outline"
              />
            </Pressable>
          ),
        }}
      />
      <Tabs.Screen
        name="categories"
        options={{
          tabBarButton: (props: any) => (
            <Pressable {...props} style={styles.tabButton}>
              <TabIcon
                name={t('nav.categories', 'Categories')}
                focused={props.accessibilityState?.selected || false}
                activeIcon="grid"
                inactiveIcon="grid-outline"
              />
            </Pressable>
          ),
        }}
      />
      <Tabs.Screen
        name="brands"
        options={{
          tabBarButton: (props: any) => (
            <Pressable {...props} style={styles.tabButton}>
              <TabIcon
                name={t('nav.brands', 'Brands')}
                focused={props.accessibilityState?.selected || false}
                activeIcon="pricetag"
                inactiveIcon="pricetag-outline"
              />
            </Pressable>
          ),
        }}
      />
      <Tabs.Screen
        name="schemes"
        options={
          user?.role === 'wholesaler'
            ? {
                tabBarButton: (props: any) => (
                  <Pressable {...props} style={styles.tabButton}>
                    <TabIcon
                      name={t('nav.schemes', 'Schemes')}
                      focused={props.accessibilityState?.selected || false}
                      activeIcon="pricetags"
                      inactiveIcon="pricetags-outline"
                    />
                  </Pressable>
                ),
              }
            : { href: null }
        }
      />
      <Tabs.Screen
        name="cart"
        options={{
          tabBarButton: (props: any) => (
            <Pressable {...props} style={styles.tabButton}>
              <TabIcon
                name={t('nav.cart', 'Cart')}
                focused={props.accessibilityState?.selected || false}
                activeIcon="cart"
                inactiveIcon="cart-outline"
                badge={cartCount}
              />
            </Pressable>
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          tabBarButton: (props: any) => (
            <Pressable {...props} style={styles.tabButton}>
              <TabIcon
                name={t('nav.profile', 'Profile')}
                focused={props.accessibilityState?.selected || false}
                activeIcon="person"
                inactiveIcon="person-outline"
              />
            </Pressable>
          ),
        }}
      />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  tabButton: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  tabIconContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 8,
  },
  activeIndicator: {
    position: 'absolute',
    top: -4,
    width: '100%',
    alignItems: 'center',
  },
  indicatorPill: {
    width: 48, // wider indicator
    height: 4, // thicker indicator
    backgroundColor: colors.primary,
    borderRadius: 2,
    ...shadows.xs, // Add subtle glow
  },
  iconWrapper: {
    width: 48,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  activeIconWrapper: {
    backgroundColor: 'rgba(26, 77, 51, 0.08)', // Very subtle tint of primary color
    borderRadius: 12,
  },
  badge: {
    position: 'absolute',
    top: -4,
    right: 0,
    minWidth: 18,
    height: 18,
    backgroundColor: colors.error,
    borderRadius: 9,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 4,
    borderWidth: 2,
    borderColor: colors.surface,
  },
  badgeText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '700',
  },
  tabLabel: {
    fontSize: 10,
    fontWeight: '500',
    marginTop: 4,
    letterSpacing: 0.2,
  },
});
