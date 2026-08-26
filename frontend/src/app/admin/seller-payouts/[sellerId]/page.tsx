"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { toast } from "react-toastify";
import api from "@/utils/api";
import Link from "next/link";

interface SubOrder {
  _id: string;
  subOrderNumber: string;
  parentOrderId: string;
  sellerId: string;
  total: number;
  tax: number;
  commissionAmount: number;
  commissionStatus: string;
  status: string;
  createdAt: string;
}

export default function SellerPayoutDetailsPage() {
  const params = useParams();
  const sellerId = params.sellerId as string;
  
  const [subOrders, setSubOrders] = useState<SubOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([]);
  const [recording, setRecording] = useState(false);

  useEffect(() => {
    if (sellerId) {
      fetchSubOrders();
    }
  }, [sellerId]);

  const fetchSubOrders = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/orders/admin/sub-orders?sellerId=${sellerId}&limit=1000`);
      setSubOrders(res.data.subOrders || []);
    } catch (error) {
      console.error("Error fetching sub-orders:", error);
      toast.error("Failed to load sub-orders");
    } finally {
      setLoading(false);
    }
  };

  const handleRecordPayout = async () => {
    const selectedOrders = subOrders.filter(so => selectedRowKeys.includes(so._id));
    const totalAmount = selectedOrders.reduce((acc, so) => {
      return acc + ((so.total || 0) - (so.commissionAmount || 0));
    }, 0);

    if (!window.confirm(`You are about to record a payout for ${selectedRowKeys.length} sub-order(s).\nTotal Payout Amount: ₹${totalAmount.toFixed(2)}\n\nThis will mark the selected sub-orders as paid in the ledger.`)) {
      return;
    }

    try {
      setRecording(true);
      
      const payload = {
        sellerId: sellerId,
        amount: totalAmount,
        subOrderIds: selectedRowKeys,
        notes: "Payout recorded via admin dashboard",
      };

      await api.post(`/seller-payouts`, payload);
      
      toast.success("Payout recorded successfully");
      setSelectedRowKeys([]);
      fetchSubOrders();
    } catch (error: any) {
      console.error("Error recording payout:", error);
      toast.error(error?.response?.data?.detail || "Failed to record payout");
    } finally {
      setRecording(false);
    }
  };

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      const allRealized = subOrders.filter(so => so.commissionStatus === "realized").map(so => so._id);
      setSelectedRowKeys(allRealized);
    } else {
      setSelectedRowKeys([]);
    }
  };

  const handleSelectRow = (id: string, checked: boolean) => {
    if (checked) {
      setSelectedRowKeys(prev => [...prev, id]);
    } else {
      setSelectedRowKeys(prev => prev.filter(key => key !== id));
    }
  };

  const selectedTotal = subOrders
    .filter(so => selectedRowKeys.includes(so._id))
    .reduce((acc, so) => acc + ((so.total || 0) - (so.commissionAmount || 0)), 0);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  const allRealizedCount = subOrders.filter(so => so.commissionStatus === "realized").length;
  const isAllSelected = allRealizedCount > 0 && selectedRowKeys.length === allRealizedCount;

  return (
    <div className="p-6">
      <div className="mb-4">
        <Link href="/admin/seller-payouts">
          <span className="text-indigo-600 hover:text-indigo-900">&larr; Back to Payouts</span>
        </Link>
      </div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Seller Sub-Orders</h2>
          <p className="text-gray-500">Select realized sub-orders to record a payout.</p>
        </div>
        <button 
          className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 ${selectedRowKeys.length === 0 || recording ? 'opacity-50 cursor-not-allowed' : ''}`}
          disabled={selectedRowKeys.length === 0 || recording}
          onClick={handleRecordPayout}
        >
          {recording ? "Recording..." : `Record Payout (₹${selectedTotal.toFixed(2)})`}
        </button>
      </div>

      <div className="overflow-x-auto bg-white rounded shadow">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <input 
                  type="checkbox" 
                  className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                  checked={isAllSelected}
                  onChange={handleSelectAll}
                  disabled={allRealizedCount === 0}
                />
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sub-Order No</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created At</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Commission Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Value</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">GST (Tax)</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Commission</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Net Payout</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {subOrders.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-6 py-4 text-center text-sm text-gray-500">
                  No sub-orders found for this seller.
                </td>
              </tr>
            ) : (
              subOrders.map((record) => {
                const net = (record.total || 0) - (record.commissionAmount || 0);
                const isRealized = record.commissionStatus === "realized";
                
                return (
                  <tr key={record._id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input 
                        type="checkbox" 
                        className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                        disabled={!isRealized}
                        checked={selectedRowKeys.includes(record._id)}
                        onChange={(e) => handleSelectRow(record._id, e.target.checked)}
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {record.subOrderNumber}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(record.createdAt).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                        {record.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        record.commissionStatus === 'paid' ? 'bg-green-100 text-green-800' :
                        record.commissionStatus === 'realized' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {record.commissionStatus || "pending"}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ₹{(record.total || 0).toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      ₹{(record.tax || 0).toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">
                      -₹{(record.commissionAmount || 0).toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">
                      ₹{net.toFixed(2)}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
