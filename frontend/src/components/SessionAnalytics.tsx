'use client';

import { useEffect, useRef } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';
import { recordBeacon, recordEvent, trackError, trackWebAdClick, getSessionId } from '@/utils/analytics';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import Cookies from 'js-cookie';

const IDLE_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes

export default function SessionAnalytics() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { user } = useAuth();
  const lastActivityRef = useRef(Date.now());
  const endedRef = useRef(false);

  // session start on mount
  useEffect(() => {
    const initSession = async () => {
      if (typeof window === 'undefined') return;

      let sid = localStorage.getItem('sessionId') || Cookies.get('sessionId');
      let isGuest = false;

      if (!sid) {
        sid = localStorage.getItem('guestSessionId') || Cookies.get('guestSessionId');
        isGuest = true;

        if (!sid) {
          sid = `guest_session_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
          localStorage.setItem('guestSessionId', sid);
          Cookies.set('guestSessionId', sid, { expires: 7 });
        }
      }

      const returningKey = 'sj_returning_user';
      const hasReturned = !!localStorage.getItem(returningKey);

      // Register session start in the backend
      try {
        await api.post('/tracking/session', {
          sessionId: sid,
          isReturning: hasReturned,
        });
      } catch (e) {
        console.error('Failed to track session start in backend', e);
      }

      recordEvent({
        type: 'session_start',
        payload: {
          returning: hasReturned,
          userRole: isGuest ? 'guest' : (user as any)?.role,
          sessionId: sid,
        },
      });

      if (!hasReturned) {
        localStorage.setItem(returningKey, '1');
      }
    };

    initSession();

    // Ad Attribution Tracking
    if (typeof window !== 'undefined' && searchParams) {
      const adId = searchParams.get('ad_id');
      const utmSource = searchParams.get('utm_source');
      const utmMedium = searchParams.get('utm_medium');
      const utmCampaign = searchParams.get('utm_campaign');
      const fbclid = searchParams.get('fbclid');
      const gclid = searchParams.get('gclid');

      if (adId || utmSource || fbclid || gclid) {
        const attribution = {
          adId,
          utmSource,
          utmMedium,
          utmCampaign,
          fbclid,
          gclid,
        };
        localStorage.setItem('sj_attribution', JSON.stringify(attribution));
        
        if (adId) {
          const platform = fbclid ? 'meta' : (gclid ? 'google' : (utmSource || 'unknown'));
          trackWebAdClick(adId, window.location.href, platform);
        }
      }
    }
  }, [user, searchParams]);

  // page views
  useEffect(() => {
    if (!pathname) return;
    recordEvent({ type: 'page_view', page: pathname });

    const sid = getSessionId();
    if (sid) {
      api.post('/tracking/page-view', {
        page: pathname,
        sessionId: sid,
      }).catch(() => {});
    }
  }, [pathname]);

  // activity listeners + idle end
  useEffect(() => {
    const markActivity = () => {
      lastActivityRef.current = Date.now();
    };

    const checkIdle = () => {
      if (endedRef.current) return;
      const now = Date.now();
      if (now - lastActivityRef.current >= IDLE_TIMEOUT_MS) {
        endedRef.current = true;
        recordBeacon({
          type: 'session_end',
          page: pathname || (typeof window !== 'undefined' ? window.location.pathname : undefined),
          reason: 'idle_timeout',
        });
      }
    };

    const onVisibility = () => {
      if (document.visibilityState === 'hidden' && !endedRef.current) {
        endedRef.current = true;
        recordBeacon({ type: 'session_end', reason: 'tab_hidden' });
      } else if (document.visibilityState === 'visible') {
        // reset timer when user comes back
        lastActivityRef.current = Date.now();
      }
    };

    const onBeforeUnload = () => {
      if (!endedRef.current) {
        recordBeacon({ type: 'session_end', reason: 'unload' });
      }
    };

    const onError = (event: ErrorEvent) => {
      trackError({
        message: event.message,
        url: event.filename,
        line: event.lineno,
        col: event.colno,
        stack: event.error?.stack,
      });
    };

    const onUnhandledRejection = (event: PromiseRejectionEvent) => {
      trackError({
        message: `Unhandled Rejection: ${event.reason?.message || event.reason}`,
        stack: event.reason?.stack,
      });
    };

    const interval = setInterval(checkIdle, 60_000);
    // Throttle scroll activity marking to once per second to reduce overhead
    let lastScrollMark = 0;
    const markActivityThrottled = () => {
      const now = Date.now();
      if (now - lastScrollMark > 1000) {
        lastScrollMark = now;
        markActivity();
      }
    };
    window.addEventListener('click', markActivity);
    window.addEventListener('keydown', markActivity);
    window.addEventListener('scroll', markActivityThrottled, { passive: true });
    document.addEventListener('visibilitychange', onVisibility);
    window.addEventListener('beforeunload', onBeforeUnload);
    window.addEventListener('error', onError);
    window.addEventListener('unhandledrejection', onUnhandledRejection);

    return () => {
      clearInterval(interval);
      window.removeEventListener('click', markActivity);
      window.removeEventListener('keydown', markActivity);
      window.removeEventListener('scroll', markActivityThrottled);
      document.removeEventListener('visibilitychange', onVisibility);
      window.removeEventListener('beforeunload', onBeforeUnload);
      window.removeEventListener('error', onError);
      window.removeEventListener('unhandledrejection', onUnhandledRejection);
    };
  }, [pathname]);

  return null;
}
