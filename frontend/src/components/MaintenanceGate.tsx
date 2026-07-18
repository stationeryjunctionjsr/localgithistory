'use client';

import { useCallback, useEffect, useState } from 'react';
import api from '@/utils/api';

const DEFAULT_MESSAGE = [
  'The application is currently undergoing a scheduled update and services will be temporarily unavailable during this time.',
  'Access to the application will be restored once the update has been successfully completed.',
  'We regret the inconvenience caused and appreciate your patience and understanding.',
];

const POLL_INTERVAL_MS = 120_000;

function envMaintenanceEnabled(): boolean {
  return process.env.NEXT_PUBLIC_MAINTENANCE_MODE === 'true';
}

export default function MaintenanceGate() {
  const [active, setActive] = useState(envMaintenanceEnabled());
  const [message, setMessage] = useState<string[]>(DEFAULT_MESSAGE);
  const [checking, setChecking] = useState(false);

  const fetchStatus = useCallback(async () => {
    if (envMaintenanceEnabled()) {
      setActive(true);
      return;
    }
    try {
      const res = await api.get('/app/maintenance', { skipAccessToken: true } as any);
      const data = res.data || {};
      setActive(Boolean(data.active));
      if (Array.isArray(data.message) && data.message.length > 0) {
        setMessage(data.message);
      } else if (!data.active) {
        setMessage(DEFAULT_MESSAGE);
      }
    } catch (err: any) {
      const payload = err?.response?.data;
      if (payload?.code === 'MAINTENANCE_MODE' || payload?.maintenance) {
        setActive(true);
        if (Array.isArray(payload.message) && payload.message.length > 0) {
          setMessage(payload.message);
        }
      }
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    let id = window.setInterval(fetchStatus, POLL_INTERVAL_MS);
    // Pause polling when the tab is hidden to avoid wasted requests
    const handleVisibility = () => {
      if (document.hidden) {
        window.clearInterval(id);
      } else {
        fetchStatus();
        id = window.setInterval(fetchStatus, POLL_INTERVAL_MS);
      }
    };
    document.addEventListener('visibilitychange', handleVisibility);
    return () => {
      window.clearInterval(id);
      document.removeEventListener('visibilitychange', handleVisibility);
    };
  }, [fetchStatus]);

  const handleCheckAgain = async () => {
    setChecking(true);
    await fetchStatus();
    setChecking(false);
  };

  if (!active) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.55)',
        zIndex: 2600,
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
          padding: '28px 24px',
          maxWidth: '520px',
          width: '100%',
          boxShadow: '0 10px 35px rgba(0,0,0,0.2)',
          textAlign: 'center',
        }}
      >
        <h2 style={{ margin: '0 0 16px 0', fontSize: '1.35rem' }}>Scheduled maintenance</h2>
        {message.map((paragraph, index) => (
          <p
            key={index}
            style={{
              margin: index < message.length - 1 ? '0 0 14px 0' : '0 0 20px 0',
              color: '#4b5563',
              lineHeight: 1.6,
              fontSize: '0.98rem',
            }}
          >
            {paragraph}
          </p>
        ))}
        <button
          type="button"
          onClick={handleCheckAgain}
          disabled={checking}
          style={{
            padding: '12px 16px',
            background: '#111827',
            color: '#fff',
            border: 'none',
            borderRadius: '10px',
            cursor: checking ? 'wait' : 'pointer',
            width: '100%',
            fontWeight: 600,
            opacity: checking ? 0.7 : 1,
          }}
        >
          {checking ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>
    </div>
  );
}
