import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  TextInput,
  Modal,
  ActivityIndicator,
  StyleSheet,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as SecureStore from 'expo-secure-store';
import api, { SESSION_KEY } from '../api/client';
import { colors, borderRadius, shadows } from '../theme';



interface SearchOverlayProps {
  visible: boolean;
  onClose: () => void;
  onSearch: (query: string) => void;
  initialQuery?: string;
}

export const SearchOverlay: React.FC<SearchOverlayProps> = ({
  visible,
  onClose,
  onSearch,
  initialQuery = '',
}) => {
  const [query, setQuery] = useState(initialQuery);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [popularTerms, setPopularTerms] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchSuggestions = useCallback(async () => {
    setLoading(true);
    try {
      const sessionId = await SecureStore.getItemAsync(SESSION_KEY);

      // Fetch recent searches
      const recentRes = await api.get('/tracking/recent', {
        params: { sessionId, limit: 5 },
      });
      setRecentSearches(recentRes.data || []);

      // Fetch popular suggestions
      const suggestionsRes = await api.get('/tracking/suggestions', {
        params: { limit: 8 },
      });
      setPopularTerms(suggestionsRes.data?.popularTerms || []);
    } catch (error) {
      if (__DEV__) console.error('Error fetching search suggestions:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (visible) {
      fetchSuggestions();
      setQuery(initialQuery);
    }
  }, [visible, initialQuery, fetchSuggestions]);

  const handleSearchSubmit = async (text: string) => {
    if (!text.trim()) return;

    // Track the search
    try {
      const sessionId = await SecureStore.getItemAsync(SESSION_KEY);
      await api.post('/tracking/search', {
        searchTerm: text.trim(),
        resultsCount: 0, // Will be updated by results page if needed
        sessionId,
      });
    } catch (e) {
      if (__DEV__) console.error('Failed to track search:', e);
    }

    onSearch(text.trim());
    onClose();
  };

  const clearRecent = async () => {
    setRecentSearches([]);
    try {
      const sessionId = await SecureStore.getItemAsync(SESSION_KEY);
      await api.delete('/tracking/recent', { params: { sessionId } });
    } catch (e) {
      if (__DEV__) console.error('Failed to clear search history:', e);
    }
  };

  return (
    <Modal visible={visible} animationType="fade" transparent={true} onRequestClose={onClose}>
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose} style={styles.backButton}>
            <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
          </TouchableOpacity>
          <View style={styles.searchBar}>
            <Ionicons name="search-outline" size={20} color={colors.textMuted} />
            <TextInput
              style={styles.input}
              placeholder="Search products, brands..."
              placeholderTextColor={colors.textMuted}
              value={query}
              onChangeText={setQuery}
              autoFocus
              returnKeyType="search"
              onSubmitEditing={() => handleSearchSubmit(query)}
            />
            {query.length > 0 && (
              <TouchableOpacity onPress={() => setQuery('')}>
                <Ionicons name="close-circle" size={20} color={colors.textMuted} />
              </TouchableOpacity>
            )}
          </View>
        </View>

        <ScrollView style={styles.content} keyboardShouldPersistTaps="handled">
          {loading ? (
            <ActivityIndicator style={styles.loader} color={colors.primary} />
          ) : (
            <>
              {/* Recent Searches */}
              {recentSearches.length > 0 && (
                <View style={styles.section}>
                  <View style={styles.sectionHeader}>
                    <Text style={styles.sectionTitle}>Recent Searches</Text>
                    <TouchableOpacity onPress={clearRecent}>
                      <Text style={styles.clearText}>Clear</Text>
                    </TouchableOpacity>
                  </View>
                  <View style={styles.tagContainer}>
                    {recentSearches.map((term, index) => (
                      <TouchableOpacity
                        key={`recent-${index}`}
                        style={styles.tag}
                        onPress={() => handleSearchSubmit(term)}
                      >
                        <Ionicons name="time-outline" size={14} color={colors.textMuted} />
                        <Text style={styles.tagText}>{term}</Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </View>
              )}

              {/* Popular Searches */}
              {popularTerms.length > 0 && (
                <View style={styles.section}>
                  <Text style={styles.sectionTitle}>Popular Searches</Text>
                  <View style={styles.tagContainer}>
                    {popularTerms.map((term, index) => (
                      <TouchableOpacity
                        key={`popular-${index}`}
                        style={[styles.tag, styles.popularTag]}
                        onPress={() => handleSearchSubmit(term)}
                      >
                        <Ionicons name="trending-up-outline" size={14} color={colors.primary} />
                        <Text style={[styles.tagText, styles.popularTagText]}>{term}</Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </View>
              )}

              {/* Quick Categories from popularTerms fallback — only shown when no other content */}
              {popularTerms.length === 0 && recentSearches.length === 0 && (
                <View style={styles.section}>
                  <Text style={styles.sectionTitle}>Search Tips</Text>
                  <Text style={[styles.tagText, { marginLeft: 0, color: colors.textMuted }]}>
                    Try searching by product name, brand, or category.
                  </Text>
                </View>
              )}
            </>
          )}
        </ScrollView>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.surface,
    paddingTop: Platform.OS === 'ios' ? 50 : 20,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  backButton: {
    marginRight: 12,
  },
  searchBar: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.backgroundAlt,
    borderRadius: borderRadius.full,
    paddingHorizontal: 16,
    height: 44,
  },
  input: {
    flex: 1,
    marginLeft: 8,
    fontSize: 16,
    color: colors.textPrimary,
  },
  content: {
    flex: 1,
  },
  loader: {
    marginTop: 40,
  },
  section: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.textPrimary,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 12,
  },
  clearText: {
    fontSize: 12,
    color: colors.primary,
    fontWeight: '600',
  },
  tagContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  tag: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.backgroundAlt,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: borderRadius.full,
    borderWidth: 1,
    borderColor: colors.border,
  },
  popularTag: {
    borderColor: 'rgba(26, 77, 51, 0.2)',
    backgroundColor: 'rgba(26, 77, 51, 0.05)',
  },
  tagText: {
    fontSize: 14,
    color: colors.textSecondary,
    marginLeft: 6,
  },
  popularTagText: {
    color: colors.primary,
    fontWeight: '500',
  },
  categoryRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  categoryChip: {
    backgroundColor: colors.surface,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.sm,
  },
  categoryChipText: {
    fontSize: 13,
    fontWeight: '500',
    color: colors.textPrimary,
  },
});
