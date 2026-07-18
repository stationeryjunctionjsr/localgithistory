import api from '@/utils/api';
import Cookies from 'js-cookie';

export interface ActivityPayload {
  type: string;
  detail?: any;
  sessionId?: string;
}

export async function logActivity(payload: ActivityPayload) {
  const sessionId =
    payload.sessionId ||
    (typeof window !== 'undefined' ? localStorage.getItem('sessionId') : null) ||
    Cookies.get('sessionId');
  await api.post(
    '/activity',
    { type: payload.type, detail: payload.detail, sessionId },
    { headers: sessionId ? { 'X-Session-Id': sessionId } : undefined }
  );
}

export async function promoteGuestActivities(guestSessionId: string, userId: string) {
  await api.post('/activity/promote', { sessionId: guestSessionId, userId });
}
