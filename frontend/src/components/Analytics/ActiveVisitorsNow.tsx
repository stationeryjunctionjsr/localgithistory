'use client';

import { useEffect, useState } from 'react';
import api from '@/utils/api';
import { logger } from '@/utils/logger';

interface ActiveVisitorsNowProps {
  refreshIntervalMs?: number;
}

export default function ActiveVisitorsNow({ refreshIntervalMs = 30000 }: ActiveVisitorsNowProps) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());

  const fetchData = async () => {
    try {
      const response = await api.get('/analytics/reports/visitors-now');
      const row = Array.isArray(response.data) ? response.data[0] : response.data;
      setData(row || null);
      setLastRefreshed(new Date());
    } catch (error) {
      logger.error('Failed to fetch active visitors:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, refreshIntervalMs);
    return () => clearInterval(interval);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const statCard = (label: string, value: number | string, color: string) => (
    <div className="flex flex-col items-center justify-center rounded-lg p-3" style={{ background: color + '18' }}>
      <span className="text-3xl font-bold" style={{ color }}>{value}</span>
      <span className="mt-1 text-center text-xs text-gray-500">{label}</span>
    </div>
  );

  return (
    <div className="rounded-lg bg-white p-4 shadow-md">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-lg font-semibold">Active Visitors Right Now</h3>
        <div className="flex items-center gap-2">
          <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-green-500" />
          <span className="text-xs text-gray-400">Live · {lastRefreshed.toLocaleTimeString()}</span>
        </div>
      </div>
      {loading && !data ? (
        <div className="flex h-32 items-center justify-center">
          <p className="text-gray-500">Loading...</p>
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-3">
          {statCard('Total Active', data?.activeVisitors ?? 0, '#6366f1')}
          {statCard('Logged In', data?.loggedInSessions ?? 0, '#10b981')}
          {statCard('Guest', data?.guestSessions ?? 0, '#f59e0b')}
        </div>
      )}
      <p className="mt-3 text-center text-xs text-gray-400">
        Sessions active in last {data?.windowMinutes ?? 15} minutes · auto-refreshes every {Math.round(refreshIntervalMs / 1000)}s
      </p>
    </div>
  );
}
