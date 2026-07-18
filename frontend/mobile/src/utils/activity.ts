import api from '../api/client';
import * as SecureStore from 'expo-secure-store';
import { SESSION_KEY } from '../api/client';

export interface ActivityPayload {
  type: string;
  detail?: any;
  sessionId?: string;
}

export async function logActivity(payload: ActivityPayload) {
  const sessionId = payload.sessionId || (await SecureStore.getItemAsync(SESSION_KEY)) || undefined;
  await api.post(
    '/activity',
    { type: payload.type, detail: payload.detail, sessionId },
    { headers: sessionId ? { 'X-Session-Id': sessionId } : undefined }
  );
}

export async function promoteGuestActivities(guestSessionId: string, userId: string) {
  await api.post('/activity/promote', { sessionId: guestSessionId, userId });
}
