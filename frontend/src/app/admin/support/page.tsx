'use client';

import { useState, useEffect, useMemo } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import { formatDateIST, formatDateTimeIST, formatTimeIST } from '@/utils/dateUtils';
import RefreshButton from '@/components/Admin/RefreshButton';

interface SupportTicket {
  _id: string;
  ticketNumber: string;
  subject: string;
  description: string;
  category: string;
  priority: string;
  status: string;
  user: {
    _id: string;
    name: string;
    email: string;
  };
  createdAt: string;
  responses: Array<{
    user: { name: string; email: string; role: string };
    message: string;
    createdAt: string;
    isAdminResponse: boolean;
  }>;
}

export default function AdminSupport() {
  const { user: currentUser } = useAuth();
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTicket, setSelectedTicket] = useState<SupportTicket | null>(null);
  const [reply, setReply] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterPriority, setFilterPriority] = useState('all');

  useEffect(() => {
    if (currentUser?.role === 'super_admin') {
      fetchTickets();
    }
  }, [currentUser]);

  const fetchTickets = async () => {
    try {
      setLoading(true);
      const response = await api.get('/support-tickets/');
      setTickets(response.data);
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to fetch support tickets');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (ticketId: string, status: string) => {
    try {
      const response = await api.put(`/support-tickets/${ticketId}/status/`, { status });
      toast.success(`Ticket marked as ${status.replace('_', ' ')}`);
      const updatedTicket = response.data;
      setTickets(tickets.map((t) => (t._id === ticketId ? updatedTicket : t)));
      if (selectedTicket?._id === ticketId) {
        setSelectedTicket(updatedTicket);
      }
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to update status');
    }
  };

  const handlePriorityUpdate = async (ticketId: string, priority: string) => {
    try {
      const response = await api.put(`/support-tickets/${ticketId}/priority/`, { priority });
      toast.success(`Priority set to ${priority}`);
      const updatedTicket = response.data;
      setTickets(tickets.map((t) => (t._id === ticketId ? updatedTicket : t)));
      if (selectedTicket?._id === ticketId) {
        setSelectedTicket(updatedTicket);
      }
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to update priority');
    }
  };

  const handleReplySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTicket || !reply.trim()) return;

    try {
      const response = await api.post(`/support-tickets/${selectedTicket._id}/response/`, {
        message: reply,
      });
      toast.success('Reply submitted');
      setSelectedTicket(response.data);
      setReply('');
      setTickets(tickets.map((t) => (t._id === selectedTicket._id ? response.data : t)));
    // eslint-disable-next-line unused-imports/no-unused-vars
    } catch (error: any) {
      toast.error('Failed to send reply');
    }
  };

  const filteredTickets = useMemo(() => {
    return tickets
      .filter((ticket) => {
        const matchesSearch =
          ticket.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
          ticket.user?.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          ticket.user?.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          ticket.ticketNumber?.toLowerCase().includes(searchTerm.toLowerCase());

        const matchesStatus = filterStatus === 'all' || ticket.status === filterStatus;
        const matchesPriority = filterPriority === 'all' || ticket.priority === filterPriority;

        return matchesSearch && matchesStatus && matchesPriority;
      })
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
  }, [tickets, searchTerm, filterStatus, filterPriority]);

  const stats = useMemo(() => {
    return {
      total: tickets.length,
      open: tickets.filter((t) => t.status === 'open').length,
      inProgress: tickets.filter((t) => t.status === 'in_progress').length,
      urgent: tickets.filter(
        (t) => t.priority === 'urgent' && t.status !== 'resolved' && t.status !== 'closed'
      ).length,
    };
  }, [tickets]);

  if (currentUser?.role !== 'super_admin') {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center rounded-3xl border border-gray-100 bg-white p-8 shadow-sm">
        <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-red-50 text-red-500">
          <svg className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 15v2m0 0v2m0-2h2m-2 0H10m11-3V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2h11l4 4V12z"
            />
          </svg>
        </div>
        <h2 className="mb-2 text-2xl font-black text-gray-900">ACCESS RESTRICTED</h2>
        <p className="font-medium text-gray-500">
          Only administrators can access the support management panel.
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-hidden min-h-0 animate-support-fade-in">
      {/* Main Workspace Card */}
      <div className="flex flex-1 flex-col overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm min-h-0">
        
        {/* Card Header (Feedback page style, incorporating inline stats and refresh button) */}
        <div className="flex flex-shrink-0 flex-wrap items-center justify-between border-b border-gray-150 bg-gray-50/50 px-6 py-4 gap-4">
          <div>
            <h2 className="inline-flex items-center gap-3 text-xl font-bold text-gray-800 uppercase tracking-normal">
              Support Tickets <RefreshButton onRefresh={fetchTickets} />
            </h2>
            <p className="text-sm text-gray-500 normal-case">Manage and respond to customer inquiries</p>
          </div>
          
          {/* Compact Inline Stats Badges */}
          <div className="flex flex-wrap items-center gap-3">
            <span className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-5 py-2 text-base font-extrabold text-slate-700 border border-slate-200">
              Total: {stats.total}
            </span>
            <span className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-5 py-2 text-base font-extrabold text-emerald-800 border border-emerald-200">
              Open: {stats.open}
            </span>
            <span className="inline-flex items-center gap-2 rounded-full bg-blue-50 px-5 py-2 text-base font-extrabold text-blue-800 border border-blue-200">
              Processing: {stats.inProgress}
            </span>
            <span className="inline-flex items-center gap-2 rounded-full bg-rose-50 px-5 py-2 text-base font-extrabold text-rose-800 border border-rose-200">
              Urgent: {stats.urgent}
            </span>
          </div>
        </div>

        {/* Card Body: Split Pane */}
        <div className="flex flex-1 gap-0 overflow-hidden min-h-0">
          {/* Tickets Sidebar */}
          <div className="flex w-1/5 min-w-[260px] flex-col overflow-hidden border-r border-gray-200 bg-white">
            <div className="flex flex-col gap-3 border-b border-gray-150 p-4 bg-slate-50/30">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search subject, name, email..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full rounded-lg border border-gray-200 bg-white px-4 py-2.5 pl-10 text-base outline-none transition-all focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-slate-700"
                />
                <svg
                  className="absolute left-3.5 top-3.5 h-4 w-4 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </div>
              <div className="flex gap-2">
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="flex-1 rounded-lg border border-gray-200 bg-white px-3 py-2 text-base font-semibold text-gray-600 outline-none cursor-pointer focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="all">All Status</option>
                  <option value="open">Open</option>
                  <option value="in_progress">In Progress</option>
                  <option value="resolved">Resolved</option>
                  <option value="closed">Closed</option>
                </select>
                <select
                  value={filterPriority}
                  onChange={(e) => setFilterPriority(e.target.value)}
                  className="flex-1 rounded-lg border border-gray-200 bg-white px-3 py-2 text-base font-semibold text-gray-600 outline-none cursor-pointer focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="all">Priority</option>
                  <option value="urgent">Urgent</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
            </div>

            <div className="custom-scrollbar flex-1 overflow-y-auto bg-slate-50/20">
              {loading ? (
                <div className="p-12 text-center">
                  <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
                  <p className="text-base font-bold uppercase tracking-wider text-gray-400">
                    Scanning Tickets...
                  </p>
                </div>
              ) : filteredTickets.length === 0 ? (
                <div className="p-12 text-center">
                  <div className="mb-4 text-gray-300">
                    <svg
                      className="mx-auto h-16 w-16"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1}
                        d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
                      />
                    </svg>
                  </div>
                  <p className="text-base font-bold uppercase tracking-wider text-gray-400">
                    No tickets found
                  </p>
                </div>
              ) : (
                filteredTickets.map((ticket) => (
                  <div
                    key={ticket._id}
                    onClick={() => setSelectedTicket(ticket)}
                    className={`cursor-pointer p-4 transition-all border-b border-slate-200 border-l-4 ${
                      selectedTicket?._id === ticket._id
                        ? 'border-l-indigo-600 bg-indigo-50/60'
                        : 'border-l-transparent bg-white hover:bg-slate-50/80'
                    }`}
                  >
                    <div className="mb-3 flex items-start justify-between gap-4">
                      <div className="space-y-1">
                        <p className="text-xs font-extrabold uppercase tracking-wider text-indigo-600">
                          {ticket.ticketNumber || 'TICKET-NUM'}
                        </p>
                        <h4 className="max-w-[180px] truncate text-base font-bold text-slate-800">
                          {ticket.subject}
                        </h4>
                      </div>
                      <span
                        className={`rounded-full px-3 py-1 text-sm font-bold uppercase tracking-wider ${
                          ticket.status === 'open'
                            ? 'bg-emerald-100 text-emerald-800'
                            : ticket.status === 'closed'
                              ? 'bg-gray-100 text-gray-800'
                              : ticket.status === 'resolved'
                                ? 'bg-indigo-100 text-indigo-800'
                                : 'bg-blue-100 text-blue-800'
                        }`}
                      >
                        {ticket.status.replace('_', ' ')}
                      </span>
                    </div>
                    <div className="mt-4 flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 border border-slate-200/50 text-sm font-bold text-slate-650">
                          {ticket.user?.name?.charAt(0).toUpperCase() || '?'}
                        </div>
                        <span className="text-sm font-semibold text-slate-700">
                          {ticket.user?.name || 'Guest User'}
                        </span>
                      </div>
                      <div
                        className={`text-xs font-bold uppercase tracking-wider ${
                          ticket.priority === 'urgent'
                            ? 'text-rose-600'
                            : ticket.priority === 'high'
                              ? 'text-amber-600'
                              : 'text-slate-500'
                        }`}
                      >
                        {ticket.priority}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Ticket Detail */}
          <div className="flex flex-1 flex-col overflow-hidden bg-slate-50/20">
            {selectedTicket ? (
              <>
                {/* Header */}
                <div className="flex items-start justify-between border-b border-gray-150 bg-slate-50/30 p-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-3">
                      <span
                        className={`h-3 w-3 rounded-full ${
                          selectedTicket.status === 'open'
                            ? 'bg-emerald-500 animate-pulse'
                            : selectedTicket.status === 'resolved'
                              ? 'bg-indigo-500'
                              : selectedTicket.status === 'in_progress'
                                ? 'bg-blue-500 animate-pulse'
                                : 'bg-gray-400'
                        }`}
                      />
                      <h3 className="text-2xl font-bold text-slate-800 uppercase tracking-normal">
                        {selectedTicket.subject}
                      </h3>
                    </div>
                    <div className="flex items-center gap-5 text-base font-semibold uppercase tracking-wider text-slate-600">
                      <span className="flex items-center gap-1.5 normal-case">
                        <svg
                          className="h-4.5 w-4.5 text-slate-500"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                          />
                        </svg>
                        {selectedTicket.user?.name || 'Guest User'}
                      </span>
                      <span className="flex items-center gap-1.5 normal-case">
                        <svg
                          className="h-4.5 w-4.5 text-slate-500"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                          />
                        </svg>
                        {selectedTicket.category}
                      </span>
                      <span className="flex items-center gap-1.5 normal-case">
                        <svg
                          className="h-4.5 w-4.5 text-slate-500"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                          />
                        </svg>
                        {formatDateIST(selectedTicket.createdAt)}
                      </span>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <div className="flex gap-2">
                      <select
                        value={selectedTicket.status}
                        onChange={(e) => handleStatusUpdate(selectedTicket._id, e.target.value)}
                        className="rounded-lg border border-gray-200 bg-white px-3.5 py-2 text-sm font-bold uppercase tracking-wider text-slate-650 shadow-sm outline-none cursor-pointer focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                      >
                        <option value="open">Open</option>
                        <option value="in_progress">Processing</option>
                        <option value="resolved">Resolved</option>
                        <option value="closed">Closed</option>
                      </select>
                      <select
                        value={selectedTicket.priority}
                        onChange={(e) => handlePriorityUpdate(selectedTicket._id, e.target.value)}
                        className="rounded-lg border border-gray-200 bg-white px-3.5 py-2 text-sm font-bold uppercase tracking-wider text-slate-650 shadow-sm outline-none cursor-pointer focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                      >
                        <option value="low">Low Priority</option>
                        <option value="medium">Mod Priority</option>
                        <option value="high">High Priority</option>
                        <option value="urgent">Urgent</option>
                      </select>
                    </div>
                    <p className="text-sm font-medium text-slate-500">
                      ID: {selectedTicket._id}
                    </p>
                  </div>
                </div>

                {/* Chat Area */}
                <div className="custom-scrollbar flex-1 space-y-6 overflow-y-auto bg-slate-50/50 p-6">
                  {/* Initial Description Card */}
                  <div className="flex justify-start">
                    <div className="max-w-[85%] rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                      <div className="mb-3 flex items-center justify-between gap-4">
                        <span className="text-sm font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                          <span className="h-2.5 w-2.5 rounded-full bg-indigo-500" />
                          Initial Request
                        </span>
                        <span className="text-sm font-semibold text-slate-400">
                          {formatDateTimeIST(selectedTicket.createdAt)}
                        </span>
                      </div>
                      <p className="whitespace-pre-wrap text-base leading-relaxed text-slate-700 font-normal">
                        {selectedTicket.description}
                      </p>
                    </div>
                  </div>

                  {selectedTicket.responses?.map((res, idx) => (
                    <div
                      key={idx}
                      className={`flex ${res.isAdminResponse ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[80%] rounded-2xl p-5 shadow-sm border transition-all ${
                          res.isAdminResponse
                            ? 'rounded-tr-none bg-gradient-to-br from-indigo-600 to-indigo-700 text-white border-transparent shadow-indigo-100/50'
                            : 'rounded-tl-none border-gray-150 bg-white text-slate-800'
                        }`}
                      >
                        <div className="mb-2 flex items-center justify-between gap-12">
                          <span
                            className={`text-sm font-bold uppercase tracking-wider ${
                              res.isAdminResponse ? 'text-indigo-100' : 'text-indigo-600'
                            }`}
                          >
                            {res.isAdminResponse ? 'SUPPORT AGENT' : res.user?.name || 'USER'}
                          </span>
                          <span
                            className={`text-sm font-semibold ${
                              res.isAdminResponse ? 'text-indigo-200/70' : 'text-slate-400'
                            }`}
                          >
                            {formatTimeIST(res.createdAt)}
                          </span>
                        </div>
                        <p className="whitespace-pre-wrap text-base font-normal leading-relaxed">
                          {res.message}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Reply Input */}
                <div className="border-t border-gray-200 bg-white p-5">
                  <form onSubmit={handleReplySubmit}>
                    <div className="relative flex items-end gap-3 bg-slate-50 p-2.5 rounded-xl border border-slate-200 focus-within:border-indigo-300 focus-within:bg-white focus-within:ring-1 focus-within:ring-indigo-100 transition-all">
                      <textarea
                        value={reply}
                        onChange={(e) => setReply(e.target.value)}
                        placeholder="Write your response, mention solutions or request details..."
                        rows={2}
                        className="w-full resize-none bg-transparent px-4 py-2 text-base font-normal text-slate-700 outline-none placeholder-slate-400"
                      />
                      <button
                        type="submit"
                        disabled={!reply.trim() || loading}
                        className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-md shadow-indigo-100 transition-all hover:bg-indigo-700 active:scale-95 disabled:opacity-40 disabled:shadow-none"
                      >
                        <svg
                          className="h-6 w-6"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2.5}
                            d="M12 19l9-7-9-7v14z"
                          />
                        </svg>
                      </button>
                    </div>
                  </form>
                </div>
              </>
            ) : (
              <div className="flex flex-1 flex-col items-center justify-center p-12 text-center">
                <div className="mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-slate-50 border border-slate-100 text-slate-300">
                  <svg
                    className="h-10 w-10 opacity-40"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                    />
                  </svg>
                </div>
                <h3 className="mb-1 text-lg font-bold text-slate-800 uppercase tracking-normal">
                  Support Command Center
                </h3>
                <p className="max-w-[320px] text-sm font-semibold text-slate-500">
                  Select a pending ticket from the queue to start resolving issues.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
