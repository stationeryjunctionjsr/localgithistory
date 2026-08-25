import { Redirect } from 'expo-router';
import { useAuth } from '../src/hooks/useAuth';
import { View, ActivityIndicator } from 'react-native';

export default function Index() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#1a4d33" />
      </View>
    );
  }

  if ((user?.role as string) === 'admin' || user?.role === 'super_admin') {
    return <Redirect href="/admin" />;
  }
  
  if ((user?.role as string) === 'seller') {
    return <Redirect href="/seller" />;
  }

  if (user?.role === 'valet') {
    return <Redirect href="/valet" />;
  }

  return <Redirect href="/(tabs)/home" />;
}
