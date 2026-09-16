import { useCallback, useEffect, useState } from 'react';
import { Modal, View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import Constants from 'expo-constants';
import api from '../api/client';
import { colors } from '../theme';


const DEFAULT_MESSAGE = [
  'The application is currently undergoing a scheduled update and services will be temporarily unavailable during this time.',
  'Access to the application will be restored once the update has been successfully completed.',
  'We regret the inconvenience caused and appreciate your patience and understanding.',
];

const POLL_INTERVAL_MS = 30_000;

function envMaintenanceEnabled(): boolean {
  const extra = Constants.expoConfig?.extra as { maintenanceMode?: boolean } | undefined;
  return extra?.maintenanceMode === true;
}

export default function MaintenanceGate() {
  const [active, setActive] = useState(envMaintenanceEnabled());
  const [message, setMessage] = useState<string[]>(DEFAULT_MESSAGE);
  const [checking, setChecking] = useState(false);

  const fetchStatus = useCallback(async () => {
    if (envMaintenanceEnabled()) {
      setActive(true);
      return;
    }
    try {
      const res = await api.get('/app/maintenance');
      const data = res.data || {};
      setActive(Boolean(data.active));
      if (Array.isArray(data.message) && data.message.length > 0) {
        setMessage(data.message);
      } else if (!data.active) {
        setMessage(DEFAULT_MESSAGE);
      }
    } catch (err: any) {
      const payload = err?.response?.data;
      if (payload?.code === 'MAINTENANCE_MODE' || payload?.maintenance) {
        setActive(true);
        if (Array.isArray(payload.message) && payload.message.length > 0) {
          setMessage(payload.message);
        }
      }
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const id = setInterval(fetchStatus, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [fetchStatus]);

  const handleCheckAgain = async () => {
    setChecking(true);
    await fetchStatus();
    setChecking(false);
  };

  if (!active) return null;

  return (
    <Modal visible transparent animationType="fade">
      <View style={styles.backdrop}>
        <View style={styles.card}>
          <Text style={styles.title}>Scheduled maintenance</Text>
          {message.map((paragraph, index) => (
            <Text key={index} style={styles.body}>
              {paragraph}
            </Text>
          ))}
          <TouchableOpacity style={styles.button} onPress={handleCheckAgain} disabled={checking}>
            {checking ? (
              <ActivityIndicator color={colors.surface} />
            ) : (
              <Text style={styles.buttonText}>Refresh</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.55)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
  },
  card: { backgroundColor: colors.surface, borderRadius: 14, padding: 24, width: '100%', maxWidth: 440 },
  title: { fontSize: 20, fontWeight: '700', marginBottom: 14, textAlign: 'center' },
  body: { fontSize: 15, color: '#4b5563', lineHeight: 22, marginBottom: 12, textAlign: 'center' },
  button: {
    marginTop: 8,
    backgroundColor: '#111827',
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
    minHeight: 44,
    justifyContent: 'center',
  },
  buttonText: { color: colors.surface, fontWeight: '700' },
});
