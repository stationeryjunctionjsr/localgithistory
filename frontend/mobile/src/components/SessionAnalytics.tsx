import { useEffect, useRef } from 'react';
import { AppState } from 'react-native';
import { usePathname } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { recordEvent, trackError } from '../utils/analytics';
import api from '../api/client';

const IDLE_TIMEOUT_MS = 30 * 60 * 1000;
const SESSION_ID_KEY = 'sj_mobile_session_id';

/** Generate or reuse a persistent session ID for this app session */
async function getOrCreateSessionId(): Promise<string> {
  try {
    let id = await AsyncStorage.getItem(SESSION_ID_KEY);
    if (!id) {
      id = `mob_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
      await AsyncStorage.setItem(SESSION_ID_KEY, id);
    }
    return id;
  } catch {
    return `mob_${Date.now()}`;
  }
}

export default function SessionAnalytics() {
  const pathname = usePathname();
  const lastActiveRef = useRef(Date.now());
  const endedRef = useRef(false);
  const appStateRef = useRef(AppState.currentState);
  const sessionIdRef = useRef<string>('');

  useEffect(() => {
    const returningKey = 'sj_returning_user_mobile';
    (async () => {
      let hasReturned = false;
      try {
        hasReturned = !!(await AsyncStorage.getItem(returningKey));
      } catch (e) {
        if (__DEV__) console.warn('[SessionAnalytics] read returning flag failed', e);
      }

      // Get / create session ID
      sessionIdRef.current = await getOrCreateSessionId();

      // 1. GA4 pipeline event
      recordEvent({
        type: 'session_start',
        page: pathname || '/',
        payload: { returning: hasReturned, source: 'mobile' },
      });

      // 2. Backend tracking table — feeds sessions-over-time, bounce-rate, active-visitors reports
      api.post('/tracking/session', {
        sessionId: sessionIdRef.current,
        isReturning: hasReturned,
      }).catch(() => {});

      if (!hasReturned) {
        try {
          await AsyncStorage.setItem(returningKey, '1');
        } catch (e) {
          if (__DEV__) console.warn('[SessionAnalytics] write returning flag failed', e);
        }
      }
    })();

    // Global Error Handler for Mobile
    const originalHandler = (global as any).ErrorUtils?.getGlobalHandler();
    if ((global as any).ErrorUtils) {
      (global as any).ErrorUtils.setGlobalHandler((error: any, isFatal?: boolean) => {
        trackError({
          message: `[MOBILE] ${isFatal ? 'Fatal: ' : ''}${error.name}: ${error.message}`,
          stack: error.stack,
        });
        if (originalHandler) {
          originalHandler(error, isFatal);
        }
      });
    }
  }, []);

  // Track page views — feeds sessions-by-landing-page report
  useEffect(() => {
    if (!pathname) return;
    // 1. GA4 pipeline
    recordEvent({ type: 'page_view', page: pathname, payload: { source: 'mobile' } });
    // 2. Backend tracking table
    api.post('/tracking/page-view', {
      page: pathname,
      sessionId: sessionIdRef.current || undefined,
    }).catch(() => {});
  }, [pathname]);

  useEffect(() => {
    const onAppStateChange = (nextState: any) => {
      const prev = appStateRef.current;
      appStateRef.current = nextState;
      if (prev?.match(/active/) && nextState?.match(/inactive|background/)) {
        lastActiveRef.current = Date.now();
      }
      if (nextState?.match(/inactive|background/) && !endedRef.current) {
        recordEvent({
          type: 'session_end',
          page: pathname || '/',
          payload: { source: 'mobile' },
        });
        endedRef.current = true;
      }
      if (nextState === 'active') {
        endedRef.current = false;
        lastActiveRef.current = Date.now();
      }
    };

    const idleInterval = setInterval(() => {
      if (endedRef.current) return;
      if (Date.now() - lastActiveRef.current >= IDLE_TIMEOUT_MS) {
        endedRef.current = true;
        recordEvent({
          type: 'session_end',
          page: pathname || '/',
          payload: { source: 'mobile', reason: 'idle_timeout' },
        });
      }
    }, 60_000);

    const sub = AppState.addEventListener('change', onAppStateChange);

    return () => {
      clearInterval(idleInterval);
      sub.remove();
    };
  }, [pathname]);

  return null;
}
