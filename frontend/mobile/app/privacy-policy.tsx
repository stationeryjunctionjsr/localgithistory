import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, shadows } from '../src/theme';
import { ContentPageSkeleton } from '../src/components/SkeletonLoader';
import api from '../src/api/client';

interface PolicySection {
  title: string;
  body: string;
}

interface PrivacyData {
  lastUpdated: string;
  sections: PolicySection[];
}

const FALLBACK: PrivacyData = {
  lastUpdated: 'April 2026',
  sections: [
    { title: '1. Information We Collect', body: 'When you use Stationery Junction, we may collect personal details (name, email, phone), business details for wholesaler accounts, delivery addresses, order history, and device/usage analytics.' },
    { title: '2. How We Use Your Information', body: 'We use your information to process orders, manage your account, send order updates, improve our services, and comply with legal obligations.' },
    { title: '3. Information Sharing', body: 'We do not sell your personal information. We may share data with delivery partners, payment processors, and law enforcement when required.' },
    { title: '4. Data Security', body: 'We implement industry-standard security measures including encrypted transmission and secure storage. No method is 100% secure.' },
    { title: '5. Your Rights', body: 'You can access and update your personal information, request account deletion, and opt out of promotional communications.' },
    { title: '6. Changes to This Policy', body: 'We may update this policy from time to time. Continued use after changes constitutes acceptance.' },
    { title: '7. Contact Us', body: 'For questions about this Privacy Policy, contact us through Customer Support or email support@stationeryjunction.com.' },
  ],
};

const Section = ({ title, body }: { title: string; body: string }) => (
  <View style={styles.section}>
    <Text style={styles.sectionTitle}>{title}</Text>
    <Text style={styles.paragraph}>{body}</Text>
  </View>
);

export default function PrivacyPolicy() {
  const router = useRouter();
  const [data, setData] = useState<PrivacyData>(FALLBACK);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get('/content/privacy/public')
      .then((res) => {
        if (res.data && res.data.sections && res.data.sections.length > 0) {
          setData({ ...FALLBACK, ...res.data });
        }
      })
      .catch((err) => {
        if (__DEV__) console.warn('[privacy-policy] API fetch failed', err);
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
          <Ionicons name="shield-checkmark" size={24} color={colors.primary} />
          <Text style={styles.headerTitle}>Privacy Policy</Text>
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
        <Ionicons name="shield-checkmark" size={24} color={colors.primary} />
        <Text style={styles.headerTitle}>Privacy Policy</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <Text style={styles.lastUpdated}>Last updated: {data.lastUpdated}</Text>

        <View style={[styles.card, shadows.sm]}>
          {data.sections.map((section, idx) => (
            <Section key={idx} title={section.title} body={section.body} />
          ))}
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
    paddingHorizontal: 16,
    paddingVertical: 14,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    gap: 10,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: colors.neutral[100],
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: { flex: 1, fontSize: 18, fontWeight: '700', color: colors.textPrimary },
  scrollContent: { padding: 16 },
  lastUpdated: { fontSize: 13, color: colors.textMuted, marginBottom: 16, paddingHorizontal: 4 },
  card: { backgroundColor: colors.surface, borderRadius: 16, padding: 20 },
  section: { marginBottom: 24 },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: colors.textPrimary, marginBottom: 10 },
  paragraph: { fontSize: 14, color: colors.textSecondary, lineHeight: 22 },
});
