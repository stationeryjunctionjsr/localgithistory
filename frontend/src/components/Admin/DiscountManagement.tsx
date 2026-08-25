'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import InfoButton from '@/components/InfoButton';
import { formatDateIST } from '@/utils/dateUtils';
import SearchableSelect from '@/components/SearchableSelect';
import ReferralOptionManagement from '@/components/Admin/ReferralOptionManagement';
import RefreshButton from './RefreshButton';
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
  quantityTiers?: { quantity: number; discount: number }[];
  excludedProductIds?: string[];
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
  productIds?: string[];
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
  { value: 'bundles', label: 'Bundles' },
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

interface AppliesToSelectorProps {
  appliesToType: string;
  appliesToValueIds: string[];
  onTypeChange: (val: string) => void;
  onValueToggle: (id: string) => void;
  onSelectAllToggle?: (ids: string[], select: boolean) => void;
  categories: Category[];
  subCategoryOptions: string[];
  brands: Brand[];
  collections: Collection[];
  products: any[];
  bundles: any[];
  labelTitle?: string;
}

function AppliesToSelector({
  appliesToType,
  appliesToValueIds,
  onTypeChange,
  onValueToggle,
  onSelectAllToggle,
  categories,
  subCategoryOptions,
  brands,
  collections,
  products,
  bundles,
  labelTitle = 'Applies to',
}: AppliesToSelectorProps) {
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
    if (appliesToType === 'bundles')
      return bundles.map((b) => ({ id: b._id, name: b.name }));
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
                      : appliesToType === 'bundles'
                        ? 'bundles'
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

          {filteredItems.length > 0 && onSelectAllToggle && (
            <label className="mb-2 flex cursor-pointer items-center gap-2 rounded bg-gray-100 p-2 font-medium hover:bg-gray-200">
              <input
                type="checkbox"
                checked={filteredItems.length > 0 && filteredItems.map(item => item.id).every(id => appliesToValueIds?.includes(id))}
                onChange={(e) => {
                  const filteredIds = filteredItems.map(item => item.id);
                  onSelectAllToggle(filteredIds, e.target.checked);
                }}
                className="rounded text-blue-600 focus:ring-blue-500"
              />
              <span className="text-xs text-gray-700">Select All / Deselect All ({filteredItems.length} items)</span>
            </label>
          )}

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
}

interface SelectiveUsersSelectorProps {
  discountCategory: 'retail' | 'business';
  applicableUserIds: string[];
  selectiveUserList: UserOption[];
  onUserToggle: (userId: string) => void;
  onSelectAllToggle?: (userIds: string[], select: boolean) => void;
}

function SelectiveUsersSelector({
  discountCategory,
  applicableUserIds,
  selectiveUserList,
  onUserToggle,
  onSelectAllToggle,
}: SelectiveUsersSelectorProps) {
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
          {applicableUserIds?.length || 0} selected
        </span>
      </div>

      <input
        type="text"
        placeholder={`Search ${filteredUsers.length} users by name, email or phone...`}
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        className="mb-2 w-full rounded border-2 border-gray-400 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
      />

      {filteredUsers.length > 0 && onSelectAllToggle && (
        <label className="mb-2 flex cursor-pointer items-center gap-2 rounded bg-gray-100 p-2 font-medium hover:bg-gray-200">
          <input
            type="checkbox"
            checked={filteredUsers.length > 0 && filteredUsers.map(u => u._id).every(id => applicableUserIds?.includes(id))}
            onChange={(e) => {
              const filteredIds = filteredUsers.map(u => u._id);
              onSelectAllToggle(filteredIds, e.target.checked);
            }}
            className="rounded text-blue-600 focus:ring-blue-500"
          />
          <span className="text-xs text-gray-700">Select All / Deselect All ({filteredUsers.length} users)</span>
        </label>
      )}

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
                checked={applicableUserIds?.includes(u._id)}
                onChange={() => onUserToggle(u._id)}
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
}

interface DiscountManagementProps {
  discountCategory: 'retail' | 'business';
}

