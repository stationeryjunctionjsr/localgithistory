import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../../src/theme';

export default function SellerLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: true,
        headerStyle: { backgroundColor: '#4f46e5' }, // Distinct color for seller
        headerTintColor: colors.surface,
        tabBarActiveTintColor: '#4f46e5',
        tabBarInactiveTintColor: colors.neutral[500],
        tabBarStyle: { paddingBottom: 5, height: 60 },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Dashboard',
          tabBarIcon: ({ color, size }) => <Ionicons name="stats-chart" size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="orders"
        options={{
          title: 'Orders',
          tabBarIcon: ({ color, size }) => <Ionicons name="cart" size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="products"
        options={{
          title: 'Inventory',
          tabBarIcon: ({ color, size }) => <Ionicons name="cube" size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="availability"
        options={{
          title: 'Availability',
          tabBarIcon: ({ color, size }) => <Ionicons name="calendar" size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="discounts"
        options={{
          title: 'Discounts',
          tabBarIcon: ({ color, size }) => <Ionicons name="pricetag" size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: ({ color, size }) => <Ionicons name="person" size={size} color={color} />,
        }}
      />
    </Tabs>
  );
}
