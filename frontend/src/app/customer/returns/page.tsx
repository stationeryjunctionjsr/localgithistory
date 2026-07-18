'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import Link from 'next/link';
import Header from '@/components/Header';

export default function MyReturns() {
  const { user } = useAuth();
  const [returns, setReturns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReturns = async () => {
      try {
        const res = await api.get('/returns/my-returns');
        setReturns(res.data || []);
      } catch (err) {
        console.error('Failed to fetch return requests', err);
      } finally {
        setLoading(false);
      }
    };
    if (user) {
      fetchReturns();
    } else {
      setLoading(false);
    }
  }, [user]);

  const getStatusBadgeClass = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'assigned':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'collected':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'returned':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'rejected':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      <Header />
      
      <main className="max-w-6xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">My Returns</h1>
            <p className="text-sm text-gray-500 mt-1">
              Track the status of your product return and refund requests.
            </p>
          </div>
          <Link
            href="/customer/orders"
            className="px-4 py-2 text-sm font-semibold text-gray-700 bg-white border border-gray-300 rounded-lg shadow-sm hover:bg-gray-50 transition"
          >
            Back to Orders
          </Link>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1a4d33]"></div>
          </div>
        ) : !user ? (
          <div className="text-center py-12 bg-white rounded-xl shadow-sm border border-gray-100">
            <p className="text-gray-500">Please sign in to view returns.</p>
          </div>
        ) : returns.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-xl shadow-sm border border-gray-100">
            <svg
              className="mx-auto h-12 w-12 text-gray-300"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M16 15v-1a4 4 0 00-4-4H8m0 0l3 3m-3-3l3-3m9 14V5a2 2 0 00-2-2H6a2 2 0 00-2 2v16l4-2 4 2 4-2 4 2z"
              />
            </svg>
            <h3 className="mt-4 text-sm font-semibold text-gray-900">No returns found</h3>
            <p className="mt-1 text-sm text-gray-500">You haven't requested any returns yet.</p>
            <div className="mt-6">
              <Link
                href="/customer/orders"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-[#1a4d33] hover:bg-[#153e29]"
              >
                Go to Orders
              </Link>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {returns.map((req) => (
              <div
                key={req._id}
                className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden"
              >
                {/* Request Header */}
                <div className="px-6 py-4 bg-gray-50 border-b border-gray-100 flex flex-wrap items-center justify-between gap-4">
                  <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
                    <div>
                      <span className="text-xs text-gray-400 font-semibold uppercase tracking-wider block">
                        Return ID
                      </span>
                      <span className="text-sm font-mono font-medium text-gray-700">
                        #{req._id?.slice(-8)}
                      </span>
                    </div>
                    <div>
                      <span className="text-xs text-gray-400 font-semibold uppercase tracking-wider block">
                        Order ID
                      </span>
                      <span className="text-sm font-mono font-medium text-gray-700">
                        #{req.orderId?.slice(-8)}
                      </span>
                    </div>
                    <div>
                      <span className="text-xs text-gray-400 font-semibold uppercase tracking-wider block">
                        Requested On
                      </span>
                      <span className="text-sm text-gray-700 font-medium">
                        {new Date(req.createdAt).toLocaleDateString('en-IN', {
                          day: 'numeric',
                          month: 'short',
                          year: 'numeric',
                        })}
                      </span>
                    </div>
                  </div>

                  <div>
                    <span
                      className={`px-3 py-1 text-xs font-semibold rounded-full border ${getStatusBadgeClass(
                        req.status
                      )}`}
                    >
                      {req.status}
                    </span>
                  </div>
                </div>

                {/* Items */}
                <div className="p-6">
                  <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                    Returned Items
                  </h4>
                  <div className="divide-y divide-gray-100">
                    {req.items?.map((item: any, idx: number) => (
                      <div key={idx} className="py-3 first:pt-0 last:pb-0 flex items-center justify-between">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">
                            {item.product?.name || 'Product'}
                          </p>
                          <p className="text-xs text-red-500 mt-1">
                            Reason: {item.reason}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-semibold text-gray-900">
                            ₹{item.price || 0}
                          </p>
                          <p className="text-xs text-gray-500">
                            Qty: {item.quantity}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Return Details */}
                  <div className="mt-6 pt-6 border-t border-gray-100 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm bg-gray-50 p-4 rounded-lg">
                    <div>
                      <p className="text-gray-500">
                        <span className="font-semibold text-gray-700">Refund Method:</span>{' '}
                        {req.paymentMethod?.toUpperCase()}
                      </p>
                      {req.notes && (
                        <p className="text-gray-500 mt-1">
                          <span className="font-semibold text-gray-700">Notes:</span> {req.notes}
                        </p>
                      )}
                    </div>
                    <div className="md:text-right">
                      <p className="text-gray-500">
                        <span className="font-semibold text-gray-700">Return Pickup Charge:</span>{' '}
                        ₹{req.deliveryCharge || 0}
                      </p>
                      {req.valet && (
                        <p className="text-gray-500 mt-1">
                          <span className="font-semibold text-gray-700">Assigned Valet:</span>{' '}
                          {req.valet.name}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
