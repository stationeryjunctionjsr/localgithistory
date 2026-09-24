"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { toast } from "react-toastify";
import api from "@/utils/api";

interface SellerPayoutSummary {
  sellerId: string;
  sellerName?: string;
  totalRealized: number;
  totalPaid: number;
  totalOutstanding: number;
  totalUnrealized: number;
  totalPayoutRealized: number;
  totalPayoutPaid: number;
  totalPayoutOutstanding: number;
  totalPayoutUnrealized: number;
  totalValueRealized: number;
  totalTaxRealized: number;
  subOrderCount: number;
}

interface SellerPayoutRecord {
  id: string;
  sellerId: string;
  sellerName?: string;
  amount: number;
  status: string;
  paymentMethod?: string;
  paymentReference?: string;
  notes?: string;
  subOrderIds?: string[];
  adminPaidAt?: string;
  sellerReceivedAt?: string;
  sellerUpiId?: string;
  sellerBankAccountNumber?: string;
  sellerBankIfscCode?: string;
  sellerBankAccountHolder?: string;
  sellerBankName?: string;
  createdAt?: string;
}

export default function SellerPayoutsPage() {
  const [summaries, setSummaries] = useState<SellerPayoutSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [settlingSeller, setSettlingSeller] = useState<string | null>(null);
  const [payouts, setPayouts] = useState<SellerPayoutRecord[]>([]);
  const [markingPaid, setMarkingPaid] = useState<SellerPayoutRecord | null>(null);
  const [payMethod, setPayMethod] = useState('UPI');
  const [payRef, setPayRef] = useState('');
  const [submittingPaid, setSubmittingPaid] = useState(false);

  useEffect(() => {
    fetchSummaries();
    fetchPayouts();
  }, []);

  const fetchPayouts = async () => {
    try {
      const res = await api.get('/seller-payouts');
      setPayouts(res.data);
    } catch (error) {
      console.error("Error fetching payouts:", error);
    }
  };

  const fetchSummaries = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/seller-payouts/summaries`);
      setSummaries(res.data);
    } catch (error) {
      console.error("Error fetching summaries:", error);
      toast.error("Failed to load seller payout summaries");
    } finally {
      setLoading(false);
    }
  };

  const handleSettleAll = async (seller: SellerPayoutSummary) => {
    if (!window.confirm(`Are you sure you want to settle all realized sub-orders for ${seller.sellerName || "Unknown"}?\nTotal Payout Amount: ₹${seller.totalPayoutOutstanding.toFixed(2)}`)) {
      return;
    }
    
    try {
      setSettlingSeller(seller.sellerId);
      await api.post(`/seller-payouts/settle-all/${seller.sellerId}`, {});
      toast.success("Payout created successfully");
      fetchSummaries();
      fetchPayouts();
    } catch (error: any) {
      console.error("Error settling payouts:", error);
      toast.error(error?.response?.data?.detail || "Failed to create payout");
    } finally {
      setSettlingSeller(null);
    }
  };

  const submitMarkPaid = async () => {
    if (!markingPaid) return;
    setSubmittingPaid(true);
    try {
      await api.post(`/seller-payouts/${markingPaid.id}/mark-paid`, {
        paymentMethod: payMethod,
        paymentReference: payRef,
      });
      toast.success("Payout marked as paid");
      setMarkingPaid(null);
      setPayMethod('UPI');
      setPayRef('');
      fetchPayouts();
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Failed to mark as paid");
    } finally {
      setSubmittingPaid(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Seller Payouts Reconciliation</h2>
          <p className="text-gray-500">View and reconcile sub-order values, GST, commissions, and seller payouts.</p>
        </div>
      </div>
      
      <div className="overflow-x-auto bg-white rounded shadow">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Seller Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sub-orders</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Sub-order Value</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Commission Earned</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Net Payout Owed</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Paid</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {summaries.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-4 text-center text-sm text-gray-500">
                  No data available
                </td>
              </tr>
            ) : (
              summaries.map((record) => (
                <tr key={record.sellerId} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {record.sellerName || "Unknown"}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {record.subOrderCount}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ₹{(record.totalValueRealized || 0).toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ₹{(record.totalRealized || 0).toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold">
                    <span className={record.totalPayoutOutstanding > 0 ? "text-red-600" : "text-gray-500"}>
                      ₹{(record.totalPayoutOutstanding || 0).toFixed(2)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-green-600">
                    ₹{(record.totalPayoutPaid || 0).toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2 flex">
                    <Link href={`/admin/seller-payouts/${record.sellerId}`}>
                      <span className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 cursor-pointer">
                        Details
                      </span>
                    </Link>
                    {record.totalPayoutOutstanding > 0 && (
                      <button
                        onClick={() => handleSettleAll(record)}
                        disabled={settlingSeller === record.sellerId}
                        className={`inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 ${
                          settlingSeller === record.sellerId ? "opacity-50 cursor-not-allowed" : ""
                        }`}
                      >
                        {settlingSeller === record.sellerId ? "Settling..." : "Settle All"}
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* ── Payout Records Section ── */}
      <div className="mt-12 mb-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Payout Records</h2>
        <div className="overflow-x-auto bg-white rounded shadow">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Seller Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {payouts.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">
                    No payout records found
                  </td>
                </tr>
              ) : (
                payouts.map((payout) => (
                  <tr key={payout.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(payout.createdAt || '').toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {payout.sellerName || payout.sellerId}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-700">
                      ₹{payout.amount.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        payout.status === 'pending_payment' ? 'bg-yellow-100 text-yellow-800' :
                        payout.status === 'admin_paid' ? 'bg-blue-100 text-blue-800' :
                        payout.status === 'seller_received' ? 'bg-green-100 text-green-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {payout.status.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {payout.status === 'pending_payment' && (
                        <button
                          onClick={() => setMarkingPaid(payout)}
                          className="text-indigo-600 hover:text-indigo-900 bg-indigo-50 px-3 py-1 rounded"
                        >
                          Mark as Paid
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Mark Paid Modal */}
      {markingPaid && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-bold mb-4">Mark Payout as Paid</h3>
            <p className="text-sm text-gray-600 mb-4">
              Record the payment of ₹{markingPaid.amount.toFixed(2)} to {markingPaid.sellerName}.
            </p>
            
            <div className="bg-gray-50 p-3 rounded mb-4 text-sm border">
              <p className="font-semibold mb-1">Seller Payment Details:</p>
              <p><strong>UPI ID:</strong> {markingPaid.sellerUpiId || 'N/A'}</p>
              <p><strong>Bank A/C:</strong> {markingPaid.sellerBankAccountNumber || 'N/A'}</p>
              <p><strong>IFSC:</strong> {markingPaid.sellerBankIfscCode || 'N/A'}</p>
              <p><strong>Holder:</strong> {markingPaid.sellerBankAccountHolder || 'N/A'}</p>
              <p><strong>Bank:</strong> {markingPaid.sellerBankName || 'N/A'}</p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Payment Method</label>
                <select 
                  value={payMethod} 
                  onChange={e => setPayMethod(e.target.value)}
                  className="w-full border-gray-300 rounded shadow-sm p-2 border"
                >
                  <option value="UPI">UPI</option>
                  <option value="Bank Transfer">Bank Transfer</option>
                  <option value="Cash">Cash</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Reference / UTR (Optional)</label>
                <input 
                  type="text" 
                  value={payRef} 
                  onChange={e => setPayRef(e.target.value)}
                  className="w-full border-gray-300 rounded shadow-sm p-2 border"
                  placeholder="e.g. UTR123456789"
                />
              </div>
            </div>
            
            <div className="mt-6 flex justify-end space-x-3">
              <button 
                onClick={() => { setMarkingPaid(null); setPayMethod('UPI'); setPayRef(''); }}
                className="px-4 py-2 border border-gray-300 rounded text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button 
                onClick={submitMarkPaid}
                disabled={submittingPaid}
                className="px-4 py-2 bg-indigo-600 border border-transparent rounded text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {submittingPaid ? 'Saving...' : 'Confirm Paid'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
