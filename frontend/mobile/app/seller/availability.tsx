import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, TextInput, StyleSheet,
  ActivityIndicator, Alert, Platform,
} from 'react-native';
import api from '../../src/api/client';
import { colors, shadows } from '../../src/theme';
import Toast from 'react-native-toast-message';

const MIN_LEAD_HOURS = 3;

interface AvailabilityWindow {
  _id: string;
  startAt: string;
  endAt: string;
  reason?: string;
  status: 'scheduled' | 'active' | 'ended' | 'cancelled';
  createdAt: string;
}

function toLocalISOString(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return (
    date.getFullYear() + '-' +
    pad(date.getMonth() + 1) + '-' +
    pad(date.getDate()) + 'T' +
    pad(date.getHours()) + ':' +
    pad(date.getMinutes()) + ':00'
  );
}

function fmtDt(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
  } catch { return iso; }
}

function statusInfo(status: string) {
  if (status === 'active') return { bg: '#fee2e2', color: '#b91c1c', label: '🔴 Active now' };
  if (status === 'scheduled') return { bg: '#fef9c3', color: '#a16207', label: '🟡 Scheduled' };
  if (status === 'ended') return { bg: '#f0fdf4', color: '#15803d', label: '✅ Ended' };
  return { bg: '#f3f4f6', color: '#6b7280', label: '⚫ Cancelled' };
}

