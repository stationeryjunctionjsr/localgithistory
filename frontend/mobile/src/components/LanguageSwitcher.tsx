import React from 'react';
import {
  Modal,
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SUPPORTED_LOCALES } from '@sj/i18n';
import type { LocaleCode } from '@sj/i18n';
import { useLanguage } from '../context/LanguageContext';
import { colors, shadows, borderRadius } from '../theme';

// ─── Language metadata ────────────────────────────────────────────────────────

interface LangMeta {
  code: LocaleCode;
  native: string;
  english: string;
}

const LANG_META: LangMeta[] = [
  { code: 'en', native: 'English', english: 'English' },
  { code: 'hi', native: 'हिंदी', english: 'Hindi' },
  { code: 'bn', native: 'বাংলা', english: 'Bengali' },
  { code: 'te', native: 'తెలుగు', english: 'Telugu' },
  { code: 'mr', native: 'मराठी', english: 'Marathi' },
  { code: 'ta', native: 'தமிழ்', english: 'Tamil' },
  { code: 'gu', native: 'ગુજરાતી', english: 'Gujarati' },
  { code: 'kn', native: 'ಕನ್ನಡ', english: 'Kannada' },
  { code: 'ml', native: 'മലയാളം', english: 'Malayalam' },
  { code: 'pa', native: 'ਪੰਜਾਬੀ', english: 'Punjabi' },
  { code: 'or', native: 'ଓଡ଼ିଆ', english: 'Odia' },
  { code: 'ur', native: 'اردو', english: 'Urdu' },
];

// Keep same order as SUPPORTED_LOCALES
const LANGUAGES = SUPPORTED_LOCALES.map(
  (code) => LANG_META.find((m) => m.code === code)!
).filter(Boolean);

// ─── Props ───────────────────────────────────────────────────────────────────

interface LanguageSwitcherProps {
  visible: boolean;
  onClose: () => void;
}

// ─── Component ───────────────────────────────────────────────────────────────

export function LanguageSwitcher({ visible, onClose }: LanguageSwitcherProps) {
  const { locale, setLocale, t } = useLanguage();

  const handleSelect = async (code: LocaleCode) => {
    await setLocale(code);
    onClose();
  };

  const renderItem = ({ item }: { item: LangMeta }) => {
    const isActive = item.code === locale;
    return (
      <TouchableOpacity
        style={[styles.langItem, isActive && styles.langItemActive]}
        onPress={() => handleSelect(item.code)}
        activeOpacity={0.7}
        accessibilityRole="button"
        accessibilityLabel={`${item.native} (${item.english})`}
        accessibilityState={{ selected: isActive }}
      >
        <View style={styles.langTextContainer}>
          <Text style={[styles.langNative, isActive && styles.langNativeActive]}>
            {item.native}
          </Text>
          <Text style={[styles.langEnglish, isActive && styles.langEnglishActive]}>
            {item.english}
          </Text>
        </View>
        {isActive && (
          <Ionicons name="checkmark-circle" size={22} color={colors.primary} />
        )}
      </TouchableOpacity>
    );
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent
      onRequestClose={onClose}
      statusBarTranslucent
    >
      <View style={styles.backdrop}>
        <TouchableOpacity style={styles.backdropTouchable} onPress={onClose} activeOpacity={1} />
        <View style={[styles.sheet, shadows.lg]}>
          {/* Handle */}
          <View style={styles.handle} />

          {/* Header */}
          <View style={styles.sheetHeader}>
            <Text style={styles.sheetTitle}>{t('lang.chooseLanguage', 'Choose Language')}</Text>
            <TouchableOpacity onPress={onClose} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
              <Ionicons name="close" size={24} color={colors.textPrimary} />
            </TouchableOpacity>
          </View>

          {/* Language list */}
          <FlatList
            data={LANGUAGES}
            keyExtractor={(item) => item.code}
            renderItem={renderItem}
            ItemSeparatorComponent={() => <View style={styles.separator} />}
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.listContent}
          />
        </View>
      </View>
    </Modal>
  );
}

// ─── Styles ──────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'transparent',
  },
  backdropTouchable: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.45)',
  },
  sheet: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingBottom: 32,
    maxHeight: '80%',
  },
  handle: {
    width: 40,
    height: 4,
    borderRadius: 2,
    backgroundColor: colors.neutral[200],
    alignSelf: 'center',
    marginTop: 12,
    marginBottom: 4,
  },
  sheetHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  sheetTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  listContent: {
    paddingVertical: 8,
  },
  langItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 14,
  },
  langItemActive: {
    backgroundColor: `${colors.primary}10`,
  },
  langTextContainer: {
    flex: 1,
  },
  langNative: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 2,
  },
  langNativeActive: {
    color: colors.primary,
  },
  langEnglish: {
    fontSize: 12,
    color: colors.textMuted,
  },
  langEnglishActive: {
    color: colors.primary,
  },
  separator: {
    height: 1,
    backgroundColor: colors.border,
    marginHorizontal: 20,
  },
});
