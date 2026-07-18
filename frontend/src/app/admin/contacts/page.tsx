'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import InfoButton from '@/components/InfoButton';
import RefreshButton from '@/components/Admin/RefreshButton';

interface Address {
  address?: string;
  city?: string;
  state?: string;
  district?: string;
  zipCode?: string;
  country?: string;
  googleLocation?: string;
  latitude?: number;
  longitude?: number;
}

interface SocialMedia {
  instagram?: string;
  facebook?: string;
  twitter?: string;
  whatsapp?: string;
  youtube?: string;
  linkedin?: string;
}

interface Contact {
  _id?: string;
  addresses?: Address[];
  phoneNumbers?: string[];
  email?: string | null;
  description?: string;
  isActive?: boolean;
  displayOrder?: number;
  socialMedia?: SocialMedia;
}

export default function ContactManagement() {
  const { user } = useAuth();
  const [contacts, setContacts] = useState<Contact[]>([]);
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

  const [showForm, setShowForm] = useState(false);
  const [editingContact, setEditingContact] = useState<Contact | null>(null);
  const [formData, setFormData] = useState<Contact>({
    addresses: [
      {
        address: '',
        city: '',
        state: '',
        zipCode: '',
        country: 'India',
        googleLocation: '',
        latitude: undefined,
        longitude: undefined,
      },
      {
        address: '',
        city: '',
        state: '',
        zipCode: '',
        country: 'India',
        googleLocation: '',
        latitude: undefined,
        longitude: undefined,
      },
    ],
    phoneNumbers: ['', '', ''],
      email: '',
      description: '',
      isActive: true,
      displayOrder: 0,
      socialMedia: { instagram: '', facebook: '', twitter: '', whatsapp: '', youtube: '', linkedin: '' },
    });
  const [pageInfo, setPageInfo] = useState<{
    page: { title?: string; description?: string } | null;
    columns: Record<string, string>;
  }>({ page: null, columns: {} });

  useEffect(() => {
    if (user?.role === 'super_admin') {
      fetchContacts();
      fetchPageInfo();
    }
  }, [user]);

  const fetchPageInfo = async () => {
    try {
      const response = await api.get('/page-info/contact-management');
      setPageInfo(response.data);
    } catch (error) {
      console.error('Failed to fetch page info:', error);
    }
  };

  const fetchContacts = async () => {
    try {
      const response = await api.get('/contacts');
      setContacts(response.data);
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to fetch contacts');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // Process addresses - filter empty addresses and convert latitude/longitude
      const processedAddresses =
        formData.addresses
          ?.map((addr) => ({
            address: addr.address || undefined,
            city: addr.city || undefined,
            state: addr.state || undefined,
            district: addr.district || undefined,
            zipCode: addr.zipCode || undefined,
            country: addr.country || 'India',
            googleLocation: addr.googleLocation || undefined,
            latitude: addr.latitude,
            longitude: addr.longitude,
          }))
          .filter((addr) => addr.address || addr.city || addr.state || addr.district) || [];

      // Filter empty phone numbers
      const processedPhoneNumbers =
        formData.phoneNumbers?.filter((phone) => phone.trim() !== '') || [];

      const submitData: Contact = {
        addresses: processedAddresses.length > 0 ? processedAddresses : undefined,
        phoneNumbers: processedPhoneNumbers.length > 0 ? processedPhoneNumbers : undefined,
        email:
          formData.email && formData.email.trim() !== ''
            ? formData.email.trim()
            : editingContact?._id
              ? null
              : undefined, // Send null to remove email on update, undefined on create
        description: formData.description || undefined,
        isActive: formData.isActive,
        displayOrder: formData.displayOrder || 0,
        socialMedia: Object.fromEntries(
          Object.entries(formData.socialMedia || {}).filter(([, v]) => v && (v as string).trim())
        ) as SocialMedia || undefined,
      };

      if (editingContact?._id) {
        await api.put(`/contacts/${editingContact._id}`, submitData);
        toast.success('Contact updated successfully');
      } else {
        await api.post('/contacts', submitData);
        toast.success('Contact created successfully');
      }
      setShowForm(false);
      setEditingContact(null);
      resetForm();
      fetchContacts();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to save contact');
    }
  };

  const handleEdit = (contact: Contact) => {
    setEditingContact(contact);
    // Ensure we have 2 addresses (pad with empty if needed)
    const addresses = contact.addresses || [];
    const paddedAddresses: Address[] = [
      addresses[0] || {
        address: '',
        city: '',
        state: '',
        district: '',
        zipCode: '',
        country: 'India',
        googleLocation: '',
        latitude: undefined,
        longitude: undefined,
      },
      addresses[1] || {
        address: '',
        city: '',
        state: '',
        district: '',
        zipCode: '',
        country: 'India',
        googleLocation: '',
        latitude: undefined,
        longitude: undefined,
      },
    ];

    // Ensure we have 3 phone numbers (pad with empty if needed)
    const phoneNumbers = contact.phoneNumbers || [];
    const paddedPhoneNumbers = [
      phoneNumbers[0] || '',
      phoneNumbers[1] || '',
      phoneNumbers[2] || '',
    ];

    setFormData({
      addresses: paddedAddresses,
      phoneNumbers: paddedPhoneNumbers,
      email: contact.email || '',
      description: contact.description || '',
      isActive: contact.isActive !== undefined ? contact.isActive : true,
      displayOrder: contact.displayOrder || 0,
      socialMedia: {
        instagram: contact.socialMedia?.instagram || '',
        facebook: contact.socialMedia?.facebook || '',
        twitter: contact.socialMedia?.twitter || '',
        whatsapp: contact.socialMedia?.whatsapp || '',
        youtube: contact.socialMedia?.youtube || '',
        linkedin: contact.socialMedia?.linkedin || '',
      },
    });
    setShowForm(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this contact?')) return;
    try {
      await api.delete(`/contacts/${id}`);
      toast.success('Contact deleted successfully');
      fetchContacts();
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to delete contact');
    }
  };

  const resetForm = () => {
    setFormData({
      addresses: [
        {
          address: '',
          city: '',
          state: '',
          district: '',
          zipCode: '',
          country: 'India',
          googleLocation: '',
          latitude: undefined,
          longitude: undefined,
        },
        {
          address: '',
          city: '',
          state: '',
          district: '',
          zipCode: '',
          country: 'India',
          googleLocation: '',
          latitude: undefined,
          longitude: undefined,
        },
      ],
      phoneNumbers: ['', '', ''],
      email: '',
      description: '',
      isActive: true,
      displayOrder: 0,
      socialMedia: { instagram: '', facebook: '', twitter: '', whatsapp: '', youtube: '', linkedin: '' },
    });
  };

  const updateSocialMedia = (field: keyof SocialMedia, value: string) => {
    setFormData({ ...formData, socialMedia: { ...formData.socialMedia, [field]: value } });
  };

  const updateAddress = (
    index: number,
    field: keyof Address,
    value: string | number | undefined
  ) => {
    const newAddresses = [...(formData.addresses || [])];
    newAddresses[index] = { ...newAddresses[index], [field]: value };
    setFormData({ ...formData, addresses: newAddresses });
  };

  const updatePhoneNumber = (index: number, value: string) => {
    const newPhoneNumbers = [...(formData.phoneNumbers || [])];
    newPhoneNumbers[index] = value;
    setFormData({ ...formData, phoneNumbers: newPhoneNumbers });
  };

  const totalItems = contacts.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
  const paginatedContacts = contacts.slice(startIndex, endIndex);

  if (user?.role !== 'super_admin') {
    return <div>Access Denied</div>;
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="inline-flex items-center gap-3 text-3xl font-bold">
          <InfoButton
            info={
              user?.role === 'super_admin' && pageInfo.page?.description
                ? pageInfo.page.description
                : undefined
            }
          >
            Contact Management
          </InfoButton>
          <RefreshButton onRefresh={fetchContacts} />
        </h1>
        <div className="flex gap-2">
          <button
            onClick={() => {
              setShowForm(true);
              setEditingContact(null);
              resetForm();
            }}
            className="rounded bg-blue-600 px-6 py-2 text-white hover:bg-blue-700"
          >
            Add Contact
          </button>
        </div>
      </div>

      {showForm && (
        <div
          className="fixed inset-0 z-[110] flex items-start justify-center bg-black bg-opacity-50 pt-24"
          onClick={() => {
            setShowForm(false);
            setEditingContact(null);
            resetForm();
          }}
        >
          <div
            className="mx-4 max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-lg bg-white p-6 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-2xl font-semibold">
                {editingContact ? 'Edit Contact' : 'Add New Contact'}
              </h2>
              <button
                onClick={() => {
                  setShowForm(false);
                  setEditingContact(null);
                  resetForm();
                }}
                className="text-2xl font-bold text-gray-500 hover:text-gray-700"
                style={{ lineHeight: '1', padding: '0', width: '30px', height: '30px' }}
              >
                ×
              </button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.email
                          ? pageInfo.columns.email
                          : undefined
                      }
                    >
                      Email
                    </InfoButton>
                  </label>
                  <input
                    type="email"
                    value={formData.email || ''}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full rounded border px-3 py-2"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium">Display Order</label>
                  <input
                    type="number"
                    value={formData.displayOrder}
                    onChange={(e) =>
                      setFormData({ ...formData, displayOrder: parseInt(e.target.value) || 0 })
                    }
                    className="w-full rounded border px-3 py-2"
                  />
                </div>
              </div>

              {/* Phone Numbers Section */}
              <div className="mt-4 border-t pt-4">
                <h3 className="mb-3 text-lg font-semibold">Phone Numbers (Up to 3)</h3>
                <div className="grid gap-4 md:grid-cols-3">
                  {formData.phoneNumbers?.map((phone, index) => (
                    <div key={index}>
                      <label className="mb-1 block text-sm font-medium">Phone {index + 1}</label>
                      <input
                        type="text"
                        value={phone}
                        onChange={(e) => updatePhoneNumber(index, e.target.value)}
                        className="w-full rounded border px-3 py-2"
                        placeholder={`Phone number ${index + 1}`}
                      />
                    </div>
                  ))}
                </div>
              </div>

              {/* Addresses Section */}
              <div className="mt-4 border-t pt-4">
                <h3 className="mb-3 text-lg font-semibold">Addresses (Up to 2)</h3>
                {formData.addresses?.map((address, addrIndex) => (
                  <div key={addrIndex} className="mb-6 rounded-lg border bg-gray-50 p-4">
                    <h4 className="mb-3 font-medium text-gray-700">Address {addrIndex + 1}</h4>
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="md:col-span-2">
                        <label className="mb-1 block text-sm font-medium">Street Address</label>
                        <input
                          type="text"
                          value={address.address || ''}
                          onChange={(e) => updateAddress(addrIndex, 'address', e.target.value)}
                          className="w-full rounded border px-3 py-2"
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-sm font-medium">City</label>
                        <input
                          type="text"
                          value={address.city || ''}
                          onChange={(e) => updateAddress(addrIndex, 'city', e.target.value)}
                          className="w-full rounded border px-3 py-2"
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-sm font-medium">State</label>
                        <input
                          type="text"
                          value={address.state || ''}
                          onChange={(e) => updateAddress(addrIndex, 'state', e.target.value)}
                          className="w-full rounded border px-3 py-2"
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-sm font-medium">District</label>
                        <input
                          type="text"
                          value={address.district || ''}
                          onChange={(e) => updateAddress(addrIndex, 'district', e.target.value)}
                          className="w-full rounded border px-3 py-2"
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-sm font-medium">Pin Code</label>
                        <input
                          type="text"
                          value={address.zipCode || ''}
                          onChange={(e) => updateAddress(addrIndex, 'zipCode', e.target.value)}
                          className="w-full rounded border px-3 py-2"
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-sm font-medium">Country</label>
                        <input
                          type="text"
                          value={address.country || ''}
                          onChange={(e) => updateAddress(addrIndex, 'country', e.target.value)}
                          className="w-full rounded border px-3 py-2"
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-sm font-medium">
                          Google Maps Location URL
                        </label>
                        <input
                          type="url"
                          value={address.googleLocation || ''}
                          onChange={(e) =>
                            updateAddress(addrIndex, 'googleLocation', e.target.value)
                          }
                          className="w-full rounded border px-3 py-2"
                          placeholder="https://maps.google.com/..."
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-sm font-medium">Latitude</label>
                        <input
                          type="number"
                          step="any"
                          value={address.latitude || ''}
                          onChange={(e) =>
                            updateAddress(
                              addrIndex,
                              'latitude',
                              e.target.value ? parseFloat(e.target.value) : undefined
                            )
                          }
                          className="w-full rounded border px-3 py-2"
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-sm font-medium">Longitude</label>
                        <input
                          type="number"
                          step="any"
                          value={address.longitude || ''}
                          onChange={(e) =>
                            updateAddress(
                              addrIndex,
                              'longitude',
                              e.target.value ? parseFloat(e.target.value) : undefined
                            )
                          }
                          className="w-full rounded border px-3 py-2"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Description</label>
                <textarea
                  rows={3}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full rounded border px-3 py-2"
                />
              </div>
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.isActive}
                    onChange={(e) => setFormData({ ...formData, isActive: e.target.checked })}
                    className="mr-2"
                  />
                  Active
                </label>
              </div>
              {/* Social Media Links */}
              <div className="mt-4 border-t pt-4">
                <h3 className="mb-3 text-lg font-semibold">Social Media Links</h3>
                <div className="grid gap-4 md:grid-cols-2">
                  {(
                    [
                      { key: 'instagram', label: 'Instagram', placeholder: 'https://www.instagram.com/yourbrand' },
                      { key: 'facebook', label: 'Facebook', placeholder: 'https://www.facebook.com/yourbrand' },
                      { key: 'twitter', label: 'Twitter / X', placeholder: 'https://twitter.com/yourbrand' },
                      { key: 'whatsapp', label: 'WhatsApp', placeholder: 'https://wa.me/919999999999' },
                      { key: 'youtube', label: 'YouTube', placeholder: 'https://www.youtube.com/@yourbrand' },
                      { key: 'linkedin', label: 'LinkedIn', placeholder: 'https://www.linkedin.com/company/yourbrand' },
                    ] as { key: keyof SocialMedia; label: string; placeholder: string }[]
                  ).map(({ key, label, placeholder }) => (
                    <div key={key}>
                      <label className="mb-1 block text-sm font-medium">{label}</label>
                      <input
                        type="url"
                        value={(formData.socialMedia?.[key] as string) || ''}
                        onChange={(e) => updateSocialMedia(key, e.target.value)}
                        className="w-full rounded border px-3 py-2 text-sm"
                        placeholder={placeholder}
                      />
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  type="submit"
                  className="rounded bg-blue-600 px-6 py-2 text-white hover:bg-blue-700"
                >
                  {editingContact ? 'Update' : 'Create'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowForm(false);
                    setEditingContact(null);
                    resetForm();
                  }}
                  className="rounded bg-gray-300 px-6 py-2 text-gray-700 hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="overflow-hidden rounded-lg bg-white shadow-md">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                <InfoButton
                  info={
                    user?.role === 'super_admin' && pageInfo.columns?.phoneNumbers
                      ? pageInfo.columns.phoneNumbers
                      : undefined
                  }
                >
                  Phone Numbers
                </InfoButton>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                <InfoButton
                  info={
                    user?.role === 'super_admin' && pageInfo.columns?.email
                      ? pageInfo.columns.email
                      : undefined
                  }
                >
                  Email
                </InfoButton>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                <InfoButton
                  info={
                    user?.role === 'super_admin' && pageInfo.columns?.addresses
                      ? pageInfo.columns.addresses
                      : undefined
                  }
                >
                  Addresses
                </InfoButton>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                <InfoButton
                  info={
                    user?.role === 'super_admin' && pageInfo.columns?.status
                      ? pageInfo.columns.status
                      : undefined
                  }
                >
                  Status
                </InfoButton>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                <InfoButton
                  info={
                    user?.role === 'super_admin' && pageInfo.columns?.actions
                      ? pageInfo.columns.actions
                      : undefined
                  }
                >
                  Actions
                </InfoButton>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {paginatedContacts.map((contact) => (
              <tr key={contact._id}>
                <td className="px-6 py-4">
                  {contact.phoneNumbers && contact.phoneNumbers.length > 0 ? (
                    <div className="space-y-1">
                      {contact.phoneNumbers.map((phone, idx) => (
                        <div key={idx} className="text-sm">
                          {phone}
                        </div>
                      ))}
                    </div>
                  ) : (
                    '-'
                  )}
                </td>
                <td className="whitespace-nowrap px-6 py-4">{contact.email || '-'}</td>
                <td className="px-6 py-4">
                  {contact.addresses && contact.addresses.length > 0 ? (
                    <div className="space-y-2">
                      {contact.addresses.map((addr, idx) => (
                        <div key={idx} className="text-sm">
                          {[addr.address, addr.city, addr.state, addr.district]
                            .filter(Boolean)
                            .join(', ') || '-'}
                        </div>
                      ))}
                    </div>
                  ) : (
                    '-'
                  )}
                </td>
                <td className="whitespace-nowrap px-6 py-4">
                  <span
                    className={`rounded px-2 py-1 text-xs ${contact.isActive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
                  >
                    {contact.isActive ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="whitespace-nowrap px-6 py-4">
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleEdit(contact)}
                      className="rounded px-3 py-1 text-sm text-white"
                      style={{
                        background: 'linear-gradient(135deg, #FFC107 0%, #FF9800 100%)',
                      }}
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => contact._id && handleDelete(contact._id)}
                      className="rounded bg-red-500 px-3 py-1 text-sm text-white hover:bg-red-600"
                      style={{
                        background: 'linear-gradient(135deg, #DC3545 0%, #C82333 100%)',
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {totalItems === 0 && (
              <tr>
                <td colSpan={5} className="px-6 py-12 text-center text-slate-400">
                  No contacts found. Create your first contact!
                </td>
              </tr>
            )}
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
  );
}
