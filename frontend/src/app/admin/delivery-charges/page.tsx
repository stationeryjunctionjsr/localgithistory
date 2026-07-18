'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import SearchableSelect from '@/components/SearchableSelect';
import RefreshButton from '@/components/Admin/RefreshButton';
import InfoButton from '@/components/InfoButton';

interface DeliveryCharge {
  _id?: string;
  locationId?: number;
  pincode?: string;
  state: string;
  city: string;
  district: string;
  charge?: number | null;
  minCartValue?: number | null;
  applyDefaultCharge?: boolean;
  tiers?: Tier[];
  serviceableForCustomer?: boolean;

  serviceableForWholesaler?: boolean;
  isActive?: boolean;
  urgentDeliveryAvailable?: boolean;
  urgentDeliveryCharge?: number | null;
}

interface Tier {
  maxAmount: number | string;
  charge: number;
}

interface DefaultDeliveryCharge {
  _id?: string;
  defaultCharge: number;
  defaultMinCartValue: number;
  tiers?: Tier[];
  applicableToWholesaler?: boolean;
  deliveryChargeGst?: boolean;
  deliveryChargeGstPercentage?: number;

  isActive?: boolean;
  urgentDeliveryCharge?: number | null;
}

export default function DeliveryChargeManagement() {
  const { user } = useAuth();
  const [charges, setCharges] = useState<DeliveryCharge[]>([]);
  const [defaultCharge, setDefaultCharge] = useState<DefaultDeliveryCharge | null>(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showDefaultModal, setShowDefaultModal] = useState(false);
  const [showCsvModal, setShowCsvModal] = useState(false);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [editingCharge, setEditingCharge] = useState<DeliveryCharge | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  // Location master data (fetched from API)
  const [availableStates, setAvailableStates] = useState<string[]>([]);
  const [availableDistricts, setAvailableDistricts] = useState<string[]>([]);
  const [availablePincodes, setAvailablePincodes] = useState<string[]>([]);
  const [pincodeSearch, setPincodeSearch] = useState('');

  const [formData, setFormData] = useState({
    pincode: '',
    pincodes: [] as string[],
    state: '',
    city: '',
    district: '',
    applyDefaultCharge: false,
    tiers: [] as Tier[],
    serviceableForCustomer: true,
    serviceableForWholesaler: true,
    isActive: true,
  });
  const [defaultFormData, setDefaultFormData] = useState({
    defaultCharge: '',
    defaultMinCartValue: '',
    tiers: [] as Tier[],
    applicableToWholesaler: true,
    deliveryChargeGst: false,
    deliveryChargeGstPercentage: '18',
    isActive: true,
  });

  // Fetch states on mount
  const fetchStates = async () => {
    try {
      const response = await api.get('/pincodes/states');
      setAvailableStates(response.data || []);
    } catch (_error) {
      console.error('Failed to fetch states');
    }
  };

  // Fetch districts when state changes
  const fetchDistricts = async (state: string) => {
    if (!state) {
      setAvailableDistricts([]);
      setAvailablePincodes([]);
      return;
    }
    try {
      const response = await api.get(`/pincodes/districts?state=${encodeURIComponent(state)}`);
      setAvailableDistricts(response.data || []);
      setAvailablePincodes([]);
    } catch (_error) {
      console.error('Failed to fetch districts');
      setAvailableDistricts([]);
    }
  };

  // Fetch pincodes when district changes
  const fetchPincodes = async (state: string, district: string) => {
    if (!state || !district) {
      setAvailablePincodes([]);
      return;
    }
    try {
      const response = await api.get(
        `/pincodes/pincodes?state=${encodeURIComponent(state)}&district=${encodeURIComponent(district)}`
      );
      setAvailablePincodes(response.data || []);
    } catch (_error) {
      console.error('Failed to fetch pincodes');
      setAvailablePincodes([]);
    }
  };

  useEffect(() => {
    if (user?.role === 'super_admin') {
      fetchCharges();
      fetchDefaultCharge();
      fetchStates();
    }
  }, [user]);

  const fetchCharges = async () => {
    try {
      const response = await api.get('/delivery-charges');
      setCharges(response.data || []);
      setLoading(false);
    } catch (_error: any) {
      toast.error('Failed to fetch delivery charges');
      setLoading(false);
    }
  };

  const fetchDefaultCharge = async () => {
    try {
      const response = await api.get('/delivery-charges/default');
      setDefaultCharge(response.data);
      if (response.data) {
        setDefaultFormData({
          defaultCharge: response.data.defaultCharge?.toString() || '',
          defaultMinCartValue: response.data.defaultMinCartValue?.toString() || '',
          tiers: response.data.tiers || [],
          applicableToWholesaler: response.data.applicableToWholesaler !== false,
          deliveryChargeGst: response.data.deliveryChargeGst === true,
          deliveryChargeGstPercentage: response.data.deliveryChargeGstPercentage?.toString() || '18',
          isActive: response.data.isActive !== false,
        });
      }
    } catch (_error: any) {
      // Default charge might not exist yet
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = type === 'checkbox' ? (e.target as HTMLInputElement).checked : false;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  const handleDefaultChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;
    setDefaultFormData({
      ...defaultFormData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const { tiers, applyDefaultCharge, pincodes, pincode, ...otherData } = formData;

    try {
      if (editingCharge?._id) {
        const submitData = {
          ...otherData,
          pincode: pincode,
          charge: null,
          minCartValue: null,
          tiers: applyDefaultCharge ? null : tiers || [],
          applyDefaultCharge: applyDefaultCharge || false,
        };
        await api.put(`/delivery-charges/${editingCharge._id}`, submitData);
        toast.success('Delivery charge updated successfully');
      } else {
        if (!pincodes.length) {
          toast.error('Please select at least one pincode');
          return;
        }

        const results = await Promise.allSettled(
          pincodes.map((pc) => {
            const submitData = {
              ...otherData,
              pincode: pc,
              charge: null,
              minCartValue: null,
              tiers: applyDefaultCharge ? null : tiers || [],
              applyDefaultCharge: applyDefaultCharge || false,
            };
            return api.post('/delivery-charges', submitData);
          })
        );

        const succeeded = results.filter((r) => r.status === 'fulfilled').length;
        const failed = results.filter((r) => r.status === 'rejected');

        if (failed.length > 0) {
          const duplicates = failed
            .map((r, _i) => {
              const reason = (r as PromiseRejectedResult).reason;
              const detail = reason?.response?.data?.detail || '';
              if (detail.includes('already has a delivery charge')) {
                return pincodes[results.indexOf(r)];
              }
              return null;
            })
            .filter(Boolean);

          if (duplicates.length > 0) {
            toast.warning(
              `${duplicates.length} pincode(s) already configured: ${duplicates.join(', ')}`
            );
          }
          if (succeeded > 0) {
            toast.success(`${succeeded} delivery charge(s) created successfully`);
          }
          if (succeeded === 0 && duplicates.length === 0) {
            toast.error('Failed to create delivery charges');
          }
        } else {
          toast.success(`${pincodes.length} delivery charge(s) created successfully`);
        }
      }
      setShowModal(false);
      setEditingCharge(null);
      setFormData({
        pincode: '',
        pincodes: [],
        state: '',
        city: '',
        district: '',
        applyDefaultCharge: false,
        tiers: [],
        serviceableForCustomer: true,
        serviceableForWholesaler: true,
        isActive: true,
      });
      fetchCharges();
    } catch (error: any) {
      toast.error(
        error.response?.data?.detail || error.response?.data?.message || 'Operation failed'
      );
    }
  };

  const handleDefaultSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate that at least one tier exists
    if (!defaultFormData.tiers || defaultFormData.tiers.length === 0) {
      toast.error('Please add at least one delivery charge tier');
      return;
    }

    // Validate tiers
    for (let i = 0; i < defaultFormData.tiers.length; i++) {
      const tier = defaultFormData.tiers[i];
      if (!tier.maxAmount || !tier.charge) {
        toast.error(`Please fill in all fields for Tier ${i + 1}`);
        return;
      }
    }

    try {
      const submitData = {
        tiers: defaultFormData.tiers.map((tier) => ({
          maxAmount:
            tier.maxAmount === 'Infinity' ? 'Infinity' : parseFloat(tier.maxAmount as string),
          charge: parseFloat(tier.charge as any),
        })),
        applicableToWholesaler: defaultFormData.applicableToWholesaler,
        deliveryChargeGst: defaultFormData.deliveryChargeGst,
        deliveryChargeGstPercentage: parseFloat(defaultFormData.deliveryChargeGstPercentage as string) || 18,
        isActive: defaultFormData.isActive,
      };

      await api.post('/delivery-charges/default', submitData);
      toast.success(
        defaultCharge
          ? 'Default delivery charge updated successfully'
          : 'Default delivery charge created successfully'
      );
      setShowDefaultModal(false);
      fetchDefaultCharge();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Operation failed');
    }
  };

  const handleDeleteDefaultCharge = async () => {
    if (
      !confirm(
        'Are you sure you want to delete the default delivery charge configuration? This cannot be undone.'
      )
    ) {
      return;
    }

    try {
      await api.delete('/delivery-charges/default');
      toast.success('Default delivery charge deleted successfully');
      setDefaultCharge(null);
      setDefaultFormData({
        defaultCharge: '',
        defaultMinCartValue: '',
        tiers: [],
        applicableToWholesaler: true,
        deliveryChargeGst: false,
        deliveryChargeGstPercentage: '18',
        isActive: true,
      });
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to delete default charge');
    }
  };

  const handleAddTier = () => {
    setDefaultFormData({
      ...defaultFormData,
      tiers: [...defaultFormData.tiers, { maxAmount: '', charge: 0 }],
    });
  };

  const handleRemoveTier = (index: number) => {
    const newTiers = defaultFormData.tiers.filter((_, i) => i !== index);
    setDefaultFormData({
      ...defaultFormData,
      tiers: newTiers,
    });
  };

  const handleTierChange = (index: number, field: 'maxAmount' | 'charge', value: string) => {
    const newTiers = [...defaultFormData.tiers];
    newTiers[index][field] = value as any;
    setDefaultFormData({
      ...defaultFormData,
      tiers: newTiers,
    });
  };

  const handleEdit = (charge: DeliveryCharge) => {
    setEditingCharge(charge);
    const applyDefault = charge.applyDefaultCharge || false;
    setFormData({
      pincode: charge.pincode || '',
      pincodes: [], // Not used during edit
      state: charge.state || '',
      city: charge.city || '',
      district: charge.district || '',
      applyDefaultCharge: applyDefault,
      tiers: applyDefault ? [] : charge.tiers || [],
      serviceableForCustomer:
        charge.serviceableForCustomer !== undefined ? charge.serviceableForCustomer : true,
      serviceableForWholesaler:
        charge.serviceableForWholesaler !== undefined ? charge.serviceableForWholesaler : true,
      isActive: charge.isActive !== false,
    });
    // Fetch districts and pincodes for the current state/district
    if (charge.state) {
      fetchDistricts(charge.state);
      if (charge.district) {
        fetchPincodes(charge.state, charge.district);
      }
    }
    setShowModal(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this delivery charge?')) return;
    try {
      await api.delete(`/delivery-charges/${id}`);
      toast.success('Delivery charge deleted successfully');
      fetchCharges();
    } catch (_error: any) {
      toast.error('Failed to delete delivery charge');
    }
  };

  const handleCsvUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!csvFile) {
      toast.error('Please select a CSV file');
      return;
    }

    setUploading(true);
    try {
      const formDataUpload = new FormData();
      formDataUpload.append('file', csvFile);

      const response = await api.post('/delivery-charges/upload-csv', formDataUpload, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      toast.success(
        `CSV upload completed! ${response.data.success || 0} records processed, ${response.data.errors || 0} errors`
      );
      setCsvFile(null);
      setShowCsvModal(false);
      fetchCharges();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to upload CSV file');
    } finally {
      setUploading(false);
    }
  };

  const downloadSampleCsv = () => {
    const headers = ['pincode', 'state', 'city', 'district', 'charge', 'minCartValue', 'serviceableForCustomer', 'urgentDeliveryAvailable', 'urgentDeliveryCharge'];
    const sampleRow = ['400001', 'Maharashtra', 'Mumbai', 'Mumbai', '50', '500', 'true', 'true', '100'];

    const csvContent = [headers.join(','), sampleRow.join(',')].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'delivery_charge_template.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (user?.role !== 'super_admin') {
    return <div>Access Denied</div>;
  }

  if (loading) return <div>Loading...</div>;

  const filteredCharges = charges.filter((charge) => {
    const searchLower = searchTerm.toLowerCase();
    return (
      (charge.pincode || '').toString().includes(searchLower) ||
      (charge.state || '').toLowerCase().includes(searchLower) ||
      (charge.city || '').toLowerCase().includes(searchLower) ||
      (charge.district || '').toLowerCase().includes(searchLower) ||
      (charge.charge?.toString() || '').includes(searchLower)
    );
  });

  const totalItems = filteredCharges.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
  const paginatedCharges = filteredCharges.slice(startIndex, endIndex);

  const getPageNumbers = () => {
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

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="rounded-lg bg-white p-6 shadow-md h-full flex flex-col min-h-0">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4 flex-shrink-0">
        <h2 className="inline-flex items-center gap-3 text-2xl font-bold">
          Delivery Charge Management <RefreshButton onRefresh={fetchCharges} />
        </h2>
        <div className="flex gap-2">
          <button
            onClick={() => setShowCsvModal(true)}
            className="rounded px-4 py-2 text-white"
            style={{
              background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)',
            }}
          >
            Upload CSV
          </button>
          {!defaultCharge && (
            <button
              onClick={() => {
                setDefaultFormData({
                  defaultCharge: '',
                  defaultMinCartValue: '',
                  tiers: [],
                  applicableToWholesaler: true,
                  deliveryChargeGst: false,
                  deliveryChargeGstPercentage: '18',
                  isActive: true,
                });
                setShowDefaultModal(true);
              }}
              className="rounded px-4 py-2 text-white"
              style={{
                background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)',
              }}
            >
              + Create Default Charge
            </button>
          )}
          <button
            onClick={() => {
              setShowModal(true);
              setEditingCharge(null);
              setFormData({
                pincode: '',
                pincodes: [],
                state: '',
                city: '',
                district: '',
                applyDefaultCharge: false,
                tiers: [],
                serviceableForCustomer: true,
                serviceableForWholesaler: true,
                isActive: true,
              });
            }}
            className="rounded px-4 py-2 text-white"
            style={{
              background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)',
            }}
          >
            Add Delivery Charge
          </button>
        </div>
      </div>

      {defaultCharge && (
        <div className="relative mb-6 rounded-lg border border-blue-200 bg-blue-50 p-4 flex-shrink-0">
          <div className="mb-2 flex items-start justify-between">
            <div>
              <strong className="text-lg">Default Delivery Charge Configuration</strong>
              {!defaultCharge.isActive && (
                <span className="ml-2 text-sm text-red-600">(Inactive)</span>
              )}
            </div>
            <div className="flex gap-2">
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setDefaultFormData({
                      defaultCharge: '',
                      defaultMinCartValue: '',
                      tiers:
                        defaultCharge.tiers && defaultCharge.tiers.length > 0
                          ? defaultCharge.tiers
                          : [],
                      applicableToWholesaler: defaultCharge.applicableToWholesaler !== false,
                      deliveryChargeGst: defaultCharge.deliveryChargeGst === true,
                      deliveryChargeGstPercentage: defaultCharge.deliveryChargeGstPercentage?.toString() || '18',
                      isActive: defaultCharge.isActive !== false,
                    });
                    setShowDefaultModal(true);
                  }}
                  className="rounded px-3 py-1 text-sm text-white"
                  style={{
                    background: 'linear-gradient(135deg, #FFC107 0%, #FF9800 100%)',
                  }}
                >
                  Edit
                </button>
                <button
                  onClick={handleDeleteDefaultCharge}
                  className="rounded px-3 py-1 text-sm text-white"
                  style={{
                    background: 'linear-gradient(135deg, #DC3545 0%, #C82333 100%)',
                  }}
                >
                  Delete
                </button>
              </div>
            </div>
          </div>

          {defaultCharge.tiers && defaultCharge.tiers.length > 0 ? (
            <div className="mt-2">
              <strong>📊 Delivery Charge Tiers:</strong>
              <ul className="ml-4 mt-2 list-inside list-disc">
                {defaultCharge.tiers
                  .sort((a, b) => {
                    const aMax =
                      a.maxAmount === 'Infinity' || a.maxAmount === null
                        ? Infinity
                        : parseFloat(a.maxAmount as string);
                    const bMax =
                      b.maxAmount === 'Infinity' || b.maxAmount === null
                        ? Infinity
                        : parseFloat(b.maxAmount as string);
                    return aMax - bMax;
                  })
                  .map((tier, idx) => (
                    <li key={idx} className="mb-1 text-gray-700">
                      If order amount &lt; ₹
                      {tier.maxAmount === 'Infinity' || tier.maxAmount === null
                        ? '∞'
                        : tier.maxAmount}{' '}
                      → Delivery Charge: ₹{tier.charge || 0}
                    </li>
                  ))}
              </ul>
            </div>
          ) : (
            <div className="mt-2 rounded border border-yellow-200 bg-yellow-50 p-3">
              <strong className="text-sm text-yellow-700">⚠️ No tiers configured.</strong>
              <p className="mb-0 mt-1 text-xs text-yellow-700">
                Click &quot;Edit&quot; to add delivery charge tiers.
              </p>
            </div>
          )}

          <div className="mt-2 text-sm text-gray-600">
            <strong>Applicable To:</strong>
            <span className="ml-2">
              Business Customers: {defaultCharge.applicableToWholesaler !== false ? '✓' : '✗'}
            </span>
            {defaultCharge.deliveryChargeGst && (
              <span className="ml-4 rounded bg-indigo-100 px-2 py-1 text-xs text-indigo-800">
                GST Applied: {defaultCharge.deliveryChargeGstPercentage}%
              </span>
            )}
          </div>
        </div>
      )}

      <div className="mb-4 flex-shrink-0">
        <input
          type="text"
          placeholder="Search by state, city, district, or charge..."
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setCurrentPage(1);
          }}
          className="w-full max-w-md rounded border px-3 py-2"
        />
      </div>

      <div className="overflow-x-auto flex-1 min-h-0 border rounded border-gray-200">
        <table className="w-full min-w-[1000px]">
          <thead className="sticky top-0 z-10 bg-gray-50 shadow-sm">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                <InfoButton info="The specific pincode (postal code) this delivery charge applies to">Pincode</InfoButton>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                <InfoButton info="The Indian state this delivery charge applies to">State</InfoButton>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                <InfoButton info="The city within the state this delivery charge applies to">City</InfoButton>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                <InfoButton info="The district within the state this delivery charge applies to">District</InfoButton>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                <InfoButton info="The delivery charge amount in INR, or 'Tiered' if tiered pricing applies, or 'Default' if the default config is used">Charge (₹)</InfoButton>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                <InfoButton info="Minimum cart value above which delivery is free for this location">Free Delivery Above (₹)</InfoButton>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                <InfoButton info="Whether retail (B2C) customers can place orders for delivery to this location">Serviceable - Retail customers</InfoButton>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                <InfoButton info="Whether business/wholesaler (B2B) customers can place orders for delivery to this location">Serviceable - Business Customers</InfoButton>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                <InfoButton info="Whether this delivery charge configuration is currently active">Status</InfoButton>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                <InfoButton info="Edit or delete this delivery charge entry">Actions</InfoButton>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {paginatedCharges.length > 0 ? (
              paginatedCharges.map((charge) => (
                <tr key={charge._id}>
                  <td className="whitespace-nowrap px-6 py-4">{charge.pincode || '-'}</td>
                  <td className="whitespace-nowrap px-6 py-4">{charge.state || '-'}</td>
                  <td className="whitespace-nowrap px-6 py-4">{charge.city || '-'}</td>
                  <td className="whitespace-nowrap px-6 py-4">{charge.district || '-'}</td>
                  <td className="whitespace-nowrap px-6 py-4">
                    {charge.applyDefaultCharge ? (
                      <span className="italic text-gray-500">Default</span>
                    ) : charge.tiers && charge.tiers.length > 0 ? (
                      <span className="italic text-gray-500">Tiered</span>
                    ) : (
                      `₹${charge.charge || 0}`
                    )}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    {charge.minCartValue ? `₹${charge.minCartValue}` : '-'}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-center">
                    <span
                      className={`rounded px-2 py-1 text-xs ${charge.serviceableForCustomer ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
                    >
                      {charge.serviceableForCustomer ? '✓' : '✗'}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-center">
                    <span
                      className={`rounded px-2 py-1 text-xs ${charge.serviceableForWholesaler ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
                    >
                      {charge.serviceableForWholesaler ? '✓' : '✗'}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <span
                      className={`rounded px-2 py-1 text-xs ${charge.isActive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
                    >
                      {charge.isActive ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleEdit(charge)}
                        className="rounded px-3 py-1 text-sm text-white"
                        style={{
                          background: 'linear-gradient(135deg, #FFC107 0%, #FF9800 100%)',
                        }}
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => charge._id && handleDelete(charge._id)}
                        className="rounded px-3 py-1 text-sm text-white"
                        style={{
                          background: 'linear-gradient(135deg, #DC3545 0%, #C82333 100%)',
                        }}
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={10} className="px-6 py-4 text-center text-gray-500">
                  No delivery charges found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Premium Pagination Controls */}
      {filteredCharges.length > 0 && (
        <div className="mt-4 flex flex-shrink-0 flex-col items-center justify-between gap-4 border-t border-gray-200 pt-4 sm:flex-row">
          <div className="text-sm text-gray-700">
            Showing <span className="font-semibold">{totalItems === 0 ? 0 : startIndex + 1}</span> to{' '}
            <span className="font-semibold">{endIndex}</span> of{' '}
            <span className="font-semibold">{totalItems}</span> delivery charges
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
              {getPageNumbers().map((page, index) => {
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

      {/* Add/Edit Modal */}
      {showModal && (
        <div
          className="fixed inset-0 z-[110] flex items-center justify-center bg-black bg-opacity-50 p-4"
          onClick={() => setShowModal(false)}
        >
          <div
            className="mx-4 max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="mb-4 text-xl font-bold">
              {editingCharge ? 'Edit Delivery Charge' : 'Add Delivery Charge'}
            </h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-1 block text-sm font-medium">State *</label>
                  <SearchableSelect
                    options={availableStates}
                    value={formData.state}
                    onChange={(val) => {
                      setFormData({
                        ...formData,
                        state: val,
                        district: '',
                        city: '',
                        pincodes: [],
                        pincode: '',
                      });
                      fetchDistricts(val);
                      setAvailablePincodes([]);
                    }}
                    placeholder="Select State"
                    required
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium">District *</label>
                  <SearchableSelect
                    options={availableDistricts}
                    value={formData.district}
                    onChange={(val) => {
                      setFormData({
                        ...formData,
                        district: val,
                        pincodes: [],
                        pincode: '',
                      });
                      fetchPincodes(formData.state, val);
                      setPincodeSearch('');
                    }}
                    placeholder="Select District"
                    disabled={!formData.state}
                    required
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium">City (Optional)</label>
                  <input
                    type="text"
                    name="city"
                    value={formData.city}
                    onChange={handleChange}
                    placeholder="Enter city name"
                    className="w-full rounded border px-3 py-2"
                  />
                </div>
              </div>

              {!editingCharge ? (
                <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                  <label className="mb-2 block text-sm font-semibold">Select Pincodes *</label>
                  {!formData.district ? (
                    <p className="text-sm text-gray-500">Please select a district first</p>
                  ) : (
                    <>
                      <div className="mb-2 flex items-center gap-2">
                        <input
                          type="text"
                          placeholder="Search pincodes..."
                          value={pincodeSearch}
                          onChange={(e) => setPincodeSearch(e.target.value)}
                          className="flex-1 rounded border px-3 py-1.5 text-sm"
                        />
                        <button
                          type="button"
                          onClick={() => {
                            const filtered = availablePincodes.filter((pc) =>
                              pc.includes(pincodeSearch)
                            );
                            const allSelected = filtered.every((pc) =>
                              formData.pincodes.includes(pc)
                            );
                            if (allSelected) {
                              // Deselect all filtered
                              setFormData({
                                ...formData,
                                pincodes: formData.pincodes.filter((pc) => !filtered.includes(pc)),
                              });
                            } else {
                              // Select all filtered
                              const merged = Array.from(
                                new Set([...formData.pincodes, ...filtered])
                              );
                              setFormData({ ...formData, pincodes: merged });
                            }
                          }}
                          className="whitespace-nowrap rounded px-3 py-1.5 text-xs font-medium text-white"
                          style={{
                            background:
                              availablePincodes
                                .filter((pc) => pc.includes(pincodeSearch))
                                .every((pc) => formData.pincodes.includes(pc)) &&
                              availablePincodes.filter((pc) => pc.includes(pincodeSearch)).length >
                                0
                                ? 'linear-gradient(135deg, #DC3545 0%, #C82333 100%)'
                                : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                          }}
                        >
                          {availablePincodes
                            .filter((pc) => pc.includes(pincodeSearch))
                            .every((pc) => formData.pincodes.includes(pc)) &&
                          availablePincodes.filter((pc) => pc.includes(pincodeSearch)).length > 0
                            ? 'Deselect All'
                            : 'Select All'}
                        </button>
                      </div>
                      <div className="grid max-h-40 grid-cols-2 gap-2 overflow-y-auto rounded border bg-white p-2 sm:grid-cols-3">
                        {availablePincodes
                          .filter((pc) => pc.includes(pincodeSearch))
                          .map((pc: string) => (
                            <label
                              key={pc}
                              className="flex cursor-pointer items-center space-x-2 rounded p-1 text-sm hover:bg-gray-50"
                            >
                              <input
                                type="checkbox"
                                checked={formData.pincodes.includes(pc)}
                                onChange={(e) => {
                                  const newPincodes = e.target.checked
                                    ? [...formData.pincodes, pc]
                                    : formData.pincodes.filter((item) => item !== pc);
                                  setFormData({ ...formData, pincodes: newPincodes });
                                }}
                                className="h-4 w-4 rounded text-purple-600"
                              />
                              <span>{pc}</span>
                            </label>
                          ))}
                        {availablePincodes.filter((pc) => pc.includes(pincodeSearch)).length ===
                          0 && (
                          <p className="col-span-3 py-2 text-center text-sm text-gray-400">
                            No pincodes match your search
                          </p>
                        )}
                      </div>
                    </>
                  )}
                  {formData.pincodes.length > 0 && (
                    <p className="mt-2 text-xs font-medium text-purple-600">
                      Selected: {formData.pincodes.length} pincode(s)
                    </p>
                  )}
                </div>
              ) : (
                <div>
                  <label className="mb-1 block text-sm font-medium">Pincode *</label>
                  <SearchableSelect
                    options={availablePincodes}
                    value={formData.pincode}
                    onChange={(val) => setFormData({ ...formData, pincode: val })}
                    placeholder="Select Pincode"
                    disabled={!formData.district}
                    required
                  />
                </div>
              )}

              <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
                <label className="mb-2 flex cursor-pointer items-center font-semibold">
                  <input
                    type="checkbox"
                    name="applyDefaultCharge"
                    checked={formData.applyDefaultCharge}
                    onChange={(e) => {
                      handleChange(e);
                      if (e.target.checked) {
                        setFormData((prev) => ({
                          ...prev,
                          charge: '',
                          minCartValue: '',
                          tiers: [],
                        }));
                      }
                    }}
                    className="mr-2 h-5 w-5"
                  />
                  <span>Apply Default Delivery Charge</span>
                </label>
                <small className="block text-xs text-gray-600">
                  If checked, default delivery charge tiers will be applied to this pincode.
                  Pincode-specific fields will be disabled.
                </small>
              </div>

              {!formData.applyDefaultCharge && (
                <>
                  <div className="rounded-lg bg-gray-50 p-4">
                    <h4 className="mb-3 text-base font-semibold">📊 Delivery Charge Tiers</h4>
                    <p className="mb-4 text-sm text-gray-600">
                      Define delivery charges based on order amount. Leave blank for ₹0 delivery
                      charge.
                    </p>

                    {formData.tiers.map((tier, index) => (
                      <div
                        key={index}
                        className="mb-3 flex items-center gap-3 rounded border border-gray-300 bg-white p-3"
                      >
                        <span className="min-w-[60px] font-semibold">Tier {index + 1}:</span>
                        <div className="flex-1">
                          <label className="mb-1 block text-xs text-gray-600">If amount &lt;</label>
                          <input
                            type="number"
                            placeholder="Max Amount (₹)"
                            value={tier.maxAmount}
                            onChange={(e) => {
                              const newTiers = [...formData.tiers];
                              newTiers[index].maxAmount = e.target.value;
                              setFormData({ ...formData, tiers: newTiers });
                            }}
                            step="0.01"
                            min="0"
                            className="w-full rounded border px-3 py-2"
                          />
                        </div>
                        <span className="text-lg text-purple-600">→</span>
                        <div className="flex-1">
                          <label className="mb-1 block text-xs text-gray-600">Charge</label>
                          <input
                            type="number"
                            placeholder="Charge (₹)"
                            value={tier.charge}
                            onChange={(e) => {
                              const newTiers = [...formData.tiers];
                              newTiers[index].charge = e.target.value as any;
                              setFormData({ ...formData, tiers: newTiers });
                            }}
                            step="0.01"
                            min="0"
                            className="w-full rounded border px-3 py-2"
                          />
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            const newTiers = formData.tiers.filter((_, i) => i !== index);
                            setFormData({ ...formData, tiers: newTiers });
                          }}
                          className="rounded bg-red-500 px-3 py-2 text-white hover:bg-red-600"
                        >
                          Remove
                        </button>
                      </div>
                    ))}

                    <button
                      type="button"
                      onClick={() => {
                        setFormData({
                          ...formData,
                          tiers: [...formData.tiers, { maxAmount: '', charge: 0 }],
                        });
                      }}
                      className="mt-2 rounded bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700"
                    >
                      + Add Tier
                    </button>
                    <small className="mt-2 block text-xs text-gray-500">
                      If no tiers are added, delivery charge will be ₹0 for this pincode.
                    </small>
                  </div>
                </>
              )}

              <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
                <label className="mb-3 block text-sm font-semibold">Serviceability:</label>
                <div className="flex flex-col gap-3">
                  <label className="flex cursor-pointer items-center">
                    <input
                      type="checkbox"
                      name="serviceableForCustomer"
                      checked={formData.serviceableForCustomer}
                      onChange={handleChange}
                      className="mr-2 h-5 w-5"
                    />
                    <span>Serviceable for Retail customers</span>
                  </label>
                  <label className="flex cursor-pointer items-center">
                    <input
                      type="checkbox"
                      name="serviceableForWholesaler"
                      checked={formData.serviceableForWholesaler}
                      onChange={handleChange}
                      className="mr-2 h-5 w-5"
                    />
                    <span>Serviceable for Business Customers</span>
                  </label>
                </div>
                <small className="mt-2 block text-xs text-gray-600">
                  Only added pincodes can be marked as serviceable. If not serviceable for a user
                  segment, users from that segment cannot place orders from this pincode.
                </small>
              </div>


              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    name="isActive"
                    checked={formData.isActive}
                    onChange={handleChange}
                    className="mr-2"
                  />
                  Active
                </label>
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="rounded bg-gray-300 px-6 py-2 text-gray-700 hover:bg-gray-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded px-6 py-2 text-white"
                  style={{
                    background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)',
                  }}
                >
                  {editingCharge ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Default Charge Modal */}
      {showDefaultModal && (
        <div
          className="fixed inset-0 z-[110] flex items-center justify-center bg-black bg-opacity-50 p-4"
          onClick={() => setShowDefaultModal(false)}
        >
          <div
            className="mx-4 w-full max-w-2xl rounded-lg bg-white p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="mb-4 text-xl font-bold">
              {defaultCharge
                ? '✏️ Edit Default Delivery Charge'
                : '➕ Create Default Delivery Charge'}
            </h3>
            <p className="mb-4 text-gray-600">
              Configure tiered delivery charges based on order amount. These charges will be used
              when city-specific charges are not available.
            </p>
            <form onSubmit={handleDefaultSubmit} className="space-y-4">
              <div className="mb-6 rounded-lg border border-blue-200 bg-blue-50 p-4">
                <h4 className="mb-3 text-base font-semibold">📊 Delivery Charge Tiers *</h4>
                <p className="mb-4 text-sm text-gray-600">
                  Define delivery charges based on order amount. Add multiple tiers to create a
                  flexible pricing structure.
                  <br />
                  <strong>Example:</strong> If order &lt; ₹150 → charge ₹20; If order &lt; ₹300 →
                  charge ₹10; If order ≥ ₹300 → charge ₹0
                </p>

                {defaultFormData.tiers.map((tier, index) => (
                  <div
                    key={index}
                    className="mb-3 flex items-center gap-3 rounded border border-gray-300 bg-white p-3"
                  >
                    <span className="min-w-[60px] font-semibold">Tier {index + 1}:</span>
                    <div className="flex-1">
                      <label className="mb-1 block text-xs text-gray-600">
                        If order amount &lt;
                      </label>
                      <input
                        type="number"
                        placeholder="Max Amount (₹)"
                        value={tier.maxAmount}
                        onChange={(e) => handleTierChange(index, 'maxAmount', e.target.value)}
                        step="0.01"
                        min="0"
                        required
                        className="w-full rounded border px-3 py-2"
                      />
                    </div>
                    <span className="text-lg text-purple-600">→</span>
                    <div className="flex-1">
                      <label className="mb-1 block text-xs text-gray-600">Delivery Charge</label>
                      <input
                        type="number"
                        placeholder="Charge (₹)"
                        value={tier.charge}
                        onChange={(e) => handleTierChange(index, 'charge', e.target.value)}
                        step="0.01"
                        min="0"
                        required
                        className="w-full rounded border px-3 py-2"
                      />
                    </div>
                    <button
                      type="button"
                      onClick={() => handleRemoveTier(index)}
                      className="rounded px-3 py-2 text-sm text-white"
                      style={{
                        background: 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)',
                      }}
                    >
                      Remove
                    </button>
                  </div>
                ))}

                <button
                  type="button"
                  onClick={handleAddTier}
                  className="mt-2 rounded px-4 py-2 text-sm text-white"
                  style={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  }}
                >
                  + Add Tier
                </button>

                {defaultFormData.tiers.length === 0 && (
                  <div className="mt-4 rounded border border-yellow-200 bg-yellow-50 p-3">
                    <strong className="text-sm text-yellow-700">
                      ⚠️ At least one tier is required.
                    </strong>
                    <p className="mb-0 mt-1 text-xs text-yellow-700">
                      Click &quot;+ Add Tier&quot; to create your first delivery charge tier.
                    </p>
                  </div>
                )}
              </div>

              <div className="rounded-lg bg-gray-50 p-4">
                <h4 className="mb-3 text-base font-semibold">Applicable To:</h4>
                <div className="flex gap-6">
                  <label className="flex cursor-pointer items-center">
                    <input
                      type="checkbox"
                      name="applicableToWholesaler"
                      checked={defaultFormData.applicableToWholesaler}
                      onChange={handleDefaultChange}
                      className="mr-2 h-5 w-5"
                    />
                    <span>Business Customers</span>
                  </label>
                </div>
                <small className="mt-2 block text-xs text-gray-500">
                  Select which roles this delivery charge applies to. Retail customers always see
                  delivery charges.
                </small>
              </div>

              <div className="rounded-lg bg-gray-50 p-4">
                <h4 className="mb-3 text-base font-semibold">GST on Delivery Charge:</h4>
                <div className="flex flex-col gap-4">
                  <label className="flex cursor-pointer items-center">
                    <input
                      type="checkbox"
                      name="deliveryChargeGst"
                      checked={defaultFormData.deliveryChargeGst}
                      onChange={handleDefaultChange}
                      className="mr-2 h-5 w-5 text-indigo-600"
                    />
                    <span>Apply GST on Delivery Charge</span>
                  </label>
                  {defaultFormData.deliveryChargeGst && (
                    <div>
                      <label className="mb-1 block text-sm font-semibold">GST Percentage</label>
                      <input
                        type="number"
                        name="deliveryChargeGstPercentage"
                        value={defaultFormData.deliveryChargeGstPercentage}
                        onChange={handleDefaultChange}
                        min="0"
                        max="100"
                        step="0.1"
                        className="w-full max-w-xs rounded border px-3 py-2 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      />
                    </div>
                  )}
                </div>
              </div>


              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    name="isActive"
                    checked={defaultFormData.isActive}
                    onChange={handleDefaultChange}
                    className="mr-2"
                  />
                  Active
                </label>
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowDefaultModal(false)}
                  className="rounded bg-gray-300 px-6 py-2 text-gray-700 hover:bg-gray-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded px-6 py-2 text-white"
                  style={{
                    background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)',
                  }}
                >
                  {defaultCharge ? '💾 Update Default Charge' : '➕ Create Default Charge'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CSV Upload Modal */}
      {showCsvModal && (
        <div
          className="fixed inset-0 z-[110] flex items-center justify-center bg-black bg-opacity-50 p-4"
          onClick={() => {
            setShowCsvModal(false);
            setCsvFile(null);
          }}
        >
          <div
            className="mx-4 w-full max-w-2xl rounded-lg bg-white p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="mb-4 text-xl font-bold">Upload Delivery Charges CSV</h3>
            <form onSubmit={handleCsvUpload}>
              <div className="mb-4">
                <label className="mb-1 block text-sm font-medium">CSV File *</label>
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
                  required
                  className="w-full rounded border px-3 py-2"
                />
                <small className="text-xs text-gray-500">
                  CSV format: pincode, state, city, district, charge, minCartValue, serviceableForCustomer, urgentDeliveryAvailable, urgentDeliveryCharge
                </small>
              </div>
              <div className="mb-4">
                <button
                  type="button"
                  onClick={downloadSampleCsv}
                  className="text-sm text-blue-600 hover:underline"
                >
                  Download Sample CSV
                </button>
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowCsvModal(false);
                    setCsvFile(null);
                  }}
                  className="rounded bg-gray-300 px-6 py-2 text-gray-700 hover:bg-gray-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading}
                  className="rounded px-6 py-2 text-white disabled:bg-gray-400"
                  style={{
                    background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)',
                  }}
                >
                  {uploading ? 'Uploading...' : 'Upload CSV'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  </div>
  );
}
