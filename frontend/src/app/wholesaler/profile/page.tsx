'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import Header from '@/components/Header';
import { toast } from 'react-toastify';
import GeneralFeedbackModal from '@/components/GeneralFeedbackModal';

export default function WholesalerProfile() {
  const { user, fetchUser } = useAuth();
  const router = useRouter();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    alternatePhone: '',
    companyName: '',
    gstin: '',
    locationLink: '',
    address: {
      street: '',
      city: '',
      state: '',
      district: '',
      pincode: '',
      country: '',
      addressLine2: '',
      landmark: '',
      name: '',
    },
  });

  const [initialData, setInitialData] = useState<any>(null);

  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [showDeactivateModal, setShowDeactivateModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);

  const [sendingVerificationCode, setSendingVerificationCode] = useState(false);
  const [verifyingEmail, setVerifyingEmail] = useState(false);
  const [showOtpInput, setShowOtpInput] = useState(false);
  const [verificationCode, setVerificationCode] = useState('');
  const [emailVerificationCooldown, setEmailVerificationCooldown] = useState(0);

  useEffect(() => {
    if (emailVerificationCooldown > 0) {
      const timer = setTimeout(() => {
        setEmailVerificationCooldown((prev) => prev - 1);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [emailVerificationCooldown]);

  const handleRequestVerification = async () => {
    if (!formData.email) {
      toast.error('Please enter an email address first.');
      return;
    }
    try {
      setSendingVerificationCode(true);
      const response = await api.post('/users/request-email-verification');
      toast.success('Verification code sent to your email.');
      setShowOtpInput(true);
      setEmailVerificationCooldown(60);
      if (response.data?.code) {
        toast.info(`[Dev/Test Mode] Verification code: ${response.data.code}`, { autoClose: 10000 });
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to send verification code.');
    } finally {
      setSendingVerificationCode(false);
    }
  };

  const handleVerifyCode = async () => {
    if (!verificationCode || verificationCode.length !== 6) {
      toast.error('Please enter a valid 6-digit code.');
      return;
    }
    try {
      setVerifyingEmail(true);
      await api.post('/users/verify-email', { code: verificationCode });
      toast.success('Email verified successfully!');
      setShowOtpInput(false);
      setVerificationCode('');
      await fetchUser();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Invalid or expired verification code.');
    } finally {
      setVerifyingEmail(false);
    }
  };

  useEffect(() => {
    if (user) {
      const data = {
        name: user.name || '',
        email: user.email || '',
        phone: (user as any).phone || '',
        alternatePhone: (user as any).alternatePhone || '',
        companyName: (user as any).companyName || '',
        gstin: (user as any).gstin || '',
        locationLink: (user as any).locationLink || '',
        address: {
          street: (user as any).address?.street || '',
          city: (user as any).address?.city || '',
          state: (user as any).address?.state || '',
          district: (user as any).address?.district || '',
          pincode: (user as any).address?.pincode || '',
          country: (user as any).address?.country || '',
          addressLine2: (user as any).address?.addressLine2 || '',
          landmark: (user as any).address?.landmark || '',
          name: (user as any).address?.name || '',
        },
      };
      setFormData(data);
      setInitialData(data);
    }
  }, [user]);

  const isChanged = useMemo(() => {
    if (!initialData) return false;
    return JSON.stringify(formData) !== JSON.stringify(initialData);
  }, [formData, initialData]);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await api.put(`/users/${user?._id}`, formData);
      toast.success('Business profile updated successfully');
      setInitialData(formData);
    } catch (error: any) {
      const errorMsg =
        error.response?.data?.message || error.response?.data?.detail || 'Failed to update profile';
      toast.error(errorMsg);
      console.error('Profile update error:', error.response?.data || error);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }
    try {
      await api.put(`/users/${user?._id}/password`, {
        currentPassword: passwordData.currentPassword,
        newPassword: passwordData.newPassword,
      });
      toast.success('Password changed successfully');
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
      setShowPasswordForm(false);
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to change password');
    }
  };

  const handleDeactivate = async () => {
    try {
      await api.put('/users/me/deactivate');
      toast.success('Account deactivated successfully');
      setTimeout(() => {
        window.location.href = '/login';
      }, 1000);
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to deactivate account');
    }
  };

  const handleDeleteAccount = async () => {
    try {
      await api.delete('/auth/me');
      toast.success('Your account has been permanently deleted.');
      setTimeout(() => {
        window.location.href = '/login';
      }, 1000);
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to delete account');
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      <Header />

      <div className="container mx-auto flex-1 px-4 py-8 pb-24 md:pb-8">
        <div className="mb-6 flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="rounded-full p-2 transition-colors hover:bg-gray-100"
            title="Go Back"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
              />
            </svg>
          </button>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">Business Profile</h1>
        </div>

        <div className="mb-8 rounded-2xl border border-gray-100 bg-white p-8 shadow-sm">
          <h2 className="mb-8 flex items-center gap-3 text-xl font-black text-gray-800">
            <span className="h-8 w-2 rounded-full bg-emerald-600"></span>
            WHOLESALE ACCOUNT DETAILS
          </h2>

          <form onSubmit={handleUpdate} className="space-y-8">
            <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
              <div>
                <label className="mb-2 block text-xs font-black uppercase tracking-widest text-gray-400">
                  Full Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 font-bold outline-none transition-all focus:bg-white focus:ring-2 focus:ring-emerald-500"
                  required
                />
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-xs font-black uppercase tracking-widest text-gray-400">
                    Email Address
                  </label>
                  {user?.email && (
                    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ${
                      (user as any).isEmailVerified 
                        ? 'bg-green-50 text-green-700 border border-green-200' 
                        : 'bg-yellow-50 text-yellow-700 border border-yellow-200'
                    }`}>
                      {(user as any).isEmailVerified ? (
                        <>
                          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                          </svg>
                          Verified
                        </>
                      ) : (
                        'Unverified'
                      )}
                    </span>
                  )}
                </div>
                <div className="relative">
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 font-bold outline-none transition-all focus:bg-white focus:ring-2 focus:ring-emerald-500 pr-24"
                  />
                  {user?.email && !(user as any).isEmailVerified && (
                    <button
                      type="button"
                      onClick={handleRequestVerification}
                      disabled={sendingVerificationCode || emailVerificationCooldown > 0}
                      className="absolute right-3 top-3.5 text-xs font-bold text-emerald-600 hover:text-emerald-700 disabled:text-gray-400"
                    >
                      {emailVerificationCooldown > 0 
                        ? `${emailVerificationCooldown}s` 
                        : sendingVerificationCode 
                          ? 'Sending...' 
                          : 'Verify'}
                    </button>
                  )}
                </div>
                {showOtpInput && (
                  <div className="mt-2 rounded-xl border border-emerald-100 bg-emerald-50/30 p-4">
                    <label className="block text-xs font-bold text-emerald-800 mb-1.5 uppercase tracking-wider">Verification Code</label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        maxLength={6}
                        value={verificationCode}
                        onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                        placeholder="000000"
                        className="w-32 rounded-xl border border-gray-200 px-3 py-2 text-center font-mono text-sm outline-none focus:border-emerald-500"
                      />
                      <button
                        type="button"
                        onClick={handleVerifyCode}
                        disabled={verifyingEmail || verificationCode.length !== 6}
                        className="rounded-xl bg-emerald-600 px-5 py-2 text-xs font-bold text-white hover:bg-emerald-700 disabled:bg-gray-300"
                      >
                        {verifyingEmail ? 'Verifying...' : 'Submit'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
              <div>
                <label className="mb-2 block text-xs font-black uppercase tracking-widest text-gray-400">
                  Phone (Primary)
                </label>
                <div className="relative">
                  <input
                    type="tel"
                    value={formData.phone}
                    disabled
                    className="w-full cursor-not-allowed rounded-xl border border-gray-200 bg-gray-100 px-4 py-3 font-medium text-gray-500"
                  />
                  <span className="absolute right-4 top-3.5 opacity-50 grayscale" title="Locked">
                    🔒
                  </span>
                </div>
              </div>
              
              <div>
                <label className="mb-2 block text-xs font-black uppercase tracking-widest text-gray-400">
                  Alternate Phone
                </label>
                <input
                  type="tel"
                  value={formData.alternatePhone}
                  onChange={(e) => setFormData({ ...formData, alternatePhone: e.target.value })}
                  className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 font-bold outline-none transition-all focus:bg-white focus:ring-2 focus:ring-emerald-500"
                  placeholder="Optional alternate phone"
                />
              </div>

              <div>
                <label className="mb-2 block text-xs font-black uppercase tracking-widest text-gray-400">
                  Company Name *
                </label>
                <input
                  type="text"
                  value={formData.companyName}
                  onChange={(e) => setFormData({ ...formData, companyName: e.target.value })}
                  className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 font-bold outline-none transition-all focus:bg-white focus:ring-2 focus:ring-emerald-500"
                  required
                  placeholder="Official business name"
                />
              </div>
              <div>
                <label className="mb-2 block text-xs font-black uppercase tracking-widest text-gray-400">
                  GSTIN
                </label>
                <input
                  type="text"
                  value={formData.gstin}
                  onChange={(e) =>
                    setFormData({ ...formData, gstin: e.target.value.toUpperCase() })
                  }
                  className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 font-bold outline-none transition-all focus:bg-white focus:ring-2 focus:ring-emerald-500"
                  maxLength={15}
                  placeholder="15-digit Tax ID (Optional)"
                />
              </div>
              <div>
                <label className="mb-2 block text-xs font-black uppercase tracking-widest text-gray-400">
                  Location Link
                </label>
                <input
                  type="url"
                  value={formData.locationLink}
                  onChange={(e) => setFormData({ ...formData, locationLink: e.target.value })}
                  className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 font-medium outline-none transition-all focus:bg-white focus:ring-2 focus:ring-emerald-500"
                  placeholder="Google Maps URL"
                />
              </div>
            </div>

            <div className="border-t border-gray-100 pt-4">
              <h3 className="mb-6 px-1 text-xs font-black uppercase tracking-widest text-gray-400">
                Registered Business Address
              </h3>
              <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
                <div className="md:col-span-2 lg:col-span-3">
                  <label className="mb-2 block text-xs font-bold text-gray-500">
                    Recipient Name
                  </label>
                  <input
                    type="text"
                    value={formData.address.name || ''}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        address: { ...formData.address, name: e.target.value },
                      })
                    }
                    className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 font-medium outline-none transition-all focus:ring-2 focus:ring-emerald-500"
                    placeholder="Full name of recipient"
                  />
                </div>
                <div className="md:col-span-2 lg:col-span-3">
                  <label className="mb-2 block text-xs font-bold text-gray-500">
                    Street Address
                  </label>
                  <input
                    type="text"
                    value={formData.address.street}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        address: { ...formData.address, street: e.target.value },
                      })
                    }
                    className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 font-medium outline-none transition-all focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
                <div className="md:col-span-2 lg:col-span-3">
                  <label className="mb-2 block text-xs font-bold text-gray-500">
                    Address Line 2 (Optional)
                  </label>
                  <input
                    type="text"
                    value={formData.address.addressLine2 || ''}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        address: { ...formData.address, addressLine2: e.target.value },
                      })
                    }
                    className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 font-medium outline-none transition-all focus:ring-2 focus:ring-emerald-500"
                    placeholder="Apartment, suite, unit, etc."
                  />
                </div>
                <div className="md:col-span-2 lg:col-span-3">
                  <label className="mb-2 block text-xs font-bold text-gray-500">
                    Landmark (Optional)
                  </label>
                  <input
                    type="text"
                    value={formData.address.landmark || ''}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        address: { ...formData.address, landmark: e.target.value },
                      })
                    }
                    className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 font-medium outline-none transition-all focus:ring-2 focus:ring-emerald-500"
                    placeholder="Near hospital, next to mall, etc."
                  />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-bold text-gray-500">City</label>
                  <input
                    type="text"
                    value={formData.address.city}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        address: { ...formData.address, city: e.target.value },
                      })
                    }
                    className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 font-medium outline-none transition-all focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-bold text-gray-500">State</label>
                  <input
                    type="text"
                    value={formData.address.state}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        address: { ...formData.address, state: e.target.value },
                      })
                    }
                    className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 font-medium outline-none transition-all focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-bold text-gray-500">District</label>
                  <input
                    type="text"
                    value={formData.address.district}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        address: { ...formData.address, district: e.target.value },
                      })
                    }
                    className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 font-medium outline-none transition-all focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-bold text-gray-500">Pincode</label>
                  <input
                    type="text"
                    value={formData.address.pincode}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        address: { ...formData.address, pincode: e.target.value },
                      })
                    }
                    className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 font-medium outline-none transition-all focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-bold text-gray-500">Country</label>
                  <input
                    type="text"
                    value={formData.address.country}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        address: { ...formData.address, country: e.target.value },
                      })
                    }
                    className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 font-medium outline-none transition-all focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
              </div>
            </div>

            <div className="pt-6">
              <button
                type="submit"
                disabled={!isChanged}
                className={`rounded-2xl px-10 py-4 text-sm font-black uppercase tracking-widest shadow-xl transition-all ${
                  isChanged
                    ? 'bg-emerald-600 text-white shadow-emerald-200 hover:bg-emerald-700 active:scale-95'
                    : 'cursor-not-allowed bg-gray-200 text-gray-400 shadow-none'
                }`}
              >
                SYNC PROFILE CHANGES
              </button>
            </div>
          </form>
        </div>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
          <div className="rounded-2xl border border-gray-100 bg-white p-8 shadow-sm">
            <h2 className="mb-8 flex items-center gap-3 text-lg font-black text-gray-800">
              <span className="h-6 w-2 rounded-full bg-gray-800"></span>
              SECURITY PROTOCOL
            </h2>
            {!showPasswordForm ? (
              <div className="flex flex-col items-start gap-4">
                <p className="text-sm font-medium text-gray-500">
                  Regular password updates are recommended for wholesale accounts.
                </p>
                <button
                  onClick={() => setShowPasswordForm(true)}
                  className="rounded-xl bg-gray-900 px-8 py-3 text-xs font-black uppercase tracking-widest text-white transition-all hover:bg-black"
                >
                  Modify Access Password
                </button>
              </div>
            ) : (
              <form onSubmit={handlePasswordChange} className="space-y-6">
                <div>
                  <label className="mb-2 block text-xs font-bold text-gray-500">
                    CURRENT PASSWORD
                  </label>
                  <input
                    type="password"
                    value={passwordData.currentPassword}
                    onChange={(e) =>
                      setPasswordData({ ...passwordData, currentPassword: e.target.value })
                    }
                    className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 font-bold outline-none focus:ring-2 focus:ring-emerald-500"
                    required
                  />
                </div>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-2 block text-xs font-bold text-gray-500">
                      NEW PASSWORD
                    </label>
                    <input
                      type="password"
                      value={passwordData.newPassword}
                      onChange={(e) =>
                        setPasswordData({ ...passwordData, newPassword: e.target.value })
                      }
                      className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 font-bold outline-none focus:ring-2 focus:ring-emerald-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="mb-2 block text-xs font-bold text-gray-500">
                      CONFIRM NEW
                    </label>
                    <input
                      type="password"
                      value={passwordData.confirmPassword}
                      onChange={(e) =>
                        setPasswordData({ ...passwordData, confirmPassword: e.target.value })
                      }
                      className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 font-bold outline-none focus:ring-2 focus:ring-emerald-500"
                      required
                    />
                  </div>
                </div>
                <div className="flex gap-4 pt-4">
                  <button
                    type="submit"
                    className="flex-1 rounded-xl bg-emerald-600 py-3 text-xs font-black uppercase tracking-widest text-white transition-all hover:bg-emerald-700"
                  >
                    Confirm Change
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowPasswordForm(false);
                      setPasswordData({
                        currentPassword: '',
                        newPassword: '',
                        confirmPassword: '',
                      });
                    }}
                    className="flex-1 rounded-xl bg-gray-100 py-3 text-xs font-black uppercase tracking-widest text-gray-800 transition-all hover:bg-gray-200"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}
          </div>

          <div className="rounded-2xl border border-gray-100 bg-white p-8 shadow-sm">
            <h2 className="mb-8 flex items-center gap-3 text-lg font-black text-gray-800">
              <span className="h-6 w-2 rounded-full bg-red-600"></span>
              ACCOUNT ARCHIVE
            </h2>
            <div className="rounded-2xl border-2 border-dashed border-red-100 bg-red-50/30 p-6 space-y-6">
              <div>
                <p className="mb-2 text-sm font-black uppercase tracking-tight text-gray-900">
                  Deactivate Business Outlet
                </p>
                <p className="mb-4 text-xs font-medium leading-relaxed text-gray-500">
                  This will pause your wholesale status. You will need to contact support to re-enable
                  ordering after deactivation.
                </p>
                <button
                  type="button"
                  onClick={() => setShowDeactivateModal(true)}
                  className="w-full rounded-xl border-2 border-red-600 bg-white py-3 text-xs font-black uppercase tracking-widest text-red-600 transition-all hover:bg-red-600 hover:text-white"
                >
                  Restrict Account Access
                </button>
              </div>
              <div className="border-t border-red-100/50 pt-4">
                <p className="mb-2 text-sm font-black uppercase tracking-tight text-red-800">
                  Permanently Delete Business Account
                </p>
                <p className="mb-4 text-xs font-medium leading-relaxed text-gray-500">
                  This will permanently delete all records of your wholesale business and account. This action is irreversible.
                </p>
                <button
                  type="button"
                  onClick={() => setShowDeleteModal(true)}
                  className="w-full rounded-xl bg-red-700 py-3 text-xs font-black uppercase tracking-widest text-white transition-all hover:bg-red-850"
                >
                  PERMANENTLY DELETE ACCOUNT
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Feedback Section */}
        <div className="group relative mb-8 mt-8 overflow-hidden rounded-3xl bg-gradient-to-r from-emerald-600 to-teal-700 p-10 text-white shadow-2xl">
          <div className="absolute right-0 top-0 transform p-4 opacity-10 transition-transform duration-700 group-hover:rotate-12 group-hover:scale-125">
            <svg className="h-48 w-48" fill="currentColor" viewBox="0 0 24 24">
              <path d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
            </svg>
          </div>
          <div className="relative z-10">
            <h2 className="mb-4 flex items-center gap-4 text-3xl font-black uppercase tracking-tighter">
              Partner Experience
            </h2>
            <p className="mb-8 max-w-xl text-lg font-medium leading-relaxed text-emerald-50 opacity-90">
              We value our business relationships. Share your thoughts on how we can improve our
              logistics, pricing, or service for your business.
            </p>
            <button
              onClick={() => setShowFeedbackModal(true)}
              className="rounded-2xl bg-white px-10 py-4 text-sm font-black uppercase tracking-widest text-emerald-700 shadow-xl transition-all hover:bg-emerald-50 active:scale-95"
            >
              Submit Partner Feedback
            </button>
          </div>
        </div>

        <GeneralFeedbackModal
          isOpen={showFeedbackModal}
          onClose={() => setShowFeedbackModal(false)}
        />

        {showDeactivateModal && (
          <div
            className="fixed inset-0 z-[1000] flex items-center justify-center bg-gray-900/80 px-4 backdrop-blur-md"
            onClick={() => setShowDeactivateModal(false)}
          >
            <div
              className="animate-scale-up w-full max-w-md rounded-3xl bg-white p-10 shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-red-50 text-red-600">
                <svg className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
              </div>
              <h3 className="mb-4 text-center text-2xl font-black uppercase tracking-tight text-gray-900">
                Confirm Restriction?
              </h3>
              <p className="mb-10 text-center font-medium text-gray-500">
                Your business account status will be set to inactive. Proceed with caution.
              </p>
              <div className="flex flex-col gap-3">
                <button
                  onClick={handleDeactivate}
                  className="w-full rounded-2xl bg-red-600 py-4 text-sm font-black uppercase tracking-widest text-white shadow-xl shadow-red-200 transition-all hover:bg-red-700"
                >
                  DEACTIVATE NOW
                </button>
                <button
                  onClick={() => setShowDeactivateModal(false)}
                  className="w-full rounded-2xl bg-gray-100 py-4 text-sm font-black uppercase tracking-widest text-gray-800 transition-all hover:bg-gray-200"
                >
                  DISMISS
                </button>
              </div>
            </div>
          </div>
        )}

        {showDeleteModal && (
          <div
            className="fixed inset-0 z-[1000] flex items-center justify-center bg-gray-900/80 px-4 backdrop-blur-md"
            onClick={() => setShowDeleteModal(false)}
          >
            <div
              className="animate-scale-up w-full max-w-md rounded-3xl bg-white p-10 shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-red-50 text-red-600">
                <svg className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </div>
              <h3 className="mb-4 text-center text-2xl font-black uppercase tracking-tight text-gray-900">
                Confirm Deletion?
              </h3>
              <p className="mb-10 text-center font-medium text-gray-500">
                This will permanently delete all records of your wholesale business and account. This action cannot be undone.
              </p>
              <div className="flex flex-col gap-3">
                <button
                  onClick={handleDeleteAccount}
                  className="w-full rounded-2xl bg-red-700 py-4 text-sm font-black uppercase tracking-widest text-white shadow-xl shadow-red-200 transition-all hover:bg-red-800"
                >
                  PERMANENTLY DELETE
                </button>
                <button
                  onClick={() => setShowDeleteModal(false)}
                  className="w-full rounded-2xl bg-gray-100 py-4 text-sm font-black uppercase tracking-widest text-gray-800 transition-all hover:bg-gray-200"
                >
                  DISMISS
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
