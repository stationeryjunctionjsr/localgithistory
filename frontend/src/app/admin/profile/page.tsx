'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';

export default function SuperAdminProfile() {
  const { user, fetchUser } = useAuth();
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    email: '',
    companyName: '',
    gstin: '',
    qrCode: '',
    upiId: '',
  });
  const [selectedQRFile, setSelectedQRFile] = useState<File | null>(null);
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [qrUploading, setQRUploading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [passwordData, setPasswordData] = useState({
    newPassword: '',
    confirmPassword: '',
  });
  const [changingPassword, setChangingPassword] = useState(false);

  useEffect(() => {
    if (user) {
      fetchUPIDetails();
      setFormData({
        name: user.name || '',
        phone: (user as any).phone || '',
        email: user.email || '',
        companyName: (user as any).companyName || '',
        gstin: (user as any).gstin || '',
        qrCode: '',
        upiId: '',
      });
      setLoading(false);
    }
  }, [user]);

  const fetchUPIDetails = async () => {
    try {
      const response = await api.get('/upi/details');
      setFormData((prev) => ({
        ...prev,
        qrCode: response.data.qrCodeUrl || '',
        upiId: response.data.upiId || '',
      }));
    } catch (error) {
      console.error('Failed to fetch UPI details', error);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.size > 2 * 1024 * 1024) {
        toast.error('File size must be less than 2MB');
        return;
      }
      setSelectedQRFile(file);

      // Local preview
      const reader = new FileReader();
      reader.onload = (event) => {
        setFormData((prev) => ({ ...prev, qrCode: event.target?.result as string }));
      };
      reader.readAsDataURL(file);
    }
  };

  const uploadQRCode = async () => {
    if (!selectedQRFile) return formData.qrCode;

    setQRUploading(true);
    const uploadData = new FormData();
    uploadData.append('image', selectedQRFile);

    try {
      const response = await api.post('/upi/upload-qr', uploadData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data.qrCodeUrl;
    } catch (error) {
      console.error('QR Upload failed:', error);
      throw new Error('Failed to upload QR code');
    } finally {
      setQRUploading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // 1. Upload QR code if a new file is selected
      let finalQRCodeUrl = formData.qrCode;
      if (selectedQRFile) {
        try {
          finalQRCodeUrl = await uploadQRCode();
        } catch (err: any) {
          toast.error(err.message);
          return;
        }
      }

      // 2. Update user profile (name, phone, email, company, gstin)
      await api.put(`/users/${user?._id}`, {
        name: formData.name,
        phone: formData.phone,
        email: formData.email,
        companyName: formData.companyName,
        gstin: formData.gstin,
      });

      // 3. Update UPI details separately
      if (formData.upiId || finalQRCodeUrl) {
        await api.put('/upi/details', {
          upiId: formData.upiId,
          qrCodeUrl: finalQRCodeUrl,
        });
      }

      setSelectedQRFile(null);

      toast.success('Profile updated successfully');
      if (fetchUser) fetchUser();
      fetchUPIDetails(); // Refresh UPI details
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to update profile');
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }
    if (passwordData.newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    setChangingPassword(true);
    try {
      await api.put(`/users/${user?._id}/password`, {
        newPassword: passwordData.newPassword,
      });
      toast.success('Password changed successfully');
      setShowPasswordModal(false);
      setPasswordData({ newPassword: '', confirmPassword: '' });
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to change password');
    } finally {
      setChangingPassword(false);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h1 className="mb-6 text-3xl font-bold">My Profile</h1>

      <div className="mb-6 rounded-lg bg-white p-6 shadow">
        <h2 className="mb-4 text-xl font-semibold">Edit Profile</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block">Full Name</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className="w-full rounded border border-gray-300 px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="mb-1 block">Email</label>
            <input
              type="email"
              value={user?.email || ''}
              disabled
              className="w-full rounded border border-gray-300 bg-gray-100 px-3 py-2"
            />
          </div>
          <div>
            <label className="mb-1 block">Phone Number</label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              className="w-full rounded border border-gray-300 px-3 py-2"
            />
          </div>

          <h3 className="mb-3 mt-6 text-lg font-semibold">Business Information</h3>
          <div>
            <label className="mb-1 block">Company Name</label>
            <input
              type="text"
              name="companyName"
              value={formData.companyName}
              onChange={handleChange}
              className="w-full rounded border border-gray-300 px-3 py-2"
              placeholder="Enter company name"
            />
          </div>
          <div>
            <label className="mb-1 block">GSTIN</label>
            <input
              type="text"
              name="gstin"
              value={formData.gstin}
              onChange={(e) => setFormData({ ...formData, gstin: e.target.value.toUpperCase() })}
              className="w-full rounded border border-gray-300 px-3 py-2"
              placeholder="Enter GSTIN"
              maxLength={15}
            />
          </div>

          <button
            type="submit"
            className="rounded px-6 py-2 font-medium text-white"
            style={{
              background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)',
            }}
          >
            Update Profile
          </button>
        </form>
      </div>

      {/* UPI Details Section */}
      <div className="mb-6 rounded-lg bg-white p-6 shadow">
        <h2 className="mb-4 text-xl font-semibold">UPI Payment Details</h2>
        <div className="space-y-4">
          <div>
            <label className="mb-1 block">UPI ID</label>
            <input
              type="text"
              name="upiId"
              value={formData.upiId}
              onChange={handleChange}
              placeholder="e.g., stationeryjunction@paytm"
              className="w-full rounded border border-gray-300 px-3 py-2"
            />
          </div>
          <div>
            <label className="mb-1 block font-medium">QR Code Image</label>
            <div className="flex flex-col gap-3">
              <input
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="w-full cursor-pointer text-sm text-gray-500 file:mr-4 file:rounded-full file:border-0 file:bg-blue-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-blue-700 hover:file:bg-blue-100"
              />
              <p className="text-xs text-gray-400">
                Recommended: Square image, max 2MB. This will be shown to retail customers using
                UPI.
              </p>
            </div>
          </div>
          {formData.qrCode && (
            <div className="mt-4 text-center">
              <img
                src={
                  formData.qrCode.startsWith('data:')
                    ? formData.qrCode
                    : formData.qrCode.startsWith('http')
                      ? formData.qrCode
                      : `${process.env.NEXT_PUBLIC_API_URL?.replace('/api', '') || ''}${formData.qrCode}`
                }
                alt="UPI QR Code"
                className="mx-auto max-h-[250px] max-w-[250px] rounded-xl border-4 border-white shadow-lg"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
            </div>
          )}
        </div>
      </div>

      {/* Account Settings */}
      <div className="rounded-lg bg-white p-6 shadow">
        <h2 className="mb-4 text-xl font-semibold">Account Settings</h2>
        <button
          onClick={() => setShowPasswordModal(true)}
          className="rounded px-6 py-2 font-medium text-white"
          style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          }}
        >
          Change Password
        </button>
      </div>

      {/* Change Password Modal */}
      {showPasswordModal && (
        <div
          className="fixed inset-0 z-[110] flex items-start justify-center bg-black bg-opacity-50 pt-24"
          onClick={() => {
            setShowPasswordModal(false);
            setPasswordData({ newPassword: '', confirmPassword: '' });
          }}
        >
          <div
            className="w-full max-w-md rounded-lg bg-white p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="mb-4 text-xl font-bold">Change Password</h3>
            <form onSubmit={handleChangePassword} className="space-y-4">
              <div>
                <label className="mb-1 block">New Password</label>
                <input
                  type="password"
                  value={passwordData.newPassword}
                  onChange={(e) =>
                    setPasswordData({ ...passwordData, newPassword: e.target.value })
                  }
                  className="w-full rounded border border-gray-300 px-3 py-2"
                  required
                  minLength={6}
                />
              </div>
              <div>
                <label className="mb-1 block">Confirm New Password</label>
                <input
                  type="password"
                  value={passwordData.confirmPassword}
                  onChange={(e) =>
                    setPasswordData({ ...passwordData, confirmPassword: e.target.value })
                  }
                  className="w-full rounded border border-gray-300 px-3 py-2"
                  required
                  minLength={6}
                />
              </div>
              <div className="flex justify-end gap-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowPasswordModal(false);
                    setPasswordData({ newPassword: '', confirmPassword: '' });
                  }}
                  disabled={changingPassword}
                  className="rounded bg-gray-600 px-4 py-2 text-white hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={changingPassword}
                  className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
                >
                  {changingPassword ? 'Changing...' : 'Change Password'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
