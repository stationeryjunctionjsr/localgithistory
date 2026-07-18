import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Modal,
  Pressable,
  StyleSheet,
  StatusBar,
  ScrollView,
  Share,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as Clipboard from 'expo-clipboard';
import Toast from 'react-native-toast-message';
import api from '../../src/api/client';
import { GeneralFeedbackModal } from '../../src/components/GeneralFeedbackModal';
import { useAuth } from '../../src/hooks/useAuth';
import { colors, shadows, borderRadius } from '../../src/theme';
import { ProfileScreenSkeleton } from '../../src/components/SkeletonLoader';

export default function Profile() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const [showMenu, setShowMenu] = useState(true);
  const [guestDismissed, setGuestDismissed] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);

  const [hasDeliveredOrder, setHasDeliveredOrder] = useState(false);
  const [referralScheme, setReferralScheme] = useState<any>(null);

  useEffect(() => {
    if (user && user.role === 'customer') {
      const fetchReferralData = async () => {
        try {
          const [ordersRes, schemeRes] = await Promise.all([
            api.get('/orders', { params: { limit: 1, status: 'delivered' } }),
            api.get('/referrals/scheme'),
          ]);
          setHasDeliveredOrder(ordersRes.data?.orders?.length > 0);
          setReferralScheme(schemeRes.data);
        } catch (error) {
          console.error('Failed to fetch referral data:', error);
        }
      };
      fetchReferralData();
    }
  }, [user]);

  const MenuItem = ({
    icon,
    label,
    subtitle,
    onPress,
    iconBg = colors.backgroundAlt,
    iconColor = colors.primary,
    showArrow = true,
  }: {
    icon: string;
    label: string;
    subtitle?: string;
    onPress: () => void;
    iconBg?: string;
    iconColor?: string;
    showArrow?: boolean;
  }) => (
    <TouchableOpacity style={styles.menuItem} onPress={onPress} activeOpacity={0.7}>
      <View style={[styles.menuIconContainer, { backgroundColor: iconBg }]}>
        <Ionicons name={icon as any} size={20} color={iconColor} />
      </View>
      <View style={styles.menuItemContent}>
        <Text style={styles.menuLabel}>{label}</Text>
        {subtitle && <Text style={styles.menuSubtitle}>{subtitle}</Text>}
      </View>
      {showArrow && <Ionicons name="chevron-forward" size={18} color={colors.neutral[300]} />}
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="dark-content" backgroundColor={colors.surface} />

      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Profile</Text>
      </View>

      {loading ? (
        <ProfileScreenSkeleton />
      ) : user ? (
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* User Card */}
          <View style={[styles.userCard, shadows.card]}>
            <View style={styles.userCardGradient}>
              <View style={styles.userAvatarContainer}>
                <View style={styles.userAvatar}>
                  <Text style={styles.userAvatarText}>{(user.name || 'U')[0].toUpperCase()}</Text>
                </View>
              </View>
              <View style={styles.userInfo}>
                <Text style={styles.userName}>{user.name || 'User'}</Text>
                <Text style={styles.userEmail}>{user.email}</Text>
              </View>
              <TouchableOpacity style={styles.editButton} onPress={() => router.push('/edit-profile')}>
                <Ionicons name="create-outline" size={18} color={colors.surface} />
              </TouchableOpacity>
            </View>
          </View>

          {/* Referral Card */}
          {user.role === 'customer' && hasDeliveredOrder && referralScheme && (
            <View style={[styles.referralCard, shadows.sm]}>
              <View style={styles.referralHeader}>
                <View style={styles.referralIconContainer}>
                  <Ionicons name="gift-outline" size={20} color="#8b5cf6" />
                </View>
                <Text style={styles.referralTitle}>Refer & Earn</Text>
              </View>
              <Text style={styles.referralDesc}>
                Share your code and earn ₹{referralScheme.referrerRewardAmount} when a friend makes their first order!
              </Text>
              
              <View style={styles.referralCodeBox}>
                <Text style={styles.referralCodeText}>{user.referralCode}</Text>
                <View style={styles.referralActions}>
                  <TouchableOpacity 
                    style={styles.referralActionBtn}
                    onPress={async () => {
                      await Clipboard.setStringAsync(user.referralCode || '');
                      Toast.show({ type: 'success', text1: 'Copied!', text2: 'Referral code copied to clipboard.' });
                    }}
                  >
                    <Ionicons name="copy-outline" size={20} color={colors.primary} />
                  </TouchableOpacity>
                  <TouchableOpacity 
                    style={styles.referralActionBtn}
                    onPress={async () => {
                      try {
                        await Share.share({
                          message: `Use my referral code ${user.referralCode} to get a discount on your first order!`,
                        });
                      } catch (e) {}
                    }}
                  >
                    <Ionicons name="share-social-outline" size={20} color={colors.primary} />
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          )}

          {/* Quick Actions */}
          <View style={styles.quickActions}>
            <TouchableOpacity
              style={[styles.quickAction, shadows.sm]}
              onPress={() => router.push('/orders')}
            >
              <View style={[styles.quickActionIcon, { backgroundColor: '#E8F5E9' }]}>
                <Ionicons name="receipt-outline" size={22} color="#43A047" />
              </View>
              <Text style={styles.quickActionLabel}>Orders</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.quickAction, shadows.sm]}
              onPress={() => router.push('/wishlist')}
            >
              <View style={[styles.quickActionIcon, { backgroundColor: '#FCE4EC' }]}>
                <Ionicons name="heart-outline" size={22} color="#E91E63" />
              </View>
              <Text style={styles.quickActionLabel}>Wishlist</Text>
            </TouchableOpacity>

          </View>

          {/* Menu Section */}
          <View style={[styles.menuSection, shadows.sm]}>
            <MenuItem
              icon="location-outline"
              label="Addresses"
              subtitle="Manage delivery addresses"
              onPress={() => router.push('/addresses')}
              iconBg="#FFF8E1"
              iconColor="#FF8F00"
            />
            {user.role === 'customer' && (
              <>
                <View style={styles.menuDivider} />
                <MenuItem
                  icon="arrow-undo-outline"
                  label="My Returns"
                  subtitle="Track return and refund requests"
                  onPress={() => router.push('/returns')}
                  iconBg="#FEE2E2"
                  iconColor="#EF4444"
                />
              </>
            )}
            {user.role === 'wholesaler' && (
              <>
                <View style={styles.menuDivider} />
                <MenuItem
                  icon="pricetags-outline"
                  label="Discount Schemes"
                  subtitle="Exclusive offers for your business"
                  onPress={() => router.push('/schemes')}
                  iconBg="#FCE4EC"
                  iconColor="#E91E63"
                />
              </>
            )}
            <View style={styles.menuDivider} />
            <MenuItem
              icon="headset-outline"
              label="Customer Support"
              subtitle="Get help with your orders"
              onPress={() => router.push('/support')}
              iconBg="#E8F5E9"
              iconColor="#43A047"
            />
            <View style={styles.menuDivider} />
            <MenuItem
              icon="help-circle-outline"
              label="FAQs"
              subtitle="Frequently asked questions"
              onPress={() => router.push('/faq')}
              iconBg="#E3F2FD"
              iconColor="#1976D2"
            />
            <View style={styles.menuDivider} />
            <MenuItem
              icon="information-circle-outline"
              label="About Us"
              onPress={() => router.push('/about')}
              iconBg="#FFF8E1"
              iconColor="#FF8F00"
            />
            <View style={styles.menuDivider} />
            <MenuItem
              icon="shield-checkmark-outline"
              label="Privacy Policy"
              onPress={() => router.push('/privacy-policy')}
              iconBg="#F3E5F5"
              iconColor="#8E24AA"
            />
            <View style={styles.menuDivider} />
            <MenuItem
              icon="chatbubble-ellipses-outline"
              label="Give Feedback"
              subtitle="Help us improve your experience"
              onPress={() => setShowFeedback(true)}
              iconBg="#E0F2F1"
              iconColor="#00897B"
            />
          </View>

          {/* Feedback Modal */}
          <GeneralFeedbackModal visible={showFeedback} onClose={() => setShowFeedback(false)} />

          {/* Logout Button */}
          <TouchableOpacity style={styles.logoutButton} onPress={logout}>
            <Ionicons name="log-out-outline" size={18} color={colors.error} />
            <Text style={styles.logoutText}>Sign Out</Text>
          </TouchableOpacity>

          {/* App Info */}
          <View style={styles.appInfo}>
            <Text style={styles.appInfoText}>Stationery Junction v1.0.0</Text>
          </View>
        </ScrollView>
      ) : (
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.guestContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Guest Welcome */}
          <View style={styles.guestWelcome}>
            <View style={styles.guestIconContainer}>
              <Ionicons name="person-outline" size={40} color={colors.neutral[300]} />
            </View>
            <Text style={styles.guestTitle}>Welcome to Stationery Junction</Text>
            <Text style={styles.guestSubtitle}>
              Sign in to access your orders, wishlist, and more
            </Text>
          </View>

          {/* Guest Menu */}
          <View style={[styles.menuSection, shadows.sm]}>
            <MenuItem
              icon="headset-outline"
              label="Customer Support"
              onPress={() => router.push('/support')}
              iconBg="#E8F5E9"
              iconColor="#43A047"
            />
            <View style={styles.menuDivider} />
            <MenuItem
              icon="help-circle-outline"
              label="FAQs"
              onPress={() => router.push('/faq')}
              iconBg="#E3F2FD"
              iconColor="#1976D2"
            />
            <View style={styles.menuDivider} />
            <MenuItem
              icon="information-circle-outline"
              label="About Us"
              onPress={() => router.push('/about')}
              iconBg="#FFF8E1"
              iconColor="#FF8F00"
            />
            <View style={styles.menuDivider} />
            <MenuItem
              icon="shield-checkmark-outline"
              label="Privacy Policy"
              onPress={() => router.push('/privacy-policy')}
              iconBg="#F3E5F5"
              iconColor="#8E24AA"
            />
          </View>
        </ScrollView>
      )}

      {/* Bottom Sheet for Guest */}
      <Modal
        visible={!user && showMenu && !guestDismissed}
        transparent
        animationType="slide"
        onRequestClose={() => { setShowMenu(false); setGuestDismissed(true); }}
      >
        <Pressable style={styles.modalBackdrop} onPress={() => { setShowMenu(false); setGuestDismissed(true); }} />
        <View style={styles.bottomSheet}>
          <View style={styles.bottomSheetHandle} />
          <Text style={styles.bottomSheetTitle}>Get Started</Text>
          <Text style={styles.bottomSheetSubtitle}>Sign in or create an account to continue</Text>

          <TouchableOpacity
            style={styles.primaryButton}
            onPress={() => {
              setShowMenu(false);
              router.push('/login');
            }}
            activeOpacity={0.9}
          >
            <View style={styles.primaryButtonGradient}>
              <Text style={styles.primaryButtonText}>Sign In</Text>
            </View>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.secondaryButton}
            onPress={() => {
              setShowMenu(false);
              router.push('/register');
            }}
            activeOpacity={0.8}
          >
            <Text style={styles.secondaryButtonText}>Create Account</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.closeLink} onPress={() => { setShowMenu(false); setGuestDismissed(true); }}>
            <Text style={styles.closeLinkText}>Maybe later</Text>
          </TouchableOpacity>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.backgroundAlt,
  },
  header: {
    backgroundColor: colors.surface,
    paddingHorizontal: 16,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.primary,
    letterSpacing: -0.3,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 40,
  },
  userCard: {
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    marginBottom: 20,
  },
  userCardGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
    backgroundColor: colors.primary,
  },
  userAvatarContainer: {
    marginRight: 16,
  },
  userAvatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255,255,255,0.3)',
  },
  userAvatarText: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.surface,
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.surface,
    marginBottom: 2,
  },
  userEmail: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.8)',
  },
  editButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  quickActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  quickAction: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    padding: 16,
    alignItems: 'center',
    marginHorizontal: 4,
  },
  quickActionIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
  },
  quickActionLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  menuSection: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    paddingVertical: 8,
    marginBottom: 20,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
  },
  menuIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  menuItemContent: {
    flex: 1,
  },
  menuLabel: {
    fontSize: 15,
    fontWeight: '500',
    color: colors.textPrimary,
  },
  menuSubtitle: {
    fontSize: 12,
    color: colors.textMuted,
    marginTop: 2,
  },
  menuDivider: {
    height: 1,
    backgroundColor: colors.border,
    marginHorizontal: 16,
    marginLeft: 70,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    marginBottom: 20,
  },
  logoutText: {
    fontSize: 15,
    fontWeight: '500',
    color: colors.error,
    marginLeft: 8,
  },
  appInfo: {
    alignItems: 'center',
  },
  appInfoText: {
    fontSize: 11,
    color: colors.neutral[300],
  },
  guestContent: {
    padding: 16,
    paddingBottom: 40,
  },
  guestWelcome: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  guestIconContainer: {
    width: 88,
    height: 88,
    borderRadius: 44,
    backgroundColor: colors.neutral[100],
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  guestTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.textPrimary,
    textAlign: 'center',
    marginBottom: 8,
  },
  guestSubtitle: {
    fontSize: 14,
    color: colors.textMuted,
    textAlign: 'center',
    lineHeight: 20,
    paddingHorizontal: 20,
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
  },
  bottomSheet: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: colors.surface,
    borderTopLeftRadius: borderRadius.xxl,
    borderTopRightRadius: borderRadius.xxl,
    padding: 24,
    paddingBottom: 40,
  },
  bottomSheetHandle: {
    width: 40,
    height: 4,
    borderRadius: 2,
    backgroundColor: colors.neutral[200],
    alignSelf: 'center',
    marginBottom: 20,
  },
  bottomSheetTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: 8,
  },
  bottomSheetSubtitle: {
    fontSize: 14,
    color: colors.textMuted,
    marginBottom: 24,
  },
  primaryButton: {
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
    marginBottom: 12,
  },
  primaryButtonGradient: {
    paddingVertical: 16,
    alignItems: 'center',
    backgroundColor: colors.primary,
  },
  primaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.surface,
  },
  secondaryButton: {
    paddingVertical: 16,
    backgroundColor: colors.backgroundAlt,
    borderRadius: borderRadius.lg,
    alignItems: 'center',
    marginBottom: 16,
  },
  secondaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  closeLink: {
    alignItems: 'center',
    paddingVertical: 8,
  },
  closeLinkText: {
    fontSize: 14,
    color: colors.textMuted,
  },
  referralCard: {
    backgroundColor: '#f5f3ff',
    borderRadius: borderRadius.xl,
    padding: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#ede9fe',
  },
  referralHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  referralIconContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#ede9fe',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  referralTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#6d28d9',
  },
  referralDesc: {
    fontSize: 13,
    color: '#5b21b6',
    marginBottom: 16,
    lineHeight: 18,
  },
  referralCodeBox: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#fff',
    borderRadius: borderRadius.lg,
    padding: 12,
    borderWidth: 1,
    borderColor: '#ede9fe',
  },
  referralCodeText: {
    fontSize: 18,
    fontWeight: '800',
    letterSpacing: 2,
    color: '#6d28d9',
  },
  referralActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  referralActionBtn: {
    padding: 6,
    backgroundColor: '#f5f3ff',
    borderRadius: 8,
  },
});
