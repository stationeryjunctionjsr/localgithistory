import React, { useEffect, useRef } from 'react';
import { Animated, StyleSheet, View, ViewStyle, StyleProp } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

interface SkeletonProps {
  width?: any;
  height?: number;
  borderRadius?: number;
  style?: StyleProp<ViewStyle>;
}

/** Single skeleton bone with left-to-right shimmer animation. */
export function SkeletonBone({ width = '100%', height = 16, borderRadius = 8, style }: SkeletonProps) {
  const shimmer = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const loop = Animated.loop(
      Animated.timing(shimmer, {
        toValue: 1,
        duration: 1200,
        useNativeDriver: true,
      })
    );
    loop.start();
    return () => loop.stop();
  }, [shimmer]);

  const translateX = shimmer.interpolate({
    inputRange: [0, 1],
    outputRange: [-300, 300],
  });

  return (
    <View
      style={[
        styles.bone,
        { width, height, borderRadius },
        style,
      ]}
    >
      <Animated.View
        style={[StyleSheet.absoluteFill, { transform: [{ translateX }] }]}
      >
        <LinearGradient
          colors={['transparent', 'rgba(255,255,255,0.55)', 'transparent']}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={StyleSheet.absoluteFill}
        />
      </Animated.View>
    </View>
  );
}

/** Home screen skeleton — banner + two product rows */
export function HomeScreenSkeleton() {
  return (
    <View style={styles.container}>
      {/* Banner */}
      <SkeletonBone height={200} borderRadius={16} style={styles.mb16} />
      {/* Section header */}
      <SkeletonBone width="45%" height={18} style={styles.mb12} />
      {/* Product row */}
      <View style={styles.row}>
        {[0, 1, 2].map((i) => (
          <ProductCardSkeleton key={i} />
        ))}
      </View>
      {/* Section header */}
      <SkeletonBone width="50%" height={18} style={[styles.mb12, styles.mt8]} />
      {/* Product row */}
      <View style={styles.row}>
        {[0, 1, 2].map((i) => (
          <ProductCardSkeleton key={i} />
        ))}
      </View>
    </View>
  );
}

/** Small product card skeleton used in horizontal rows */
function ProductCardSkeleton() {
  return (
    <View style={styles.productCard}>
      <SkeletonBone height={110} borderRadius={12} style={styles.mb8} />
      <SkeletonBone width="80%" height={12} style={styles.mb6} />
      <SkeletonBone width="50%" height={12} />
    </View>
  );
}

/** Product detail skeleton — image + details block */
export function ProductDetailSkeleton() {
  return (
    <View style={styles.container}>
      {/* Image */}
      <SkeletonBone height={320} borderRadius={0} style={styles.mb16} />
      <View style={styles.padded}>
        {/* Brand */}
        <SkeletonBone width="30%" height={12} style={styles.mb10} />
        {/* Name */}
        <SkeletonBone width="85%" height={22} style={styles.mb6} />
        <SkeletonBone width="60%" height={22} style={styles.mb16} />
        {/* Price */}
        <SkeletonBone width="40%" height={30} style={styles.mb16} />
        {/* Divider */}
        <SkeletonBone height={1} borderRadius={0} style={styles.mb16} />
        {/* Variant chips */}
        <SkeletonBone width="25%" height={12} style={styles.mb10} />
        <View style={styles.chipRow}>
          {[80, 65, 75].map((w, i) => (
            <SkeletonBone key={i} width={w} height={36} borderRadius={18} style={styles.chip} />
          ))}
        </View>
        {/* Description */}
        <SkeletonBone width="35%" height={14} style={[styles.mb10, styles.mt8]} />
        <SkeletonBone height={12} style={styles.mb6} />
        <SkeletonBone height={12} style={styles.mb6} />
        <SkeletonBone width="75%" height={12} />
      </View>
    </View>
  );
}

/** Cart screen skeleton — 3 cart item rows */
export function CartScreenSkeleton() {
  return (
    <View style={styles.container}>
      {[0, 1, 2].map((i) => (
        <View key={i} style={[styles.cartRow, styles.mb12]}>
          <SkeletonBone width={80} height={80} borderRadius={10} />
          <View style={styles.cartDetails}>
            <SkeletonBone width="80%" height={14} style={styles.mb8} />
            <SkeletonBone width="50%" height={12} style={styles.mb8} />
            <SkeletonBone width="40%" height={18} />
          </View>
        </View>
      ))}
      {/* Summary box */}
      <View style={[styles.summaryBox, styles.mt8]}>
        <SkeletonBone width="55%" height={14} style={styles.mb10} />
        <SkeletonBone width="40%" height={14} style={styles.mb10} />
        <SkeletonBone height={44} borderRadius={22} style={styles.mt8} />
      </View>
    </View>
  );
}

