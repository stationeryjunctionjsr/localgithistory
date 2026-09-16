import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  LayoutAnimation,
  Platform,
  UIManager,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, shadows } from '../src/theme';
import { ContentPageSkeleton } from '../src/components/SkeletonLoader';
import api from '../src/api/client';
import { useLanguage } from '../src/context/LanguageContext';

if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

interface FAQItem {
  question: string;
  answer: string;
}

interface FAQSection {
  _id?: string;
  title: string;
  icon: string;
  items: FAQItem[];
}

const FALLBACK_SECTIONS: FAQSection[] = [
  {
    title: 'Orders & Delivery',
    icon: 'cube-outline',
    items: [
      { question: 'How do I place an order?', answer: 'Browse products, add items to your cart, and proceed to checkout. You can choose your delivery address and preferred payment method to complete your order.' },
      { question: 'How can I track my order?', answer: 'Go to "My Orders" from your profile. Tap on any order to view its current status and tracking details.' },
    ],
  },
  {
    title: 'Payments',
    icon: 'card-outline',
    items: [
      { question: 'What payment methods are accepted?', answer: 'We accept UPI, credit/debit cards, net banking, cash on delivery (COD), and credit-based payment for approved wholesalers.' },
    ],
  },
  {
    title: 'Account',
    icon: 'person-outline',
    items: [
      { question: 'How do I create an account?', answer: 'Tap "Create Account" on the login screen. Enter your name, email, phone number, and password.' },
      { question: 'I forgot my password. What do I do?', answer: 'On the login screen, tap "Forgot Password" and enter your registered email or phone.' },
    ],
  },
];

const FAQAccordion = ({ item, expanded, onToggle }: { item: FAQItem; expanded: boolean; onToggle: () => void }) => (
  <TouchableOpacity style={styles.faqItem} onPress={onToggle} activeOpacity={0.7}>
    <View style={styles.faqQuestion}>
      <Text style={styles.faqQuestionText}>{item.question}</Text>
      <Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={18} color={colors.textSecondary} />
    </View>
    {expanded && <Text style={styles.faqAnswer}>{item.answer}</Text>}
  </TouchableOpacity>
);

export default function FAQ() {
  const router = useRouter();
  const { t } = useLanguage();
  const [sections, setSections] = useState<FAQSection[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedKey, setExpandedKey] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchFAQs();
  }, []);

  const fetchFAQs = async () => {
    try {
      setLoading(true);
      const res = await api.get('/content/faq/public');
      if (res.data && res.data.length > 0) {
        setSections(res.data);
      }
    } catch (err) {
      if (__DEV__) console.warn('Failed to fetch FAQs, using fallback', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleItem = (id: string) => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setExpandedKey(expandedKey === id ? null : id);
  };

  const trimmedQuery = searchQuery.trim().toLowerCase();

  const filteredSections = trimmedQuery
    ? sections
        .map((section) => ({
          ...section,
          items: section.items.filter(
            (item) =>
              item.question.toLowerCase().includes(trimmedQuery) ||
              item.answer.toLowerCase().includes(trimmedQuery)
          ),
        }))
        .filter((section) => section.items.length > 0)
    : sections;

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={[styles.header, shadows.sm]}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={20} color={colors.textPrimary} />
        </TouchableOpacity>
        <Ionicons name="help-circle" size={24} color={colors.primary} />
        <Text style={styles.headerTitle}>{t('pages.faq.title', 'FAQs')}</Text>
        <View style={{ width: 40 }} />
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <View style={[styles.searchBar, shadows.sm]}>
          <Ionicons name="search" size={18} color={colors.textMuted} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search FAQs..."
            placeholderTextColor={colors.textMuted}
            value={searchQuery}
            onChangeText={setSearchQuery}
            autoCapitalize="none"
            returnKeyType="search"
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <Ionicons name="close-circle" size={18} color={colors.textMuted} />
            </TouchableOpacity>
          )}
        </View>
      </View>

      {loading ? (
        <ContentPageSkeleton />
      ) : (
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          {trimmedQuery && filteredSections.length === 0 ? (
            <View style={styles.emptySearch}>
              <Ionicons name="search-outline" size={40} color={colors.neutral[300]} />
              <Text style={styles.emptySearchTitle}>No results found</Text>
              <Text style={styles.emptySearchSubtitle}>Try a different search term</Text>
            </View>
          ) : (
            filteredSections.map((section, sIdx) => (
              <View key={section._id || sIdx} style={[styles.section, shadows.sm]}>
                <View style={styles.sectionHeader}>
                  <Ionicons name={section.icon as any} size={20} color={colors.primary} />
                  <Text style={styles.sectionTitle}>{section.title}</Text>
                </View>
                {section.items.map((item, iIdx) => {
                  const key = `${sIdx}-${iIdx}`;
                  return (
                    <React.Fragment key={key}>
                      {iIdx > 0 && <View style={styles.divider} />}
                      <FAQAccordion item={item} expanded={expandedKey === key} onToggle={() => toggleItem(key)} />
                    </React.Fragment>
                  );
                })}
              </View>
            ))
          )}

          <View style={styles.contactBanner}>
            <Ionicons name="chatbubbles-outline" size={24} color={colors.primary} />
            <Text style={styles.contactText}>Still have questions?</Text>
            <TouchableOpacity style={styles.contactButton} onPress={() => router.push('/support')}>
              <Text style={styles.contactButtonText}>Contact Support</Text>
            </TouchableOpacity>
          </View>

          <View style={{ height: 32 }} />
        </ScrollView>
      )}
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
  searchContainer: { paddingHorizontal: 16, paddingVertical: 12 },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
    gap: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 15,
    color: colors.textPrimary,
    paddingVertical: 0,
  },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  scrollContent: { paddingHorizontal: 16, paddingBottom: 16 },
  emptySearch: { alignItems: 'center', paddingVertical: 48 },
  emptySearchTitle: { fontSize: 16, fontWeight: '600', color: colors.textPrimary, marginTop: 12 },
  emptySearchSubtitle: { fontSize: 14, color: colors.textSecondary, marginTop: 4 },
  section: {
    backgroundColor: colors.surface,
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: colors.textPrimary },
  divider: { height: 1, backgroundColor: colors.border, marginVertical: 2 },
  faqItem: { paddingVertical: 12 },
  faqQuestion: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  faqQuestionText: {
    flex: 1,
    fontSize: 14,
    fontWeight: '600',
    color: colors.textPrimary,
    marginRight: 12,
  },
  faqAnswer: {
    fontSize: 13,
    color: colors.textSecondary,
    lineHeight: 20,
    marginTop: 10,
  },
  contactBanner: { alignItems: 'center', paddingVertical: 28, gap: 8 },
  contactText: { fontSize: 15, fontWeight: '600', color: colors.textPrimary },
  contactButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
    marginTop: 4,
  },
  contactButtonText: { color: colors.surface, fontWeight: '600', fontSize: 14 },
});
