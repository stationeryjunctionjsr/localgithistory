'use client';

const APP_VERSION = process.env.NEXT_PUBLIC_APP_VERSION || 'dev';

export default function VersionBadge() {
  return (
    <div style={{ position: 'fixed', bottom: 12, right: 12, zIndex: 1900 }}>
      <div
        style={{
          background: 'rgba(17,24,39,0.85)',
          color: '#f9fafb',
          padding: '6px 10px',
          borderRadius: '10px',
          fontSize: '12px',
          fontWeight: 600,
          boxShadow: '0 6px 20px rgba(0,0,0,0.2)',
        }}
      >
        v{APP_VERSION}
      </div>
    </div>
  );
}
