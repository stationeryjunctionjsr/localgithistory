import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Switch,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, shadows, borderRadius } from '../src/theme';
import { useLanguage } from '../src/context/LanguageContext';
import { LanguageSwitcher } from '../src/components/LanguageSwitcher';

export default function Accessibility() {
  const router = useRouter();
  const { t, locale } = useLanguage();
  const [largeText, setLargeText] = useState(false);
  const [highContrast, setHighContrast] = useState(false);
  const [reduceMotion, setReduceMotion] = useState(false);
  const [showLanguageSwitcher, setShowLanguageSwitcher] = useState(false);

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        >
          <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t('accessibility.settings', 'Accessibility Settings')}</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Text style={styles.sectionSubtitle}>
          {t('accessibility.settingsDesc', 'Customize your display and interaction settings for a better viewing experience.')}
        </Text>

        <View style={[styles.card, shadows.sm]}>
          {/* Large Text */}
          <View style={styles.settingItem}>
            <View style={styles.settingTextContainer}>
              <Text style={styles.settingTitle}>{t('accessibility.largeText', 'Large Text Mode')}</Text>
              <Text style={styles.settingDescription}>{t('accessibility.largeTextDesc', 'Increase font size across the app.')}</Text>
            </View>
            <Switch
              value={largeText}
              onValueChange={setLargeText}
              trackColor={{ false: colors.neutral[200], true: colors.primary }}
            />
          </View>

          <View style={styles.divider} />

          {/* High Contrast */}
          <View style={styles.settingItem}>
            <View style={styles.settingTextContainer}>
              <Text style={styles.settingTitle}>{t('accessibility.highContrast', 'High Contrast')}</Text>
              <Text style={styles.settingDescription}>{t('accessibility.highContrastDesc', 'Enhance text and border contrast for clearer visibility.')}</Text>
            </View>
            <Switch
              value={highContrast}
              onValueChange={setHighContrast}
              trackColor={{ false: colors.neutral[200], true: colors.primary }}
            />
          </View>

          <View style={styles.divider} />

          {/* Reduce Motion */}
          <View style={styles.settingItem}>
            <View style={styles.settingTextContainer}>
              <Text style={styles.settingTitle}>{t('accessibility.reduceMotion', 'Reduce Motion')}</Text>
              <Text style={styles.settingDescription}>{t('accessibility.reduceMotionDesc', 'Minimize animations and transitions throughout the app.')}</Text>
            </View>
            <Switch
              value={reduceMotion}
              onValueChange={setReduceMotion}
              trackColor={{ false: colors.neutral[200], true: colors.primary }}
            />
          </View>

          <View style={styles.divider} />

          {/* Language */}
          <TouchableOpacity
            style={styles.settingItem}
            onPress={() => setShowLanguageSwitcher(true)}
            activeOpacity={0.7}
          >
            <View style={styles.settingTextContainer}>
              <Text style={styles.settingTitle}>{t('accessibility.language', 'Language')}</Text>
              <Text style={styles.settingDescription}>
                {t('accessibility.languageDesc', 'Choose your preferred language.')}
                {' — '}
                <Text style={{ color: colors.primary, fontWeight: '600' }}>
                  {t(`lang.${locale}`, locale.toUpperCase())}
                </Text>
              </Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color={colors.neutral[300]} />
          </TouchableOpacity>
        </View>

        {/* Screen Reader info card */}
        <View style={[styles.infoCard, shadows.sm]}>
          <Ionicons name="information-circle-outline" size={24} color={colors.primary} style={{ marginRight: 12 }} />
          <View style={{ flex: 1 }}>
            <Text style={styles.infoTitle}>{t('accessibility.screenReader', 'Screen Reader Support')}</Text>
            <Text style={styles.infoBody}>
              {t('accessibility.screenReaderDesc', 'This app is compatible with system screen readers (TalkBack / VoiceOver). Enable them in your device settings for full audio navigation.')}
            </Text>
          </View>
        </View>
      </ScrollView>

      {/* Language Switcher Modal */}
      <LanguageSwitcher
        visible={showLanguageSwitcher}
        onClose={() => setShowLanguageSwitcher(false)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.backgroundAlt,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: colors.surface,
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  backButton: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  content: {
    padding: 16,
  },
  sectionSubtitle: {
    fontSize: 14,
    color: colors.textMuted,
    marginBottom: 16,
    lineHeight: 20,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    paddingHorizontal: 16,
    marginBottom: 20,
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 16,
  },
  settingTextContainer: {
    flex: 1,
    marginRight: 16,
  },
  settingTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 4,
  },
  settingDescription: {
    fontSize: 12,
    color: colors.textMuted,
    lineHeight: 16,
  },
  divider: {
    height: 1,
    backgroundColor: colors.border,
  },
  infoCard: {
    flexDirection: 'row',
    backgroundColor: '#E8F5E9',
    borderRadius: borderRadius.lg,
    padding: 16,
    alignItems: 'flex-start',
  },
  infoTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.primary,
    marginBottom: 4,
  },
  infoBody: {
    fontSize: 12,
    color: colors.success,
    lineHeight: 18,
  },
});