/** Orders list skeleton — 4 order cards */
export function OrdersListSkeleton() {
  return (
    <View style={styles.container}>
      {[0, 1, 2, 3].map((i) => (
        <View key={i} style={[styles.orderCard, styles.mb12]}>
          <View style={styles.orderHeader}>
            <SkeletonBone width="40%" height={14} />
            <SkeletonBone width={70} height={24} borderRadius={12} />
          </View>
          <SkeletonBone width="55%" height={12} style={styles.mb6} />
          <SkeletonBone width="35%" height={18} style={styles.mb6} />
          <SkeletonBone width="45%" height={12} />
        </View>
      ))}
    </View>
  );
}

/** Products list skeleton — filter bar + 2-column product grid */
export function ProductsListSkeleton() {
  return (
    <View style={styles.container}>
      {/* Filter bar */}
      <View style={styles.filterRow}>
        <SkeletonBone width="60%" height={36} borderRadius={18} />
        <SkeletonBone width={80} height={36} borderRadius={18} />
        <SkeletonBone width={72} height={36} borderRadius={18} />
      </View>
      {/* 2-column grid — 3 rows */}
      {[0, 1, 2].map((row) => (
        <View key={row} style={[styles.gridRow, styles.mb12]}>
          <GridProductSkeleton />
          <GridProductSkeleton />
        </View>
      ))}
    </View>
  );
}

/** Single product card skeleton for 2-column grid */
function GridProductSkeleton() {
  return (
    <View style={styles.gridCard}>
      <SkeletonBone height={140} borderRadius={12} style={styles.mb8} />
      <SkeletonBone width="80%" height={13} style={styles.mb6} />
      <SkeletonBone width="55%" height={13} style={styles.mb6} />
      <SkeletonBone width="40%" height={18} />
    </View>
  );
}

/** Categories screen skeleton — search bar + 2-column category grid */
export function CategoriesScreenSkeleton() {
  return (
    <View style={styles.container}>
      {/* Tag chips row */}
      <View style={styles.filterRow}>
        {[50, 70, 60, 80].map((w, i) => (
          <SkeletonBone key={i} width={w} height={32} borderRadius={16} />
        ))}
      </View>
      {/* Banner placeholder */}
      <SkeletonBone height={160} borderRadius={12} style={styles.mb16} />
      {/* Section label */}
      <SkeletonBone width="35%" height={16} style={styles.mb12} />
      {/* 2-column category cards — 3 rows */}
      {[0, 1, 2].map((row) => (
        <View key={row} style={[styles.gridRow, styles.mb12]}>
          <CategoryCardSkeleton />
          <CategoryCardSkeleton />
        </View>
      ))}
    </View>
  );
}

/** Single category card skeleton */
function CategoryCardSkeleton() {
  return (
    <View style={styles.categoryCard}>
      <SkeletonBone height={80} borderRadius={10} style={styles.mb8} />
      <SkeletonBone width="70%" height={13} style={styles.mb6} />
      <SkeletonBone width="45%" height={11} />
    </View>
  );
}

/** Static content page skeleton — title + 3 sections */
export function ContentPageSkeleton() {
  return (
    <View style={styles.container}>
      {/* Brand logo + Title area */}
      <View style={[styles.summaryBox, { alignItems: 'center', marginBottom: 16 }]}>
        <SkeletonBone width={72} height={72} borderRadius={20} style={styles.mb12} />
        <SkeletonBone width="55%" height={20} style={styles.mb8} />
        <SkeletonBone width="40%" height={14} />
      </View>
      
      {/* Sections */}
      {[0, 1, 2].map((i) => (
        <View key={i} style={[styles.summaryBox, styles.mb12]}>
          <SkeletonBone width="35%" height={16} style={styles.mb12} />
          <SkeletonBone height={12} style={styles.mb8} />
          <SkeletonBone height={12} style={styles.mb8} />
          <SkeletonBone width="80%" height={12} />
        </View>
      ))}
    </View>
  );
}

