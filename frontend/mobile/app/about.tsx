import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Linking,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, shadows } from '../src/theme';
import api from '../src/api/client';

interface AboutData {
  brandName: string;
  tagline: string;
  mission: string;
  offerings: string[];
  contactEmail: string;
  contactWebsite: string;
  sections: { title: string; body: string }[];
}

const FALLBACK: AboutData = {
  brandName: 'Stationery Junction',
  tagline: 'Premium Stationery at Wholesale Prices',
  mission:
    'Stationery Junction is your one-stop destination for premium stationery products. We connect wholesalers and retail customers with the finest stationery brands, offering competitive pricing and a seamless shopping experience.',
  offerings: [
    'Wide range of premium stationery products from top brands',
    'Competitive wholesale and retail pricing',
    'Dedicated wholesaler accounts with credit facilities',
    'Fast and reliable delivery across India',
    'Responsive customer support',
  ],
  contactEmail: 'support@stationeryjunction.com',
  contactWebsite: 'https://www.stationeryjunction.com',
  sections: [],
};

const InfoRow = ({ icon, label, value, onPress }: { icon: string; label: string; value: string; onPress?: () => void }) => (
  <TouchableOpacity style={styles.infoRow} disabled={!onPress} onPress={onPress} activeOpacity={onPress ? 0.7 : 1}>
    <View style={styles.infoIcon}>
      <Ionicons name={icon as any} size={18} color={colors.primary} />
    </View>
    <View style={{ flex: 1 }}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={[styles.infoValue, onPress && styles.infoValueLink]}>{value}</Text>
    </View>
    {onPress && <Ionicons name="open-outline" size={16} color={colors.textMuted} />}
  </TouchableOpacity>
);

import { ContentPageSkeleton } from '../src/components/SkeletonLoader';

