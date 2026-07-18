import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  Modal,
  Image,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  Linking,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api, { getImageUrl } from '../api/client';
import { colors, borderRadius, shadows } from '../theme';
import { useRouter } from 'expo-router';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const POPUP_SHOWN_KEY = 'launch_popup_shown_date';

export const LaunchPopup: React.FC = () => {
  const router = useRouter();
  const [visible, setVisible] = useState(false);
  const [banner, setBanner] = useState<any>(null);

  useEffect(() => {
    const checkAndFetchPopup = async () => {
      try {
        // Only show once per day
        const today = new Date().toISOString().split('T')[0];
        const lastShown = await AsyncStorage.getItem(POPUP_SHOWN_KEY);

        if (lastShown === today) return;

        const res = await api.get('/banners/public', {
          params: { pageType: 'launch_popup' },
        });

        const banners = res.data || [];
        if (banners.length > 0) {
          setBanner(banners[0]);
          setVisible(true);
          await AsyncStorage.setItem(POPUP_SHOWN_KEY, today);
        }
      } catch (error) {
        if (__DEV__) console.error('Error fetching launch popup:', error);
      }
    };

    checkAndFetchPopup();
  }, []);

  if (!visible || !banner) return null;

  const handlePress = () => {
    setVisible(false);
    if (banner.linkUrl) {
      if (banner.linkUrl.startsWith('http://') || banner.linkUrl.startsWith('https://')) {
        Linking.openURL(banner.linkUrl);
      } else {
        router.push(banner.linkUrl);
      }
    }
  };

  return (
    <Modal
      visible={visible}
      transparent={true}
      animationType="fade"
      onRequestClose={() => setVisible(false)}
    >
      <View style={styles.overlay}>
        <View style={styles.content}>
          <TouchableOpacity style={styles.closeButton} onPress={() => setVisible(false)}>
            <Ionicons name="close" size={24} color={colors.surface} />
          </TouchableOpacity>

          <TouchableOpacity activeOpacity={0.9} onPress={handlePress}>
            <Image
              source={{ uri: getImageUrl(banner.imageUrl || banner.image) }}
              style={styles.image}
              resizeMode="cover"
            />

            <View style={styles.details}>
              <Text style={styles.title}>{banner.title}</Text>
              {banner.description && (
                <Text style={styles.description} numberOfLines={2}>
                  {banner.description}
                </Text>
              )}
              <View style={styles.actionButton}>
                <Text style={styles.actionButtonText}>Shop Now</Text>
                <Ionicons name="arrow-forward" size={16} color={colors.surface} />
              </View>
            </View>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  content: {
    width: SCREEN_WIDTH - 60,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.xl,
    overflow: 'visible',
    ...shadows.lg,
  },
  closeButton: {
    position: 'absolute',
    top: -40,
    right: 0,
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(255,255,255,0.3)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 10,
  },
  image: {
    width: '100%',
    height: 300,
    borderTopLeftRadius: borderRadius.xl,
    borderTopRightRadius: borderRadius.xl,
  },
  details: {
    padding: 20,
    alignItems: 'center',
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.textPrimary,
    textAlign: 'center',
    marginBottom: 8,
  },
  description: {
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: 20,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: borderRadius.full,
  },
  actionButtonText: {
    color: colors.surface,
    fontSize: 15,
    fontWeight: '600',
    marginRight: 8,
  },
});
