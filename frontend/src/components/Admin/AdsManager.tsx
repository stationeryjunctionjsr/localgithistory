'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import RefreshButton from './RefreshButton';

interface AdStats {
  impressions: number; clicks: number; leads: number; purchases: number;
  add_to_cart: number; conversions: number; conversion_value: number;
  ctr: number; cvr: number;
}
interface Ad {
  id: string; name: string; platform: 'google' | 'meta' | 'both' | 'social' | 'email' | 'qr' | 'whatsapp';
  objective: string; status: 'draft' | 'active' | 'paused' | 'completed' | 'archived';
  budget_daily: number; budget_total: number; currency: string;
  start_date?: string; end_date?: string; target_url?: string;
  headline?: string; description?: string; image_url?: string;
  google_campaign_id?: string; google_ad_group_id?: string;
  meta_campaign_id?: string; meta_ad_set_id?: string;
  utm_source?: string; utm_medium?: string; utm_campaign?: string;
  google_conversion_id?: string; google_conversion_label?: string;
  meta_pixel_id?: string; notes?: string;
  created_at: string; updated_at: string; launched_at?: string;
  stats?: AdStats;
}
interface Summary {
  total_ads: number; active: number; paused: number; draft: number;
  total_impressions: number; total_clicks: number; total_conversions: number;
  total_spend_estimate: number; overall_ctr: number;
}

const emptyForm = (): Partial<Ad> => ({
  name: '', platform: 'google', objective: 'traffic',
  budget_daily: 0, budget_total: 0, currency: 'INR',
  start_date: '', end_date: '', target_url: '', headline: '', description: '',
  image_url: '', google_campaign_id: '', google_ad_group_id: '',
  meta_campaign_id: '', meta_ad_set_id: '',
  utm_source: '', utm_medium: 'cpc', utm_campaign: '',
  google_conversion_id: '', google_conversion_label: '', meta_pixel_id: '', notes: '',
});

const PLATFORM_COLORS: Record<string, string> = {
  google: 'bg-blue-100 text-blue-700',
  meta: 'bg-indigo-100 text-indigo-700',
  both: 'bg-purple-100 text-purple-700',
  social: 'bg-pink-100 text-pink-700',
  email: 'bg-yellow-100 text-yellow-700',
  qr: 'bg-teal-100 text-teal-700',
  whatsapp: 'bg-green-100 text-green-700',
};
const PLATFORM_LABELS: Record<string, string> = {
  google: '🔵 Google',
  meta: '📘 Meta',
  both: '🌐 Both',
  social: '📸 Social',
  email: '📧 Email',
  qr: '🏁 QR Code',
  whatsapp: '💬 WhatsApp',
};
const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-600', active: 'bg-green-100 text-green-700',
  paused: 'bg-yellow-100 text-yellow-700', completed: 'bg-blue-100 text-blue-700', archived: 'bg-red-100 text-red-600',
};

