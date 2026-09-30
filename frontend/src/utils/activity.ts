import api from '@/utils/api';
import Cookies from 'js-cookie';

export interface ActivityPayload {
  type: string;
  detail?: {
    method?: string;
    role?: string;
    source?: string;
    pageUrl?: string;
    [key: string]: string | undefined;
  };
  sessionId?: string;
}

/**
 * Logs an auth activity event (login / register / logout) to the unified
 * /api/activity endpoint, which now writes directly to sj_tracking.
 */
export async function logActivity(payload: ActivityPayload) {
  const sessionId =
    payload.sessionId ||
    (typeof window !== 'undefined' ? localStorage.getItem('sessionId') : null) ||
    Cookies.get('sessionId');

  await api.post(
    '/activity',
    {
      type: payload.type,
      sessionId,
      meta: {
        source: payload.detail?.method ?? payload.detail?.source ?? undefined,
        pageUrl: payload.detail?.pageUrl ?? undefined,
      },
    },
    { headers: sessionId ? { 'X-Session-Id': sessionId } : undefined }
  );
}

/**
 * Kept for backwards compatibility — guest promotion is now handled
 * automatically server-side by linking session_id in sj_tracking.
 */
export async function promoteGuestActivities(guestSessionId: string, userId: string) {
  await api.post('/activity/promote', { sessionId: guestSessionId, userId }).catch(() => {
    // non-critical — silently ignore
  });
}
