'use client';

import { useState, useEffect } from 'react';
import Header from '@/components/Header';
import { useTheme } from '@/context/ThemeContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';

interface ContentSection {
  title: string;
  body: string;
}

interface PrivacyData {
  lastUpdated?: string;
  version?: string;
  sections?: ContentSection[];
}

export default function PrivacyPolicyPage() {
  const { theme } = useTheme();
  const [data, setData] = useState<PrivacyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchPrivacyPolicy();
  }, []);

  const fetchPrivacyPolicy = async () => {
    try {
      setLoading(true);
      setError(false);
      const res = await api.get('/content/privacy/public');
      setData(res.data || null);
    } catch (err) {
      console.error('Failed to fetch Privacy Policy', err);
      setError(true);
      toast.error('Could not load Privacy Policy content. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
      });
    } catch {
      return dateString;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-16">
      <Header />

      {/* Hero Header */}
      <div 
        className="py-16 text-center text-white" 
        style={{ background: theme.gradient || theme.primary }}
      >
        <div className="mx-auto max-w-3xl px-4">
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
            Privacy Policy
          </h1>
          <p className="mt-4 text-sm sm:text-base opacity-90 font-medium">
            We value your trust. Read how we protect and manage your personal data.
          </p>
        </div>
      </div>

      <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8">
        {loading ? (
          <div className="flex justify-center py-20">
            <div 
              className="h-10 w-10 animate-spin rounded-full border-4 border-t-transparent" 
              style={{ borderColor: theme.primary, borderTopColor: 'transparent' }}
            />
          </div>
        ) : error ? (
          <div className="text-center py-20">
            <h3 className="text-lg font-bold text-gray-900">Failed to load Privacy Policy</h3>
            <p className="text-gray-500 mt-2">There was an issue fetching the latest privacy policy.</p>
            <button
              onClick={fetchPrivacyPolicy}
              className="mt-6 rounded-xl px-6 py-2.5 font-bold text-white shadow transition-all hover:opacity-90"
              style={{ backgroundColor: theme.primary }}
            >
              Try Again
            </button>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Meta Info */}
            <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm flex flex-col sm:flex-row justify-between gap-4">
              <div>
                <span className="text-xs text-gray-400 font-bold uppercase tracking-wider block">
                  Last Updated
                </span>
                <span className="text-sm font-bold text-gray-800">
                  {formatDate(data?.lastUpdated)}
                </span>
              </div>
              {data?.version && (
                <div className="sm:text-right">
                  <span className="text-xs text-gray-400 font-bold uppercase tracking-wider block">
                    Version
                  </span>
                  <span className="text-sm font-bold text-gray-800">
                    {data.version}
                  </span>
                </div>
              )}
            </div>

            {/* Policy Sections */}
            {data?.sections && data.sections.length > 0 ? (
              <div className="space-y-6">
                {data.sections.map((section, idx) => (
                  <div key={idx} className="bg-white rounded-2xl border border-gray-100 p-8 shadow-sm">
                    <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                      <span className="h-5 w-1.5 rounded-full" style={{ backgroundColor: theme.primary }} />
                      {section.title}
                    </h2>
                    <p className="text-gray-600 leading-relaxed whitespace-pre-line text-sm sm:text-base">
                      {section.body}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-20 rounded-2xl bg-white shadow-sm border border-gray-100">
                <h3 className="text-lg font-bold text-gray-900">No policy sections found</h3>
                <p className="text-gray-500 mt-2">Privacy policy document is currently empty.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