export default function About() {
  const router = useRouter();
  const [data, setData] = useState<AboutData>(FALLBACK);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get('/content/about/public')
      .then((res) => {
        if (res.data && Object.keys(res.data).length > 0) {
          setData({ ...FALLBACK, ...res.data });
        }
      })
      .catch((err) => {
        if (__DEV__) console.warn('[about] API fetch failed', err);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={20} color={colors.textPrimary} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>About Us</Text>
          <View style={{ width: 40 }} />
        </View>
        <ContentPageSkeleton />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={[styles.header, shadows.sm]}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={20} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>About Us</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Brand */}
        <View style={[styles.brandSection, shadows.sm]}>
          <View style={styles.logoContainer}>
            <Ionicons name="storefront" size={36} color={colors.primary} />
          </View>
          <Text style={styles.brandName}>{data.brandName}</Text>
          <Text style={styles.brandTagline}>{data.tagline}</Text>
        </View>

        {/* Mission */}
        {data.mission ? (
          <View style={[styles.section, shadows.sm]}>
            <View style={styles.sectionHeader}>
              <Ionicons name="flag-outline" size={20} color={colors.primary} />
              <Text style={styles.sectionTitle}>Our Mission</Text>
            </View>
            <Text style={styles.sectionBody}>{data.mission}</Text>
          </View>
        ) : null}

        {/* Offerings */}
        {data.offerings.length > 0 && (
          <View style={[styles.section, shadows.sm]}>
            <View style={styles.sectionHeader}>
              <Ionicons name="sparkles-outline" size={20} color={colors.primary} />
              <Text style={styles.sectionTitle}>What We Offer</Text>
            </View>
            {data.offerings.map((text, idx) => (
              <View key={idx} style={styles.offerItem}>
                <Ionicons name="checkmark-circle-outline" size={18} color={colors.primary} />
                <Text style={styles.offerText}>{text}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Dynamic sections from admin */}
        {data.sections.map((section, idx) => (
          <View key={idx} style={[styles.section, shadows.sm]}>
            <View style={styles.sectionHeader}>
              <Ionicons name="document-text-outline" size={20} color={colors.primary} />
              <Text style={styles.sectionTitle}>{section.title}</Text>
            </View>
            <Text style={styles.sectionBody}>{section.body}</Text>
          </View>
        ))}

        {/* Contact */}
        <View style={[styles.section, shadows.sm]}>
          <View style={styles.sectionHeader}>
            <Ionicons name="call-outline" size={20} color={colors.primary} />
            <Text style={styles.sectionTitle}>Contact Us</Text>
          </View>
          {data.contactWebsite ? (
            <InfoRow
              icon="globe-outline"
              label="Website"
              value={data.contactWebsite.replace(/^https?:\/\//, '')}
              onPress={() => Linking.openURL(data.contactWebsite)}
            />
          ) : null}
          {data.contactEmail ? (
            <InfoRow
              icon="mail-outline"
              label="Email"
              value={data.contactEmail}
              onPress={() => Linking.openURL(`mailto:${data.contactEmail}`)}
            />
          ) : null}
          <InfoRow
            icon="headset-outline"
            label="Support"
            value="Reach out for any help"
            onPress={() => router.push('/support')}
          />
        </View>

        {/* Links */}
        <View style={[styles.section, shadows.sm]}>
          <TouchableOpacity style={styles.linkRow} onPress={() => router.push('/privacy-policy')}>
            <Ionicons name="shield-checkmark-outline" size={18} color={colors.primary} />
            <Text style={styles.linkText}>Privacy Policy</Text>
            <Ionicons name="chevron-forward" size={16} color={colors.textMuted} />
          </TouchableOpacity>
          <View style={styles.divider} />
          <TouchableOpacity style={styles.linkRow} onPress={() => router.push('/faq')}>
            <Ionicons name="help-circle-outline" size={18} color={colors.primary} />
            <Text style={styles.linkText}>FAQs</Text>
            <Ionicons name="chevron-forward" size={16} color={colors.textMuted} />
          </TouchableOpacity>
        </View>

        <View style={styles.versionContainer}>
          <Text style={styles.versionText}>{data.brandName} v1.0.0</Text>
          <Text style={styles.versionSubtext}>Made with care in India</Text>
        </View>

        <View style={{ height: 32 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.backgroundAlt },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: colors.neutral[100],
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: { fontSize: 18, fontWeight: '700', color: colors.textPrimary },
  scrollContent: { padding: 16 },
  brandSection: {
    backgroundColor: colors.surface,
    borderRadius: 16,
    padding: 28,
    alignItems: 'center',
    marginBottom: 16,
  },
  logoContainer: {
    width: 72,
    height: 72,
    borderRadius: 20,
    backgroundColor: colors.backgroundAlt,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 14,
  },
  brandName: { fontSize: 22, fontWeight: '700', color: colors.textPrimary, marginBottom: 4 },
  brandTagline: { fontSize: 14, color: colors.textSecondary },
  section: {
    backgroundColor: colors.surface,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 14 },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: colors.textPrimary },
  sectionBody: { fontSize: 14, color: colors.textSecondary, lineHeight: 22 },
  offerItem: { flexDirection: 'row', alignItems: 'flex-start', gap: 10, marginBottom: 12 },
  offerText: { flex: 1, fontSize: 14, color: colors.textSecondary, lineHeight: 20 },
  infoRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10, gap: 12 },
  infoIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: colors.backgroundAlt,
    alignItems: 'center',
    justifyContent: 'center',
  },
  infoLabel: { fontSize: 12, color: colors.textMuted, marginBottom: 2 },
  infoValue: { fontSize: 14, color: colors.textPrimary, fontWeight: '500' },
  infoValueLink: { color: colors.primary },
  linkRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 14, gap: 10 },
  linkText: { flex: 1, fontSize: 15, fontWeight: '500', color: colors.textPrimary },
  divider: { height: 1, backgroundColor: colors.border },
  versionContainer: { alignItems: 'center', paddingVertical: 24 },
  versionText: { fontSize: 13, color: colors.textMuted, fontWeight: '500' },
  versionSubtext: { fontSize: 12, color: colors.textMuted, marginTop: 2 },
});
