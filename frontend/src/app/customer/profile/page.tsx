'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import Header from '@/components/Header';
import SearchableSelect from '@/components/SearchableSelect';
import { toast } from 'react-toastify';

export default function Profile() {
  const { user, loading: authLoading, fetchUser } = useAuth();
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
  const [showCurrentPwd, setShowCurrentPwd] = useState(false);
  const [showNewPwd, setShowNewPwd] = useState(false);
  const [showConfirmPwd, setShowConfirmPwd] = useState(false);
  const [showDeactivateModal, setShowDeactivateModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const [profileStates, setProfileStates] = useState<string[]>([]);
  const [profileDistricts, setProfileDistricts] = useState<string[]>([]);
  const [pincodeServiceable, setPincodeServiceable] = useState<boolean | null>(null);
  const [checkingServiceability, setCheckingServiceability] = useState(false);

  const [referralScheme, setReferralScheme] = useState<{
    isActive: boolean;
    discountType: 'percentage' | 'fixed';
    discountValue: number;
  } | null>(null);
  const [loadingScheme, setLoadingScheme] = useState(false);

  const [hasDeliveredOrder, setHasDeliveredOrder] = useState(false);

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

  const fetchProfileStates = async () => {
    try {
      const res = await api.get('/pincodes/states', { skipAccessToken: true } as any);
      setProfileStates(res.data || []);
    } catch {
      setProfileStates([]);
    }
  };

  const fetchProfileDistricts = async (state: string) => {
    if (!state) {
      setProfileDistricts([]);
      return;
    }
    try {
      const res = await api.get(`/pincodes/districts?state=${encodeURIComponent(state)}`, {
        skipAccessToken: true,
      } as any);
      setProfileDistricts(res.data || []);
    } catch {
      setProfileDistricts([]);
    }
  };

  const checkPincodeServiceability = async (pincode: string) => {
    const digits = pincode.replace(/\D/g, '');
    if (!digits || digits.length !== 6) {
      setPincodeServiceable(null);
      return;
    }
    try {
      setCheckingServiceability(true);
      const userRole = (user as any)?.role || 'customer';
      const response = await api.get('/delivery-charges/check-serviceability', {
        params: { pincode: digits, userRole },
      });
      setPincodeServiceable(response.data.isServiceable);
    } catch {
      setPincodeServiceable(null);
    } finally {
      setCheckingServiceability(false);
    }
  };

  useEffect(() => {
    fetchProfileStates();
  }, []);

  useEffect(() => {
    const fetchReferralScheme = async () => {
      if ((user as any)?.role === 'customer') {
        try {
          setLoadingScheme(true);
          const res = await api.get('/referrals/scheme');
          setReferralScheme(res.data);
        } catch (error) {
          console.error('Failed to fetch referral scheme:', error);
        } finally {
          setLoadingScheme(false);
        }
      }
    };
    fetchReferralScheme();

    const checkDeliveredOrders = async () => {
      if ((user as any)?.role === 'customer') {
        try {
          const res = await api.get('/orders', { params: { limit: 1, status: 'delivered' } });
          if (res.data && res.data.total > 0) {
            setHasDeliveredOrder(true);
          }
        } catch (error) {
          console.error('Failed to fetch orders:', error);
        }
      }
    };
    checkDeliveredOrders();
  }, [user]);

  useEffect(() => {
    if (user) {
      const addr = (user as any).address || {};
      const data = {
        name: user.name || '',
        email: user.email || '',
        phone: (user as any).phone || '',
        alternatePhone: (user as any).alternatePhone || '',
        companyName: (user as any).companyName || '',
        gstin: (user as any).gstin || '',
        locationLink: (user as any).locationLink || '',
        address: {
          street: addr.street || '',
          city: addr.city || '',
          state: addr.state || '',
          district: addr.district || '',
          pincode: (addr.pincode || '').replace(/\D/g, '').slice(0, 6),
          country: addr.country || 'India',
          addressLine2: addr.addressLine2 || '',
          landmark: addr.landmark || '',
          name: addr.name || '',
        },
      };
      setFormData(data);
      setInitialData(data);
      if (data.address.state) {
        fetchProfileDistricts(data.address.state);
      } else {
        setProfileDistricts([]);
      }
      const pin = data.address.pincode;
      if (pin && pin.length === 6) checkPincodeServiceability(pin);
      else setPincodeServiceable(null);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const isChanged = useMemo(() => {
    if (!initialData) return false;
    return JSON.stringify(formData) !== JSON.stringify(initialData);
  }, [formData, initialData]);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();

    const pinDigits = (formData.address.pincode || '').replace(/\D/g, '').slice(0, 6);
    if (!formData.address.state?.trim() || !formData.address.district?.trim()) {
      toast.error('Please select state and district from the lists.');
      return;
    }
    if (pinDigits.length !== 6) {
      toast.error('Please enter a valid 6-digit pincode.');
      return;
    }

    const payload = {
      ...formData,
      address: { ...formData.address, pincode: pinDigits },
    };
    try {
      await api.put(`/users/${user?._id}`, payload);
      toast.success('Profile updated successfully');
      setFormData(payload);
      setInitialData(payload);
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

  if (authLoading) {
    return (
      <div className="flex min-h-screen flex-col bg-gray-50">
        <Header />
        <div className="flex flex-1 items-center justify-center">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600" />
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex min-h-screen flex-col bg-gray-50">
        <Header />
        <div className="flex flex-1 flex-col items-center justify-center gap-4 px-4 text-center">
          <svg className="h-16 w-16 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          <h2 className="text-xl font-semibold text-gray-800">Sign in to view your profile</h2>
          <p className="text-gray-500">You need to be logged in to access this page.</p>
          <button
            onClick={() => router.push('/login')}
            className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-blue-700"
          >
            Sign In
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      <Header />

      <div className="container mx-auto flex-1 px-4 py-8 pb-24 md:pb-8">
        <div className="mb-6 flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="rounded-full p-2 transition-colors hover:bg-gray-100"
            aria-label="Go back"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
              />
            </svg>
          </button>
          <h1 className="text-3xl font-bold">Profile</h1>
        </div>

        <div className="mb-6 rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
          <h2 className="mb-6 flex items-center gap-2 text-xl font-semibold">
            <span className="h-6 w-1.5 rounded-full bg-blue-600"></span>
            Personal & Business Details
          </h2>

          {/* Referral Code Section */}
          {(user as any)?.role === 'customer' && hasDeliveredOrder && (
            <div className="mb-8 flex flex-col items-center justify-between gap-4 rounded-xl border border-blue-100 bg-blue-50 p-4 sm:flex-row">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-blue-600 p-2 text-white shadow-md">
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
                    />
                  </svg>
                </div>
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-blue-600">
                    Your Referral Code
                  </p>
                  <p className="text-sm font-medium text-blue-800">
                    {loadingScheme ? (
                      'Loading referral benefits...'
                    ) : referralScheme ? (
                      !referralScheme.isActive || referralScheme.discountValue <= 0 ? (
                        'Referrals are currently inactive.'
                      ) : (
                        `Friends you refer get ${
                          referralScheme.discountType === 'percentage'
                            ? `${referralScheme.discountValue}%`
                            : `₹${referralScheme.discountValue}`
                        } off their first order!`
                      )
                    ) : (
                      'Share this code with friends to earn bonuses!'
                    )}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="rounded-lg border-2 border-dashed border-blue-300 bg-white px-6 py-2 text-xl font-black tracking-widest text-blue-700 shadow-inner">
                  {user?.referralCode || '------'}
                </div>
                <button
                  type="button"
                  onClick={() => {
                    if (user?.referralCode) {
                      navigator.clipboard.writeText(user.referralCode);
                      toast.info('Referral code copied!');
                    }
                  }}
                  className="rounded-lg bg-blue-100 p-2.5 text-blue-600 transition-colors hover:bg-blue-200"
                  title="Copy Code"
                >
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"
                    />
                  </svg>
                </button>
              </div>
            </div>
          )}

          <form onSubmit={handleUpdate} className="space-y-6">
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-sm font-medium text-gray-700">Email</label>
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
                    className="w-full rounded-lg border border-gray-300 px-4 py-2 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500 pr-24"
                  />
                  {user?.email && !(user as any).isEmailVerified && (
                    <button
                      type="button"
                      onClick={handleRequestVerification}
                      disabled={sendingVerificationCode || emailVerificationCooldown > 0}
                      className="absolute right-3 top-2.5 text-xs font-bold text-blue-600 hover:text-blue-700 disabled:text-gray-400"
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
                  <div className="mt-2 rounded-lg border border-blue-100 bg-blue-50/50 p-3">
                    <label className="block text-xs font-semibold text-blue-800 mb-1">Enter 6-digit verification code</label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        maxLength={6}
                        value={verificationCode}
                        onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                        placeholder="000000"
                        className="w-32 rounded-lg border border-gray-300 px-3 py-1.5 text-center font-mono text-sm outline-none focus:border-blue-500"
                      />
                      <button
                        type="button"
                        onClick={handleVerifyCode}
                        disabled={verifyingEmail || verificationCode.length !== 6}
                        className="rounded-lg bg-blue-600 px-4 py-1.5 text-xs font-bold text-white hover:bg-blue-700 disabled:bg-gray-300"
                      >
                        {verifyingEmail ? 'Verifying...' : 'Submit'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Phone Number</label>
                <div className="relative">
                  <input
                    type="tel"
                    value={formData.phone}
                    disabled
                    className="w-full cursor-not-allowed rounded-lg border border-gray-300 bg-gray-50 px-4 py-2 text-gray-500"
                  />
                  <span
                    className="absolute right-3 top-2.5 text-gray-400"
                    title="Phone cannot be changed"
                  >
                    🔒
                  </span>
                </div>
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Alternate Phone</label>
                <input
                  type="tel"
                  value={formData.alternatePhone}
                  onChange={(e) => setFormData({ ...formData, alternatePhone: e.target.value })}
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
                  placeholder="Optional alternate phone"
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Company Name {(user as any)?.role === 'wholesaler' ? '*' : ''}
                </label>
                <input
                  type="text"
                  value={formData.companyName}
                  onChange={(e) => setFormData({ ...formData, companyName: e.target.value })}
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
                  required={(user as any)?.role === 'wholesaler'}
                  placeholder="Enter company name"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  GSTIN {(user as any)?.role === 'wholesaler' ? '*' : ''}
                </label>
                <input
                  type="text"
                  value={formData.gstin}
                  onChange={(e) =>
                    setFormData({ ...formData, gstin: e.target.value.toUpperCase() })
                  }
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
                  required={(user as any)?.role === 'wholesaler'}
                  maxLength={15}
                  placeholder="15-digit GSTIN"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Location (Google Maps Link)
                </label>
                <input
                  type="url"
                  value={formData.locationLink}
                  onChange={(e) => setFormData({ ...formData, locationLink: e.target.value })}
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
                  placeholder="https://maps.google.com/..."
                />
              </div>
            </div>

            <h3 className="mb-4 mt-8 border-b pb-2 text-lg font-semibold text-gray-800">
              Address Information
            </h3>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              <div className="md:col-span-2 lg:col-span-3">
                <label className="mb-1 block text-sm font-medium text-gray-700">
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
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
                  placeholder="Full name of recipient"
                />
              </div>
              <div className="md:col-span-2 lg:col-span-3">
                <label className="mb-1 block text-sm font-medium text-gray-700">
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
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
                  placeholder="House No, Building, Area"
                />
              </div>
              <div className="md:col-span-2 lg:col-span-3">
                <label className="mb-1 block text-sm font-medium text-gray-700">
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
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
                  placeholder="Apartment, suite, unit, etc."
                />
              </div>
              <div className="md:col-span-2 lg:col-span-3">
                <label className="mb-1 block text-sm font-medium text-gray-700">
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
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
                  placeholder="Near hospital, next to mall, etc."
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">State *</label>
                <SearchableSelect
                  options={profileStates}
                  value={formData.address.state}
                  onChange={(val) => {
                    setFormData({
                      ...formData,
                      address: { ...formData.address, state: val, district: '' },
                    });
                    fetchProfileDistricts(val);
                  }}
                  placeholder="Select State"
                  required
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">District *</label>
                <SearchableSelect
                  options={profileDistricts}
                  value={formData.address.district || ''}
                  onChange={(val) =>
                    setFormData({
                      ...formData,
                      address: { ...formData.address, district: val },
                    })
                  }
                  placeholder="Select District"
                  disabled={!formData.address.state}
                  required
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">City *</label>
                <input
                  type="text"
                  value={formData.address.city}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      address: { ...formData.address, city: e.target.value },
                    })
                  }
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Pincode *</label>
                <input
                  type="text"
                  inputMode="numeric"
                  value={formData.address.pincode}
                  onChange={(e) => {
                    const v = e.target.value.replace(/\D/g, '').slice(0, 6);
                    setFormData({
                      ...formData,
                      address: { ...formData.address, pincode: v },
                    });
                    if (v.length === 6) checkPincodeServiceability(v);
                    else setPincodeServiceable(null);
                  }}
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
                  required
                  maxLength={6}
                  pattern="[0-9]{6}"
                />
                {checkingServiceability && (
                  <p className="mt-1 text-xs text-gray-500">Checking serviceability…</p>
                )}
                {pincodeServiceable === false && !checkingServiceability && (
                  <p className="mt-1 text-sm text-amber-800">
                    Delivery may not be available to this pincode. You can still save your address.
                  </p>
                )}
                {pincodeServiceable === true && !checkingServiceability && (
                  <p className="mt-1 text-xs text-green-600">Delivery available to this pincode.</p>
                )}
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Country</label>
                <input
                  type="text"
                  value={formData.address.country}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      address: { ...formData.address, country: e.target.value },
                    })
                  }
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="pt-4">
              <button
                type="submit"
                disabled={!isChanged}
                className={`rounded-lg px-8 py-3 font-bold text-white shadow-md transition-all ${
                  isChanged
                    ? 'bg-blue-600 hover:bg-blue-700 active:scale-95'
                    : 'cursor-not-allowed bg-gray-400'
                }`}
              >
                Update Profile
              </button>
            </div>
          </form>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
            <h2 className="mb-6 flex items-center gap-2 text-xl font-semibold">
              <span className="h-6 w-1.5 rounded-full bg-orange-500"></span>
              Security
            </h2>
            {!showPasswordForm ? (
              <div>
                <p className="mb-4 text-gray-600">You can change your account password here.</p>
                <button
                  onClick={() => setShowPasswordForm(true)}
                  className="rounded-lg bg-gray-800 px-6 py-2 font-medium text-white transition-all hover:bg-gray-900"
                >
                  Change Password
                </button>
              </div>
            ) : (
              <form onSubmit={handlePasswordChange} className="space-y-4">
                <div>
                  <label htmlFor="current-password" className="mb-1 block text-sm font-medium text-gray-700">
                    Current Password
                  </label>
                  <div className="relative">
                    <input
                      id="current-password"
                      type={showCurrentPwd ? 'text' : 'password'}
                      autoComplete="current-password"
                      value={passwordData.currentPassword}
                      onChange={(e) =>
                        setPasswordData({ ...passwordData, currentPassword: e.target.value })
                      }
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 pr-10 outline-none focus:ring-2 focus:ring-orange-500"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowCurrentPwd(!showCurrentPwd)}
                      aria-label={showCurrentPwd ? 'Hide password' : 'Show password'}
                      className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600"
                    >
                      {showCurrentPwd ? '👁️' : '👁️‍🗨️'}
                    </button>
                  </div>
                </div>
                <div>
                  <label htmlFor="new-password" className="mb-1 block text-sm font-medium text-gray-700">
                    New Password
                  </label>
                  <div className="relative">
                    <input
                      id="new-password"
                      type={showNewPwd ? 'text' : 'password'}
                      autoComplete="new-password"
                      minLength={8}
                      value={passwordData.newPassword}
                      onChange={(e) =>
                        setPasswordData({ ...passwordData, newPassword: e.target.value })
                      }
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 pr-10 outline-none focus:ring-2 focus:ring-orange-500"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowNewPwd(!showNewPwd)}
                      aria-label={showNewPwd ? 'Hide password' : 'Show password'}
                      className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600"
                    >
                      {showNewPwd ? '👁️' : '👁️‍🗨️'}
                    </button>
                  </div>
                  <p className="mt-1 text-xs text-gray-400">Minimum 8 characters</p>
                </div>
                <div>
                  <label htmlFor="confirm-password" className="mb-1 block text-sm font-medium text-gray-700">
                    Confirm New Password
                  </label>
                  <div className="relative">
                    <input
                      id="confirm-password"
                      type={showConfirmPwd ? 'text' : 'password'}
                      autoComplete="new-password"
                      minLength={8}
                      value={passwordData.confirmPassword}
                      onChange={(e) =>
                        setPasswordData({ ...passwordData, confirmPassword: e.target.value })
                      }
                      className={`w-full rounded-lg border px-3 py-2 pr-10 outline-none focus:ring-2 focus:ring-orange-500 ${
                        passwordData.confirmPassword && passwordData.confirmPassword !== passwordData.newPassword
                          ? 'border-red-400 bg-red-50'
                          : 'border-gray-300'
                      }`}
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPwd(!showConfirmPwd)}
                      aria-label={showConfirmPwd ? 'Hide password' : 'Show password'}
                      className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600"
                    >
                      {showConfirmPwd ? '👁️' : '👁️‍🗨️'}
                    </button>
                  </div>
                  {passwordData.confirmPassword && passwordData.confirmPassword !== passwordData.newPassword && (
                    <p className="mt-1 text-xs text-red-500">Passwords do not match</p>
                  )}
                </div>
                <div className="flex gap-4 pt-2">
                  <button
                    type="submit"
                    className="rounded-lg bg-orange-500 px-6 py-2 font-bold text-white transition-all hover:bg-orange-600"
                  >
                    Update Password
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowPasswordForm(false);
                      setShowCurrentPwd(false);
                      setShowNewPwd(false);
                      setShowConfirmPwd(false);
                      setPasswordData({
                        currentPassword: '',
                        newPassword: '',
                        confirmPassword: '',
                      });
                    }}
                    className="rounded-lg bg-gray-200 px-6 py-2 font-medium text-gray-800 transition-all hover:bg-gray-300"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}
          </div>

          <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
            <h2 className="mb-6 flex items-center gap-2 text-xl font-semibold">
              <span className="h-6 w-1.5 rounded-full bg-red-600"></span>
              Danger Zone
            </h2>
            <div className="space-y-4">
              <div className="rounded-lg border border-red-100 bg-red-50/50 p-4">
                <p className="mb-1 font-medium text-gray-800">Deactivate Account</p>
                <p className="mb-4 text-sm text-red-700">
                  Once you deactivate your account, you will not be able to log in until we
                  re-activate it.
                </p>
                <button
                  onClick={() => setShowDeactivateModal(true)}
                  className="rounded-xl bg-red-600 px-6 py-2 font-bold text-white transition-all hover:bg-red-700"
                >
                  Deactivate My Account
                </button>
              </div>
              <div className="rounded-lg border border-red-200 bg-red-100/30 p-4">
                <p className="mb-1 font-bold text-red-800">Permanently Delete Account</p>
                <p className="mb-4 text-sm text-red-700">
                  All your personal data, orders, and credentials will be permanently erased under the GDPR Right-to-Erasure. This action cannot be undone.
                </p>
                <button
                  onClick={() => setShowDeleteModal(true)}
                  className="rounded-xl bg-red-700 px-6 py-2 font-bold text-white transition-all hover:bg-red-800"
                >
                  Permanently Delete My Account
                </button>
              </div>
            </div>
          </div>
        </div>


        {showDeactivateModal && (
          <div
            className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/60 backdrop-blur-sm"
            onClick={() => setShowDeactivateModal(false)}
          >
            <div
              className="animate-scale-up mx-4 w-full max-w-md rounded-2xl bg-white p-8 shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100 text-red-600">
                <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
              </div>
              <h3 className="mb-2 text-center text-2xl font-bold text-gray-900">
                Deactivate Account?
              </h3>
              <p className="mb-8 text-center text-lg text-gray-600">
                Are you sure? This action will restrict your access to the platform.
              </p>
              <div className="flex gap-4">
                <button
                  onClick={() => setShowDeactivateModal(false)}
                  className="flex-1 rounded-xl bg-gray-100 py-3 font-bold text-gray-800 transition-all hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeactivate}
                  className="flex-1 rounded-xl bg-red-600 py-3 font-bold text-white shadow-lg shadow-red-200 transition-all hover:bg-red-700"
                >
                  Yes, Deactivate
                </button>
              </div>
            </div>
          </div>
        )}

        {showDeleteModal && (
          <div
            className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/60 backdrop-blur-sm"
            onClick={() => setShowDeleteModal(false)}
          >
            <div
              className="animate-scale-up mx-4 w-full max-w-md rounded-2xl bg-white p-8 shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100 text-red-600">
                <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </div>
              <h3 className="mb-2 text-center text-2xl font-bold text-gray-900">
                Permanently Delete Account?
              </h3>
              <p className="mb-8 text-center text-sm text-gray-600">
                Are you absolutely sure? This will delete all your personal records, orders, and credentials permanently. This action is irreversible.
              </p>
              <div className="flex gap-4">
                <button
                  onClick={() => setShowDeleteModal(false)}
                  className="flex-1 rounded-xl bg-gray-100 py-3 font-bold text-gray-800 transition-all hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteAccount}
                  className="flex-1 rounded-xl bg-red-700 py-3 font-bold text-white shadow-lg shadow-red-200 transition-all hover:bg-red-800"
                >
                  Permanently Delete
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
