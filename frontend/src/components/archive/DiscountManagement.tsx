'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import InfoButton from '@/components/InfoButton';
import { formatDateIST } from '@/utils/dateUtils';
import SearchableSelect from '@/components/SearchableSelect';
import ReferralOptionManagement from '@/components/Admin/ReferralOptionManagement';
import { logger } from '@/utils/logger';

interface Discount {
  _id?: string;
  displayId?: string;
  typeOfDiscount?: string;
  code?: string | null;
  method?: string;
  couponMode?: 'override' | 'extra';
  discountType: 'percentage' | 'fixed';
  discountValue: number;
  minPurchaseAmount?: number;
  minRequirementType?: string;
  minQuantityOfEligibleItems?: number | null;
  validFrom?: string;
  validUntil?: string;
  usageLimit?: number;
  usedCount?: number;
  applicableRoles?: string[];
  applicableUserIds?: string[];
  appliesToType?: string;
  appliesToValueIds?: string[];
  userBehavior?: string | null;
  isActive?: boolean;
  maxUsagePerUser?: number;
  applicableItemType?: 'units' | 'cases';
  buyXGetYCustomerGetsQuantity?: number | null;
  buyXGetYCustomerGetsAppliesToType?: string;
  buyXGetYCustomerGetsAppliesToValueIds?: string[];
  buyXGetYCustomerGetsDiscountType?: string;
  buyXGetYCustomerGetsDiscountValue?: number | null;
  shippingStates?: string[];
  shippingDistricts?: string[];
  shippingPincodes?: string[];
  applicablePaymentMethods?: string[];
}

interface Category {
  _id: string;
  name: string;
  subCategories?: string[];
}
interface Brand {
  _id: string;
  name: string;
}
interface Collection {
  _id: string;
  name: string;
}
interface UserOption {
  _id: string;
  name?: string;
  phone?: string;
  email?: string;
}

const APPLIES_TO_OPTIONS = [
  { value: 'all', label: 'All Products' },
  { value: 'categories', label: 'Categories' },
  { value: 'subCategories', label: 'Sub-categories' },
  { value: 'brands', label: 'Brands' },
  { value: 'collections', label: 'Collections' },
  { value: 'products', label: 'Products' },
] as const;

const MIN_REQUIREMENT_OPTIONS = [
  { value: 'none', label: 'No requirement' },
  { value: 'min_amount', label: 'Minimum purchase amount' },
  { value: 'min_quantity', label: 'Minimum quantity of items' },
];

const TYPE_OF_DISCOUNT_OPTIONS = [
  { value: 'product_discount', label: 'Amount off each Product' },
  { value: 'buy_x_get_y', label: 'Buy X Get Y' },
  { value: 'total_order_discount', label: 'Total order discount' },
  { value: 'shipping_discount', label: 'Shipping discount' },
];

interface DiscountManagementProps {
  discountCategory: 'retail' | 'business';
}