const Pill = ({ v, map, labels }: { v: string; map: Record<string, string>; labels: Record<string, string> }) => (
  <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${map[v] || 'bg-gray-100 text-gray-600'}`}>
    {labels[v] || v}
  </span>
);

const KPI = ({ label, value, color }: { label: string; value: string | number; color?: string }) => (
  <div className="rounded-xl bg-white p-4 shadow-sm border border-gray-100">
    <p className="text-xs text-gray-500">{label}</p>
    <p className={`text-2xl font-bold mt-1 ${color || 'text-gray-900'}`}>{value}</p>
  </div>
);

export default function AdsManager() {
  const { user } = useAuth();
  const [ads, setAds] = useState<Ad[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editAd, setEditAd] = useState<Ad | null>(null);
  const [form, setForm] = useState<Partial<Ad>>(emptyForm());
  const [saving, setSaving] = useState(false);
  const [filterStatus, setFilterStatus] = useState('');
  const [filterPlatform, setFilterPlatform] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  const getPageNumbers = (currentPage: number, totalPages: number) => {
    const delta = 2;
    const range = [];
    for (let i = Math.max(2, currentPage - delta); i <= Math.min(totalPages - 1, currentPage + delta); i++) {
      range.push(i);
    }
    if (currentPage - delta > 2) {
      range.unshift('...');
    }
    if (currentPage + delta < totalPages - 1) {
      range.push('...');
    }
    range.unshift(1);
    if (totalPages > 1) {
      range.push(totalPages);
    }
    return range;
  };

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const params: Record<string, string> = {};
      if (filterStatus) params.status = filterStatus;
      if (filterPlatform) params.platform = filterPlatform;
      const [adsRes, sumRes] = await Promise.all([
        api.get('/ads/', { params }),
        api.get('/ads/summary'),
      ]);
      setAds(adsRes.data.ads ?? []);
      setSummary(sumRes.data);
    } catch (e: any) {
      toast.error('Failed to load ads: ' + (e.response?.data?.detail || e.message));
    } finally {
      setLoading(false);
    }
  }, [filterStatus, filterPlatform]);

  useEffect(() => { load(); }, [load]);

  const openCreate = () => { setEditAd(null); setForm(emptyForm()); setShowForm(true); };
  const openEdit = (ad: Ad) => { setEditAd(ad); setForm({ ...ad }); setShowForm(true); };

  const handleSave = async () => {
    if (!form.name?.trim()) { toast.error('Campaign name is required'); return; }
    setSaving(true);
    try {
      if (editAd) { await api.put(`/ads/${editAd.id}`, form); toast.success('Campaign updated'); }
      else { await api.post('/ads/', form); toast.success('Campaign created'); }
      setShowForm(false);
      load();
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Save failed');
    } finally { setSaving(false); }
  };

  const setStatus = async (ad: Ad, status: string) => {
    try {
      await api.patch(`/ads/${ad.id}/status`, { status });
      toast.success(`Campaign ${status}`);
      load();
    } catch (e: any) { toast.error(e.response?.data?.detail || 'Update failed'); }
  };

  const handleDelete = async (ad: Ad) => {
    if (!window.confirm(`Delete "${ad.name}"?`)) return;
    try {
      await api.delete(`/ads/${ad.id}`);
      toast.success('Campaign deleted');
      load();
    } catch (e: any) { toast.error(e.response?.data?.detail || 'Delete failed'); }
  };

  type FieldKey = keyof Ad;
  const inp = (key: FieldKey, label: string, type = 'text', placeholder?: string) => (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-semibold text-gray-600">{label}</label>
      <input
        type={type} placeholder={placeholder}
        className="rounded border px-2 py-1.5 text-sm focus:ring-2 focus:ring-indigo-300 outline-none"
        value={((form as any)[key] as string | number) ?? ''}
        onChange={e => setForm(p => ({
          ...p,
          [key]: type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value,
        }))}
      />
    </div>
  );

  const sel = (key: FieldKey, label: string, opts: string[]) => (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-semibold text-gray-600">{label}</label>
      <select
        className="rounded border px-2 py-1.5 text-sm focus:ring-2 focus:ring-indigo-300 outline-none bg-white"
        value={((form as any)[key] as string) || ''}
        onChange={e => setForm(p => ({ ...p, [key]: e.target.value }))}
      >
        {opts.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  );

  const totalItems = ads.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
  const paginatedAds = ads.slice(startIndex, endIndex);

  if (user?.role !== 'super_admin') {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6">
        <p className="font-semibold text-red-700">Access denied. Super admin required.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="inline-flex items-center gap-2 text-2xl font-bold text-gray-900">
            Ad Campaigns <RefreshButton onRefresh={load} />
          </h1>
          <p className="mt-0.5 text-sm text-gray-500">
            Manage Google Ads &amp; Meta campaigns. Track impressions, clicks and conversions in real time.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            id="ads-create-btn"
            onClick={openCreate}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 transition-colors"
          >
            + New Campaign
          </button>
        </div>
      </div>

      {/* KPI Summary */}
      {summary && (
        <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          <KPI label="Total Campaigns" value={summary.total_ads} />
          <KPI label="Active" value={summary.active} color="text-green-600" />
          <KPI label="Impressions" value={summary.total_impressions.toLocaleString()} />
          <KPI label="Clicks" value={summary.total_clicks.toLocaleString()} />
          <KPI label="Conversions" value={summary.total_conversions.toLocaleString()} color="text-indigo-600" />
        </div>
      )}

      {/* Filters */}
      <div className="mb-6 flex flex-wrap gap-4">
        <select
          id="ads-filter-status"
          className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          value={filterStatus}
          onChange={e => {
            setFilterStatus(e.target.value);
            setCurrentPage(1);
          }}
        >
          <option value="">All Statuses</option>
          {['draft', 'active', 'paused', 'completed', 'archived'].map(s => (
            <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
          ))}
        </select>
        <select
          id="ads-filter-platform"
          className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          value={filterPlatform}
          onChange={e => {
            setFilterPlatform(e.target.value);
            setCurrentPage(1);
          }}
        >
          <option value="">All Platforms</option>
          <option value="google">Google</option>
          <option value="meta">Meta</option>
          <option value="both">Both</option>
          <option value="social">Social Media</option>
          <option value="email">Email</option>
          <option value="qr">QR Code</option>
          <option value="whatsapp">WhatsApp</option>
        </select>
      </div>

      {/* Campaign Table */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-indigo-600" />
        </div>
      ) : (
        <div>
          <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 text-xs font-semibold uppercase tracking-wide text-gray-500">
                <tr>
                  {['Campaign', 'Platform', 'Status', 'Daily Budget', 'Impressions', 'Clicks', 'CTR', 'Conv.', 'CVR', 'Actions'].map(h => (
                    <th key={h} className="whitespace-nowrap px-4 py-3 text-left">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {totalItems === 0 && (
                  <tr>
                    <td colSpan={10} className="py-16 text-center text-gray-400">
                      No campaigns found. Create your first ad campaign.
                    </td>
                  </tr>
                )}
                {paginatedAds.map(ad => (
                  <tr key={ad.id} className="transition-colors hover:bg-gray-50">
                    <td className="max-w-[160px] truncate px-4 py-3 font-medium text-gray-900">{ad.name}</td>
                    <td className="px-4 py-3"><Pill v={ad.platform} map={PLATFORM_COLORS} labels={PLATFORM_LABELS} /></td>
                    <td className="px-4 py-3"><Pill v={ad.status} map={STATUS_COLORS} labels={{}} /></td>
                    <td className="px-4 py-3 text-gray-600">₹{(ad.budget_daily ?? 0).toLocaleString()}</td>
                    <td className="px-4 py-3 text-gray-600">{(ad.stats?.impressions ?? 0).toLocaleString()}</td>
                    <td className="px-4 py-3 text-gray-600">{(ad.stats?.clicks ?? 0).toLocaleString()}</td>
                    <td className="px-4 py-3 text-gray-600">{ad.stats?.ctr ?? 0}%</td>
                    <td className="px-4 py-3 text-gray-600">{ad.stats?.conversions ?? 0}</td>
                    <td className="px-4 py-3 text-gray-600">{ad.stats?.cvr ?? 0}%</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap items-center gap-1">
                        <button onClick={() => openEdit(ad)} className="rounded px-2 py-0.5 text-xs bg-gray-100 hover:bg-gray-200">Edit</button>
                        {ad.status === 'draft' && (
                          <button onClick={() => setStatus(ad, 'active')} className="rounded px-2 py-0.5 text-xs bg-green-100 text-green-700 hover:bg-green-200">Launch</button>
                        )}
                        {ad.status === 'active' && (
                          <button onClick={() => setStatus(ad, 'paused')} className="rounded px-2 py-0.5 text-xs bg-yellow-100 text-yellow-700 hover:bg-yellow-200">Pause</button>
                        )}
                        {ad.status === 'paused' && (
                          <button onClick={() => setStatus(ad, 'active')} className="rounded px-2 py-0.5 text-xs bg-green-100 text-green-700 hover:bg-green-200">Resume</button>
                        )}
                        {['active', 'paused'].includes(ad.status) && (
                          <button onClick={() => setStatus(ad, 'completed')} className="rounded px-2 py-0.5 text-xs bg-blue-100 text-blue-700 hover:bg-blue-200">Complete</button>
                        )}
                        {ad.status === 'active' && ad.target_url && (
                          <button
                            onClick={() => {
                              try {
                                let target = ad.target_url || '';
                                if (!/^https?:\/\//i.test(target)) {
                                  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || window.location.origin;
                                  target = `${baseUrl.replace(/\/$/, '')}/${target.replace(/^\//, '')}`;
                                }
                                const url = new URL(target);
                                url.searchParams.set('ad_id', ad.id);
                                
                                const source = ad.utm_source || (ad.platform === 'google' ? 'google' : ad.platform === 'meta' ? 'facebook' : ad.platform === 'both' ? 'paid' : ad.platform === 'social' ? 'social' : ad.platform === 'email' ? 'newsletter' : ad.platform === 'qr' ? 'offline' : ad.platform === 'whatsapp' ? 'whatsapp' : 'paid');
                                const medium = ad.utm_medium || (ad.platform === 'social' ? 'post' : ad.platform === 'email' ? 'email' : ad.platform === 'qr' ? 'qr' : ad.platform === 'whatsapp' ? 'broadcast' : 'cpc');
                                const campaign = ad.utm_campaign || ad.name.toLowerCase().replace(/\s+/g, '_');

                                url.searchParams.set('utm_source', source);
                                url.searchParams.set('utm_medium', medium);
                                if (campaign) url.searchParams.set('utm_campaign', campaign);
                                
                                navigator.clipboard.writeText(url.toString());
                                toast.success('Copied campaign link to clipboard!');
                              } catch (e) {
                                toast.error('Invalid destination URL');
                              }
                            }}
                            className="rounded px-2 py-0.5 text-xs bg-indigo-100 text-indigo-700 hover:bg-indigo-200"
                          >
                            📋 Copy Link
                          </button>
                        )}
                        <button onClick={() => handleDelete(ad)} className="rounded px-2 py-0.5 text-xs bg-red-100 text-red-600 hover:bg-red-200">Delete</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Premium Pagination Controls */}
          {totalItems > 0 && (
            <div className="mt-4 flex flex-shrink-0 flex-col items-center justify-between gap-4 border-t border-slate-200 pt-4 sm:flex-row px-6 pb-6">
              <div className="text-sm text-gray-700">
                Showing <span className="font-semibold">{totalItems === 0 ? 0 : startIndex + 1}</span> to{' '}
                <span className="font-semibold">{endIndex}</span> of{' '}
                <span className="font-semibold">{totalItems}</span> entries
              </div>
              <div className="flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-2 text-sm text-gray-700">
                  <span>Show</span>
                  <select
                    value={itemsPerPage}
                    onChange={(e) => {
                      setItemsPerPage(Number(e.target.value));
                      setCurrentPage(1);
                    }}
                    className="rounded border px-2 py-1 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value={5}>5</option>
                    <option value={10}>10</option>
                    <option value={25}>25</option>
                    <option value={50}>50</option>
                  </select>
                  <span>entries</span>
                </div>
                <nav className="inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
                  <button
                    onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
                    disabled={currentPage === 1}
                    className="inline-flex items-center rounded-l-md border border-gray-300 bg-white px-2 py-2 text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span className="sr-only">Previous</span>
                    <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                      <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </button>
                  {getPageNumbers(currentPage, totalPages).map((page, index) => {
                    if (page === '...') {
                      return (
                        <span
                          key={`dots-${index}`}
                          className="inline-flex items-center border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-500"
                        >
                          ...
                        </span>
                      );
                    }
                    return (
                      <button
                        key={page}
                        onClick={() => setCurrentPage(page as number)}
                        className={`inline-flex items-center border px-4 py-2 text-sm font-medium transition-colors ${
                          currentPage === page
                            ? 'z-10 bg-indigo-50 border-indigo-500 text-indigo-600 font-semibold'
                            : 'border-gray-300 bg-white text-gray-500 hover:bg-gray-50'
                        }`}
                      >
                        {page}
                      </button>
                    );
                  })}
                  <button
                    onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
                    disabled={currentPage === totalPages}
                    className="inline-flex items-center rounded-r-md border border-gray-300 bg-white px-2 py-2 text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span className="sr-only">Next</span>
                    <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                      <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                    </svg>
                  </button>
                </nav>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Create / Edit Modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/50 px-4 py-8">
          <div className="w-full max-w-3xl rounded-2xl bg-white p-6 shadow-2xl">
            <div className="mb-5 flex items-center justify-between">
              <h2 className="text-lg font-bold text-gray-900">{editAd ? 'Edit Campaign' : 'New Campaign'}</h2>
              <button onClick={() => setShowForm(false)} className="text-2xl leading-none text-gray-400 hover:text-gray-600">&times;</button>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {inp('name', 'Campaign Name *', 'text', 'e.g. Summer Sale 2025')}
              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold text-gray-600">Platform *</label>
                <select
                  className="rounded border px-2 py-1.5 text-sm focus:ring-2 focus:ring-indigo-300 outline-none bg-white"
                  value={form.platform || 'google'}
                  onChange={e => {
                    const newPlatform = e.target.value as Ad['platform'];
                    let defaultSource = '';
                    let defaultMedium = '';
                    if (newPlatform === 'google') { defaultSource = 'google'; defaultMedium = 'cpc'; }
                    else if (newPlatform === 'meta') { defaultSource = 'facebook'; defaultMedium = 'cpc'; }
                    else if (newPlatform === 'both') { defaultSource = 'paid'; defaultMedium = 'cpc'; }
                    else if (newPlatform === 'social') { defaultSource = 'social'; defaultMedium = 'post'; }
                    else if (newPlatform === 'email') { defaultSource = 'newsletter'; defaultMedium = 'email'; }
                    else if (newPlatform === 'qr') { defaultSource = 'offline'; defaultMedium = 'qr'; }
                    else if (newPlatform === 'whatsapp') { defaultSource = 'whatsapp'; defaultMedium = 'broadcast'; }

                    setForm(p => ({
                      ...p,
                      platform: newPlatform,
                      utm_source: defaultSource,
                      utm_medium: defaultMedium,
                    }));
                  }}
                >
                  <option value="google">Google Ads</option>
                  <option value="meta">Meta Ads</option>
                  <option value="both">Both (Google & Meta)</option>
                  <option value="social">Social Media Post</option>
                  <option value="email">Email Marketing</option>
                  <option value="qr">QR Code Channel</option>
                  <option value="whatsapp">WhatsApp Broadcast</option>
                </select>
              </div>
              {sel('objective', 'Objective', ['awareness', 'traffic', 'engagement', 'leads', 'conversions', 'catalog_sales', 'app_installs'])}
              {inp('budget_daily', 'Daily Budget (₹)', 'number')}
              {inp('budget_total', 'Total Budget (₹)', 'number')}
              {inp('start_date', 'Start Date', 'date')}
              {inp('end_date', 'End Date', 'date')}
              {inp('target_url', 'Landing Page URL', 'url', 'https://')}
              {inp('headline', 'Ad Headline')}
              {inp('description', 'Ad Description')}
              {inp('image_url', 'Creative Image URL', 'url')}

              {/* Google Ads Section */}
              {['google', 'both'].includes(form.platform || '') && (
                <div className="sm:col-span-2">
                  <p className="mb-2 text-xs font-bold uppercase tracking-wide text-blue-600">🔵 Google Ads Configuration</p>
                  <div className="grid grid-cols-2 gap-3">
                    {inp('google_campaign_id', 'Campaign ID')}
                    {inp('google_ad_group_id', 'Ad Group ID')}
                    {inp('google_conversion_id', 'Conversion ID (AW-...)')}
                    {inp('google_conversion_label', 'Conversion Label')}
                  </div>
                </div>
              )}

              {/* Meta Section */}
              {['meta', 'both'].includes(form.platform || '') && (
                <div className="sm:col-span-2">
                  <p className="mb-2 text-xs font-bold uppercase tracking-wide text-indigo-600">📘 Meta Configuration (Facebook / Instagram)</p>
                  <div className="grid grid-cols-2 gap-3">
                    {inp('meta_campaign_id', 'Campaign ID')}
                    {inp('meta_ad_set_id', 'Ad Set ID')}
                    {inp('meta_pixel_id', 'Pixel ID')}
                  </div>
                </div>
              )}

              {/* UTM Section */}
              <div className="sm:col-span-2">
                <p className="mb-2 text-xs font-bold uppercase tracking-wide text-gray-500">UTM Parameters</p>
                <div className="grid grid-cols-3 gap-3">
                  {inp('utm_source', 'utm_source')}
                  {inp('utm_medium', 'utm_medium')}
                  {inp('utm_campaign', 'utm_campaign')}
                </div>
              </div>

              {/* Final Trackable URL Section */}
              {form.target_url && (
                <div className="sm:col-span-2 rounded-xl bg-indigo-50/50 p-4 border border-indigo-100/50">
                  <p className="text-xs font-bold uppercase tracking-wide text-indigo-700 mb-1">🔗 Final Trackable Campaign Link</p>
                  <p className="text-xs text-gray-500 mb-2">
                    Use this link in your {PLATFORM_LABELS[form.platform || 'google'] || form.platform} campaign. Clicks and purchases will automatically associate to this ad campaign.
                  </p>
                  <div className="flex gap-2 items-center">
                    <input
                      type="text"
                      readOnly
                      id="ads-campaign-final-url"
                      className="w-full rounded border border-indigo-200 px-3 py-1.5 text-xs text-gray-700 bg-white select-all font-mono"
                      value={(() => {
                        try {
                          let target = form.target_url || '';
                          if (!target) return '';
                          if (!/^https?:\/\//i.test(target)) {
                            const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || (typeof window !== 'undefined' ? window.location.origin : 'https://www.stationeryjunction.com');
                            target = `${baseUrl.replace(/\/$/, '')}/${target.replace(/^\//, '')}`;
                          }
                          const url = new URL(target);
                          url.searchParams.set('ad_id', editAd?.id || 'CAMPAIGN_ID_AUTO_GENERATED');
                          
                          const source = form.utm_source || (form.platform === 'google' ? 'google' : form.platform === 'meta' ? 'facebook' : form.platform === 'both' ? 'paid' : form.platform === 'social' ? 'social' : form.platform === 'email' ? 'newsletter' : form.platform === 'qr' ? 'offline' : form.platform === 'whatsapp' ? 'whatsapp' : 'paid');
                          const medium = form.utm_medium || (form.platform === 'social' ? 'post' : form.platform === 'email' ? 'email' : form.platform === 'qr' ? 'qr' : form.platform === 'whatsapp' ? 'broadcast' : 'cpc');
                          const campaign = form.utm_campaign || (form.name || '').toLowerCase().replace(/\s+/g, '_');

                          url.searchParams.set('utm_source', source);
                          url.searchParams.set('utm_medium', medium);
                          if (campaign) url.searchParams.set('utm_campaign', campaign);
                          return url.toString();
                        } catch (e) {
                          return form.target_url || '';
                        }
                      })()}
                    />
                    <button
                      type="button"
                      onClick={() => {
                        const val = (document.getElementById('ads-campaign-final-url') as HTMLInputElement)?.value;
                        if (val) {
                          navigator.clipboard.writeText(val);
                          toast.success('Copied campaign link to clipboard!');
                        }
                      }}
                      className="rounded bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-700 whitespace-nowrap"
                    >
                      Copy Link
                    </button>
                  </div>
                </div>
              )}

              <div className="sm:col-span-2">{inp('notes', 'Internal Notes')}</div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setShowForm(false)}
                className="rounded-lg border px-4 py-2 text-sm hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                id="ads-save-btn"
                onClick={handleSave}
                disabled={saving}
                className="rounded-lg bg-indigo-600 px-6 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50 transition-colors"
              >
                {saving ? 'Saving…' : editAd ? 'Update Campaign' : 'Create Campaign'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}