export default function SellerAvailability() {
  const [windows, setWindows] = useState<AvailabilityWindow[]>([]);
  const [loading, setLoading] = useState(true);
  const [cancellingId, setCancellingId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Form: use simple date+time string inputs (YYYY-MM-DD and HH:MM)
  const [startDate, setStartDate] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endDate, setEndDate] = useState('');
  const [endTime, setEndTime] = useState('');
  const [reason, setReason] = useState('');

  const fetchWindows = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/seller-availability/my');
      setWindows(res.data || []);
    } catch { /* silent */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchWindows(); }, [fetchWindows]);

  const handleSchedule = async () => {
    if (!startDate || !startTime || !endDate || !endTime) {
      Toast.show({ type: 'error', text1: 'Required', text2: 'Please fill start and end date/time' });
      return;
    }
    const startAt = new Date(`${startDate}T${startTime}:00`);
    const endAt = new Date(`${endDate}T${endTime}:00`);
    const now = new Date();

    if (isNaN(startAt.getTime()) || isNaN(endAt.getTime())) {
      Toast.show({ type: 'error', text1: 'Invalid', text2: 'Check date/time format (YYYY-MM-DD, HH:MM)' });
      return;
    }
    if (startAt <= now) {
      Toast.show({ type: 'error', text1: 'Invalid', text2: 'Start time must be in the future' });
      return;
    }
    const hoursDiff = (startAt.getTime() - now.getTime()) / 3600000;
    if (hoursDiff < MIN_LEAD_HOURS) {
      Toast.show({ type: 'error', text1: `Min ${MIN_LEAD_HOURS}h Notice`, text2: `Must schedule at least ${MIN_LEAD_HOURS} hours before start` });
      return;
    }
    if (endAt <= startAt) {
      Toast.show({ type: 'error', text1: 'Invalid', text2: 'End time must be after start time' });
      return;
    }

    setSubmitting(true);
    try {
      await api.post('/seller-availability', {
        startAt: startAt.toISOString(),
        endAt: endAt.toISOString(),
        reason: reason || undefined,
      });
      Toast.show({ type: 'success', text1: 'Scheduled', text2: 'Store time-off window scheduled' });
      setStartDate(''); setStartTime(''); setEndDate(''); setEndTime(''); setReason('');
      fetchWindows();
    } catch (e: any) {
      Toast.show({ type: 'error', text1: 'Error', text2: e?.response?.data?.detail || 'Failed to schedule' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = (id: string) => {
    Alert.alert('Cancel Time-Off?', 'This will restore your store availability for this window.', [
      { text: 'No', style: 'cancel' },
      {
        text: 'Yes, Cancel', style: 'destructive',
        onPress: async () => {
          setCancellingId(id);
          try {
            await api.delete(`/seller-availability/${id}`);
            Toast.show({ type: 'success', text1: 'Cancelled' });
            fetchWindows();
          } catch (e: any) {
            Toast.show({ type: 'error', text1: 'Error', text2: e?.response?.data?.detail || 'Failed' });
          } finally { setCancellingId(null); }
        },
      },
    ]);
  };

  const upcoming = windows.filter(w => w.status === 'scheduled' || w.status === 'active');
  const past = windows.filter(w => w.status === 'ended' || w.status === 'cancelled').slice(0, 10);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Store Availability</Text>
        <Text style={styles.subtitle}>
          Schedule time off. Your products will be hidden for your pincodes during the window.{' '}
          <Text style={styles.bold}>Min {MIN_LEAD_HOURS}h notice required.</Text>
        </Text>
      </View>

      {/* Schedule Form */}
      <View style={styles.card}>
        <Text style={styles.sectionLabel}>Schedule Time Off</Text>

        <View style={styles.row}>
          <View style={styles.half}>
            <Text style={styles.fieldLabel}>Start Date</Text>
            <TextInput
              style={styles.input}
              placeholder="YYYY-MM-DD"
              value={startDate}
              onChangeText={setStartDate}
              keyboardType="numbers-and-punctuation"
              maxLength={10}
            />
          </View>
          <View style={styles.half}>
            <Text style={styles.fieldLabel}>Start Time</Text>
            <TextInput
              style={styles.input}
              placeholder="HH:MM"
              value={startTime}
              onChangeText={setStartTime}
              keyboardType="numbers-and-punctuation"
              maxLength={5}
            />
          </View>
        </View>

        <View style={styles.row}>
          <View style={styles.half}>
            <Text style={styles.fieldLabel}>End Date</Text>
            <TextInput
              style={styles.input}
              placeholder="YYYY-MM-DD"
              value={endDate}
              onChangeText={setEndDate}
              keyboardType="numbers-and-punctuation"
              maxLength={10}
            />
          </View>
          <View style={styles.half}>
            <Text style={styles.fieldLabel}>End Time</Text>
            <TextInput
              style={styles.input}
              placeholder="HH:MM"
              value={endTime}
              onChangeText={setEndTime}
              keyboardType="numbers-and-punctuation"
              maxLength={5}
            />
          </View>
        </View>

        <Text style={styles.fieldLabel}>Reason (optional)</Text>
        <TextInput
          style={[styles.input, { height: 70, textAlignVertical: 'top' }]}
          placeholder="e.g. Festival, stock replenishment…"
          value={reason}
          onChangeText={setReason}
          multiline
        />

        <TouchableOpacity
          style={[styles.submitBtn, submitting && styles.btnDisabled]}
          onPress={handleSchedule}
          disabled={submitting}
        >
          <Text style={styles.submitBtnText}>{submitting ? 'Scheduling…' : '⏸ Schedule Time Off'}</Text>
        </TouchableOpacity>
      </View>

      {/* Upcoming/Active Windows */}
      {loading ? (
        <ActivityIndicator color="#4f46e5" style={{ marginTop: 20 }} />
      ) : (
        <>
          {upcoming.length > 0 && (
            <View style={styles.card}>
              <Text style={styles.sectionLabel}>Upcoming / Active</Text>
              {upcoming.map(w => {
                const si = statusInfo(w.status);
                return (
                  <View key={w._id} style={[styles.windowRow, { backgroundColor: si.bg }]}>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.windowTime}>{fmtDt(w.startAt)}</Text>
                      <Text style={styles.windowArrow}>↓</Text>
                      <Text style={styles.windowTime}>{fmtDt(w.endAt)}</Text>
                      {w.reason ? <Text style={styles.windowReason}>{w.reason}</Text> : null}
                    </View>
                    <View style={styles.windowRight}>
                      <Text style={[styles.windowBadge, { color: si.color }]}>{si.label}</Text>
                      {w.status === 'scheduled' && (
                        <TouchableOpacity
                          style={styles.cancelBtn}
                          onPress={() => handleCancel(w._id)}
                          disabled={cancellingId === w._id}
                        >
                          <Text style={styles.cancelBtnText}>
                            {cancellingId === w._id ? '…' : 'Cancel'}
                          </Text>
                        </TouchableOpacity>
                      )}
                    </View>
                  </View>
                );
              })}
            </View>
          )}

          {past.length > 0 && (
            <View style={styles.card}>
              <Text style={[styles.sectionLabel, { color: '#9ca3af' }]}>Recent History</Text>
              {past.map(w => {
                const si = statusInfo(w.status);
                return (
                  <View key={w._id} style={styles.historyRow}>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.historyTime}>{fmtDt(w.startAt)} → {fmtDt(w.endAt)}</Text>
                    </View>
                    <Text style={[styles.windowBadge, { color: si.color }]}>{si.label}</Text>
                  </View>
                );
              })}
            </View>
          )}

          {upcoming.length === 0 && past.length === 0 && (
            <View style={styles.empty}>
              <Text style={styles.emptyText}>No time-off windows scheduled.</Text>
              <Text style={styles.emptySubText}>Your store is fully available right now.</Text>
            </View>
          )}
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  content: { padding: 16, paddingBottom: 40 },
  header: { marginBottom: 16 },
  title: { fontSize: 22, fontWeight: '700', color: '#111827' },
  subtitle: { fontSize: 13, color: '#6b7280', marginTop: 4 },
  bold: { fontWeight: '700', color: '#111827' },
  card: {
    backgroundColor: '#fff', borderRadius: 14, padding: 16, marginBottom: 14,
    ...shadows.sm,
  },
  sectionLabel: { fontSize: 14, fontWeight: '700', color: '#374151', marginBottom: 14, textTransform: 'uppercase', letterSpacing: 0.5 },
  row: { flexDirection: 'row', gap: 10, marginBottom: 12 },
  half: { flex: 1 },
  fieldLabel: { fontSize: 12, fontWeight: '600', color: '#374151', marginBottom: 5 },
  input: {
    borderWidth: 1, borderColor: '#d1d5db', borderRadius: 8,
    paddingHorizontal: 11, paddingVertical: 9, fontSize: 14, backgroundColor: '#fff',
  },
  submitBtn: {
    backgroundColor: '#f59e0b', borderRadius: 10, paddingVertical: 13,
    alignItems: 'center', marginTop: 6,
  },
  btnDisabled: { backgroundColor: '#9ca3af' },
  submitBtnText: { color: '#fff', fontSize: 15, fontWeight: '700' },
  windowRow: {
    borderRadius: 10, padding: 12, marginBottom: 10,
    flexDirection: 'row', alignItems: 'flex-start',
  },
  windowTime: { fontSize: 13, fontWeight: '600', color: '#111827' },
  windowArrow: { fontSize: 11, color: '#9ca3af', marginVertical: 1 },
  windowReason: { fontSize: 12, color: '#6b7280', marginTop: 4 },
  windowRight: { alignItems: 'flex-end', gap: 8 },
  windowBadge: { fontSize: 12, fontWeight: '700' },
  cancelBtn: { backgroundColor: '#fee2e2', borderRadius: 7, paddingHorizontal: 10, paddingVertical: 5 },
  cancelBtnText: { fontSize: 12, fontWeight: '600', color: '#b91c1c' },
  historyRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 6, borderTopWidth: 1, borderTopColor: '#f3f4f6' },
  historyTime: { fontSize: 12, color: '#6b7280' },
  empty: { alignItems: 'center', paddingVertical: 32 },
  emptyText: { fontSize: 15, fontWeight: '600', color: '#374151' },
  emptySubText: { fontSize: 13, color: '#9ca3af', marginTop: 6 },
});
