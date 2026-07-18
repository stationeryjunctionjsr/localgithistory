'use client';

import { useEffect, useState } from 'react';
import api from '@/utils/api';

interface SessionsByLandingPageProps {
  startDate: Date | null;
  endDate: Date | null;
}

export default function SessionsByLandingPage({ startDate, endDate }: SessionsByLandingPageProps) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startDate, endDate]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (startDate) params.start_date = startDate.toISOString();
      if (endDate) params.end_date = endDate.toISOString();

      const response = await api.get('/analytics/sessions-by-landing-page', { params });
      setData(response.data || []);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch sessions by landing page:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-lg bg-white p-4 shadow-md">
        <h3 className="mb-4 text-lg font-semibold">Sessions by landing page</h3>
        <div className="flex h-64 items-center justify-center">
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="rounded-lg bg-white p-4 shadow-md">
        <h3 className="mb-4 text-lg font-semibold">Sessions by landing page</h3>
        <div className="flex h-64 items-center justify-center">
          <p className="text-gray-500">No data for this date range</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg bg-white p-4 shadow-md">
      <h3 className="mb-4 text-lg font-semibold">Sessions by landing page</h3>
      <div className="space-y-3">
        {data.map((item, index) => (
          <div key={index} className="flex items-center justify-between">
            <span className="truncate text-sm">{item.landing_page || 'Unknown'}</span>
            <span className="text-sm font-medium">{item.sessions || 0}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
