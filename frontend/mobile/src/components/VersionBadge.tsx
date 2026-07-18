import { View, Text, StyleSheet } from 'react-native';
import Constants from 'expo-constants';

const APP_VERSION = Constants.expoConfig?.version || Constants.manifest?.version || 'dev';

export default function VersionBadge() {
  return (
    <View style={styles.container}>
      <View style={styles.badge}>
        <Text style={styles.text}>v{APP_VERSION}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { position: 'absolute', bottom: 12, right: 12, zIndex: 100 },
  badge: {
    backgroundColor: 'rgba(17,24,39,0.85)',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 10,
  },
  text: { color: '#f9fafb', fontWeight: '600', fontSize: 12 },
});