export default function DiscountManagement({ discountCategory }: DiscountManagementProps) {
  const router = useRouter();
  const { user } = useAuth();
  const discountOptions = [
    ...TYPE_OF_DISCOUNT_OPTIONS,
    ...(discountCategory === 'retail'
      ? [{ value: 'quantity_discount', label: 'Quantity-Based Discount' }]
      : []),
  ];
  const [discounts, setDiscounts] = useState<Discount[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showReferralModal, setShowReferralModal] = useState(false);
  const [editingDiscount, setEditingDiscount] = useState<Discount | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [retailUsers, setRetailUsers] = useState<UserOption[]>([]);
  const [businessUsers, setBusinessUsers] = useState<UserOption[]>([]);
  const [pageInfo, setPageInfo] = useState<{
    page: { title?: string; description?: string } | null;
    columns: Record<string, string>;
  }>({ page: null, columns: {} });
  const [availableStates, setAvailableStates] = useState<string[]>([]);
  const [availableDistricts, setAvailableDistricts] = useState<string[]>([]);
  const [availablePincodes, setAvailablePincodes] = useState<string[]>([]);
  const [pincodeSearch, setPincodeSearch] = useState('');
  const [customSegments, setCustomSegments] = useState<any[]>([]);
  const [overlapConflict, setOverlapConflict] = useState<any>(null);
  const [formData, setFormData] = useState({
    typeOfDiscount: 'product_discount' as string,
    method: 'automatic' as string,
    code: '',
    couponMode: 'override' as 'override' | 'extra',
    discountType: 'percentage' as 'percentage' | 'fixed',
    discountValue: '',
    minRequirementType: 'none' as string,
    minPurchaseAmount: '',
    minQuantityOfEligibleItems: '' as string,
    validFrom: new Date().toISOString().split('T')[0],
    validUntil: '',
    maxUsageCount: '',
    maxUsagePerUser: '',
    applicableRoles: ['customer'] as string[],
    applicableUserIds: [] as string[],
    appliesToType: 'all' as string,
    appliesToValueIds: [] as string[],
    userBehavior: 'none' as string,
    applicableItemType: 'units' as 'units' | 'cases',
    isActive: true,
    buyXGetYCustomerGetsQuantity: '' as string,
    buyXGetYCustomerGetsAppliesToType: 'all' as string,
    buyXGetYCustomerGetsAppliesToValueIds: [] as string[],
    buyXGetYCustomerGetsDiscountType: 'percentage' as string,
    buyXGetYCustomerGetsDiscountValue: '' as string,
    shippingState: '' as string,
    shippingDistrict: '' as string,
    shippingPincodes: [] as string[],
    applicablePaymentMethods: ['all'] as string[],
  });

  useEffect(() => {
    if (user?.role === 'super_admin') {
      fetchDiscounts();
      fetchPageInfo();
      Promise.all([
        api.get('/categories').then((r) => setCategories(r.data || [])),
        api.get('/brands').then((r) => setBrands(r.data || [])),
        api.get('/collections').then((r) => setCollections(r.data || [])),
        api.get('/products', { params: { limit: 1000 } }).then((r) => setProducts(r.data?.products || r.data || [])),
        api
          .get('/users', { params: { role: 'customer' } })
          .then((r) => setRetailUsers(r.data || [])),
        api
          .get('/users', { params: { role: 'wholesaler' } })
          .then((r) => setBusinessUsers(r.data || [])),
        api.get('/pincodes/states').then((r) => setAvailableStates(r.data || [])),
        api
          .get(`/customer-segments?type=${discountCategory}`)
          .then((r) => setCustomSegments(r.data || [])),
      ]).catch((e) => logger.warn("Promise rejected silently:", e));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const fetchPageInfo = async () => {
    try {
      const response = await api.get('/page-info/discount-management');
      setPageInfo(response.data);
    } catch (error) {
      logger.error('Failed to fetch page info:', error);
    }
  };

  // eslint-disable-next-line unused-imports/no-unused-vars
  const fetchStates = async () => {
    try {
      const response = await api.get('/pincodes/states');
      setAvailableStates(response.data || []);
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error) {
      logger.error('Failed to fetch states');
    }
  };

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
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error) {
      logger.error('Failed to fetch districts');
      setAvailableDistricts([]);
    }
  };

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
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error) {
      logger.error('Failed to fetch pincodes');
      setAvailablePincodes([]);
    }
  };

  const fetchDiscounts = async () => {
    try {
      const response = await api.get('/coupons');
      setDiscounts(response.data || []);
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to fetch discounts');
    } finally {
      setLoading(false);
    }
  };

  const subCategoryOptions = (() => {
    const set = new Set<string>();
    categories.forEach((c) => (c.subCategories || []).forEach((s: string) => set.add(s)));
    return Array.from(set).sort();
  })();

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;
    let newFormData = { ...formData, [name]: type === 'checkbox' ? checked : value };
    if (
      name === 'typeOfDiscount' &&
      value === 'buy_x_get_y' &&
      newFormData.minRequirementType === 'none'
    ) {
      newFormData.minRequirementType = 'min_amount';
    }
    if (name === 'typeOfDiscount' && value === 'quantity_discount') {
      newFormData.minRequirementType = 'min_quantity';
    }
    if (name === 'method' && value === 'discount_code') {
      newFormData.userBehavior = discountCategory === 'retail' ? 'selective_retail' : 'selective_business';
    }
    if (name === 'method' && value === 'automatic') {
      newFormData.userBehavior = 'none';
    }
    setFormData(newFormData);
  };

  const handleAppliesToTypeChange = (value: string) => {
    setFormData({ ...formData, appliesToType: value, appliesToValueIds: [] });
  };

  const toggleAppliesToValue = (idOrName: string) => {
    const current = formData.appliesToValueIds || [];
    const next = current.includes(idOrName)
      ? current.filter((x) => x !== idOrName)
      : [...current, idOrName];
    setFormData({ ...formData, appliesToValueIds: next });
  };

  const toggleApplicableUser = (userId: string) => {
    const current = formData.applicableUserIds || [];
    const next = current.includes(userId)
      ? current.filter((x) => x !== userId)
      : [...current, userId];
    setFormData({ ...formData, applicableUserIds: next });
  };

  const handleGetsAppliesToTypeChange = (value: string) => {
    setFormData({
      ...formData,
      buyXGetYCustomerGetsAppliesToType: value,
      buyXGetYCustomerGetsAppliesToValueIds: [],
    });
  };

  const toggleGetsAppliesToValue = (idOrName: string) => {
    const current = formData.buyXGetYCustomerGetsAppliesToValueIds || [];
    const next = current.includes(idOrName)
      ? current.filter((x) => x !== idOrName)
      : [...current, idOrName];
    setFormData({ ...formData, buyXGetYCustomerGetsAppliesToValueIds: next });
  };

  const AppliesToSelector = ({
    appliesToType,
    appliesToValueIds,
    onTypeChange,
    onValueToggle,
    labelTitle = 'Applies to',
  }: {
    appliesToType: string;
    appliesToValueIds: string[];
    onTypeChange: (val: string) => void;
    onValueToggle: (id: string) => void;
    labelTitle?: string;
  }) => {
    const [searchQuery, setSearchQuery] = useState('');

    const getItems = () => {
      if (appliesToType === 'categories')
        return categories.map((c) => ({ id: c._id, name: c.name }));
      if (appliesToType === 'subCategories')
        return subCategoryOptions.map((s) => ({ id: s, name: s }));
      if (appliesToType === 'brands') return brands.map((b) => ({ id: b._id, name: b.name }));
      if (appliesToType === 'collections')
        return collections.map((c) => ({ id: c._id, name: c.name }));
      if (appliesToType === 'products')
        return products.map((p) => ({ id: p._id, name: p.name }));
      return [];
    };

    const items = getItems();
    const filteredItems = items.filter((item) =>
      item.name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
      <div className="pt-2">
        <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
          {labelTitle}
        </label>
        <select
          value={appliesToType}
          onChange={(e) => {
            onTypeChange(e.target.value);
            setSearchQuery('');
          }}
          className="w-full rounded border-2 border-gray-400 bg-white px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          {APPLIES_TO_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        {appliesToType !== 'all' && (
          <div className="mt-3 rounded border-2 border-gray-400 bg-white p-3 shadow-sm">
            <div className="mb-2 flex items-center justify-between">
              <label className="block text-sm font-medium">
                Select{' '}
                {appliesToType === 'categories'
                  ? 'categories'
                  : appliesToType === 'subCategories'
                    ? 'sub-categories'
                    : appliesToType === 'brands'
                      ? 'brands'
                      : appliesToType === 'products'
                        ? 'products'
                        : 'collections'}{' '}
                *
              </label>
              <span className="rounded-full bg-gray-100 px-2 py-1 text-xs font-semibold text-gray-500">
                {appliesToValueIds?.length || 0} selected
              </span>
            </div>

            <input
              type="text"
              placeholder={`Search ${filteredItems.length} items...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="mb-2 w-full rounded border-2 border-gray-400 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />

            <div className="h-48 space-y-1 overflow-y-auto rounded border-2 border-gray-400 bg-gray-50 p-2">
              {filteredItems.length === 0 ? (
                <div className="p-4 text-center text-sm text-gray-500">No matching items found</div>
              ) : (
                filteredItems.map((item) => (
                  <label
                    key={item.id}
                    className="group flex cursor-pointer items-center gap-2 rounded p-1.5 transition-colors hover:bg-white"
                  >
                    <input
                      type="checkbox"
                      checked={appliesToValueIds?.includes(item.id)}
                      onChange={() => onValueToggle(item.id)}
                      className="rounded text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm group-hover:text-blue-700">{item.name}</span>
                  </label>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  const SelectiveUsersSelector = () => {
    const [searchQuery, setSearchQuery] = useState('');

    const filteredUsers = selectiveUserList.filter(
      (u) =>
        (u.name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
        (u.phone || '').includes(searchQuery) ||
        (u.email || '').toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
      <div className="rounded border-2 border-gray-400 bg-white p-3 shadow-sm">
        <div className="mb-2 flex items-center justify-between">
          <label className="block text-sm font-medium">
            Select {discountCategory === 'retail' ? 'retail' : 'business'} customers *
          </label>
          <span className="rounded-full bg-gray-100 px-2 py-1 text-xs font-semibold text-gray-500">
            {formData.applicableUserIds?.length || 0} selected
          </span>
        </div>

        <input
          type="text"
          placeholder={`Search ${filteredUsers.length} users by name, email or phone...`}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="mb-2 w-full rounded border-2 border-gray-400 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />

        <div className="h-48 space-y-1 overflow-y-auto rounded border-2 border-gray-400 bg-gray-50 p-2">
          {filteredUsers.length === 0 ? (
            <div className="p-4 text-center text-sm text-gray-500">No matching users found</div>
          ) : (
            filteredUsers.map((u) => (
              <label
                key={u._id}
                className="group flex cursor-pointer items-center gap-2 rounded p-1.5 transition-colors hover:bg-white"
              >
                <input
                  type="checkbox"
                  checked={formData.applicableUserIds?.includes(u._id)}
                  onChange={() => toggleApplicableUser(u._id)}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm group-hover:text-blue-700">
                  {u.name ? `${u.name} ` : ''}
                  {u.phone ? `(${u.phone}) ` : ''}
                  {u.email ? `[${u.email}]` : ''}
                  {!u.name && !u.phone && !u.email ? u._id : ''}
                </span>
              </label>
            ))
          )}
        </div>
      </div>
    );
  };

  const showUserBehaviour = true;
  const showSelectiveUsers =
    formData.userBehavior === 'selective_retail' || formData.userBehavior === 'selective_business';
  const selectiveUserList = discountCategory === 'retail' ? retailUsers : businessUsers;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.method === 'discount_code' && !formData.code?.trim()) {
      toast.error('Discount code is required when method is Discount code');
      return;
    }
    if (showSelectiveUsers && !formData.applicableUserIds?.length) {
      toast.error(
        `Select at least one ${discountCategory === 'retail' ? 'retail' : 'business'} customer for selective discount`
      );
      return;
    }
    try {
      const submitData: Record<string, unknown> = {
        typeOfDiscount: formData.typeOfDiscount || 'product_discount',
        method: formData.method,
        code:
          formData.method === 'discount_code' ? (formData.code || '').trim().toUpperCase() : null,
        couponMode: formData.method === 'discount_code' ? formData.couponMode : 'override',
        discountType: formData.discountType,
        discountValue: parseFloat(formData.discountValue) || 0,
        minRequirementType: formData.minRequirementType || 'none',
        minPurchaseAmount:
          formData.minRequirementType === 'min_amount'
            ? parseFloat(formData.minPurchaseAmount) || 0
            : 0,
        minQuantityOfEligibleItems:
          formData.minRequirementType === 'min_quantity'
            ? parseInt(formData.minQuantityOfEligibleItems, 10) || null
            : null,
        usageLimit: formData.maxUsageCount ? parseInt(formData.maxUsageCount, 10) : null,
        maxUsagePerUser: formData.maxUsagePerUser ? parseInt(formData.maxUsagePerUser, 10) : null,
        validFrom: formData.validFrom ? new Date(formData.validFrom).toISOString() : undefined,
        validUntil: formData.validUntil ? new Date(formData.validUntil).toISOString() : null,
        applicableRoles: formData.applicableRoles?.length
          ? formData.applicableRoles
          : discountCategory === 'retail'
            ? ['customer']
            : ['wholesaler'],
        applicableUserIds: formData.applicableUserIds?.length ? formData.applicableUserIds : [],
        appliesToType: formData.appliesToType || 'all',
        appliesToValueIds: (formData.appliesToValueIds?.length
          ? formData.appliesToValueIds
          : []) as string[],
        userBehavior:
          formData.userBehavior !== 'none' &&
          formData.userBehavior !== 'selective_retail' &&
          formData.userBehavior !== 'selective_business'
            ? formData.userBehavior
            : null,
        applicableItemType:
          discountCategory === 'business' ? formData.applicableItemType : undefined,
        isActive: formData.isActive,
        buyXGetYCustomerGetsQuantity: formData.buyXGetYCustomerGetsQuantity
          ? parseInt(formData.buyXGetYCustomerGetsQuantity, 10)
          : null,
        buyXGetYCustomerGetsAppliesToType: formData.buyXGetYCustomerGetsAppliesToType,
        buyXGetYCustomerGetsAppliesToValueIds: formData.buyXGetYCustomerGetsAppliesToValueIds,
        buyXGetYCustomerGetsDiscountType: formData.buyXGetYCustomerGetsDiscountType,
        buyXGetYCustomerGetsDiscountValue: formData.buyXGetYCustomerGetsDiscountValue
          ? parseFloat(formData.buyXGetYCustomerGetsDiscountValue)
          : null,
        shippingStates: formData.shippingState ? [formData.shippingState] : [],
        shippingDistricts: formData.shippingDistrict ? [formData.shippingDistrict] : [],
        shippingPincodes: formData.shippingPincodes,
        applicablePaymentMethods: formData.applicablePaymentMethods.includes('all')
          ? ['cod', 'upi', 'credit']
          : formData.applicablePaymentMethods,
      };
      if (editingDiscount?._id) {
        await api.put(`/coupons/${editingDiscount._id}`, submitData);
        toast.success('Discount updated successfully');
      } else {
        await api.post('/coupons', submitData);
        toast.success('Discount created successfully');
      }
      setShowModal(false);
      setEditingDiscount(null);
      resetForm();
      fetchDiscounts();
    } catch (error: any) {
      if (error.response?.status === 409 && error.response.data?.detail?.overlap) {
        setOverlapConflict(error.response.data.detail.overlap);
        return;
      }
      toast.error(
        error.response?.data?.detail?.message ||
          error.response?.data?.detail ||
          error.response?.data?.message ||
          'Operation failed'
      );
    }
  };

  const handleManualResolution = async (resolution: 'overwrite' | 'retain') => {
    if (!overlapConflict) return;
    try {
      const submitData: Record<string, unknown> = {
        typeOfDiscount: formData.typeOfDiscount || 'product_discount',
        method: formData.method,
        code:
          formData.method === 'discount_code' ? (formData.code || '').trim().toUpperCase() : null,
        couponMode: formData.method === 'discount_code' ? formData.couponMode : 'override',
        discountType: formData.discountType,
        discountValue: parseFloat(formData.discountValue) || 0,
        minRequirementType: formData.minRequirementType || 'none',
        minPurchaseAmount:
          formData.minRequirementType === 'min_amount'
            ? parseFloat(formData.minPurchaseAmount) || 0
            : 0,
        minQuantityOfEligibleItems:
          formData.minRequirementType === 'min_quantity'
            ? parseInt(formData.minQuantityOfEligibleItems, 10) || null
            : null,
        usageLimit: formData.maxUsageCount ? parseInt(formData.maxUsageCount, 10) : null,
        maxUsagePerUser: formData.maxUsagePerUser ? parseInt(formData.maxUsagePerUser, 10) : null,
        validFrom: formData.validFrom ? new Date(formData.validFrom).toISOString() : undefined,
        validUntil: formData.validUntil ? new Date(formData.validUntil).toISOString() : null,
        applicableRoles: formData.applicableRoles?.length
          ? formData.applicableRoles
          : discountCategory === 'retail'
            ? ['customer']
            : ['wholesaler'],
        applicableUserIds: formData.applicableUserIds?.length ? formData.applicableUserIds : [],
        appliesToType: formData.appliesToType || 'all',
        appliesToValueIds: (formData.appliesToValueIds?.length
          ? formData.appliesToValueIds
          : []) as string[],
        userBehavior:
          formData.userBehavior !== 'none' &&
          formData.userBehavior !== 'selective_retail' &&
          formData.userBehavior !== 'selective_business'
            ? formData.userBehavior
            : null,
        applicableItemType:
          discountCategory === 'business' ? formData.applicableItemType : undefined,
        isActive: formData.isActive,
        buyXGetYCustomerGetsQuantity: formData.buyXGetYCustomerGetsQuantity
          ? parseInt(formData.buyXGetYCustomerGetsQuantity, 10)
          : null,
        buyXGetYCustomerGetsAppliesToType: formData.buyXGetYCustomerGetsAppliesToType,
        buyXGetYCustomerGetsAppliesToValueIds: formData.buyXGetYCustomerGetsAppliesToValueIds,
        buyXGetYCustomerGetsDiscountType: formData.buyXGetYCustomerGetsDiscountType,
        buyXGetYCustomerGetsDiscountValue: formData.buyXGetYCustomerGetsDiscountValue
          ? parseFloat(formData.buyXGetYCustomerGetsDiscountValue)
          : null,
        shippingStates: formData.shippingState ? [formData.shippingState] : [],
        shippingDistricts: formData.shippingDistrict ? [formData.shippingDistrict] : [],
        shippingPincodes: formData.shippingPincodes,
        applicablePaymentMethods: formData.applicablePaymentMethods.includes('all')
          ? ['cod', 'upi', 'credit']
          : formData.applicablePaymentMethods,
      };

      const params = { resolution };
      if (editingDiscount?._id) {
        await api.put(`/coupons/${editingDiscount._id}`, submitData, { params });
        toast.success('Discount updated with resolution');
      } else {
        await api.post('/coupons', submitData, { params });
        toast.success('Discount created with resolution');
      }
      setOverlapConflict(null);
      setShowModal(false);
      setEditingDiscount(null);
      resetForm();
      fetchDiscounts();
    } catch (error: any) {
      toast.error(
        error.response?.data?.detail || error.response?.data?.message || 'Resolution failed'
      );
    }
  };

  const resetForm = () => {
    setFormData({
      typeOfDiscount: 'product_discount',
      method: 'automatic',
      code: '',
      couponMode: 'override',
      discountType: 'percentage',
      discountValue: '',
      minRequirementType: 'none',
      minPurchaseAmount: '',
      minQuantityOfEligibleItems: '',
      validFrom: new Date().toISOString().split('T')[0],
      validUntil: '',
      maxUsageCount: '',
      maxUsagePerUser: '',
      applicableRoles: discountCategory === 'retail' ? ['customer'] : ['wholesaler'],
      applicableUserIds: [],
      appliesToType: 'all',
      appliesToValueIds: [],
      userBehavior: 'none',
      applicableItemType: 'units',
      isActive: true,
      buyXGetYCustomerGetsQuantity: '',
      buyXGetYCustomerGetsAppliesToType: 'all',
      buyXGetYCustomerGetsAppliesToValueIds: [],
      buyXGetYCustomerGetsDiscountType: 'percentage',
      buyXGetYCustomerGetsDiscountValue: '',
      shippingState: '',
      shippingDistrict: '',
      shippingPincodes: [],
      applicablePaymentMethods: ['all'],
    });
  };

  const handleEdit = (d: Discount) => {
    setEditingDiscount(d);
    let behavior = d.userBehavior || 'none';
    if (d.applicableUserIds?.length) {
      behavior = discountCategory === 'business' ? 'selective_business' : 'selective_retail';
    }
    setFormData({
      typeOfDiscount: d.typeOfDiscount || 'product_discount',
      method: d.method || 'discount_code',
      code: d.code || '',
      couponMode: d.couponMode || 'override',
      discountType: d.discountType || 'percentage',
      discountValue: d.discountValue?.toString() || '',
      minRequirementType:
        d.typeOfDiscount === 'buy_x_get_y' &&
        (!d.minRequirementType || d.minRequirementType === 'none')
          ? 'min_amount'
          : d.minRequirementType || 'none',
      minPurchaseAmount: d.minPurchaseAmount?.toString() || '',
      minQuantityOfEligibleItems: d.minQuantityOfEligibleItems?.toString() || '',
      validFrom: d.validFrom ? d.validFrom.split('T')[0] : '',
      validUntil: d.validUntil ? d.validUntil.split('T')[0] : '',
      maxUsageCount: d.usageLimit?.toString() || '',
      maxUsagePerUser: d.maxUsagePerUser?.toString() || '',
      applicableRoles:
        d.applicableRoles || (discountCategory === 'business' ? ['wholesaler'] : ['customer']),
      applicableUserIds: d.applicableUserIds || [],
      appliesToType: d.appliesToType || 'all',
      appliesToValueIds: d.appliesToValueIds || [],
      userBehavior: behavior,
      applicableItemType: d.applicableItemType || 'units',
      isActive: d.isActive !== false,
      buyXGetYCustomerGetsQuantity: d.buyXGetYCustomerGetsQuantity?.toString() || '',
      buyXGetYCustomerGetsAppliesToType: d.buyXGetYCustomerGetsAppliesToType || 'all',
      buyXGetYCustomerGetsAppliesToValueIds: d.buyXGetYCustomerGetsAppliesToValueIds || [],
      buyXGetYCustomerGetsDiscountType: d.buyXGetYCustomerGetsDiscountType || 'percentage',
      buyXGetYCustomerGetsDiscountValue: d.buyXGetYCustomerGetsDiscountValue?.toString() || '',
      shippingState: d.shippingStates?.[0] || '',
      shippingDistrict: d.shippingDistricts?.[0] || '',
      shippingPincodes: d.shippingPincodes || [],
      applicablePaymentMethods: d.applicablePaymentMethods || ['all'],
    });

    if (d.shippingStates?.[0]) {
      fetchDistricts(d.shippingStates[0]);
      if (d.shippingDistricts?.[0]) {
        fetchPincodes(d.shippingStates[0], d.shippingDistricts[0]);
      }
    }
    setShowModal(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this discount?')) return;
    try {
      await api.delete(`/coupons/${id}`);
      toast.success('Discount deleted successfully');
      fetchDiscounts();
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to delete discount');
    }
  };

  const isExpired = (d: Discount) => (d.validUntil ? new Date(d.validUntil) < new Date() : false);
  const isUsageExceeded = (d: Discount) =>
    d.usageLimit ? (d.usedCount || 0) >= d.usageLimit : false;
  const displayCode = (d: Discount) => (d.method === 'automatic' ? 'Automatic' : d.code || '-');
  const displayType = (d: Discount) => {
    const allOptions = [
      ...TYPE_OF_DISCOUNT_OPTIONS,
      { value: 'quantity_discount', label: 'Quantity-Based Discount' }
    ];
    return allOptions.find((o) => o.value === (d.typeOfDiscount || 'product_discount'))?.label || 'Amount off each Product';
  };

  const displayedDiscounts = discounts.filter((d) => {
    if (discountCategory === 'retail') {
      return (
        d.applicableRoles?.includes('customer') ||
        (!d.applicableRoles?.includes('wholesaler') && !d.applicableRoles?.includes('customer'))
      );
    } else {
      return d.applicableRoles?.includes('wholesaler');
    }
  });

  if (user?.role !== 'super_admin') return <div>Access Denied</div>;
  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <div className="rounded-lg bg-white p-6 shadow-md">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="inline-flex items-baseline gap-2 text-2xl font-bold">
            <InfoButton
              info={
                user?.role === 'super_admin' && pageInfo.page?.description
                  ? pageInfo.page.description
                  : undefined
              }
            >
              {discountCategory === 'retail' ? 'Retail Discounts' : 'Business Discounts'}
            </InfoButton>
          </h2>
          <div className="flex gap-2">
            {discountCategory === 'retail' && (
              <button
                onClick={() => setShowReferralModal(true)}
                className="flex items-center gap-2 rounded px-4 py-2 text-white shadow-sm transition-all hover:shadow-md"
                style={{ background: 'linear-gradient(135deg, #007BFF 0%, #0056b3 100%)' }}
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
                  />
                </svg>
                Referral Bonus
              </button>
            )}
            <button
              onClick={() => {
                setShowModal(true);
                setEditingDiscount(null);
                resetForm();
              }}
              className="rounded px-4 py-2 text-white shadow-sm transition-all hover:shadow-md"
              style={{ background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)' }}
            >
              Add Discount
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                  <span className="inline-flex items-baseline gap-1">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.displayId
                          ? pageInfo.columns.displayId
                          : undefined
                      }
                    >
                      ID
                    </InfoButton>
                  </span>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                  <span className="inline-flex items-baseline gap-1">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.type
                          ? pageInfo.columns.type
                          : undefined
                      }
                    >
                      Type
                    </InfoButton>
                  </span>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                  <span className="inline-flex items-baseline gap-1">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.method
                          ? pageInfo.columns.method
                          : undefined
                      }
                    >
                      Method
                    </InfoButton>
                  </span>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                  <span className="inline-flex items-baseline gap-1">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.code
                          ? pageInfo.columns.code
                          : undefined
                      }
                    >
                      Code
                    </InfoButton>
                  </span>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                  <span className="inline-flex items-baseline gap-1">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.discount
                          ? pageInfo.columns.discount
                          : undefined
                      }
                    >
                      Discount
                    </InfoButton>
                  </span>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                  <span className="inline-flex items-baseline gap-1">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.validUntil
                          ? pageInfo.columns.validUntil
                          : undefined
                      }
                    >
                      Valid Until
                    </InfoButton>
                  </span>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                  <span className="inline-flex items-baseline gap-1">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.usageLimit
                          ? pageInfo.columns.usageLimit
                          : undefined
                      }
                    >
                      Max Usage
                    </InfoButton>
                  </span>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                  <span className="inline-flex items-baseline gap-1">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.usedCount
                          ? pageInfo.columns.usedCount
                          : undefined
                      }
                    >
                      Used
                    </InfoButton>
                  </span>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                  <span className="inline-flex items-baseline gap-1">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.status
                          ? pageInfo.columns.status
                          : undefined
                      }
                    >
                      Status
                    </InfoButton>
                  </span>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                  <span className="inline-flex items-baseline gap-1">
                    <InfoButton
                      info={
                        user?.role === 'super_admin' && pageInfo.columns?.actions
                          ? pageInfo.columns.actions
                          : undefined
                      }
                    >
                      Actions
                    </InfoButton>
                  </span>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {displayedDiscounts.length > 0 ? (
                displayedDiscounts.map((d) => {
                  const expired = isExpired(d);
                  const usageExceeded = isUsageExceeded(d);
                  return (
                    <tr key={d._id}>
                      <td className="whitespace-nowrap px-6 py-4">{d.displayId || '-'}</td>
                      <td className="whitespace-nowrap px-6 py-4">{displayType(d)}</td>
                      <td className="whitespace-nowrap px-6 py-4">
                        {d.method === 'automatic' ? 'Automatic' : 'Discount code'}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <strong>{displayCode(d)}</strong>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        {d.discountType === 'percentage'
                          ? `${d.discountValue}%`
                          : `₹${d.discountValue}`}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        {d.validUntil ? formatDateIST(d.validUntil) : 'No expiry'}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">{d.usageLimit || 'Unlimited'}</td>
                      <td className="whitespace-nowrap px-6 py-4">{d.usedCount || 0}</td>
                      <td className="whitespace-nowrap px-6 py-4">
                        {!d.isActive ? (
                          <span className="rounded bg-red-100 px-2 py-1 text-xs text-red-800">
                            Inactive
                          </span>
                        ) : expired ? (
                          <span className="rounded bg-yellow-100 px-2 py-1 text-xs text-yellow-800">
                            Expired
                          </span>
                        ) : usageExceeded ? (
                          <span className="rounded bg-yellow-100 px-2 py-1 text-xs text-yellow-800">
                            Usage Exceeded
                          </span>
                        ) : (
                          <span className="rounded bg-green-100 px-2 py-1 text-xs text-green-800">
                            Active
                          </span>
                        )}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <div className="flex gap-2">
                          <button
                            type="button"
                            onClick={() => handleEdit(d)}
                            className="rounded px-3 py-1 text-sm text-white"
                            style={{
                              background: 'linear-gradient(135deg, #FFC107 0%, #FF9800 100%)',
                            }}
                          >
                            Edit
                          </button>
                          <button
                            type="button"
                            onClick={() => d._id && handleDelete(d._id)}
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
                  );
                })
              ) : (
                <tr>
                  <td colSpan={9} className="px-6 py-4 text-center text-gray-500">
                    No discounts found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

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
              {editingDiscount ? 'Edit Discount' : 'Add Discount'}
            </h3>
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Type of discount - first field */}
              <div>
                <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                  Type of discount *
                </label>
                <select
                  name="typeOfDiscount"
                  value={formData.typeOfDiscount}
                  onChange={handleChange}
                  className="w-full rounded border-2 border-gray-400 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  {discountOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
              {discountCategory === 'business' &&
                formData.typeOfDiscount !== 'total_order_discount' &&
                formData.typeOfDiscount !== 'shipping_discount' && (
                  <div>
                    <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                      Apply discount to
                    </label>
                    <select
                      name="applicableItemType"
                      value={formData.applicableItemType}
                      onChange={handleChange}
                      className="w-full rounded border-2 border-gray-400 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    >
                      <option value="units">Units</option>
                      <option value="cases">Cases</option>
                    </select>
                  </div>
                )}
              {/* Method */}
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                    Method *
                  </label>
                  <select
                    name="method"
                    value={formData.method}
                    onChange={handleChange}
                    className="w-full rounded border-2 border-gray-400 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="discount_code">Discount code</option>
                    <option value="automatic">Automatic discount</option>
                  </select>
                  <small className="mt-1 block text-xs text-gray-500">
                    Automatic discount is applied for the selected segment, behaviour and products.
                  </small>
                </div>
                {formData.method === 'discount_code' && (
                  <>
                    <div>
                      <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                        Discount Code *
                      </label>
                      <input
                        type="text"
                        name="code"
                        value={formData.code}
                        onChange={handleChange}
                        required={formData.method === 'discount_code'}
                        style={{ textTransform: 'uppercase' }}
                        className="w-full rounded border-2 border-gray-400 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </div>
                    <div className="md:col-span-2">
                      <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                        Coupon Mode *
                      </label>
                      <select
                        name="couponMode"
                        value={formData.couponMode}
                        onChange={handleChange}
                        className="w-full rounded border-2 border-gray-400 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        <option value="override">Override (replaces default automatic discount)</option>
                        <option value="extra">Extra (applies on top of default automatic discount)</option>
                      </select>
                      <small className="mt-1 block text-xs text-gray-500">
                        Define whether this coupon code overrides/replaces the default automatic discount or stacks on top of it.
                      </small>
                    </div>
                  </>
                )}
              </div>

              {/* Eligibility */}
              <div className="border-t pt-4">
                <h4 className="mb-3 text-sm font-semibold text-gray-700">Eligibility</h4>
                <div className="space-y-3">
                  {showUserBehaviour && (
                    <div>
                      <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                        User behaviour
                      </label>
                      {formData.method === 'discount_code' ? (
                        <div className="w-full rounded border border-gray-300 bg-gray-100 px-3 py-2 text-sm text-gray-600 font-semibold">
                          {discountCategory === 'retail' ? 'Selective Retail Customers' : 'Selective Business Customers'}
                        </div>
                      ) : (
                        <select
                          name="userBehavior"
                          value={formData.userBehavior}
                          onChange={handleChange}
                          className="w-full rounded border-2 border-gray-400 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        >
                          <option value="none">All</option>
                          {customSegments.map((seg) => (
                            <option
                              key={`segment_${seg._id || seg.id}`}
                              value={`segment_${seg._id || seg.id}`}
                            >
                              {seg.name}
                            </option>
                          ))}
                          {discountCategory === 'retail' ? (
                            <option value="selective_retail">Selective Retail Customers</option>
                          ) : (
                            <option value="selective_business">Selective Business Customers</option>
                          )}
                        </select>
                      )}
                    </div>
                  )}
                  {showSelectiveUsers && <SelectiveUsersSelector />}
                </div>
              </div>

              {/* Minimum purchase requirements */}
              <div className="border-t pt-4">
                <h4 className="mb-3 text-sm font-semibold text-gray-700">
                  {formData.typeOfDiscount === 'buy_x_get_y'
                    ? 'Customer buys (Minimum purchase requirements)'
                    : 'Minimum purchase requirements'}
                </h4>
                <div className="space-y-3">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                        Requirement type
                      </label>
                      {formData.typeOfDiscount === 'quantity_discount' ? (
                        <div className="w-full rounded border border-gray-300 bg-gray-100 px-3 py-2 text-sm text-gray-600 font-semibold">
                          Minimum quantity of items
                        </div>
                      ) : (
                        <select
                          name="minRequirementType"
                          value={formData.minRequirementType}
                          onChange={handleChange}
                          className="w-full rounded border-2 border-gray-400 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        >
                          {(formData.typeOfDiscount === 'buy_x_get_y'
                            ? MIN_REQUIREMENT_OPTIONS.filter((o) => o.value !== 'none')
                            : MIN_REQUIREMENT_OPTIONS
                          ).map((opt) => (
                            <option key={opt.value} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      )}
                    </div>
                    {formData.minRequirementType === 'min_amount' && (
                      <div>
                        <label className="mb-1 block text-sm font-medium">
                          Minimum purchase amount (₹) — on eligible items
                        </label>
                        <input
                          type="number"
                          name="minPurchaseAmount"
                          value={formData.minPurchaseAmount}
                          onChange={handleChange}
                          step="0.01"
                          min="0"
                          placeholder="0"
                          className="w-full rounded border-2 border-gray-400 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                      </div>
                    )}
                    {formData.minRequirementType === 'min_quantity' && (
                      <div>
                        <label className="mb-1 block text-sm font-medium">
                          Minimum quantity of eligible items
                        </label>
                        <input
                          type="number"
                          name="minQuantityOfEligibleItems"
                          value={formData.minQuantityOfEligibleItems}
                          onChange={handleChange}
                          min="1"
                          placeholder="e.g. 2"
                          className="w-full rounded border-2 border-gray-400 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                        <small className="mt-1 block text-xs text-gray-500">
                          User must have this many quantity of products eligible for the discount in
                          cart.
                        </small>
                      </div>
                    )}
                  </div>
                  {formData.typeOfDiscount === 'buy_x_get_y' &&
                    formData.minRequirementType !== 'none' && (
                      <div className="mt-2 rounded border bg-gray-50 p-4 text-gray-700">
                        <AppliesToSelector
                          appliesToType={formData.appliesToType}
                          appliesToValueIds={formData.appliesToValueIds}
                          onTypeChange={handleAppliesToTypeChange}
                          onValueToggle={toggleAppliesToValue}
                          labelTitle="Applies to"
                        />
                      </div>
                    )}
                </div>
              </div>

              {/* Discount value / Customer gets */}
              {formData.typeOfDiscount === 'buy_x_get_y' ? (
                <div className="border-t pt-4">
                  <h4 className="mb-3 text-sm font-semibold text-gray-700">Customer gets</h4>
                  <div className="space-y-3">
                    <div>
                      <label className="mb-1 block text-sm font-medium">Quantity</label>
                      <input
                        type="number"
                        name="buyXGetYCustomerGetsQuantity"
                        value={formData.buyXGetYCustomerGetsQuantity}
                        onChange={handleChange}
                        min="1"
                        required
                        className="w-full rounded border-2 border-gray-400 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                      <small className="block text-xs text-gray-500">
                        Customers must add the quantity of items specified above to their cart.
                      </small>
                    </div>

                    <div className="rounded border-2 border-gray-400 bg-gray-50 p-4 text-gray-700">
                      <AppliesToSelector
                        appliesToType={formData.buyXGetYCustomerGetsAppliesToType}
                        appliesToValueIds={formData.buyXGetYCustomerGetsAppliesToValueIds}
                        onTypeChange={handleGetsAppliesToTypeChange}
                        onValueToggle={toggleGetsAppliesToValue}
                        labelTitle="Applies to"
                      />
                    </div>

                    <div className="pt-3">
                      <label className="mb-3 block text-sm font-medium font-semibold text-gray-700">
                        At a discounted value
                      </label>
                      <div className="space-y-4">
                        <label className="flex cursor-pointer items-start gap-2">
                          <input
                            type="radio"
                            name="buyXGetYCustomerGetsDiscountType"
                            value="percentage"
                            checked={formData.buyXGetYCustomerGetsDiscountType === 'percentage'}
                            onChange={handleChange}
                            className="mt-1"
                          />
                          <div className="flex-1">
                            <span className="block text-sm font-medium">Percentage</span>
                            {formData.buyXGetYCustomerGetsDiscountType === 'percentage' && (
                              <input
                                type="number"
                                name="buyXGetYCustomerGetsDiscountValue"
                                value={formData.buyXGetYCustomerGetsDiscountValue}
                                onChange={handleChange}
                                placeholder="%"
                                step="0.01"
                                min="0"
                                required
                                className="mt-2 w-full rounded border-2 border-gray-400 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                              />
                            )}
                          </div>
                        </label>
                        <label className="flex cursor-pointer items-start gap-2">
                          <input
                            type="radio"
                            name="buyXGetYCustomerGetsDiscountType"
                            value="amount_off"
                            checked={formData.buyXGetYCustomerGetsDiscountType === 'amount_off'}
                            onChange={handleChange}
                            className="mt-1"
                          />
                          <div className="flex-1">
                            <span className="block text-sm font-medium">Amount off each</span>
                            {formData.buyXGetYCustomerGetsDiscountType === 'amount_off' && (
                              <input
                                type="number"
                                name="buyXGetYCustomerGetsDiscountValue"
                                value={formData.buyXGetYCustomerGetsDiscountValue}
                                onChange={handleChange}
                                placeholder="₹"
                                step="0.01"
                                min="0"
                                required
                                className="mt-2 w-full rounded border-2 border-gray-400 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                              />
                            )}
                          </div>
                        </label>
                        <label className="flex cursor-pointer items-center gap-2">
                          <input
                            type="radio"
                            name="buyXGetYCustomerGetsDiscountType"
                            value="free"
                            checked={formData.buyXGetYCustomerGetsDiscountType === 'free'}
                            onChange={handleChange}
                          />
                          <span className="text-sm font-medium">Free</span>
                        </label>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="border-t pt-4">
                  <h4 className="mb-3 text-sm font-semibold text-gray-700">Discount value</h4>
                  <div className="space-y-3">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                          Discount type *
                        </label>
                        <select
                          name="discountType"
                          value={formData.discountType}
                          onChange={handleChange}
                          required
                          className="w-full rounded border-2 border-gray-400 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        >
                          <option value="percentage">Percentage (%)</option>
                          <option value="fixed">Fixed amount (₹)</option>
                        </select>
                      </div>
                      <div>
                        <label className="mb-1 block text-sm font-medium">Discount value *</label>
                        <input
                          type="number"
                          name="discountValue"
                          value={formData.discountValue}
                          onChange={handleChange}
                          step="0.01"
                          min="0"
                          required
                          className="w-full rounded border-2 border-gray-400 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                      </div>
                    </div>
                    {formData.typeOfDiscount !== 'total_order_discount' &&
                      formData.typeOfDiscount !== 'shipping_discount' && (
                        <div className="rounded border-2 border-gray-400 bg-gray-50 p-4 text-gray-700">
                          <AppliesToSelector
                            appliesToType={formData.appliesToType}
                            appliesToValueIds={formData.appliesToValueIds}
                            onTypeChange={handleAppliesToTypeChange}
                            onValueToggle={toggleAppliesToValue}
                            labelTitle="Applies to"
                          />
                        </div>
                      )}
                    {formData.typeOfDiscount === 'shipping_discount' && (
                      <div className="mt-4 border-t pt-4">
                        <h4 className="mb-3 text-sm font-semibold text-gray-700">
                          Shipping Criteria
                        </h4>
                        <div className="grid gap-4 md:grid-cols-2">
                          <div>
                            <label className="mb-1 block text-sm font-medium">State *</label>
                            <SearchableSelect
                              options={availableStates}
                              value={formData.shippingState}
                              onChange={(val) => {
                                setFormData({
                                  ...formData,
                                  shippingState: val,
                                  shippingDistrict: '',
                                  shippingPincodes: [],
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
                              value={formData.shippingDistrict}
                              onChange={(val) => {
                                setFormData({
                                  ...formData,
                                  shippingDistrict: val,
                                  shippingPincodes: [],
                                });
                                fetchPincodes(formData.shippingState, val);
                                setPincodeSearch('');
                              }}
                              placeholder="Select District"
                              disabled={!formData.shippingState}
                              required
                            />
                          </div>
                        </div>

                        {formData.shippingDistrict && (
                          <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-4">
                            <label className="mb-2 block text-sm font-semibold">
                              Select Pincodes *
                            </label>
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
                                  const allSelected =
                                    filtered.length > 0 &&
                                    filtered.every((pc) => formData.shippingPincodes.includes(pc));
                                  if (allSelected) {
                                    setFormData({
                                      ...formData,
                                      shippingPincodes: formData.shippingPincodes.filter(
                                        (pc) => !filtered.includes(pc)
                                      ),
                                    });
                                  } else {
                                    const merged = Array.from(
                                      new Set([...formData.shippingPincodes, ...filtered])
                                    );
                                    setFormData({ ...formData, shippingPincodes: merged });
                                  }
                                }}
                                className="rounded px-3 py-1.5 text-xs font-medium text-white"
                                style={{
                                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                }}
                              >
                                {availablePincodes.filter((pc) => pc.includes(pincodeSearch))
                                  .length > 0 &&
                                availablePincodes
                                  .filter((pc) => pc.includes(pincodeSearch))
                                  .every((pc) => formData.shippingPincodes.includes(pc))
                                  ? 'Deselect All'
                                  : 'Select All'}
                              </button>
                            </div>
                            <div className="grid max-h-40 grid-cols-2 gap-2 overflow-y-auto rounded border bg-white p-2 sm:grid-cols-4">
                              {availablePincodes
                                .filter((pc) => pc.includes(pincodeSearch))
                                .map((pc) => (
                                  <label
                                    key={pc}
                                    className="flex cursor-pointer items-center space-x-2 rounded p-1 text-sm hover:bg-gray-50"
                                  >
                                    <input
                                      type="checkbox"
                                      checked={formData.shippingPincodes.includes(pc)}
                                      onChange={(e) => {
                                        const newPincodes = e.target.checked
                                          ? [...formData.shippingPincodes, pc]
                                          : formData.shippingPincodes.filter((item) => item !== pc);
                                        setFormData({ ...formData, shippingPincodes: newPincodes });
                                      }}
                                      className="h-4 w-4 rounded text-purple-600"
                                    />
                                    <span>{pc}</span>
                                  </label>
                                ))}
                              {availablePincodes.filter((pc) => pc.includes(pincodeSearch))
                                .length === 0 && (
                                <p className="col-span-4 py-2 text-center text-sm text-gray-400">
                                  No pincodes match your search
                                </p>
                              )}
                            </div>
                            {formData.shippingPincodes.length > 0 && (
                              <p className="mt-2 text-xs font-medium text-purple-600">
                                Selected: {formData.shippingPincodes.length} pincode(s)
                              </p>
                            )}
                          </div>
                        )}

                        <div className="mt-4">
                          <label className="mb-1 block text-sm font-medium">
                            Applicable Payment Methods
                          </label>
                          <div className="flex flex-wrap items-center gap-4">
                            <label className="flex cursor-pointer items-center space-x-2 text-sm">
                              <input
                                type="checkbox"
                                checked={formData.applicablePaymentMethods.includes('all')}
                                onChange={(e) => {
                                  if (e.target.checked)
                                    setFormData({ ...formData, applicablePaymentMethods: ['all'] });
                                  else setFormData({ ...formData, applicablePaymentMethods: [] });
                                }}
                                className="h-4 w-4 rounded text-purple-600"
                              />
                              <span>All</span>
                            </label>

                            {!formData.applicablePaymentMethods.includes('all') &&
                              [
                                'cod',
                                'upi',
                                ...(discountCategory === 'business' ? ['credit'] : []),
                              ].map((method) => (
                                <label
                                  key={method}
                                  className="flex cursor-pointer items-center space-x-2 text-sm"
                                >
                                  <input
                                    type="checkbox"
                                    checked={formData.applicablePaymentMethods.includes(method)}
                                    onChange={(e) => {
                                      const next = e.target.checked
                                        ? [
                                            ...formData.applicablePaymentMethods.filter(
                                              (m) => m !== 'all'
                                            ),
                                            method,
                                          ]
                                        : formData.applicablePaymentMethods.filter(
                                            (m) => m !== method
                                          );
                                      setFormData({ ...formData, applicablePaymentMethods: next });
                                    }}
                                    className="h-4 w-4 rounded text-purple-600"
                                  />
                                  <span className="uppercase">{method}</span>
                                </label>
                              ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Maximum discount uses */}
              <div className="border-t pt-4">
                <h4 className="mb-3 text-sm font-semibold text-gray-700">Maximum discount uses</h4>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-sm font-medium">
                      Max usage count (total)
                    </label>
                    <input
                      type="number"
                      name="maxUsageCount"
                      value={formData.maxUsageCount}
                      onChange={handleChange}
                      min="1"
                      placeholder="Unlimited"
                      className="w-full rounded border-2 border-gray-400 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium">Usage limit per user</label>
                    <input
                      type="number"
                      name="maxUsagePerUser"
                      value={formData.maxUsagePerUser}
                      onChange={handleChange}
                      min="1"
                      placeholder="Unlimited"
                      className="w-full rounded border-2 border-gray-400 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-1 block text-sm font-medium">Valid from (start date)</label>
                  <input
                    type="date"
                    name="validFrom"
                    value={formData.validFrom}
                    onChange={handleChange}
                    className="w-full rounded border-2 border-gray-400 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium">Valid until (end date)</label>
                  <input
                    type="date"
                    name="validUntil"
                    value={formData.validUntil}
                    onChange={handleChange}
                    className="w-full rounded border-2 border-gray-400 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
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

              <div className="flex justify-end gap-2 pt-2">
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
                  style={{ background: 'linear-gradient(135deg, #28A745 0%, #20C997 100%)' }}
                >
                  {editingDiscount ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {overlapConflict && (
        <div className="fixed inset-0 z-[120] flex items-center justify-center bg-black bg-opacity-60 p-4">
          <div className="w-full max-w-md rounded-xl border-t-4 border-yellow-500 bg-white p-8 shadow-2xl">
            <div className="mb-4 flex items-center gap-4 text-yellow-600">
              <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <h3 className="text-xl font-bold text-gray-800">Similar Offer Exists</h3>
            </div>

            <p className="mb-6 leading-relaxed text-gray-600">
              Another similar offer already exists for{' '}
              <span className="font-bold text-gray-800">
                {overlapConflict.totalOverlappingProducts}
              </span>{' '}
              products in the group for which this discount is getting created.
            </p>

            <div className="flex flex-col gap-3">
              <button
                onClick={() => handleManualResolution('overwrite')}
                className="w-full rounded-lg px-4 py-3 font-semibold text-white shadow-md transition-all hover:shadow-lg"
                style={{ background: 'linear-gradient(135deg, #FFC107 0%, #FF9800 100%)' }}
              >
                Overwrite Earlier Discount
              </button>
              <button
                onClick={() => handleManualResolution('retain')}
                className="w-full rounded-lg border border-gray-300 bg-gray-100 px-4 py-3 font-semibold text-gray-700 transition-all hover:bg-gray-200"
              >
                Retain Earlier Discount
              </button>
              <button
                onClick={() => setOverlapConflict(null)}
                className="mt-2 w-full rounded-lg px-4 py-2 text-sm font-medium text-gray-500 transition-colors hover:text-gray-700"
              >
                Go Back and Edit
              </button>
            </div>
          </div>
        </div>
      )}

      {showReferralModal && (
        <div
          className="fixed inset-0 z-[110] flex items-center justify-center bg-black bg-opacity-50 p-4"
          onClick={() => setShowReferralModal(false)}
        >
          <div
            className="mx-4 max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-lg bg-white p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <ReferralOptionManagement isModal={true} onClose={() => setShowReferralModal(false)} />
          </div>
        </div>
      )}
    </div>
  );
}
