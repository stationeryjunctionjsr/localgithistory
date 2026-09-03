'use client';

import { useState, useEffect } from 'react';
import Header from '@/components/Header';
import { useTheme } from '@/context/ThemeContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';

import { useLanguage } from '@/context/LanguageContext';

interface ContentSection {
  title: string;
  body: string;
}

interface AboutData {
  brandName?: string;
  tagline?: string;
  mission?: string;
  offerings?: string[];
  contactEmail?: string;
  contactWebsite?: string;
  sections?: ContentSection[];
}

export default function AboutPage() {
  const { theme } = useTheme();
  const { t } = useLanguage();
  const [data, setData] = useState<AboutData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchAboutInfo();
  }, []);

  const fetchAboutInfo = async () => {
    try {
      setLoading(true);
      setError(false);
      const res = await api.get('/content/about/public');
      setData(res.data || null);
    } catch (err) {
      console.error('Failed to fetch About Info', err);
      setError(true);
      toast.error('Could not load About page content. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const brandName = data?.brandName || 'Stationery Junction';
  const tagline = data?.tagline || 'Your Premium Destination for Quality Stationery';

  return (
    <div className="min-h-screen bg-gray-50 pb-16">
      <Header />

      {/* Hero Header */}
      <div 
        className="py-20 text-center text-white" 
        style={{ background: theme.gradient || theme.primary }}
      >
        <div className="mx-auto max-w-3xl px-4">
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
            {t('pages.about.title', `About ${brandName}`)}
          </h1>
          <p className="mt-4 text-xl opacity-90 font-medium">
            {t('pages.about.subtitle', tagline)}
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
            <h3 className="text-lg font-bold text-gray-900">Failed to load About details</h3>
            <p className="text-gray-500 mt-2">There was an issue fetching the latest company details.</p>
            <button
              onClick={fetchAboutInfo}
              className="mt-6 rounded-xl px-6 py-2.5 font-bold text-white shadow transition-all hover:opacity-90"
              style={{ backgroundColor: theme.primary }}
            >
              Try Again
            </button>
          </div>
        ) : (
          <div className="space-y-10">
            {/* Mission Section */}
            {data?.mission && (
              <div className="bg-white rounded-2xl border border-gray-100 p-8 shadow-sm">
                <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <span className="h-6 w-1.5 rounded-full" style={{ backgroundColor: theme.primary }} />
                  Our Mission
                </h2>
                <p className="text-gray-600 leading-relaxed text-base">
                  {data.mission}
                </p>
              </div>
            )}

            {/* Offerings Section */}
            {data?.offerings && data.offerings.length > 0 && (
              <div className="bg-white rounded-2xl border border-gray-100 p-8 shadow-sm">
                <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <span className="h-6 w-1.5 rounded-full" style={{ backgroundColor: theme.primary }} />
                  What We Offer
                </h2>
                <div className="grid gap-3 sm:grid-cols-2">
                  {data.offerings.map((item, idx) => (
                    <div key={idx} className="flex items-start gap-2.5 text-gray-600 text-sm">
                      <span className="text-emerald-500">✔</span>
                      <span className="font-semibold">{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Custom Sections */}
            {data?.sections && data.sections.map((section, idx) => (
              <div key={idx} className="bg-white rounded-2xl border border-gray-100 p-8 shadow-sm">
                <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <span className="h-6 w-1.5 rounded-full" style={{ backgroundColor: theme.primary }} />
                  {section.title}
                </h2>
                <p className="text-gray-600 leading-relaxed whitespace-pre-line text-sm sm:text-base">
                  {section.body}
                </p>
              </div>
            ))}

            {/* Contact details */}
            {(data?.contactEmail || data?.contactWebsite) && (
              <div className="rounded-2xl bg-neutral-900 p-8 text-white shadow-xl">
                <h2 className="text-xl font-bold mb-4">Connect With Us</h2>
                <div className="space-y-3 text-sm opacity-90">
                  {data.contactEmail && (
                    <p>
                      <strong>Email: </strong>
                      <a href={`mailto:${data.contactEmail}`} className="underline hover:opacity-80">
                        {data.contactEmail}
                      </a>
                    </p>
                  )}
                  {data.contactWebsite && (
                    <p>
                      <strong>Website: </strong>
                      <a 
                        href={data.contactWebsite} 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        className="underline hover:opacity-80"
                      >
                        {data.contactWebsite}
                      </a>
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