/** Brands screen skeleton — search bar + 3-column grid */
export function BrandsScreenSkeleton() {
  return (
    <View style={styles.container}>
      {/* Search area placeholder */}
      <SkeletonBone height={48} borderRadius={12} style={styles.mb16} />
      
      {/* 3-column grid — 4 rows */}
      {[0, 1, 2, 3].map((row) => (
        <View key={row} style={[styles.gridRow, styles.mb12]}>
          <BrandCardSkeleton />
          <BrandCardSkeleton />
          <BrandCardSkeleton />
        </View>
      ))}
    </View>
  );
}

function BrandCardSkeleton() {
  return (
    <View style={[styles.gridCard, { alignItems: 'center' }]}>
      <SkeletonBone width={50} height={50} borderRadius={25} style={styles.mb8} />
      <SkeletonBone width="70%" height={10} />
    </View>
  );
}

/** Wishlist screen skeleton — image grid of wishlist cards */
export function WishlistScreenSkeleton() {
  return (
    <View style={styles.container}>
      {/* Header area */}
      <SkeletonBone width="40%" height={22} style={styles.mb16} />
      {/* 2-column grid of wishlist item cards */}
      {[0, 1, 2].map((row) => (
        <View key={row} style={[styles.gridRow, styles.mb12]}>
          <WishlistCardSkeleton />
          <WishlistCardSkeleton />
        </View>
      ))}
    </View>
  );
}

function WishlistCardSkeleton() {
  return (
    <View style={styles.gridCard}>
      <SkeletonBone height={130} borderRadius={10} style={styles.mb8} />
      <SkeletonBone width="85%" height={13} style={styles.mb6} />
      <SkeletonBone width="55%" height={13} style={styles.mb6} />
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <SkeletonBone width="40%" height={18} />
        <SkeletonBone width={32} height={32} borderRadius={16} />
      </View>
    </View>
  );
}

/** Profile tab skeleton — avatar + menu list items */
export function ProfileScreenSkeleton() {
  return (
    <View style={styles.container}>
      {/* Avatar + name */}
      <View style={[styles.summaryBox, { alignItems: 'center', marginBottom: 20 }]}>
        <SkeletonBone width={72} height={72} borderRadius={36} style={styles.mb12} />
        <SkeletonBone width="45%" height={18} style={styles.mb8} />
        <SkeletonBone width="35%" height={13} />
      </View>
      {/* Menu items */}
      {[0, 1, 2, 3, 4].map((i) => (
        <View key={i} style={[styles.menuItem, styles.mb12]}>
          <SkeletonBone width={40} height={40} borderRadius={12} />
          <View style={{ flex: 1, marginLeft: 12 }}>
            <SkeletonBone width="55%" height={14} style={styles.mb6} />
            <SkeletonBone width="38%" height={11} />
          </View>
          <SkeletonBone width={20} height={20} borderRadius={10} />
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#FAFAFA' },
  bone: { backgroundColor: '#E8E8E8', overflow: 'hidden' },
  row: { flexDirection: 'row', gap: 10 },
  productCard: { flex: 1, backgroundColor: '#fff', borderRadius: 12, padding: 8 },
  padded: { paddingHorizontal: 20 },
  chipRow: { flexDirection: 'row', gap: 8 },
  chip: { marginRight: 0 },
  cartRow: { flexDirection: 'row', gap: 12, backgroundColor: '#fff', borderRadius: 12, padding: 12 },
  cartDetails: { flex: 1, justifyContent: 'center' },
  summaryBox: { backgroundColor: '#fff', borderRadius: 14, padding: 16 },
  orderCard: { backgroundColor: '#fff', borderRadius: 14, padding: 16 },
  orderHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  filterRow: { flexDirection: 'row', gap: 8, marginBottom: 16, flexWrap: 'wrap' },
  gridRow: { flexDirection: 'row', gap: 12 },
  gridCard: { flex: 1, backgroundColor: '#fff', borderRadius: 14, padding: 10 },
  categoryCard: { flex: 1, backgroundColor: '#fff', borderRadius: 14, padding: 10 },
  menuItem: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#fff', borderRadius: 14, padding: 14 },
  mb6: { marginBottom: 6 },
  mb8: { marginBottom: 8 },
  mb10: { marginBottom: 10 },
  mb12: { marginBottom: 12 },
  mb16: { marginBottom: 16 },
  mt8: { marginTop: 8 },
  mt16: { marginTop: 16 },
});
