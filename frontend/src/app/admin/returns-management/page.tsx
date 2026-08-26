'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import { formatDateTimeIST } from '@/utils/dateUtils';


export default function ReturnsManagement() {
  const { user } = useAuth();
  const [returns, setReturns] = useState<any[]>([]);
  const [valets, setValets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  
  // Modals state
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [selectedReturn, setSelectedReturn] = useState<any>(null);
  const [selectedValetId, setSelectedValetId] = useState('');
  const [assigning, setAssigning] = useState(false);

  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectNotes, setRejectNotes] = useState('');
  const [rejecting, setRejecting] = useState(false);
  const [autoAssigningId, setAutoAssigningId] = useState<string | null>(null);

  const handleAutoAssign = async (returnId: string) => {
    setAutoAssigningId(returnId);
    try {
      await api.post(`/returns/admin/${returnId}/auto-assign`);
      toast.success('Auto-assigned return pickup to best available valet.');
      fetchReturns();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to auto-assign valet');
    } finally {
      setAutoAssigningId(null);
    }
  };

  const fetchReturns = async () => {
    try {
      const params = statusFilter ? { status: statusFilter } : {};
      const res = await api.get('/returns/admin/all', { params });
      setReturns(res.data || []);
    } catch (err) {
      toast.error('Failed to fetch return requests');
    }
  };

  const fetchValets = async () => {
    try {
      const res = await api.get('/users', { params: { role: 'valet' } });
      setValets(res.data || []);
    } catch (err) {
      console.error('Failed to fetch valets', err);
    }
  };

  useEffect(() => {
    if (user?.role === 'super_admin') {
      setLoading(true);
      Promise.all([fetchReturns(), fetchValets()]).finally(() => setLoading(false));
    }
  }, [user, statusFilter]);

  if (user?.role !== 'super_admin') return <div className="p-8 text-center text-red-500 font-bold">Access Denied</div>;

  const handleOpenAssignModal = (ret: any) => {
    setSelectedReturn(ret);
    setSelectedValetId(ret.valetId || '');
    setShowAssignModal(true);
  };

  const handleAssignValet = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedValetId) {
      toast.error('Please select a valet.');
      return;
    }
    setAssigning(true);
    try {
      await api.put(`/returns/admin/${selectedReturn._id}/assign`, {
        valetId: selectedValetId,
      });
      toast.success('Valet assigned successfully.');
      setShowAssignModal(false);
      fetchReturns();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to assign valet');
    } finally {
      setAssigning(false);
    }
  };

  const handleCompleteReturn = async (returnId: string) => {
    if (!confirm('Are you sure you want to complete this return? This will refund the customer and increment product stock.')) return;
    try {
      await api.put(`/returns/admin/${returnId}/complete`);
      toast.success('Return completed and stock updated.');
      fetchReturns();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to complete return');
    }
  };

  const handleOpenRejectModal = (ret: any) => {
    setSelectedReturn(ret);
    setRejectNotes('');
    setShowRejectModal(true);
  };

  const handleRejectReturn = async (e: React.FormEvent) => {
    e.preventDefault();
    setRejecting(true);
    try {
      await api.put(`/returns/admin/${selectedReturn._id}/reject`, {
        notes: rejectNotes,
      });
      toast.success('Return request rejected.');
      setShowRejectModal(false);
      fetchReturns();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to reject return');
    } finally {
      setRejecting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'pending':
        return <span className="bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded text-xs font-semibold">Pending</span>;
      case 'assigned':
        return <span className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded text-xs font-semibold">Assigned</span>;
      case 'collected':
        return <span className="bg-purple-100 text-purple-800 px-2 py-0.5 rounded text-xs font-semibold">Collected</span>;
      case 'returned':
        return <span className="bg-green-100 text-green-800 px-2 py-0.5 rounded text-xs font-semibold">Returned</span>;
      case 'rejected':
        return <span className="bg-red-100 text-red-800 px-2 py-0.5 rounded text-xs font-semibold">Rejected</span>;
      default:
        return <span className="bg-gray-100 text-gray-800 px-2 py-0.5 rounded text-xs font-semibold">{status}</span>;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Returns Management</h1>
            <p className="text-slate-500 text-sm mt-1">Manage return requests, assign pickup valets, and process refunds.</p>
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-slate-650">Filter:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 outline-none"
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
                <option value="pending_valet">Awaiting Valet</option>
              <option value="assigned">Assigned</option>
              <option value="collected">Collected</option>
              <option value="returned">Returned</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
        </div>

        {/* Table/List */}
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-800"></div>
          </div>
        ) : returns.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-2xl border border-slate-100">
            <p className="text-slate-500">No return requests found.</p>
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="bg-slate-55 border-b border-slate-100 text-slate-600 font-semibold">
                    <th className="px-6 py-4">Return/Order ID</th>
                    <th className="px-6 py-4">Customer Details</th>
                    <th className="px-6 py-4">Items Requested</th>
                    <th className="px-6 py-4">Pickup Charge</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {returns.map((ret) => (
                    <tr key={ret._id} className="hover:bg-slate-50/50 transition">
                      <td className="px-6 py-4">
                        <div className="font-mono text-xs font-semibold text-slate-700">RET: #{ret._id?.slice(-8)}</div>
                        <div className="font-mono text-[10px] text-slate-400 mt-1">ORD: #{ret.orderId?.slice(-8)}</div>
                        {ret.createdAt && (
                          <div className="text-[10px] text-slate-400 mt-1">
                            {formatDateTimeIST(ret.createdAt)}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="font-medium text-slate-800">{ret.user?.name || 'Customer'}</div>
                        <div className="text-xs text-slate-405">{ret.user?.phone || ret.user?.email}</div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="space-y-1">
                          {ret.items?.map((item: any, idx: number) => (
                            <div key={idx} className="text-xs">
                              <span className="font-medium text-slate-700">{item.product?.name}</span>{' '}
                              <span className="text-slate-400">(Qty: {item.quantity})</span>
                              <div className="text-[10px] text-red-500 italic">Reason: {item.reason}</div>
                            </div>
                          ))}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-slate-700 font-semibold">
                        â‚¹{ret.deliveryCharge || 0}
                        <div className="text-[10px] text-slate-400 font-normal uppercase mt-0.5">{ret.paymentMethod}</div>
                        {ret.upiPaymentScreenshot && (
                          <a
                            href={ret.upiPaymentScreenshot}
                            target="_blank"
                            rel="noreferrer"
                            className="text-[10px] text-blue-600 underline block mt-1"
                          >
                            View Screenshot
                          </a>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        {getStatusBadge(ret.status)}
                        {ret.status === 'pending_valet' && ret.pendingValet && (
                          <div className="text-[10px] text-amber-700 font-medium mt-1">
                            Offered to: {ret.pendingValet.name}
                            {(ret.valetCascadeCount || 0) > 0 && (
                              <span className="text-slate-400 block text-[9px]">Cascade #{ret.valetCascadeCount}</span>
                            )}
                          </div>
                        )}
                        {ret.valet && ret.status !== 'pending_valet' && (
                          <div className="text-[10px] text-slate-500 mt-1">Valet: {ret.valet.name}</div>
                        )}
                        {ret.deliverySlot && (
                          <div className="text-[10px] text-purple-600 font-medium mt-0.5">
                            Slot: {ret.deliverySlot.startTime} - {ret.deliverySlot.endTime}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex justify-end gap-2">
                          {(ret.status === 'pending' || ret.status === 'pending_valet') && (
                            <button
                              onClick={() => handleAutoAssign(ret._id)}
                              disabled={autoAssigningId === ret._id}
                              className="bg-purple-600 hover:bg-purple-700 text-white px-2.5 py-1 rounded text-xs font-semibold transition"
                            >
                              {autoAssigningId === ret._id ? '...' : 'Auto Assign'}
                            </button>
                          )}
                          {(ret.status === 'pending' || ret.status === 'pending_valet' || ret.status === 'assigned') && (
                            <button
                              onClick={() => handleOpenAssignModal(ret)}
                              className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-xs font-semibold transition"
                            >
                              Assign Valet
                            </button>
                          )}
                          {(ret.status === 'collected' || ret.status === 'assigned') && (
                            <button
                              onClick={() => handleCompleteReturn(ret._id)}
                              className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-xs font-semibold transition"
                            >
                              Complete
                            </button>
                          )}
                          {(ret.status === 'pending' || ret.status === 'assigned') && (
                            <button
                              onClick={() => handleOpenRejectModal(ret)}
                              className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-xs font-semibold transition"
                            >
                              Reject
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Assign Valet Modal */}
      {showAssignModal && selectedReturn && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white p-6 rounded-xl max-w-md w-full mx-4 shadow-xl">
            <h3 className="text-lg font-bold text-slate-800 mb-4">Assign Pickup Valet</h3>
            <form onSubmit={handleAssignValet} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-slate-650 mb-1">Select Valet</label>
                <select
                  value={selectedValetId}
                  onChange={(e) => setSelectedValetId(e.target.value)}
                  required
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-slate-700 outline-none"
                >
                  <option value="">Choose a Valet...</option>
                  {valets.map((v) => (
                    <option key={v._id} value={v._id}>
                      {v.name} ({v.phone || v.email})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAssignModal(false)}
                  className="rounded-lg bg-slate-100 hover:bg-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition"
                  disabled={assigning}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-blue-600 hover:bg-blue-700 px-5 py-2 text-sm font-bold text-white transition"
                  disabled={assigning}
                >
                  {assigning ? 'Assigning...' : 'Assign'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {showRejectModal && selectedReturn && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white p-6 rounded-xl max-w-md w-full mx-4 shadow-xl">
            <h3 className="text-lg font-bold text-slate-800 mb-4">Reject Return Request</h3>
            <form onSubmit={handleRejectReturn} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-slate-650 mb-1">Reason for Rejection</label>
                <textarea
                  rows={3}
                  value={rejectNotes}
                  onChange={(e) => setRejectNotes(e.target.value)}
                  required
                  placeholder="Explain why this request is rejected..."
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-slate-700 outline-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowRejectModal(false)}
                  className="rounded-lg bg-slate-100 hover:bg-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition"
                  disabled={rejecting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-red-600 hover:bg-red-700 px-5 py-2 text-sm font-bold text-white transition"
                  disabled={rejecting}
                >
                  {rejecting ? 'Rejecting...' : 'Reject Request'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
