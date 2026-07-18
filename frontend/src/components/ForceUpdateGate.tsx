'use client';

import { useEffect, useMemo, useState } from 'react';
import api from '@/utils/api';

interface VersionPayload {
  currentVersion?: string;
  minVersion?: string;
}

const CURRENT_VERSION = process.env.NEXT_PUBLIC_APP_VERSION || '0.0.0';

function compareVersions(a: string, b: string): number {
  const pa = a.split('.').map((n) => parseInt(n, 10) || 0);
  const pb = b.split('.').map((n) => parseInt(n, 10) || 0);
  const len = Math.max(pa.length, pb.length);
  for (let i = 0; i < len; i++) {
    const diff = (pa[i] || 0) - (pb[i] || 0);
    if (diff !== 0) return diff;
  }
  return 0;
}

export default function ForceUpdateGate() {
  const [serverVersions, setServerVersions] = useState<VersionPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    (async () => {
      try {
        const res = await api.get('/app/version', { params: { platform: 'web' } });
        if (isMounted) setServerVersions(res.data || {});
      } catch (err: any) {
        if (isMounted) setError(err?.response?.data?.detail || 'Unable to check version');
      }
    })();
    return () => {
      isMounted = false;
    };
  }, []);

  const isOutdated = useMemo(() => {
    if (!serverVersions?.minVersion) return false;
    return compareVersions(CURRENT_VERSION, serverVersions.minVersion) < 0;
  }, [serverVersions]);

  if (!isOutdated) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.55)',
        zIndex: 2500,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px',
      }}
    >
      <div
        style={{
          background: '#fff',
          borderRadius: '12px',
          padding: '24px',
          maxWidth: '440px',
          width: '100%',
          boxShadow: '0 10px 35px rgba(0,0,0,0.2)',
          textAlign: 'center',
        }}
      >
        <h2 style={{ margin: '0 0 8px 0' }}>Update required</h2>
        <p style={{ margin: '0 0 12px 0', color: '#4b5563' }}>
          Your app version ({CURRENT_VERSION}) is below the minimum required version (
          {serverVersions?.minVersion}). Please update to continue.
        </p>
        {serverVersions?.currentVersion && (
          <p style={{ margin: '0 0 12px 0', color: '#6b7280', fontSize: '0.9rem' }}>
            Latest available: {serverVersions.currentVersion}
          </p>
        )}
        {error && <p style={{ color: '#b91c1c', marginBottom: '12px' }}>{error}</p>}

        {/* Play Store Link for Mobile / Reload for Web */}
        <button
          onClick={() => {
            const isAndroid = /Android/i.test(navigator.userAgent);
            if (isAndroid) {
              window.location.href =
                'https://play.google.com/store/apps/details?id=com.stationeryjunction.app';
            } else {
              window.location.reload();
            }
          }}
          style={{
            padding: '12px 16px',
            background: '#111827',
            color: '#fff',
            border: 'none',
            borderRadius: '10px',
            cursor: 'pointer',
            width: '100%',
            fontWeight: 600,
          }}
        >
          Update Now
        </button>
      </div>
    </div>
  );
}
