'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import { formatDateIST } from '@/utils/dateUtils';
import RefreshButton from '@/components/Admin/RefreshButton';
import InfoButton from '@/components/InfoButton';

interface Payment {
  _id: string;
  paymentId?: number;
  orderId?: string;
  userId?: number;
  customerName?: string;
  orderDate?: string;
  paymentMethod?: string;
  totalAmount?: number;
  amountPaid?: number;
  amountRemaining?: number;
  paymentEntries?: PaymentEntry[];
}

interface PaymentEntry {
  entryId?: number;
  amount?: number;
  image?: string;
  verified?: boolean;
  createdAt?: string;
}

export default function PaymentManagement() {
  const { user } = useAuth();
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [dateFilter, setDateFilter] = useState('all'); // 'all', 'day', 'week', 'month', 'year', 'custom'
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [expandedPayments, setExpandedPayments] = useState<Set<string>>(new Set());
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  const [flags, setFlags] = useState<any[]>([]);
  const [savingSettings, setSavingSettings] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  const fetchFlags = async () => {
    try {
      const response = await api.get('/feature-flags');
      setFlags(response.data || []);
    } catch (error) {
      toast.error('Failed to fetch feature flags');
    }
  };

  useEffect(() => {
    if (user?.role === 'super_admin') {
      fetchPayments();
      fetchFlags();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, dateFilter, customStartDate, customEndDate]);

  const getDateRange = () => {
    const now = new Date();
    let startDate: Date,
      endDate: Date = new Date(now);

    switch (dateFilter) {
      case 'day':
        startDate = new Date(now);
        startDate.setHours(0, 0, 0, 0);
        break;
      case 'week':
        startDate = new Date(now);
        startDate.setDate(now.getDate() - 7);
        startDate.setHours(0, 0, 0, 0);
        break;
      case 'month':
        startDate = new Date(now.getFullYear(), now.getMonth(), 1);
        break;
      case 'year':
        startDate = new Date(now.getFullYear(), 0, 1);
        break;
      case 'custom':
        if (customStartDate && customEndDate) {
          startDate = new Date(customStartDate);
          endDate = new Date(customEndDate);
          endDate.setHours(23, 59, 59, 999);
        } else {
          return null;
        }
        break;
      default:
        return null;
    }

    return {
      startDate: startDate.toISOString().split('T')[0],
      endDate: endDate.toISOString().split('T')[0],
    };
  };

  const fetchPayments = async () => {
    try {
      const dateRange = getDateRange();
      const params: any = {};
      if (dateRange) {
        params.startDate = dateRange.startDate;
        params.endDate = dateRange.endDate;
      }
      const response = await api.get('/payments', { params });
      setPayments(response.data || []);
      setLoading(false);
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to fetch payments');
      setLoading(false);
    }
  };

  const filteredPayments = useMemo(() => {
    return payments.filter((payment) => {
      const matchesSearch =
        (payment.paymentId?.toString() || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (payment.userId?.toString() || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (payment.customerName || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (payment.orderId || '').toLowerCase().includes(searchTerm.toLowerCase());

      return matchesSearch;
    });
  }, [payments, searchTerm]);

  const totalItems = filteredPayments.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems);

  const paginatedPayments = useMemo(() => {
    return filteredPayments.slice(startIndex, endIndex);
  }, [filteredPayments, startIndex, endIndex]);

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

  const togglePayment = (paymentId: string) => {
    const newExpanded = new Set(expandedPayments);
    if (newExpanded.has(paymentId)) {
      newExpanded.delete(paymentId);
    } else {
      newExpanded.add(paymentId);
    }
    setExpandedPayments(newExpanded);
  };

  const handleVerifyEntry = async (paymentId: string, entryId: number, verified: boolean) => {
    try {
      await api.put(`/payments/${paymentId}/verify-entry/${entryId}`, { verified });
      toast.success('Payment entry verification updated');
      fetchPayments();
    } catch (error: any) {
      toast.error(
        error.response?.data?.message ||
          error.response?.data?.detail ||
          'Failed to update verification status'
      );
    }
  };

  const handleToggleFlag = (flagId: string) => {
    setFlags((prev) =>
      prev.map((f) => (f.id === flagId ? { ...f, enabled: !f.enabled } : f))
    );
  };

  const handleSaveSettings = async () => {
    setSavingSettings(true);
    try {
      const segmentFlags = [
        'retail_enable_cod',
        'retail_enable_upi',
        'retail_enable_gst',
        'wholesale_enable_cod',
        'wholesale_enable_upi',
        'wholesale_enable_credit',
        'wholesale_enable_gst',
      ];
      const promises = flags
        .filter((f) => segmentFlags.includes(f.id))
        .map((f) =>
          api.put(`/feature-flags/${f.id}`, {
            name: f.name,
            description: f.description,
            category: f.category,
            enabled: f.enabled,
          })
        );
      await Promise.all(promises);
      toast.success('Configuration saved successfully');
      setShowSettings(false);
    } catch (error) {
      toast.error('Failed to save configuration');
    } finally {
      setSavingSettings(false);
    }
  };

  const renderToggle = (flagId: string, label: string, description: string) => {
    const flag = flags.find((f) => f.id === flagId);
    const isEnabled = flag ? !!flag.enabled : false;

    return (
      <div className="flex items-start justify-between gap-4 p-2 rounded-md hover:bg-white transition-colors duration-150">
        <div className="flex flex-col">
          <span className="text-sm font-semibold text-gray-900">{label}</span>
          <span className="text-xs text-gray-500">{description}</span>
        </div>
        <label className="relative inline-flex items-center cursor-pointer mt-1 select-none">
          <input
            type="checkbox"
            checked={isEnabled}
            onChange={() => handleToggleFlag(flagId)}
            className="sr-only peer"
          />
          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-indigo-600"></div>
        </label>
      </div>
    );
  };

  if (user?.role !== 'super_admin') {
    return <div>Access Denied</div>;
  }

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <div className="rounded-lg bg-white p-6 shadow-md">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="inline-flex items-center gap-3 text-3xl font-bold">
            Payment Management <RefreshButton onRefresh={fetchPayments} />
          </h1>
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 transition-colors"
          >
            Payments and Tax Settings
          </button>
        </div>

        {/* Payments & Tax Settings Panel */}
        {showSettings && (
          <div className="mb-8 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-bold text-gray-900 mb-2">Payments & Tax Settings</h2>
            <p className="text-sm text-gray-500 mb-6">
              Configure payment options and tax rules for Retail and Wholesale customer segments.
            </p>

            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              {/* Retail Segment */}
              <div className="rounded-lg border border-gray-100 bg-gray-50/50 p-5">
                <h3 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-100 text-xs font-bold text-indigo-700">R</span>
                  Retail Segment (B2C)
                </h3>
                <div className="space-y-4">
                  {renderToggle('retail_enable_cod', 'Cash on Delivery', 'Allow Retail customers to pay using COD')}
                  {renderToggle('retail_enable_upi', 'UPI Payment', 'Allow Retail customers to pay using UPI')}
                  {renderToggle('retail_enable_gst', 'GST Calculation', 'Calculate and display GST for Retail invoices')}
                </div>
              </div>

              {/* Wholesale Segment */}
              <div className="rounded-lg border border-gray-100 bg-gray-50/50 p-5">
                <h3 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100 text-xs font-bold text-emerald-700">W</span>
                  Wholesale Segment (B2B)
                </h3>
                <div className="space-y-4">
                  {renderToggle('wholesale_enable_cod', 'Cash on Delivery', 'Allow Wholesalers to pay using COD')}
                  {renderToggle('wholesale_enable_upi', 'UPI Payment', 'Allow Wholesalers to pay using UPI')}
                  {renderToggle('wholesale_enable_credit', 'Credit', 'Allow Wholesalers to request credit terms')}
                  {renderToggle('wholesale_enable_gst', 'GST Calculation', 'Calculate and display GST for Wholesale invoices')}
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={handleSaveSettings}
                disabled={savingSettings}
                className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50 transition-colors"
              >
                {savingSettings ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        )}

        {/* Search and Date Filters */}
        <div className="mb-6 flex flex-wrap gap-4">
          <div className="min-w-[300px] flex-1">
            <input
              type="text"
              placeholder="Search by payment ID, retail customer ID, retail customer name, or order ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-2"
            />
          </div>
          <select
            value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value)}
            className="rounded-lg border border-gray-300 px-4 py-2"
          >
            <option value="all">All Time</option>
            <option value="day">Today</option>
            <option value="week">Last 7 Days</option>
            <option value="month">This Month</option>
            <option value="year">This Year</option>
            <option value="custom">Custom Range</option>
          </select>
          {dateFilter === 'custom' && (
            <>
              <input
                type="date"
                value={customStartDate}
                onChange={(e) => setCustomStartDate(e.target.value)}
                className="rounded-lg border border-gray-300 px-4 py-2"
                placeholder="Start Date"
              />
              <input
                type="date"
                value={customEndDate}
                onChange={(e) => setCustomEndDate(e.target.value)}
                className="rounded-lg border border-gray-300 px-4 py-2"
                placeholder="End Date"
              />
            </>
          )}
        </div>

        {/* Payments Table */}
        <div className="overflow-x-auto">
          <table className="w-full border-collapse" style={{ minWidth: '1400px' }}>
            <thead>
              <tr className="bg-gray-100">
                <th className="border p-3 text-left"><InfoButton info="Unique identifier for this payment record">Payment ID</InfoButton></th>
                <th className="border p-3 text-left"><InfoButton info="The order ID this payment is associated with">Order ID</InfoButton></th>
                <th className="border p-3 text-left"><InfoButton info="The unique ID of the retail customer who placed the order">Retail Customer ID</InfoButton></th>
                <th className="border p-3 text-left"><InfoButton info="The name of the retail customer who placed the order">Retail Customer Name</InfoButton></th>
                <th className="border p-3 text-left"><InfoButton info="The date the order was placed">Order Date</InfoButton></th>
                <th className="border p-3 text-left"><InfoButton info="The payment method used (e.g. Cash, UPI, Bank Transfer)">Payment Method</InfoButton></th>
                <th className="border p-3 text-left"><InfoButton info="The full invoice amount for this order">Total Amount</InfoButton></th>
                <th className="border p-3 text-left"><InfoButton info="The cumulative amount paid so far across all payment entries">Amount Paid</InfoButton></th>
                <th className="border p-3 text-left"><InfoButton info="The outstanding balance yet to be collected (Total - Paid)">Amount Remaining</InfoButton></th>
                <th className="border p-3 text-left"><InfoButton info="Individual payment installments or transactions associated with this order. Click Show to expand.">Payment Entries</InfoButton></th>
                <th className="border p-3 text-left"><InfoButton info="Actions available for this payment record">Actions</InfoButton></th>
              </tr>
            </thead>
            <tbody>
              {paginatedPayments.length > 0 ? (
                paginatedPayments.map((payment) => (
                  <React.Fragment key={payment._id}>
                    <tr className="hover:bg-gray-50">
                      <td className="border p-3">{payment.paymentId || payment._id}</td>
                      <td className="border p-3">{payment.orderId || '-'}</td>
                      <td className="border p-3">
                        {(payment as any).userIdFormatted || payment.userId || '-'}
                      </td>
                      <td className="border p-3">{payment.customerName || '-'}</td>
                      <td className="border p-3">
                        {payment.orderDate ? formatDateIST(payment.orderDate) : '-'}
                      </td>
                      <td className="border p-3">
                        <span className="rounded bg-blue-100 px-2 py-1 text-xs font-semibold text-blue-800">
                          {payment.paymentMethod?.toUpperCase() || 'N/A'}
                        </span>
                      </td>
                      <td className="border p-3">₹{(payment.totalAmount || 0).toFixed(2)}</td>
                      <td className="border p-3">
                        <span className="rounded bg-green-100 px-2 py-1 text-xs font-semibold text-green-800">
                          ₹{(payment.amountPaid || 0).toFixed(2)}
                        </span>
                      </td>
                      <td className="border p-3">
                        <span
                          className={`rounded px-2 py-1 text-xs font-semibold ${(payment.amountRemaining || 0) > 0 ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}`}
                        >
                          ₹{(payment.amountRemaining || 0).toFixed(2)}
                        </span>
                      </td>
                      <td className="border p-3">
                        <button
                          onClick={() => togglePayment(payment._id)}
                          className="rounded bg-gray-600 px-3 py-1 text-sm text-white hover:bg-gray-700"
                        >
                          {expandedPayments.has(payment._id) ? '▼ Hide' : '▶ Show'} (
                          {payment.paymentEntries?.length || 0})
                        </button>
                      </td>
                      <td className="border p-3">{/* No actions needed currently */}</td>
                    </tr>
                    {expandedPayments.has(payment._id) &&
                      payment.paymentEntries &&
                      payment.paymentEntries.length > 0 && (
                        <tr>
                          <td colSpan={11} className="border bg-gray-50 p-0">
                            <div className="p-6">
                              <h4 className="mb-4 text-lg font-semibold">Payment Entries</h4>
                              <table className="w-full border-collapse">
                                <thead>
                                  <tr className="bg-gray-100">
                                    <th className="border p-2 text-left"><InfoButton info="A unique identifier for this individual payment entry">Entry ID</InfoButton></th>
                                    <th className="border p-2 text-left"><InfoButton info="Amount paid in this specific transaction">Amount</InfoButton></th>
                                    <th className="border p-2 text-left"><InfoButton info="An uploaded image of the payment proof (e.g. bank transfer screenshot)">Transaction Image</InfoButton></th>
                                    <th className="border p-2 text-left"><InfoButton info="Whether this payment entry has been verified by the admin">Verified</InfoButton></th>
                                    <th className="border p-2 text-left"><InfoButton info="The date this payment entry was recorded">Date</InfoButton></th>
                                    <th className="border p-2 text-left"><InfoButton info="Verify or unverify this payment entry">Actions</InfoButton></th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {payment.paymentEntries.map((entry, idx) => (
                                    <tr key={entry.entryId || idx}>
                                      <td className="border p-2">{entry.entryId || idx + 1}</td>
                                      <td className="border p-2">
                                        ₹{(entry.amount || 0).toFixed(2)}
                                      </td>
                                      <td className="border p-2">
                                        {entry.image ? (
                                          <img
                                            src={entry.image}
                                            alt="Transaction"
                                            className="max-h-[100px] max-w-[100px] cursor-pointer hover:opacity-75"
                                            onClick={() => window.open(entry.image, '_blank')}
                                          />
                                        ) : (
                                          <span className="text-gray-400">N/A</span>
                                        )}
                                      </td>
                                      <td className="border p-2">
                                        <span
                                          className={`rounded px-2 py-1 text-xs font-semibold ${entry.verified ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}
                                        >
                                          {entry.verified ? 'Yes' : 'No'}
                                        </span>
                                      </td>
                                      <td className="border p-2">
                                        {entry.createdAt ? formatDateIST(entry.createdAt) : '-'}
                                      </td>
                                      <td className="border p-2">
                                        <select
                                          value={entry.verified ? 'yes' : 'no'}
                                          onChange={(e) =>
                                            handleVerifyEntry(
                                              payment._id,
                                              entry.entryId || idx + 1,
                                              e.target.value === 'yes'
                                            )
                                          }
                                          className={`rounded border px-3 py-1 ${
                                            entry.verified
                                              ? 'border-green-300 bg-green-100 text-green-800'
                                              : 'border-yellow-300 bg-yellow-100 text-yellow-800'
                                          }`}
                                        >
                                          <option value="no">No</option>
                                          <option value="yes">Yes</option>
                                        </select>
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </td>
                        </tr>
                      )}
                  </React.Fragment>
                ))
              ) : (
                <tr>
                  <td colSpan={11} className="border p-3 text-center">
                    No payments found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Premium Pagination Controls */}
        {filteredPayments.length > 0 && (
          <div className="mt-4 flex flex-shrink-0 flex-col items-center justify-between gap-4 border-t border-gray-200 pt-4 sm:flex-row">
            <div className="text-sm text-gray-700">
              Showing <span className="font-semibold">{totalItems === 0 ? 0 : startIndex + 1}</span> to{' '}
              <span className="font-semibold">{endIndex}</span> of{' '}
              <span className="font-semibold">{totalItems}</span> payments
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
      </div>
    </div>
  );
}
