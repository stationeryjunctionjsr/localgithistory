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

export default function SellerPayoutsPage() {
  const [summaries, setSummaries] = useState<SellerPayoutSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [settlingSeller, setSettlingSeller] = useState<string | null>(null);

  useEffect(() => {
    fetchSummaries();
  }, []);

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
      toast.success("Payouts settled successfully");
      fetchSummaries();
    } catch (error: any) {
      console.error("Error settling payouts:", error);
      toast.error(error?.response?.data?.detail || "Failed to settle payouts");
    } finally {
      setSettlingSeller(null);
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
    </div>
  );
}