export default function DiscountManagement({ discountCategory }: DiscountManagementProps) {
  const router = useRouter();
  const { user } = useAuth();
  const discountOptions = [...TYPE_OF_DISCOUNT_OPTIONS];
  const [discounts, setDiscounts] = useState<Discount[]>([]);
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

  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showReferralModal, setShowReferralModal] = useState(false);
  const [showBehaviorPopover, setShowBehaviorPopover] = useState(false);
  const [behaviorSearch, setBehaviorSearch] = useState('');
  const [editingDiscount, setEditingDiscount] = useState<Discount | null>(null);
  const behaviorRef = useRef<HTMLDivElement>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [bundles, setBundles] = useState<any[]>([]);
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
  const [viewingAppliesToDiscount, setViewingAppliesToDiscount] = useState<Discount | null>(null);
  const [viewingUsersDiscount, setViewingUsersDiscount] = useState<Discount | null>(null);
  const [modalSearchQuery, setModalSearchQuery] = useState('');
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
    quantityTiers: [] as { quantity: string | number; discount: string | number }[],
  });

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (behaviorRef.current && !behaviorRef.current.contains(event.target as Node)) {
        setShowBehaviorPopover(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (user?.role === 'super_admin') {
      fetchDiscounts();
      fetchPageInfo();
      Promise.all([
        api.get('/categories').then((r) => setCategories(r.data || [])),
        api.get('/brands').then((r) => setBrands(r.data || [])),
        api.get('/collections').then((r) => setCollections(r.data || [])),
        api.get('/products', { params: { limit: 1000 } }).then((r) => setProducts(r.data?.products || r.data || [])),
        api.get('/bundles/admin/all').then((r) => setBundles(Array.isArray(r.data) ? r.data : r.data?.bundles || [])),
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
    if (name === 'typeOfDiscount' && value !== 'product_discount' && newFormData.minRequirementType === 'quantity_based') {
      newFormData.minRequirementType = 'none';
    }
    if (name === 'minRequirementType' && value === 'quantity_based') {
      newFormData.discountType = 'percentage';
      if (!newFormData.quantityTiers || newFormData.quantityTiers.length === 0) {
        newFormData.quantityTiers = [{ quantity: '', discount: '' }];
      }
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

  const handleSelectAllAppliesToValue = (filteredIds: string[], select: boolean) => {
    let next: string[];
    if (select) {
      next = Array.from(new Set([...(formData.appliesToValueIds || []), ...filteredIds]));
    } else {
      next = (formData.appliesToValueIds || []).filter(id => !filteredIds.includes(id));
    }
    setFormData({ ...formData, appliesToValueIds: next });
  };

  const handleSelectAllGetsAppliesToValue = (filteredIds: string[], select: boolean) => {
    let next: string[];
    if (select) {
      next = Array.from(new Set([...(formData.buyXGetYCustomerGetsAppliesToValueIds || []), ...filteredIds]));
    } else {
      next = (formData.buyXGetYCustomerGetsAppliesToValueIds || []).filter(id => !filteredIds.includes(id));
    }
    setFormData({ ...formData, buyXGetYCustomerGetsAppliesToValueIds: next });
  };

  const handleSelectAllUsers = (filteredIds: string[], select: boolean) => {
    let next: string[];
    if (select) {
      next = Array.from(new Set([...(formData.applicableUserIds || []), ...filteredIds]));
    } else {
      next = (formData.applicableUserIds || []).filter(id => !filteredIds.includes(id));
    }
    setFormData({ ...formData, applicableUserIds: next });
  };

  const getSelectedBehaviors = () => {
    if (!formData.userBehavior || formData.userBehavior === 'none') {
      return ['none'];
    }
    return formData.userBehavior.split(',').map((s) => s.trim()).filter(Boolean);
  };

  const handleToggleBehavior = (val: string) => {
    let newBehaviors: string[];
    if (val === 'none') {
      newBehaviors = ['none'];
    } else {
      const current = getSelectedBehaviors().filter((x) => x !== 'none');
      if (current.includes(val)) {
        newBehaviors = current.filter((x) => x !== val);
        if (newBehaviors.length === 0) {
          newBehaviors = ['none'];
        }
      } else {
        newBehaviors = [...current, val];
      }
    }
    const userBehaviorStr = newBehaviors.join(',');
    setFormData({
      ...formData,
      userBehavior: userBehaviorStr,
      applicableUserIds: newBehaviors.some(x => x.startsWith('selective_')) ? formData.applicableUserIds : [],
    });
  };

  const showUserBehaviour = true;
  const showSelectiveUsers =
    formData.userBehavior?.split(',').map((s) => s.trim()).includes('selective_retail') ||
    formData.userBehavior?.split(',').map((s) => s.trim()).includes('selective_business');
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
    if (formData.minRequirementType === 'quantity_based') {
      if (!formData.quantityTiers || formData.quantityTiers.length === 0) {
        toast.error('Please add at least one quantity tier');
        return;
      }
      for (let i = 0; i < formData.quantityTiers.length; i++) {
        const tier = formData.quantityTiers[i];
        if (tier.quantity === '' || tier.discount === '') {
          toast.error(`Please fill in all fields for Tier ${i + 1}`);
          return;
        }
        const qty = parseInt(tier.quantity as string, 10);
        const disc = parseFloat(tier.discount as string);
        if (isNaN(qty) || qty <= 0) {
          toast.error(`Tier ${i + 1}: Quantity must be a positive integer`);
          return;
        }
        if (isNaN(disc) || disc < 0 || disc > 100) {
          toast.error(`Tier ${i + 1}: Discount must be between 0% and 100%`);
          return;
        }
      }
    }
    try {
      const submitData: Record<string, unknown> = {
        typeOfDiscount: formData.typeOfDiscount || 'product_discount',
        method: formData.method,
        code:
          formData.method === 'discount_code' ? (formData.code || '').trim().toUpperCase() : null,
        couponMode: formData.method === 'discount_code' ? formData.couponMode : 'override',
        discountType: formData.minRequirementType === 'quantity_based' ? 'percentage' : formData.discountType,
        discountValue: formData.minRequirementType === 'quantity_based' ? 0 : (parseFloat(formData.discountValue) || 0),
        minRequirementType: formData.minRequirementType || 'none',
        minPurchaseAmount:
          formData.minRequirementType === 'min_amount'
            ? parseFloat(formData.minPurchaseAmount) || 0
            : 0,
        minQuantityOfEligibleItems:
          formData.minRequirementType === 'min_quantity'
            ? parseInt(formData.minQuantityOfEligibleItems, 10) || null
            : null,
        quantityTiers:
          formData.minRequirementType === 'quantity_based'
            ? (formData.quantityTiers || []).map((t) => ({
                quantity: parseInt(t.quantity as string, 10),
                discount: parseFloat(t.discount as string),
              }))
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
        userBehavior: (() => {
          const behaviors = formData.userBehavior.split(',').map((s) => s.trim()).filter((s) => s && s !== 'none' && s !== 'selective_retail' && s !== 'selective_business');
          return behaviors.length > 0 ? behaviors.join(',') : null;
        })(),
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
      const overlap = error.response?.data?.overlap || error.response?.data?.detail?.overlap;
      if (error.response?.status === 409 && overlap) {
        setOverlapConflict(overlap);
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
        discountType: formData.minRequirementType === 'quantity_based' ? 'percentage' : formData.discountType,
        discountValue: formData.minRequirementType === 'quantity_based' ? 0 : (parseFloat(formData.discountValue) || 0),
        minRequirementType: formData.minRequirementType || 'none',
        minPurchaseAmount:
          formData.minRequirementType === 'min_amount'
            ? parseFloat(formData.minPurchaseAmount) || 0
            : 0,
        minQuantityOfEligibleItems:
          formData.minRequirementType === 'min_quantity'
            ? parseInt(formData.minQuantityOfEligibleItems, 10) || null
            : null,
        quantityTiers:
          formData.minRequirementType === 'quantity_based'
            ? (formData.quantityTiers || []).map((t) => ({
                quantity: parseInt(t.quantity as string, 10),
                discount: parseFloat(t.discount as string),
              }))
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
        userBehavior: (() => {
          const behaviors = formData.userBehavior.split(',').map((s) => s.trim()).filter((s) => s && s !== 'none' && s !== 'selective_retail' && s !== 'selective_business');
          return behaviors.length > 0 ? behaviors.join(',') : null;
        })(),
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
      setOverlapConflict(null);
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
      quantityTiers: [],
    });
  };

  const handleAddQuantityTier = () => {
    setFormData((prev) => ({
      ...prev,
      quantityTiers: [...(prev.quantityTiers || []), { quantity: '', discount: '' }],
    }));
  };

  const handleRemoveQuantityTier = (index: number) => {
    setFormData((prev) => ({
      ...prev,
      quantityTiers: (prev.quantityTiers || []).filter((_, i) => i !== index),
    }));
  };

  const handleQuantityTierChange = (index: number, field: 'quantity' | 'discount', value: string) => {
    setFormData((prev) => {
      const newTiers = [...(prev.quantityTiers || [])];
      newTiers[index] = { ...newTiers[index], [field]: value };
      return { ...prev, quantityTiers: newTiers };
    });
  };

  const handleEdit = (d: Discount) => {
    setEditingDiscount(d);
    let behavior = d.userBehavior || 'none';
    if (d.applicableUserIds?.length) {
      if (behavior === 'none') {
        behavior = discountCategory === 'business' ? 'selective_business' : 'selective_retail';
      } else {
        behavior = behavior + ',' + (discountCategory === 'business' ? 'selective_business' : 'selective_retail');
      }
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
      quantityTiers: d.quantityTiers || [],
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

  const handleToggleActive = async (discount: Discount) => {
    const nextActive = !discount.isActive;
    const actionText = nextActive ? 'enable' : 'disable';
    if (!confirm(`Are you sure you want to ${actionText} this discount?`)) return;
    try {
      await api.put(`/coupons/${discount._id}`, { isActive: nextActive });
      toast.success(`Discount ${nextActive ? 'enabled' : 'disabled'} successfully`);
      fetchDiscounts();
    } catch (error: any) {
      toast.error(
        error.response?.data?.detail?.message ||
          error.response?.data?.detail ||
          error.response?.data?.message ||
          'Operation failed'
      );
    }
  };

  const getAffectedProducts = (d: Discount) => {
    const appliesToType = d.appliesToType || 'all';
    const valIds = d.appliesToValueIds || [];
    const excludedIds = d.excludedProductIds || [];

    let resolved: any[] = [];
    if (appliesToType === 'all') {
      resolved = products;
    } else if (appliesToType === 'products') {
      resolved = products.filter((p) => valIds.includes(p._id));
    } else if (appliesToType === 'categories') {
      const eligibleCategoryNames = categories
        .filter((c) => valIds.includes(c._id))
        .map((c) => c.name.trim().toLowerCase());
      resolved = products.filter((p) => p.category && eligibleCategoryNames.includes(p.category.trim().toLowerCase()));
    } else if (appliesToType === 'subCategories') {
      resolved = products.filter((p) => p.subCategory && valIds.includes(p.subCategory.trim()));
    } else if (appliesToType === 'brands') {
      const eligibleBrandNames = brands
        .filter((b) => valIds.includes(b._id))
        .map((b) => b.name.trim().toLowerCase());
      resolved = products.filter((p) => p.brand && eligibleBrandNames.includes(p.brand.trim().toLowerCase()));
    } else if (appliesToType === 'collections') {
      const eligibleProductIds = new Set<string>();
      collections
        .filter((col) => valIds.includes(col._id))
        .forEach((col) => {
          const pids = col.productIds || [];
          pids.forEach((pid: string) => eligibleProductIds.add(pid));
        });
      resolved = products.filter((p) => eligibleProductIds.has(p._id));
    }
    
    // Filter out excluded products (e.g. disassociated/overwritten products)
    return resolved.filter((p) => !excludedIds.includes(p._id));
  };

  const getTargetedUsers = (d: Discount) => {
    const userList = discountCategory === 'retail' ? retailUsers : businessUsers;
    const eligibleUserIds = new Set<string>();
    let hasTargets = false;

    if (d.applicableUserIds && d.applicableUserIds.length > 0) {
      hasTargets = true;
      d.applicableUserIds.forEach((uid) => eligibleUserIds.add(uid));
    }

    if (d.userBehavior && d.userBehavior !== 'none') {
      const behaviors = d.userBehavior.split(',').map((s) => s.trim()).filter(Boolean);
      behaviors.forEach((singleBehavior) => {
        if (singleBehavior.startsWith('segment_')) {
          hasTargets = true;
          const segmentId = singleBehavior.substring('segment_'.length);
          const segment = customSegments.find((s) => (s._id || s.id) === segmentId);
          if (segment && segment.userIds) {
            segment.userIds.forEach((uid: string) => eligibleUserIds.add(uid));
          }
        }
      });
    }

    if (hasTargets) {
      return userList.filter((u) => eligibleUserIds.has(u._id));
    }

    return userList;
  };

  const isExpired = (d: Discount) => (d.validUntil ? new Date(d.validUntil) < new Date() : false);
  const isUsageExceeded = (d: Discount) =>
    d.usageLimit ? (d.usedCount || 0) >= d.usageLimit : false;
  const displayCode = (d: Discount) => (d.method === 'automatic' || !d.code || d.code.trim() === '' ? '-' : d.code);
  const displayType = (d: Discount) => {
    return TYPE_OF_DISCOUNT_OPTIONS.find((o) => o.value === (d.typeOfDiscount || 'product_discount'))?.label || 'Amount off each Product';
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

  const totalItems = displayedDiscounts.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
  const paginatedDiscounts = displayedDiscounts.slice(startIndex, endIndex);

  if (user?.role !== 'super_admin') return <div>Access Denied</div>;
  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <div className="rounded-lg bg-white p-6 shadow-md">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="inline-flex items-center gap-3 text-2xl font-bold">
            <InfoButton
              info={
                user?.role === 'super_admin' && pageInfo.page?.description
                  ? pageInfo.page.description
                  : undefined
              }
            >
              {discountCategory === 'retail' ? 'Retail Discounts' : 'Business Discounts'}
            </InfoButton>
            <RefreshButton onRefresh={fetchDiscounts} />
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
                    <InfoButton info="The products or categories this discount is applied to.">
                      Applies To
                    </InfoButton>
                  </span>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                  <span className="inline-flex items-baseline gap-1">
                    <InfoButton info="The customer segment or specific users eligible for this discount.">
                      Users
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
              {paginatedDiscounts.length > 0 ? (
                paginatedDiscounts.map((d) => {
                  const expired = isExpired(d);
                  const usageExceeded = isUsageExceeded(d);
                  return (
                    <tr key={d._id}>
                      <td className="whitespace-nowrap px-6 py-4">{d.displayId || d._id || '-'}</td>
                      <td className="whitespace-nowrap px-6 py-4">{displayType(d)}</td>
                      <td className="whitespace-nowrap px-6 py-4">
                        {d.method === 'automatic' ? 'Automatic' : 'Discount code'}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <strong>{displayCode(d)}</strong>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        {d.minRequirementType === 'quantity_based' && d.quantityTiers && d.quantityTiers.length > 0 ? (
                          <span className="italic text-gray-600">Tiered (%)</span>
                        ) : d.discountType === 'percentage' ? (
                          `${d.discountValue}%`
                        ) : (
                          `₹${d.discountValue}`
                        )}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        {d.validUntil ? formatDateIST(d.validUntil) : 'No expiry'}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">{d.usageLimit || 'Unlimited'}</td>
                      <td className="whitespace-nowrap px-6 py-4">{d.usedCount || 0}</td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <button
                          type="button"
                          onClick={() => {
                            setViewingAppliesToDiscount(d);
                            setModalSearchQuery('');
                          }}
                          className="rounded px-2.5 py-1 text-xs font-semibold text-blue-700 bg-blue-50 border border-blue-200 hover:bg-blue-100 hover:text-blue-800 transition-all shadow-sm"
                        >
                          {d.appliesToType === 'all' && getAffectedProducts(d).length === products.length
                            ? `All Products (${products.length})` 
                            : `View (${getAffectedProducts(d).length})`}
                        </button>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <button
                          type="button"
                          onClick={() => {
                            setViewingUsersDiscount(d);
                            setModalSearchQuery('');
                          }}
                          className="rounded px-2.5 py-1 text-xs font-semibold text-purple-700 bg-purple-50 border border-purple-200 hover:bg-purple-100 hover:text-purple-800 transition-all shadow-sm"
                        >
                          {!(d.applicableUserIds && d.applicableUserIds.length > 0) && !(d.userBehavior && d.userBehavior.startsWith('segment_'))
                            ? `All ${discountCategory === 'retail' ? 'Retail' : 'Business'} (${(discountCategory === 'retail' ? retailUsers : businessUsers).length})`
                            : `View (${getTargetedUsers(d).length})`}
                        </button>
                      </td>
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
                            onClick={() => handleToggleActive(d)}
                            className="rounded px-3 py-1 text-sm text-white font-medium shadow-sm transition-all hover:shadow-md"
                            style={{
                              background: d.isActive
                                ? 'linear-gradient(135deg, #FF5722 0%, #D84315 100%)' // Vivid orange-red for Disable
                                : 'linear-gradient(135deg, #28A745 0%, #20C997 100%)', // Green for Enable
                            }}
                          >
                            {d.isActive ? 'Disable' : 'Enable'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={12} className="px-6 py-4 text-center text-gray-500">
                    No discounts found
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
                  type="button"
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
                      type="button"
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
                  type="button"
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
                    <div className="relative" ref={behaviorRef}>
                      <label className="mb-1 block inline-flex items-baseline gap-1 text-sm font-medium">
                        User behaviour
                      </label>
                      {formData.method === 'discount_code' ? (
                        <div className="w-full rounded border border-gray-300 bg-gray-100 px-3 py-2 text-sm text-gray-600 font-semibold">
                          {discountCategory === 'retail' ? 'Selective Retail Customers' : 'Selective Business Customers'}
                        </div>
                      ) : (
                        <div className="relative">
                          {/* Input field trigger */}
                          <div
                            onClick={() => setShowBehaviorPopover(!showBehaviorPopover)}
                            className="w-full min-h-[42px] cursor-pointer rounded border-2 border-gray-400 bg-white px-3 py-2 pr-10 text-sm text-gray-700 flex flex-wrap gap-1.5 items-center transition-all duration-200 focus-within:border-indigo-500 focus-within:ring-1 focus-within:ring-indigo-500 hover:border-gray-500 shadow-sm"
                          >
                            {getSelectedBehaviors().length === 0 || getSelectedBehaviors().includes('none') ? (
                              <span className="text-gray-400">All Users</span>
                            ) : (
                              getSelectedBehaviors().map((val) => {
                                let label = 'All';
                                if (val === 'selective_retail') label = 'Selective Retail Customers';
                                else if (val === 'selective_business') label = 'Selective Business Customers';
                                else if (val.startsWith('segment_')) {
                                  const segId = val.substring('segment_'.length);
                                  const seg = customSegments.find((s) => (s._id || s.id) === segId);
                                  label = seg ? seg.name : 'Custom Segment';
                                }
                                return (
                                  <span
                                    key={val}
                                    className="inline-flex items-center gap-1 rounded bg-indigo-50 px-2 py-0.5 text-xs font-semibold text-indigo-700 border border-indigo-200"
                                    onClick={(e) => e.stopPropagation()}
                                  >
                                    {label}
                                    {val !== 'none' && (
                                      <button
                                        type="button"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleToggleBehavior(val);
                                        }}
                                        className="text-indigo-500 hover:text-indigo-800 font-bold ml-0.5 focus:outline-none"
                                      >
                                        &times;
                                      </button>
                                    )}
                                  </span>
                                );
                              })
                            )}
                            <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-gray-500">
                              <svg className={`h-4 w-4 transition-transform duration-200 ${showBehaviorPopover ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                              </svg>
                            </div>
                          </div>

                          {/* Popover Dropdown */}
                          {showBehaviorPopover && (
                            <div className="absolute left-0 right-0 z-[150] mt-1.5 max-h-[350px] overflow-hidden rounded-xl border border-slate-200 bg-white shadow-2xl flex flex-col">
                              {/* Search Box */}
                              <div className="p-2.5 border-b border-slate-100 bg-slate-50 flex items-center gap-2">
                                <svg className="h-4 w-4 text-slate-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                                <input
                                  type="text"
                                  placeholder="Search segments..."
                                  value={behaviorSearch}
                                  onChange={(e) => setBehaviorSearch(e.target.value)}
                                  className="w-full bg-transparent text-sm text-slate-800 placeholder-slate-400 outline-none"
                                  onClick={(e) => e.stopPropagation()}
                                />
                                {behaviorSearch && (
                                  <button
                                    type="button"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setBehaviorSearch('');
                                    }}
                                    className="text-slate-400 hover:text-slate-600 text-xs font-semibold"
                                  >
                                    Clear
                                  </button>
                                )}
                              </div>

                              {/* Options List */}
                              <div className="flex-1 overflow-y-auto p-2.5 space-y-3">
                                {(() => {
                                  const searchLower = behaviorSearch.toLowerCase();
                                  
                                  const showAllOption = 'all users'.includes(searchLower) || 'all'.includes(searchLower);
                                  
                                  const filteredSegments = customSegments.filter(s => 
                                    s.name.toLowerCase().includes(searchLower)
                                  );

                                  const selectiveTitle = discountCategory === 'retail' 
                                    ? 'Selective Retail Customers' 
                                    : 'Selective Business Customers';
                                  const showSelectiveOption = selectiveTitle.toLowerCase().includes(searchLower) || 'manual selection'.includes(searchLower);

                                  const noResults = !showAllOption && filteredSegments.length === 0 && !showSelectiveOption;

                                  if (noResults) {
                                    return (
                                      <div className="py-6 text-center text-sm text-gray-400 italic">
                                        No segments found
                                      </div>
                                    );
                                  }

                                  return (
                                    <>
                                      {/* General Section */}
                                      {showAllOption && (
                                        <div className="space-y-0.5">
                                          <h4 className="px-2 text-[10px] font-bold uppercase tracking-wider text-gray-400">General</h4>
                                          <label
                                            onClick={(e) => e.stopPropagation()}
                                            className="flex items-center gap-3 p-1 rounded hover:bg-indigo-50/55 cursor-pointer transition-colors"
                                          >
                                            <input
                                              type="checkbox"
                                              checked={getSelectedBehaviors().includes('none')}
                                              onChange={() => handleToggleBehavior('none')}
                                              className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                            />
                                            <span className="text-sm text-gray-800">All Users</span>
                                          </label>
                                        </div>
                                      )}

                                      {/* Custom Segments Section */}
                                      {filteredSegments.length > 0 && (
                                        <div className="space-y-0.5">
                                          <h4 className="px-2 text-[10px] font-bold uppercase tracking-wider text-gray-400">Custom Segments</h4>
                                          {filteredSegments.map((seg) => {
                                            const val = `segment_${seg._id || seg.id}`;
                                            return (
                                              <label
                                                key={val}
                                                onClick={(e) => e.stopPropagation()}
                                                className="flex items-center gap-3 p-1 rounded hover:bg-indigo-50/55 cursor-pointer transition-colors"
                                              >
                                                <input
                                                  type="checkbox"
                                                  checked={getSelectedBehaviors().includes(val)}
                                                  onChange={() => handleToggleBehavior(val)}
                                                  className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                                />
                                                <span className="text-sm text-gray-800">
                                                  {seg.name} ({seg.userIds?.length || 0} users)
                                                </span>
                                              </label>
                                            );
                                          })}
                                        </div>
                                      )}

                                      {/* Manual Selection Section */}
                                      {showSelectiveOption && (
                                        <div className="space-y-0.5">
                                          <h4 className="px-2 text-[10px] font-bold uppercase tracking-wider text-gray-400">Manual Selection</h4>
                                          {discountCategory === 'retail' ? (
                                            <label
                                              onClick={(e) => e.stopPropagation()}
                                              className="flex items-center gap-3 p-1 rounded hover:bg-indigo-50/55 cursor-pointer transition-colors"
                                            >
                                              <input
                                                type="checkbox"
                                                checked={getSelectedBehaviors().includes('selective_retail')}
                                                onChange={() => handleToggleBehavior('selective_retail')}
                                                className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                              />
                                              <span className="text-sm text-gray-800">Selective Retail Customers</span>
                                            </label>
                                          ) : (
                                            <label
                                              onClick={(e) => e.stopPropagation()}
                                              className="flex items-center gap-3 p-1 rounded hover:bg-indigo-50/55 cursor-pointer transition-colors"
                                            >
                                              <input
                                                type="checkbox"
                                                checked={getSelectedBehaviors().includes('selective_business')}
                                                onChange={() => handleToggleBehavior('selective_business')}
                                                className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                              />
                                              <span className="text-sm text-gray-800">Selective Business Customers</span>
                                            </label>
                                          )}
                                        </div>
                                      )}
                                    </>
                                  );
                                })()}
                              </div>

                              {/* Footer */}
                              <div className="px-3.5 py-2.5 border-t border-slate-100 bg-slate-50 flex justify-between items-center">
                                <span className="text-xs font-semibold text-gray-500">
                                  {getSelectedBehaviors().includes('none') 
                                    ? 'All Selected' 
                                    : `${getSelectedBehaviors().length} selected`}
                                </span>
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setShowBehaviorPopover(false);
                                  }}
                                  className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md text-xs font-bold transition-colors shadow-sm"
                                >
                                  Done
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                  {showSelectiveUsers && (
                    <SelectiveUsersSelector
                      discountCategory={discountCategory}
                      applicableUserIds={formData.applicableUserIds}
                      selectiveUserList={selectiveUserList}
                      onUserToggle={toggleApplicableUser}
                      onSelectAllToggle={handleSelectAllUsers}
                    />
                  )}
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
                      <select
                        name="minRequirementType"
                        value={formData.minRequirementType}
                        onChange={handleChange}
                        className="w-full rounded border-2 border-gray-400 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        {(formData.typeOfDiscount === 'product_discount'
                          ? [
                              ...MIN_REQUIREMENT_OPTIONS,
                              { value: 'quantity_based', label: 'Quantity-based Discount' },
                            ]
                          : formData.typeOfDiscount === 'buy_x_get_y'
                            ? MIN_REQUIREMENT_OPTIONS.filter((o) => o.value !== 'none')
                            : MIN_REQUIREMENT_OPTIONS
                        ).map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
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
                          onSelectAllToggle={handleSelectAllAppliesToValue}
                          categories={categories}
                          subCategoryOptions={subCategoryOptions}
                          brands={brands}
                          collections={collections}
                          products={products}
                          bundles={bundles}
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
                        onSelectAllToggle={handleSelectAllGetsAppliesToValue}
                        categories={categories}
                        subCategoryOptions={subCategoryOptions}
                        brands={brands}
                        collections={collections}
                        products={products}
                        bundles={bundles}
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
              ) : formData.minRequirementType === 'quantity_based' ? (
                <div className="border-t pt-4">
                  <h4 className="mb-3 text-sm font-semibold text-gray-700">Quantity-Based Tiers (Percentage Only)</h4>
                  <div className="space-y-3">
                    <div className="mb-6 rounded-lg border border-blue-200 bg-blue-50 p-4">
                      <p className="mb-4 text-xs text-gray-600">
                        Define discount percentage based on item quantity. Range matching is applied (highest matched tier &le; cart quantity applies).
                        <br />
                        <strong>Example:</strong> Tier 1: Quantity 3 &rarr; 5% off. Tier 2: Quantity 4 &rarr; 8% off.
                        <br />
                        - Buying 1 or 2 units &rarr; No discount (below lowest tier).
                        <br />
                        - Buying 3 units &rarr; 5% off each unit.
                        <br />
                        - Buying 5 units &rarr; 8% off each unit (matches quantity 4 tier).
                      </p>

                      {(formData.quantityTiers || []).map((tier, index) => (
                        <div
                          key={index}
                          className="mb-3 flex items-center gap-3 rounded border border-gray-300 bg-white p-3"
                        >
                          <span className="min-w-[60px] font-semibold text-sm">Tier {index + 1}:</span>
                          <div className="flex-1">
                            <label className="mb-1 block text-xs text-gray-600">
                              Min Quantity ({discountCategory === 'business' ? formData.applicableItemType : 'units'})
                            </label>
                            <input
                              type="number"
                              placeholder="Min Quantity"
                              value={tier.quantity}
                              onChange={(e) => handleQuantityTierChange(index, 'quantity', e.target.value)}
                              min="1"
                              required
                              className="w-full rounded border px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 border-gray-400"
                            />
                          </div>
                          <span className="text-lg text-purple-600">&rarr;</span>
                          <div className="flex-1">
                            <label className="mb-1 block text-xs text-gray-600">Discount (%)</label>
                            <input
                              type="number"
                              placeholder="Discount %"
                              value={tier.discount}
                              onChange={(e) => handleQuantityTierChange(index, 'discount', e.target.value)}
                              step="0.01"
                              min="0"
                              max="100"
                              required
                              className="w-full rounded border px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 border-gray-400"
                            />
                          </div>
                          <button
                            type="button"
                            onClick={() => handleRemoveQuantityTier(index)}
                            className="rounded px-3 py-2 text-sm text-white focus:outline-none"
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
                        onClick={handleAddQuantityTier}
                        className="mt-2 rounded px-4 py-2 text-sm text-white focus:outline-none"
                        style={{
                          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        }}
                      >
                        + Add Tier
                      </button>

                      {(!formData.quantityTiers || formData.quantityTiers.length === 0) && (
                        <div className="mt-4 rounded border border-yellow-200 bg-yellow-50 p-3">
                          <strong className="text-sm text-yellow-700">
                            ⚠️ At least one tier is required.
                          </strong>
                          <p className="mb-0 mt-1 text-xs text-yellow-700">
                            Click &quot;+ Add Tier&quot; to create your first quantity discount tier.
                          </p>
                        </div>
                      )}
                    </div>
                    {formData.typeOfDiscount !== 'total_order_discount' &&
                      formData.typeOfDiscount !== 'shipping_discount' && (
                        <div className="rounded border-2 border-gray-400 bg-gray-50 p-4 text-gray-700">
                          <AppliesToSelector
                            appliesToType={formData.appliesToType}
                            appliesToValueIds={formData.appliesToValueIds}
                            onTypeChange={handleAppliesToTypeChange}
                            onValueToggle={toggleAppliesToValue}
                            onSelectAllToggle={handleSelectAllAppliesToValue}
                            categories={categories}
                            subCategoryOptions={subCategoryOptions}
                            brands={brands}
                            collections={collections}
                            products={products}
                            bundles={bundles}
                            labelTitle="Applies to"
                          />
                        </div>
                      )}
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
                            onSelectAllToggle={handleSelectAllAppliesToValue}
                            categories={categories}
                            subCategoryOptions={subCategoryOptions}
                            brands={brands}
                            collections={collections}
                            products={products}
                            bundles={bundles}
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

            <p className="mb-4 leading-relaxed text-gray-600 text-sm">
              Another similar offer already exists for{' '}
              <span className="font-bold text-gray-800">
                {overlapConflict.totalOverlappingProducts}
              </span>{' '}
              products in the group for which this discount is getting created.
            </p>

            <div className="mb-6 max-h-44 overflow-y-auto rounded-lg border border-gray-200 bg-slate-50 p-3 text-xs text-gray-700 space-y-3 shadow-inner">
              <p className="font-semibold text-gray-800 text-sm">Overlap Details:</p>
              {(overlapConflict.details || []).map((detail: any, idx: number) => {
                const conflictCodeOrId = (() => {
                  const matchedCoupon = discounts.find(d => d._id === detail.couponId);
                  if (matchedCoupon) {
                    if (matchedCoupon.code) return `code "${matchedCoupon.code}"`;
                    if (matchedCoupon.displayId) return `ID ${matchedCoupon.displayId}`;
                  }
                  return detail.displayId ? `ID ${detail.displayId}` : `ID ${detail.couponId}`;
                })();

                return (
                  <div key={idx} className="border-b border-gray-200 pb-2 last:border-b-0 last:pb-0">
                    <p className="font-medium text-indigo-700 mb-1">
                      Overlapping with {conflictCodeOrId}:
                    </p>
                    <ul className="list-inside list-disc pl-2 space-y-0.5 text-gray-600">
                      {(detail.overlappingProductIds || []).map((pid: string) => {
                        const pName = products.find((p) => p._id === pid)?.name || pid;
                        return (
                          <li key={pid} className="truncate" title={pName}>
                            {pName}
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                );
              })}
            </div>

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

      {/* Applies To Detail Modal */}
      {viewingAppliesToDiscount && (() => {
        const affectedProducts = getAffectedProducts(viewingAppliesToDiscount);
        const filteredProducts = affectedProducts.filter(p =>
          p.name.toLowerCase().includes(modalSearchQuery.toLowerCase()) ||
          (p.category || '').toLowerCase().includes(modalSearchQuery.toLowerCase()) ||
          (p.brand || '').toLowerCase().includes(modalSearchQuery.toLowerCase())
        );
        return (
          <div
            className="fixed inset-0 z-[130] flex items-center justify-center bg-black bg-opacity-50 p-4 backdrop-blur-sm"
            onClick={() => setViewingAppliesToDiscount(null)}
          >
            <div
              className="mx-4 max-h-[80vh] w-full max-w-3xl overflow-hidden rounded-2xl bg-white shadow-2xl flex flex-col border border-gray-100"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal Header */}
              <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-blue-50 to-white">
                <div>
                  <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                    <svg className="h-5 w-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 002-2h-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                    </svg>
                    Applies To Products
                  </h3>
                  <p className="text-xs text-gray-500 mt-1">
                    Discount Mode: <span className="font-semibold text-gray-700">{(viewingAppliesToDiscount.appliesToType || 'all').toUpperCase()}</span> 
                    {viewingAppliesToDiscount.code ? ` | Code: ${viewingAppliesToDiscount.code}` : ''}
                  </p>
                </div>
                <button
                  onClick={() => setViewingAppliesToDiscount(null)}
                  className="rounded-full p-1.5 hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              {/* Search Bar */}
              <div className="p-4 border-b border-gray-100 bg-gray-50">
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </span>
                  <input
                    type="text"
                    placeholder="Search products by name, category, or brand..."
                    value={modalSearchQuery}
                    onChange={(e) => setModalSearchQuery(e.target.value)}
                    className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  />
                </div>
              </div>

              {/* Table Content */}
              <div className="flex-1 overflow-y-auto p-4">
                {filteredProducts.length === 0 ? (
                  <div className="py-12 text-center text-gray-500">
                    <svg className="h-12 w-12 text-gray-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                    </svg>
                    No matching products found
                  </div>
                ) : (
                  <table className="w-full text-left border-collapse text-sm">
                    <thead>
                      <tr className="border-b border-gray-200 text-gray-500 font-medium bg-gray-50">
                        <th className="py-2.5 px-4 rounded-l-lg">Product Name</th>
                        <th className="py-2.5 px-4">Category</th>
                        <th className="py-2.5 px-4">Brand</th>
                        <th className="py-2.5 px-4 text-right rounded-r-lg">MRP</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {filteredProducts.map((p) => (
                        <tr key={p._id} className="hover:bg-gray-50 transition-colors">
                          <td className="py-2.5 px-4 font-medium text-gray-900">{p.name}</td>
                          <td className="py-2.5 px-4 text-gray-600">{p.category || '-'}</td>
                          <td className="py-2.5 px-4 text-gray-600">{p.brand || '-'}</td>
                          <td className="py-2.5 px-4 text-right font-semibold text-gray-800">₹{p.mrp}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              {/* Footer */}
              <div className="px-6 py-4 border-t border-gray-100 bg-gray-50 flex items-center justify-between">
                <span className="text-xs text-gray-500">
                  Showing {filteredProducts.length} of {affectedProducts.length} eligible products
                </span>
                <button
                  type="button"
                  onClick={() => setViewingAppliesToDiscount(null)}
                  className="px-4 py-1.5 bg-gray-800 hover:bg-gray-900 text-white rounded-lg text-sm font-semibold transition-all shadow-sm"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        );
      })()}

      {/* Users Detail Modal */}
      {viewingUsersDiscount && (() => {
        const userBehavior = viewingUsersDiscount.userBehavior;
        const targetedUsers = getTargetedUsers(viewingUsersDiscount);
        const filteredUsers = targetedUsers.filter(u =>
          (u.name || '').toLowerCase().includes(modalSearchQuery.toLowerCase()) ||
          (u.email || '').toLowerCase().includes(modalSearchQuery.toLowerCase()) ||
          (u.phone || '').includes(modalSearchQuery)
        );
        return (
          <div
            className="fixed inset-0 z-[130] flex items-center justify-center bg-black bg-opacity-50 p-4 backdrop-blur-sm"
            onClick={() => setViewingUsersDiscount(null)}
          >
            <div
              className="mx-4 max-h-[80vh] w-full max-w-3xl overflow-hidden rounded-2xl bg-white shadow-2xl flex flex-col border border-gray-100"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal Header */}
              <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-purple-50 to-white">
                <div>
                  <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                    <svg className="h-5 w-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                    Targeted Users
                  </h3>
                  <p className="text-xs text-gray-500 mt-1">
                    Segment: <span className="font-semibold text-gray-700">
                      {userBehavior && userBehavior !== 'none'
                        ? userBehavior
                            .split(',')
                            .map((part) => {
                              const p = part.trim();
                              if (p.startsWith('segment_')) {
                                return customSegments.find((s) => (s._id || s.id) === p.substring('segment_'.length))?.name || 'Custom Segment';
                              }
                              if (p === 'selective_retail') return 'Selective Retail Customers';
                              if (p === 'selective_business') return 'Selective Business Customers';
                              return p;
                            })
                            .join(', ')
                        : viewingUsersDiscount.applicableUserIds && viewingUsersDiscount.applicableUserIds.length > 0
                          ? 'Selective Customers'
                          : `All ${discountCategory === 'retail' ? 'Retail' : 'Business'} Customers`
                      }
                    </span>
                  </p>
                </div>
                <button
                  onClick={() => setViewingUsersDiscount(null)}
                  className="rounded-full p-1.5 hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              {/* Search Bar */}
              <div className="p-4 border-b border-gray-100 bg-gray-50">
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </span>
                  <input
                    type="text"
                    placeholder="Search users by name, email, or phone number..."
                    value={modalSearchQuery}
                    onChange={(e) => setModalSearchQuery(e.target.value)}
                    className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                  />
                </div>
              </div>

              {/* Table Content */}
              <div className="flex-1 overflow-y-auto p-4">
                {filteredUsers.length === 0 ? (
                  <div className="py-12 text-center text-gray-500">
                    <svg className="h-12 w-12 text-gray-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                    No matching users found
                  </div>
                ) : (
                  <table className="w-full text-left border-collapse text-sm">
                    <thead>
                      <tr className="border-b border-gray-200 text-gray-500 font-medium bg-gray-50">
                        <th className="py-2.5 px-4 rounded-l-lg">User Name</th>
                        <th className="py-2.5 px-4">Email</th>
                        <th className="py-2.5 px-4 rounded-r-lg">Phone</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {filteredUsers.map((u) => (
                        <tr key={u._id} className="hover:bg-gray-50 transition-colors">
                          <td className="py-2.5 px-4 font-medium text-gray-900">{u.name || '-'}</td>
                          <td className="py-2.5 px-4 text-gray-600">{u.email || '-'}</td>
                          <td className="py-2.5 px-4 text-gray-600">{u.phone || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              {/* Footer */}
              <div className="px-6 py-4 border-t border-gray-100 bg-gray-50 flex items-center justify-between">
                <span className="text-xs text-gray-500">
                  Showing {filteredUsers.length} of {targetedUsers.length} eligible users
                </span>
                <button
                  type="button"
                  onClick={() => setViewingUsersDiscount(null)}
                  className="px-4 py-1.5 bg-gray-800 hover:bg-gray-900 text-white rounded-lg text-sm font-semibold transition-all shadow-sm"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        );
      })()}

    </div>
  );
}
