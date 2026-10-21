import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  View,
  TextInput,
  TouchableOpacity,
  Text,
  StyleSheet,
  Modal,
  Platform,
  ScrollView,
  ActivityIndicator,
  Image,
  Alert,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { Ionicons } from '@expo/vector-icons';
import * as SecureStore from 'expo-secure-store';
import { router } from 'expo-router';
import api from '../api/client';
import { colors, borderRadius, shadows } from '../theme';

const SESSION_KEY = 'sj_session_id';
const PINCODE_KEY = 'sj_user_pincode';

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
  const [scanningImage, setScanningImage] = useState(false);
  const inputRef = useRef<TextInput>(null);

  const handleVoiceSearch = () => {
    inputRef.current?.focus();
    Alert.alert(
      'Voice Search',
      'Speak what you want to search by tapping the microphone icon on your keyboard!',
      [{ text: 'Start Typing / Speaking' }]
    );
  };

  const handleImageSearch = () => {
    Alert.alert(
      'Visual Search / Lens',
      'Scan a stationery product, book cover, or handwritten list to search',
      [
        {
          text: 'Take Photo',
          onPress: () => processImagePick(true),
        },
        {
          text: 'Choose from Gallery',
          onPress: () => processImagePick(false),
        },
        {
          text: 'Cancel',
          style: 'cancel',
        },
      ]
    );
  };

  const processImagePick = async (isCamera: boolean) => {
    try {
      let result: ImagePicker.ImagePickerResult;

      if (isCamera) {
        const { status } = await ImagePicker.requestCameraPermissionsAsync();
        if (status !== 'granted') {
          Alert.alert('Permission Denied', 'Camera permission is required to scan products.');
          return;
        }
        result = await ImagePicker.launchCameraAsync({
          mediaTypes: ['images'],
          quality: 0.7,
        });
      } else {
        const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (status !== 'granted') {
          Alert.alert('Permission Denied', 'Photo library permission is required to upload images.');
          return;
        }
        result = await ImagePicker.launchImageLibraryAsync({
          mediaTypes: ['images'],
          quality: 0.7,
        });
      }

      if (result.canceled || !result.assets || result.assets.length === 0) {
        return;
      }

      const asset = result.assets[0];
      setScanningImage(true);

      const formData = new FormData();
      formData.append('file', {
        uri: asset.uri,
        name: 'scan.jpg',
        type: 'image/jpeg',
      } as any);

      const res = await api.post('/visual-search/scan', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const extractedQuery = res.data?.searchQuery;
      if (extractedQuery) {
        setQuery(extractedQuery);
        handleSearchSubmit(extractedQuery);
      } else {
        Alert.alert('Scan Result', 'Could not detect any product text. Please try another angle.');
      }
    } catch (err) {
      if (__DEV__) console.error('Image scan error:', err);
      Alert.alert('Scan Error', 'Failed to scan image. Please try again.');
    } finally {
      setScanningImage(false);
    }
  };
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [popularTerms, setPopularTerms] = useState<string[]>([]);
  const [recentProducts, setRecentProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Live autocomplete
  const [liveAutocomplete, setLiveAutocomplete] = useState<{ products: any[]; brands: string[]; categories: string[] }>({ products: [], brands: [], categories: [] });
  const [loadingAutocomplete, setLoadingAutocomplete] = useState(false);

  const fetchInitialData = useCallback(async () => {
    setLoading(true);
    try {
      const sessionId = await SecureStore.getItemAsync(SESSION_KEY);

      // Parallel fetch for recent searches, popular terms, and recent products
      const [recentRes, suggestionsRes, productsRes] = await Promise.all([
        api.get('/tracking/recent', { params: { sessionId, limit: 5 } }),
        api.get('/tracking/suggestions', { params: { limit: 8 } }),
        api.get('/tracking/recent-products', { params: { sessionId, limit: 10 } }).catch(() => ({ data: [] })),
      ]);

      setRecentSearches(recentRes.data || []);
      setPopularTerms(suggestionsRes.data?.popularTerms || []);
      setRecentProducts(productsRes.data || []);
    } catch (error) {
      if (__DEV__) console.error('Error fetching search initial data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (visible) {
      fetchInitialData();
      setQuery(initialQuery);
    }
  }, [visible, initialQuery, fetchInitialData]);

  // Debounced live autocomplete
  useEffect(() => {
    if (!visible) return;
    if (query.trim().length < 2) {
      setLiveAutocomplete({ products: [], brands: [], categories: [] });
      return;
    }

    const timer = setTimeout(async () => {
      setLoadingAutocomplete(true);
      try {
        const pincode = await SecureStore.getItemAsync(PINCODE_KEY);
        const params: any = { q: query.trim(), limit: '8' };
        if (pincode) params.pincode = pincode;
        
        const res = await api.get('/products/suggest', { params });
        setLiveAutocomplete({
          products: res.data?.products || [],
          brands: res.data?.brands || [],
          categories: res.data?.categories || [],
        });
      } catch (err) {
        if (__DEV__) console.error('Autocomplete error', err);
      } finally {
        setLoadingAutocomplete(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [query, visible]);

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
              ref={inputRef}
              style={styles.input}
              placeholder={scanningImage ? "Scanning image..." : "Search products, brands..."}
              placeholderTextColor={colors.textMuted}
              value={query}
              onChangeText={setQuery}
              autoFocus
              returnKeyType="search"
              onSubmitEditing={() => handleSearchSubmit(query)}
            />
            {query.length > 0 && (
              <TouchableOpacity onPress={() => setQuery('')} style={{ padding: 4 }}>
                <Ionicons name="close-circle" size={18} color={colors.textMuted} />
              </TouchableOpacity>
            )}

            {/* Visual Search / Camera Button */}
            <TouchableOpacity
              onPress={handleImageSearch}
              disabled={scanningImage}
              style={{ padding: 4, marginLeft: 2 }}
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            >
              {scanningImage ? (
                <ActivityIndicator size="small" color={colors.primary} />
              ) : (
                <Ionicons name="camera-outline" size={22} color={colors.primary} />
              )}
            </TouchableOpacity>

            {/* Voice Search Button */}
            <TouchableOpacity
              onPress={handleVoiceSearch}
              style={{ padding: 4, marginLeft: 4 }}
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            >
              <Ionicons name="mic-outline" size={22} color={colors.primary} />
            </TouchableOpacity>
          </View>
        </View>

        <ScrollView style={styles.content} keyboardShouldPersistTaps="handled">
          {loading || loadingAutocomplete ? (
            <ActivityIndicator style={styles.loader} color={colors.primary} />
          ) : query.length >= 2 ? (
            <>
              {liveAutocomplete.products.length > 0 || liveAutocomplete.brands.length > 0 || liveAutocomplete.categories.length > 0 ? (
                <View style={styles.section}>
                  {liveAutocomplete.products.map((p, i) => (
                    <TouchableOpacity
                      key={`prod-${i}`}
                      style={styles.suggestionItem}
                      onPress={() => {
                        onClose();
                        router.push(`/products/${p.productId}`);
                      }}
                    >
                      <Ionicons name="search" size={20} color={colors.textMuted} style={{ marginRight: 12 }} />
                      <Text style={styles.suggestionText} numberOfLines={1}>{p.name}</Text>
                    </TouchableOpacity>
                  ))}
                  {liveAutocomplete.brands.map((brand, i) => (
                    <TouchableOpacity
                      key={`brand-${i}`}
                      style={styles.suggestionItem}
                      onPress={() => handleSearchSubmit(brand)}
                    >
                      <Ionicons name="pricetag" size={20} color={colors.primary} style={{ marginRight: 12 }} />
                      <Text style={styles.suggestionText}>
                        <Text style={{ fontWeight: 'bold' }}>Brand:</Text> {brand}
                      </Text>
                    </TouchableOpacity>
                  ))}
                  {liveAutocomplete.categories.map((cat, i) => (
                    <TouchableOpacity
                      key={`cat-${i}`}
                      style={styles.suggestionItem}
                      onPress={() => handleSearchSubmit(cat)}
                    >
                      <Ionicons name="grid" size={20} color={colors.primary} style={{ marginRight: 12 }} />
                      <Text style={styles.suggestionText}>
                        <Text style={{ fontWeight: 'bold' }}>Category:</Text> {cat}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              ) : (
                <View style={styles.emptyState}>
                  <Ionicons name="search-outline" size={48} color={colors.textMuted} />
                  <Text style={styles.emptyStateTitle}>No matches found</Text>
                  <Text style={styles.emptyStateText}>Try checking for typos or using different keywords</Text>
                </View>
              )}
            </>
          ) : (
            <>
              {/* Recently Browsed Products */}
              {recentProducts.length > 0 && (
                <View style={styles.section}>
                  <Text style={styles.sectionTitle}>Recently Browsed</Text>
                  <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.recentProductsScroll}>
                    {recentProducts.map((p, index) => (
                      <TouchableOpacity
                        key={`rp-${index}`}
                        style={styles.recentProductCard}
                        onPress={() => {
                          onClose();
                          router.push(`/products/${p.productId}`);
                        }}
                      >
                        <Image source={{ uri: p.displayImage }} style={styles.recentProductImage} />
                        <Text style={styles.recentProductName} numberOfLines={2}>{p.name}</Text>
                      </TouchableOpacity>
                    ))}
                  </ScrollView>
                </View>
              )}

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
            </>
          )}
        </ScrollView>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  suggestionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  suggestionText: {
    fontSize: 16,
    color: colors.textPrimary,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyStateTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.textPrimary,
    marginTop: 16,
  },
  emptyStateText: {
    fontSize: 14,
    color: colors.textMuted,
    marginTop: 8,
  },
  recentProductsScroll: {
    paddingVertical: 8,
  },
  recentProductCard: {
    width: 100,
    marginRight: 16,
  },
  recentProductImage: {
    width: 100,
    height: 100,
    borderRadius: borderRadius.md,
    backgroundColor: colors.backgroundAlt,
  },
  recentProductName: {
    fontSize: 12,
    color: colors.textPrimary,
    marginTop: 8,
    lineHeight: 16,
  },
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
