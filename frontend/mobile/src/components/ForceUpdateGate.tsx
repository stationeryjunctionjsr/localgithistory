import { useEffect, useMemo, useState } from 'react';
import { Modal, View, Text, TouchableOpacity, Platform, Linking } from 'react-native';
import api from '../api/client';
import Constants from 'expo-constants';

const APP_STORE_URL = 'https://apps.apple.com/app/stationery-junction/id000000000';
const PLAY_STORE_URL = 'https://play.google.com/store/apps/details?id=com.stationeryjunction.app';

interface VersionPayload {
  currentVersion?: string;
  minVersion?: string;
}

const CURRENT_VERSION = Constants.expoConfig?.version || Constants.manifest?.version || '0.0.0';

function compareVersions(a: string, b: string): number {
  const pa = a.split('.').map((n) => parseInt(n, 10) || 0);
  const pb = b.split('.').map((n) => parseInt(n, 10) || 0);
  const len = Math.max(pa.length, pb.length);
  for (let i = 0; i < len; i++) {
    const diff = (pa[i] || 0) - (pb[i] || 0);
    if (diff !== 0) return diff;
  }
  return 0;
}

export default function ForceUpdateGate() {
  const [serverVersions, setServerVersions] = useState<VersionPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await api.get('/app/version', { params: { platform: Platform.OS } });
        if (alive) setServerVersions(res.data || {});
      } catch (err: any) {
        if (alive) setError(err?.response?.data?.detail || 'Unable to check version');
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const isOutdated = useMemo(() => {
    if (!serverVersions?.minVersion) return false;
    return compareVersions(CURRENT_VERSION, serverVersions.minVersion) < 0;
  }, [serverVersions]);

  if (__DEV__) return null;
  if (!isOutdated) return null;

  return (
    <Modal visible transparent animationType="fade">
      <View className="flex-1 items-center justify-center bg-black/60 p-6">
        <View className="w-full max-w-[420px] rounded-3xl bg-surface-light p-8 shadow-xl">
          <Text className="mb-4 text-center text-2xl font-bold text-primary">Update Required</Text>
          <Text className="mb-4 text-center text-base text-text-secondary">
            Your app version ({CURRENT_VERSION}) is below the minimum required version (
            {serverVersions?.minVersion}). Please update to continue.
          </Text>
          {serverVersions?.currentVersion && (
            <Text className="mb-4 text-center text-sm text-text-muted">
              Latest available: {serverVersions.currentVersion}
            </Text>
          )}
          {error && <Text className="mb-4 text-center text-sm font-medium text-error">{error}</Text>}
          <TouchableOpacity
            className="mt-2 items-center rounded-full bg-primary py-4 shadow-md"
            activeOpacity={0.8}
            onPress={() => {
              const storeUrl = Platform.OS === 'ios' ? APP_STORE_URL : PLAY_STORE_URL;
              Linking.openURL(storeUrl);
            }}
          >
            <Text className="text-base font-semibold text-white">Update App Now</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}
