'use client';

import { useEffect } from 'react';
import { logger } from '@/utils/logger';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to our centralized logger
    logger.error('Page-level error caught by Next.js error boundary:', error);
  }, [error]);

  return (
    <div style={{ padding: '40px 20px', textAlign: 'center', minHeight: '50vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
      <h2 style={{ fontSize: '24px', fontWeight: 'bold', color: '#111827', marginBottom: '12px' }}>
        Oops! Something went wrong.
      </h2>
      <p style={{ fontSize: '16px', color: '#4b5563', marginBottom: '24px', maxWidth: '400px' }}>
        We encountered an error while trying to load this page. Please check your connection or try again.
      </p>
      <button
        onClick={() => reset()}
        style={{
          padding: '10px 20px',
          backgroundColor: '#6d28d9',
          color: 'white',
          borderRadius: '8px',
          fontWeight: 'bold',
          border: 'none',
          cursor: 'pointer'
        }}
      >
        Try again
      </button>
    </div>
  );
}
