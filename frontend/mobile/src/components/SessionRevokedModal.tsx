import { Modal, View, Text, TouchableOpacity, StyleSheet } from 'react-native';

interface Props {
  detail: any | null;
  onCancel: () => void;
  onSignIn: () => void;
}

export function SessionRevokedModal({ detail, onCancel, onSignIn }: Props) {
  return (
    <Modal visible={!!detail} transparent animationType="fade">
      <View style={styles.backdrop}>
        <View style={styles.card}>
          <Text style={styles.title}>Session ended</Text>
          <Text style={styles.body}>
            Your account is active in another device. Do you wish to sign in here?
          </Text>
          <View style={styles.actions}>
            <TouchableOpacity style={[styles.button, styles.secondary]} onPress={onCancel}>
              <Text style={styles.secondaryText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.button, styles.primary]} onPress={onSignIn}>
              <Text style={styles.primaryText}>Sign In</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  card: { backgroundColor: '#fff', padding: 20, borderRadius: 14, width: '100%', maxWidth: 380 },
  title: { fontSize: 18, fontWeight: '700', marginBottom: 8 },
  body: { fontSize: 15, color: '#4b5563', marginBottom: 16 },
  actions: { flexDirection: 'row', justifyContent: 'flex-end', gap: 10 },
  button: { paddingHorizontal: 14, paddingVertical: 10, borderRadius: 10 },
  secondary: { borderWidth: 1, borderColor: '#d1d5db', backgroundColor: '#f9fafb' },
  primary: { backgroundColor: '#111827' },
  secondaryText: { color: '#111827', fontWeight: '600' },
  primaryText: { color: '#fff', fontWeight: '700' },
});
