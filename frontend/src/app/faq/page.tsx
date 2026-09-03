'use client';

import { useState, useEffect } from 'react';
import Header from '@/components/Header';
import { useTheme } from '@/context/ThemeContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';

import { useLanguage } from '@/context/LanguageContext';

interface FAQItem {
  question: string;
  answer: string;
}

interface FAQSection {
  _id: string;
  title: string;
  icon?: string;
  items: FAQItem[];
}

export default function FAQPage() {
  const { theme } = useTheme();
  const { t } = useLanguage();
  const [sections, setSections] = useState<FAQSection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [activeSectionIdx, setActiveSectionIdx] = useState<number>(0);
  const [expandedIndex, setExpandedIndex] = useState<string | null>(null);

  useEffect(() => {
    fetchFAQs();
  }, []);

  const fetchFAQs = async () => {
    try {
      setLoading(true);
      setError(false);
      const res = await api.get('/content/faq/public');
      setSections(res.data || []);
    } catch (err) {
      console.error('Failed to fetch FAQs', err);
      setError(true);
      toast.error('Could not load FAQ content. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (id: string) => {
    setExpandedIndex(expandedIndex === id ? null : id);
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-16">
      <Header />

      {/* Hero Section */}
      <div 
        className="py-16 text-center text-white" 
        style={{ background: theme.gradient || theme.primary }}
      >
        <div className="mx-auto max-w-3xl px-4">
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
            {t('pages.faq.title', 'Frequently Asked Questions')}
          </h1>
          <p className="mt-4 text-lg opacity-90">
            {t('pages.faq.subtitle', 'Have questions? We have answers. Find everything you need to know about our services.')}
          </p>
        </div>
      </div>

      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        {loading ? (
          <div className="flex justify-center py-20">
            <div 
              className="h-10 w-10 animate-spin rounded-full border-4 border-t-transparent" 
              style={{ borderColor: theme.primary, borderTopColor: 'transparent' }}
            />
          </div>
        ) : error ? (
          <div className="text-center py-20">
            <h3 className="text-lg font-bold text-gray-900">Failed to load FAQs</h3>
            <p className="text-gray-500 mt-2">There was an issue fetching the latest FAQ sections.</p>
            <button
              onClick={fetchFAQs}
              className="mt-6 rounded-xl px-6 py-2.5 font-bold text-white shadow transition-all hover:opacity-90"
              style={{ backgroundColor: theme.primary }}
            >
              Try Again
            </button>
          </div>
        ) : sections.length === 0 ? (
          <div className="text-center py-20 rounded-2xl bg-white shadow-sm border border-gray-100">
            <h3 className="text-lg font-bold text-gray-950">No FAQs found</h3>
            <p className="text-gray-500 mt-2">FAQ content is currently being updated. Please check back later.</p>
          </div>
        ) : (
          <div className="grid gap-8 lg:grid-cols-4">
            {/* Sidebar Navigation */}
            <div className="lg:col-span-1 space-y-2">
              <h2 className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-4 px-2">
                Categories
              </h2>
              {sections.map((section, idx) => (
                <button
                  key={section._id}
                  onClick={() => {
                    setActiveSectionIdx(idx);
                    setExpandedIndex(null);
                  }}
                  className={`w-full text-left px-4 py-3 rounded-xl font-bold transition-all text-sm flex items-center gap-3 ${
                    activeSectionIdx === idx
                      ? 'bg-white text-gray-900 shadow-sm border-l-4'
                      : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'
                  }`}
                  style={{ 
                    borderLeftColor: activeSectionIdx === idx ? theme.primary : 'transparent' 
                  }}
                >
                  <span className="text-base">❓</span>
                  <span>{section.title}</span>
                </button>
              ))}
            </div>

            {/* Questions List */}
            <div className="lg:col-span-3 space-y-4">
              <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm mb-4">
                <h2 className="text-xl font-extrabold text-gray-900">
                  {sections[activeSectionIdx]?.title}
                </h2>
                <p className="text-xs text-gray-400 mt-1 uppercase tracking-wider">
                  {sections[activeSectionIdx]?.items.length || 0} questions available
                </p>
              </div>

              {sections[activeSectionIdx]?.items.map((item, itemIdx) => {
                const uniqueId = `${activeSectionIdx}-${itemIdx}`;
                const isExpanded = expandedIndex === uniqueId;
                return (
                  <div
                    key={uniqueId}
                    className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm transition-all duration-200"
                  >
                    <button
                      onClick={() => toggleExpand(uniqueId)}
                      className="w-full flex items-center justify-between text-left p-6 font-bold text-gray-900 transition-colors hover:bg-gray-50/50"
                    >
                      <span className="text-base pr-4">{item.question}</span>
                      <span 
                        className={`text-xl text-gray-400 transition-transform duration-200 ${
                          isExpanded ? 'rotate-180 text-gray-900' : ''
                        }`}
                      >
                        ▾
                      </span>
                    </button>
                    {isExpanded && (
                      <div className="px-6 pb-6 text-sm leading-relaxed text-gray-600 border-t border-gray-50 pt-4 animate-fade-in">
                        {item.answer}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
