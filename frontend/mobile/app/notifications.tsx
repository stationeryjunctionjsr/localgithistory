import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  Image,
  RefreshControl,
  Linking,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '../src/api/client';
import { colors } from '../src/theme';

const READ_IDS_KEY = 'sj_read_notification_ids';

interface InboxNotification {
  _id: string;
  title: string;
  message: string;
  image?: string | null;
  link?: string | null;
  createdAt?: string;
}

function parseDate(iso: string): Date {
  let normalized = iso.trim();
  if (/^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}/.test(normalized)) {
    normalized = normalized.replace(/\s+/, 'T');
  }
  if (normalized.includes(':') && !normalized.endsWith('Z') && !/[+-]\d{2}(:?\d{2})?$/.test(normalized)) {
    normalized += 'Z';
  }
  return new Date(normalized);
}

function timeAgo(iso?: string): string {
  if (!iso) return '';
  const date = parseDate(iso);
  const diff = Date.now() - date.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `${days}d ago`;
  return date.toLocaleDateString('en-IN', {
    timeZone: 'Asia/Kolkata',
    day: 'numeric',
    month: 'short',
  });
}


async function loadReadIds(): Promise<Set<string>> {
  try {
    const raw = await AsyncStorage.getItem(READ_IDS_KEY);
    return new Set(raw ? JSON.parse(raw) : []);
  } catch {
    return new Set();
  }
}

async function saveReadIds(ids: Set<string>) {
  try {
    await AsyncStorage.setItem(READ_IDS_KEY, JSON.stringify([...ids]));
  } catch {
    // best-effort
  }
}

export default function NotificationsScreen() {
  const router = useRouter();
  const [notifications, setNotifications] = useState<InboxNotification[]>([]);
  const [readIds, setReadIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(false);

  const fetchNotifications = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(false);
    try {
      const [response, ids] = await Promise.all([
        api.get<InboxNotification[]>('/push-notifications/inbox'),
        loadReadIds(),
      ]);
      setNotifications(response.data || []);
      setReadIds(ids);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const handlePress = useCallback(
    async (item: InboxNotification) => {
      const newIds = new Set(readIds);
      newIds.add(item._id);
      setReadIds(newIds);
      await saveReadIds(newIds);

      if (item.link) {
        const url = item.link.startsWith('http') ? item.link : `https://www.stationeryjunction.com${item.link}`;
        Linking.openURL(url).catch(() => null);
      }
    },
    [readIds]
  );

  const markAllRead = useCallback(async () => {
    const allIds = new Set(notifications.map((n) => n._id));
    setReadIds(allIds);
    await saveReadIds(allIds);
  }, [notifications]);

  const unreadCount = notifications.filter((n) => !readIds.has(n._id)).length;

  const renderItem = ({ item }: { item: InboxNotification }) => {
    const isRead = readIds.has(item._id);
    return (
      <TouchableOpacity
        onPress={() => handlePress(item)}
        activeOpacity={0.75}
        className={`mx-4 mb-3 overflow-hidden rounded-2xl border ${
          isRead ? 'border-gray-100 bg-white' : 'border-emerald-100 bg-emerald-50'
        }`}
        style={{ elevation: isRead ? 0 : 2 }}
      >
        <View className="flex-row items-start p-4">
          {item.image ? (
            <Image
              source={{ uri: item.image }}
              className="mr-3 h-12 w-12 rounded-xl"
              resizeMode="cover"
            />
          ) : (
            <View className="mr-3 h-12 w-12 items-center justify-center rounded-xl bg-emerald-100">
              <Ionicons name="notifications-outline" size={22} color={colors.primary} />
            </View>
          )}

          <View className="flex-1">
            <View className="mb-1 flex-row items-center justify-between">
              <Text
                className={`flex-1 text-sm ${isRead ? 'font-medium text-gray-700' : 'font-bold text-gray-900'}`}
                numberOfLines={1}
              >
                {item.title}
              </Text>
              {!isRead && (
                <View className="ml-2 h-2 w-2 rounded-full bg-emerald-600" />
              )}
            </View>
            <Text className="text-xs leading-5 text-gray-500" numberOfLines={2}>
              {item.message}
            </Text>
            <Text className="mt-1.5 text-[10px] text-gray-400">{timeAgo(item.createdAt)}</Text>
          </View>
        </View>

        {item.link && (
          <View className="border-t border-gray-100 px-4 py-2">
            <Text className="text-xs font-semibold text-emerald-700">Tap to view →</Text>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView className="flex-1 bg-gray-50" edges={['top']}>
      {/* Header */}
      <View className="flex-row items-center justify-between border-b border-gray-100 bg-white px-4 py-3">
        <TouchableOpacity onPress={() => router.back()} hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}>
          <Ionicons name="arrow-back" size={24} color={colors.primary} />
        </TouchableOpacity>

        <View className="flex-row items-center gap-2">
          <Text className="text-base font-bold text-gray-900">Notifications</Text>
          {unreadCount > 0 && (
            <View className="rounded-full bg-emerald-600 px-2 py-0.5">
              <Text className="text-[10px] font-bold text-white">{unreadCount}</Text>
            </View>
          )}
        </View>

        {unreadCount > 0 ? (
          <TouchableOpacity onPress={markAllRead} hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}>
            <Text className="text-xs font-semibold text-emerald-700">Mark all read</Text>
          </TouchableOpacity>
        ) : (
          <View className="w-16" />
        )}
      </View>

      {loading ? (
        /* Skeleton */
        <View className="mt-4 px-4">
          {[...Array(5)].map((_, i) => (
            <View key={i} className="mb-3 h-20 rounded-2xl bg-gray-200" />
          ))}
        </View>
      ) : error ? (
        <View className="flex-1 items-center justify-center gap-3 px-8">
          <Ionicons name="cloud-offline-outline" size={48} color="#D1D5DB" />
          <Text className="text-center text-sm text-gray-500">
            Could not load notifications. Please try again.
          </Text>
          <TouchableOpacity
            onPress={() => fetchNotifications()}
            className="rounded-full bg-emerald-800 px-6 py-2.5"
          >
            <Text className="text-sm font-semibold text-white">Retry</Text>
          </TouchableOpacity>
        </View>
      ) : notifications.length === 0 ? (
        <View className="flex-1 items-center justify-center gap-3 px-8">
          <Ionicons name="notifications-off-outline" size={52} color="#D1D5DB" />
          <Text className="text-center text-sm font-medium text-gray-400">
            No notifications yet.{'\n'}Check back later!
          </Text>
        </View>
      ) : (
        <FlatList
          data={notifications}
          keyExtractor={(item) => item._id}
          renderItem={renderItem}
          contentContainerStyle={{ paddingTop: 16, paddingBottom: 32 }}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => fetchNotifications(true)}
              tintColor={colors.primary}
              colors={[colors.primary]}
            />
          }
        />
      )}
    </SafeAreaView>
  );
}
