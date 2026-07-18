'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import RefreshButton from '@/components/Admin/RefreshButton';

interface ReferralSetting {
  segment: string;
  discountType: 'percentage' | 'fixed';
  discountValue: number;
  isActive: boolean;
}

interface ReferralSettings {
  retail: ReferralSetting;
  business: ReferralSetting;
}

interface ReferralOptionManagementProps {
  isModal?: boolean;
  onClose?: () => void;
}

export default function ReferralOptionManagement({ isModal, onClose }: ReferralOptionManagementProps = {}) {
  const { user } = useAuth();
  const [settings, setSettings] = useState<ReferralSettings | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user?.role === 'super_admin') {
      fetchSettings();
    }
  }, [user]);

  const fetchSettings = async () => {
    try {
      const response = await api.get('/referrals/settings');
      setSettings(response.data);
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error) {
      toast.error('Failed to fetch referral settings');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async () => {
    if (!settings) return;
    try {
      await api.put('/referrals/settings', settings);
      toast.success('Referral settings updated successfully');
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error) {
      toast.error('Failed to update referral settings');
    }
  };

  const toggleActive = () => {
    if (!settings) return;
    setSettings({
      ...settings,
      retail: { ...settings.retail, isActive: !settings.retail.isActive },
    });
  };

  const handleValueChange = (value: string) => {
    if (!settings) return;
    setSettings({
      ...settings,
      retail: { ...settings.retail, discountValue: parseFloat(value) || 0 },
    });
  };

  const handleTypeChange = (type: 'percentage' | 'fixed') => {
    if (!settings) return;
    setSettings({
      ...settings,
      retail: { ...settings.retail, discountType: type },
    });
  };

  if (user?.role !== 'super_admin')
    return <div className="p-6 font-bold text-red-500">Access Denied</div>;
  if (loading || !settings)
    return (
      <div className="flex items-center justify-center p-6">
        <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-blue-600"></div>
      </div>
    );

  return (
    <div className={isModal ? "w-full" : "mx-auto max-w-4xl rounded-lg bg-white p-6 shadow-md"}>
      <div className="mb-8 flex items-center justify-between border-b pb-4">
        <h2 className="flex items-center gap-3 text-2xl font-bold">
          <svg
            className="h-6 w-6 text-blue-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
            />
          </svg>
          Referral Bonus Settings
          <RefreshButton onRefresh={fetchSettings} />
        </h2>
        <div className="flex items-center gap-2">
          {isModal && onClose ? (
            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors focus:outline-none"
              aria-label="Close"
            >
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          ) : (
            <div className="rounded-full border bg-gray-50 px-3 py-1 text-xs font-medium text-gray-400">
              Admin Panel / Referral Bonus
            </div>
          )}
        </div>
      </div>

      <div className="mb-8 overflow-hidden rounded-xl border shadow-sm">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b bg-slate-50">
              <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">Segment</th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">
                Discount Type
              </th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-slate-700">Value</th>
              <th className="px-6 py-4 text-center text-sm font-semibold text-slate-700">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            <tr className="transition-colors hover:bg-slate-50/50">
              <td className="whitespace-nowrap px-6 py-4">
                <div className="font-bold capitalize text-slate-800">Retail Customers</div>
                <div className="text-xs text-slate-500">Settings for retail segment referrals</div>
              </td>
              <td className="whitespace-nowrap px-6 py-4 text-sm">
                <select
                  value={settings.retail.discountType}
                  onChange={(e) => handleTypeChange(e.target.value as any)}
                  className="w-full rounded-lg border-2 border-slate-200 bg-white px-3 py-1.5 font-medium text-slate-700 transition-all focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100 md:w-auto"
                >
                  <option value="percentage">Percentage (%)</option>
                  <option value="fixed">Fixed Value (₹)</option>
                </select>
              </td>
              <td className="whitespace-nowrap px-6 py-4">
                <div className="relative w-32">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 font-medium text-slate-400">
                    {settings.retail.discountType === 'percentage' ? '' : '₹'}
                  </span>
                  <input
                    type="number"
                    value={settings.retail.discountValue}
                    onChange={(e) => handleValueChange(e.target.value)}
                    className={`w-full rounded-lg border-2 border-slate-200 pb-1.5 pt-1.5 font-bold text-slate-800 transition-all focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100 ${settings.retail.discountType === 'percentage' ? 'px-3 pr-6 text-right' : 'pl-8 pr-3'}`}
                    placeholder="0"
                  />
                  {settings.retail.discountType === 'percentage' && (
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 font-bold text-slate-400">
                      %
                    </span>
                  )}
                </div>
              </td>
              <td className="whitespace-nowrap px-6 py-4 text-center">
                <button
                  onClick={() => toggleActive()}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                    settings.retail.isActive ? 'bg-blue-600' : 'bg-slate-200'
                  }`}
                >
                  <span className="sr-only">Toggle segment status</span>
                  <span
                    aria-hidden="true"
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      settings.retail.isActive ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
                <div
                  className={`mt-1 text-[10px] font-bold uppercase ${settings.retail.isActive ? 'text-blue-600' : 'text-slate-400'}`}
                >
                  {settings.retail.isActive ? 'ACTIVE' : 'INACTIVE'}
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="flex flex-col items-center justify-between gap-4 rounded-xl border border-slate-200 bg-slate-50 p-4 sm:flex-row">
        <div className="flex items-start gap-3">
          <div className="rounded-lg bg-blue-100 p-2 text-blue-600">
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-800">Referral Rule:</h4>
            <p className="text-xs leading-relaxed text-slate-600">
              Referral codes are only available for retail customers. Share your code with friends
              to earn bonuses!
            </p>
          </div>
        </div>
        <button
          onClick={handleUpdate}
          className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-8 py-3 text-sm font-bold text-white shadow-lg transition-all hover:bg-blue-700 hover:shadow-xl active:scale-95 sm:w-auto"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          Save
        </button>
      </div>
    </div>
  );
}
