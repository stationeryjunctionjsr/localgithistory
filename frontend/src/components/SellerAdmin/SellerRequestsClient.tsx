'use client';

import { useState, useEffect, useMemo } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import { formatDateTimeIST } from '@/utils/dateUtils';
import RefreshButton from '@/components/Admin/RefreshButton';

interface SellerRequest {
  _id: string;
  requestNumber: string;
  subject: string;
  description: string;
  category: string;
  priority: string;
  status: string;
  responses: any[];
  createdAt: string;
}

export default function SellerRequestsClient() {
  const { user: currentUser } = useAuth();
  const [requests, setRequests] = useState<SellerRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedRequest, setSelectedRequest] = useState<SellerRequest | null>(null);
  const [replyText, setReplyText] = useState('');
  const [updating, setUpdating] = useState(false);
  const [showNewModal, setShowNewModal] = useState(false);

  const [newSubject, setNewSubject] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newPriority, setNewPriority] = useState('medium');

  useEffect(() => {
    if (currentUser?.role === 'wholesaler') {
      fetchRequests();
    }
  }, [currentUser]);

  const fetchRequests = async () => {
    try {
      setLoading(true);
      const res = await api.get('/seller-requests');
      setRequests(res.data || []);
    } catch {
      toast.error('Failed to fetch requests');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSubject.trim() || !newDesc.trim()) {
      toast.error('Subject and description are required');
      return;
    }
    try {
      setUpdating(true);
      const res = await api.post('/seller-requests', {
        subject: newSubject,
        description: newDesc,
        priority: newPriority,
        category: 'general',
      });
      setRequests((prev) => [res.data, ...prev]);
      setShowNewModal(false);
      setNewSubject('');
      setNewDesc('');
      toast.success('Request raised successfully');
    } catch {
      toast.error('Failed to raise request');
    } finally {
      setUpdating(false);
    }
  };

  const handleReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!replyText.trim() || !selectedRequest) return;
    try {
      setUpdating(true);
      const res = await api.post(`/seller-requests/${selectedRequest._id}/response`, {
        message: replyText,
      });
      setRequests((prev) => prev.map((r) => (r._id === selectedRequest._id ? res.data : r)));
      setSelectedRequest(res.data);
      setReplyText('');
      toast.success('Reply added');
    } catch {
      toast.error('Failed to send reply');
    } finally {
      setUpdating(false);
    }
  };

  const filtered = useMemo(() => {
    return requests.filter((r) => {
      if (filterStatus !== 'all' && r.status !== filterStatus) return false;
      return true;
    });
  }, [requests, filterStatus]);

  if (!currentUser || currentUser.role !== 'wholesaler') return null;

  return (
    <div className="p-6 max-w-7xl mx-auto flex gap-6">
      {/* List Panel */}
      <div className="flex-1 bg-white dark:bg-gray-800 rounded-xl shadow border border-gray-200 dark:border-gray-700 p-6 flex flex-col max-h-[calc(100vh-120px)]">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">Support Requests</h1>
          <div className="flex gap-2">
            <RefreshButton onRefresh={fetchRequests} />
            <button
              onClick={() => setShowNewModal(true)}
              className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition"
            >
              + Raise Request
            </button>
          </div>
        </div>
        <div className="mb-4">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 dark:text-white"
          >
            <option value="all">All Status</option>
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
        </div>
        <div className="flex-1 overflow-y-auto pr-2 space-y-3">
          {loading ? (
            <div className="text-center py-10">Loading...</div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-10 text-gray-400">No requests found.</div>
          ) : (
            filtered.map((req) => (
              <div
                key={req._id}
                onClick={() => setSelectedRequest(req)}
                className={`p-4 rounded-lg cursor-pointer border ${selectedRequest?._id === req._id ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20' : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50'}`}
              >
                <div className="flex justify-between items-start mb-1">
                  <div className="font-semibold text-gray-800 dark:text-gray-100">{req.subject}</div>
                  <span className="text-xs uppercase px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded-full">{req.status}</span>
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400 truncate">{req.description}</div>
                <div className="flex justify-between items-center mt-3 text-xs text-gray-400">
                  <span>{formatDateTimeIST(req.createdAt)}</span>
                  <span>{req.requestNumber}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Detail Panel */}
      {selectedRequest ? (
        <div className="flex-1 bg-white dark:bg-gray-800 rounded-xl shadow border border-gray-200 dark:border-gray-700 p-6 flex flex-col max-h-[calc(100vh-120px)]">
          <div className="flex justify-between items-start border-b border-gray-200 dark:border-gray-700 pb-4 mb-4">
            <div>
              <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-1">{selectedRequest.subject}</h2>
              <p className="text-sm text-gray-500">Status: <span className="uppercase font-medium">{selectedRequest.status}</span></p>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto pr-2 space-y-4">
            <div className="bg-gray-50 dark:bg-gray-900/50 p-4 rounded-lg">
              <div className="text-xs text-gray-400 mb-2">{formatDateTimeIST(selectedRequest.createdAt)}</div>
              <p className="text-gray-800 dark:text-gray-200 whitespace-pre-wrap">{selectedRequest.description}</p>
            </div>
            {selectedRequest.responses?.map((res, i) => (
              <div key={i} className={`p-4 rounded-lg max-w-[85%] ${!res.isAdminResponse ? 'ml-auto bg-indigo-50 dark:bg-indigo-900/20' : 'bg-gray-50 dark:bg-gray-900/50'}`}>
                <div className="text-xs text-gray-400 mb-2 flex justify-between">
                  <span>{res.isAdminResponse ? 'Support Team' : 'You'}</span>
                  <span>{formatDateTimeIST(res.createdAt)}</span>
                </div>
                <p className="text-gray-800 dark:text-gray-200 whitespace-pre-wrap">{res.message}</p>
              </div>
            ))}
          </div>
          {selectedRequest.status !== 'closed' && (
            <form onSubmit={handleReply} className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 flex gap-3">
              <textarea
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                placeholder="Type your reply..."
                className="flex-1 resize-none border border-gray-300 dark:border-gray-600 rounded-lg p-2 text-sm bg-white dark:bg-gray-700 focus:outline-none focus:border-indigo-500"
                rows={2}
              />
              <button
                type="submit"
                disabled={updating || !replyText.trim()}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                Reply
              </button>
            </form>
          )}
        </div>
      ) : (
        <div className="flex-1 bg-white dark:bg-gray-800 rounded-xl shadow border border-gray-200 dark:border-gray-700 p-6 flex items-center justify-center text-gray-400">
          Select a request to view details
        </div>
      )}

      {/* New Request Modal */}
      {showNewModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl p-6 w-full max-w-lg">
            <h2 className="text-xl font-bold mb-4 dark:text-white">Raise New Request</h2>
            <form onSubmit={handleCreateRequest} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Subject</label>
                <input
                  type="text"
                  required
                  value={newSubject}
                  onChange={(e) => setNewSubject(e.target.value)}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 focus:outline-none focus:border-indigo-500"
                  placeholder="E.g. Issue with product listing"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
                <textarea
                  required
                  rows={4}
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full resize-none border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 focus:outline-none focus:border-indigo-500"
                  placeholder="Provide details about your request..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Priority</label>
                <select
                  value={newPriority}
                  onChange={(e) => setNewPriority(e.target.value)}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 focus:outline-none focus:border-indigo-500"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowNewModal(false)}
                  className="px-4 py-2 text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={updating}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"
                >
                  {updating ? 'Submitting...' : 'Submit Request'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
