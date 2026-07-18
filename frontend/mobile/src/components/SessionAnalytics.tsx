import { useEffect, useRef } from 'react';
import { AppState } from 'react-native';
import { usePathname } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { recordEvent, trackError } from '../utils/analytics';

const IDLE_TIMEOUT_MS = 30 * 60 * 1000;

export default function SessionAnalytics() {
  const pathname = usePathname();
  const lastActiveRef = useRef(Date.now());
  const endedRef = useRef(false);
  const appStateRef = useRef(AppState.currentState);

  useEffect(() => {
    const returningKey = 'sj_returning_user_mobile';
    (async () => {
      let hasReturned = false;
      try {
        hasReturned = !!(await AsyncStorage.getItem(returningKey));
      } catch (e) {
        if (__DEV__) console.warn('[SessionAnalytics] read returning flag failed', e);
      }
      recordEvent({
        type: 'session_start',
        page: pathname || '/',
        payload: { returning: hasReturned, source: 'mobile' },
      });
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
        // Call original handler to maintain default behavior
        if (originalHandler) {
          originalHandler(error, isFatal);
        }
      });
    }
  }, []);

  useEffect(() => {
    if (!pathname) return;
    recordEvent({ type: 'page_view', page: pathname, payload: { source: 'mobile' } });
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
          reason: 'background',
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
          reason: 'idle_timeout',
          payload: { source: 'mobile' },
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
