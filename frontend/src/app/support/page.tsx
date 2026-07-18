'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import api from '@/utils/api';
import { toast } from 'react-toastify';
import { formatDateTimeIST, formatTimeIST } from '@/utils/dateUtils';
import Header from '@/components/Header';

interface Contact {
  _id: string;
  name: string;
  phoneNumbers?: string[];
  email?: string;
  addresses?: Array<{
    address?: string;
    city?: string;
    state?: string;
    district?: string;
    zipCode?: string;
    googleLocation?: string;
  }>;
  description?: string;
  socialMedia?: {
    instagram?: string;
    facebook?: string;
    twitter?: string;
    whatsapp?: string;
    youtube?: string;
    linkedin?: string;
  };
}

interface SupportTicket {
  _id: string;
  ticketNumber: string;
  subject: string;
  description: string;
  category: string;
  status: string;
  createdAt: string;
  responses: Array<{
    user: { name: string; email: string; role: string };
    message: string;
    createdAt: string;
    isAdminResponse: boolean;
  }>;
}

export default function CustomerSupport() {
  const { user } = useAuth();
  const { theme } = useTheme();
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [activeTab, setActiveTab] = useState<'submit' | 'history'>('submit');
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [loadingTickets, setLoadingTickets] = useState(false);
  const [contactsError, setContactsError] = useState(false);
  const [ticketsError, setTicketsError] = useState(false);
  const [expandedTicket, setExpandedTicket] = useState<string | null>(null);
  const [supportForm, setSupportForm] = useState({
    name: '',
    email: '',
    phone: '',
    company: '',
    subject: '',
    description: '',
    category: 'general',
  });

  useEffect(() => {
    fetchContacts();
    if (user) {
      fetchTickets();
      setSupportForm((prev) => ({
        ...prev,
        name: user.name || '',
        email: user.email || '',
        phone: (user as any).phone || '',
        company: (user as any).companyName || '',
      }));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const fetchContacts = async () => {
    try {
      setContactsError(false);
      const response = await api.get('/contacts/public/');
      setContacts(response.data || []);
    } catch (error: any) {
      if (process.env.NODE_ENV !== 'production') {
        console.error('Error fetching contacts:', error);
      }
      setContactsError(true);
      toast.error('Could not load contact information.');
    }
  };

  const fetchTickets = async () => {
    if (!user) return;
    try {
      setLoadingTickets(true);
      setTicketsError(false);
      const response = await api.get('/support-tickets/');
      setTickets(response.data);
    } catch (error: any) {
      if (process.env.NODE_ENV !== 'production') {
        console.error('Error fetching tickets:', error);
      }
      setTicketsError(true);
      toast.error('Could not load your support tickets.');
    } finally {
      setLoadingTickets(false);
    }
  };

  const handleSupportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      // Use skipAccessToken for guest submissions so the auth interceptor
      // does not attempt a refresh or redirect when there is no token.
      const config = !user ? ({ skipAccessToken: true } as any) : undefined;
      await api.post('/support-tickets/', supportForm, config);
      toast.success('Support ticket created successfully! We will get back to you soon.');
      fetchTickets();
      setSupportForm((prev) => ({
        ...prev,
        subject: '',
        description: '',
      }));
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to create ticket. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-12">
      <Header />

      {(contactsError || ticketsError) && (
        <div className="mx-auto max-w-7xl px-4 pt-6 sm:px-6 lg:px-8">
          {contactsError && (
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-amber-900">
              <span>Contact details could not be loaded.</span>
              <button
                type="button"
                onClick={fetchContacts}
                className="rounded-md bg-amber-800 px-3 py-1 text-sm font-medium text-white hover:bg-amber-900"
              >
                Retry
              </button>
            </div>
          )}
          {ticketsError && user && (
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-amber-900">
              <span>Your tickets could not be loaded.</span>
              <button
                type="button"
                onClick={fetchTickets}
                className="rounded-md bg-amber-800 px-3 py-1 text-sm font-medium text-white hover:bg-amber-900"
              >
                Retry
              </button>
            </div>
          )}
        </div>
      )}

      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Main Content Area */}
          <div className="lg:col-span-2 space-y-6">
            {user && (
              <div className="flex justify-start">
                <div className="inline-flex rounded-xl bg-gray-100 p-1">
                  <button
                    onClick={() => setActiveTab('submit')}
                    className={`rounded-lg px-8 py-2.5 font-bold transition-all ${activeTab === 'submit' ? 'scale-105 bg-white text-gray-900 shadow' : 'text-gray-500 hover:text-gray-700'}`}
                  >
                    Submit Query
                  </button>
                  <button
                    onClick={() => setActiveTab('history')}
                    className={`rounded-lg px-8 py-2.5 font-bold transition-all ${activeTab === 'history' ? 'scale-105 bg-white text-gray-900 shadow' : 'text-gray-500 hover:text-gray-700'}`}
                  >
                    My Queries
                  </button>
                </div>
              </div>
            )}
            {activeTab === 'submit' ? (
              <div className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-xl">
                <div className="p-6 text-white" style={{ backgroundColor: theme.primary }}>
                  <h2 className="text-2xl font-bold">Submit a Support Ticket</h2>
                  <p className="text-sm opacity-80">
                    Detailed information helps us solve your issue faster.
                  </p>
                </div>
                <form onSubmit={handleSupportSubmit} className="space-y-6 p-8">
                  <div className="grid gap-6 md:grid-cols-2">
                    <div>
                      <label className="mb-2 block text-sm font-bold uppercase tracking-wide text-gray-700">
                        Name *
                      </label>
                      <input
                        type="text"
                        required
                        placeholder="Your Full Name"
                        value={supportForm.name}
                        onChange={(e) => setSupportForm({ ...supportForm, name: e.target.value })}
                        className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:ring-2"
                        style={{ '--tw-ring-color': theme.primary } as any}
                      />
                    </div>
                    <div>
                      <label className="mb-2 block text-sm font-bold uppercase tracking-wide text-gray-700">
                        Company
                      </label>
                      <input
                        type="text"
                        placeholder="Company Name (Optional)"
                        value={supportForm.company}
                        onChange={(e) =>
                          setSupportForm({ ...supportForm, company: e.target.value })
                        }
                        className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:ring-2"
                        style={{ '--tw-ring-color': theme.primary } as any}
                      />
                    </div>
                  </div>

                  <div className="grid gap-6 md:grid-cols-2">
                    <div>
                      <label className="mb-2 block text-sm font-bold uppercase tracking-wide text-gray-700">
                        Email Address *
                      </label>
                      <input
                        type="email"
                        required
                        placeholder="your.email@example.com"
                        value={supportForm.email}
                        onChange={(e) => setSupportForm({ ...supportForm, email: e.target.value })}
                        className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:ring-2"
                        style={{ '--tw-ring-color': theme.primary } as any}
                      />
                    </div>
                    <div>
                      <label className="mb-2 block text-sm font-bold uppercase tracking-wide text-gray-700">
                        Phone Number *
                      </label>
                      <input
                        type="tel"
                        required
                        placeholder="+91 XXXXX XXXXX"
                        value={supportForm.phone}
                        onChange={(e) => setSupportForm({ ...supportForm, phone: e.target.value })}
                        className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:ring-2"
                        style={{ '--tw-ring-color': theme.primary } as any}
                      />
                    </div>
                  </div>

                  <div className="grid gap-6 md:grid-cols-1">
                    <div>
                      <label className="mb-2 block text-sm font-bold uppercase tracking-wide text-gray-700">
                        Category
                      </label>
                      <select
                        value={supportForm.category}
                        onChange={(e) =>
                          setSupportForm({ ...supportForm, category: e.target.value })
                        }
                        className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:ring-2"
                        style={{ '--tw-ring-color': theme.primary } as any}
                      >
                        <option value="general">General Inquiry</option>
                        <option value="order">Order Issues</option>
                        <option value="payment">Payment & Billing</option>
                        <option value="product">Product Information</option>
                        <option value="technical">Technical Support</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-bold uppercase tracking-wide text-gray-700">
                      Subject *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="Briefly describe your issue"
                      value={supportForm.subject}
                      onChange={(e) => setSupportForm({ ...supportForm, subject: e.target.value })}
                      className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:ring-2"
                      style={{ '--tw-ring-color': theme.primary } as any}
                    />
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-bold uppercase tracking-wide text-gray-700">
                      Description *
                    </label>
                    <textarea
                      required
                      rows={6}
                      placeholder="Tell us more about your problem..."
                      value={supportForm.description}
                      onChange={(e) =>
                        setSupportForm({ ...supportForm, description: e.target.value })
                      }
                      className="w-full resize-none rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:ring-2"
                      style={{ '--tw-ring-color': theme.primary } as any}
                    />
                  </div>

                  <div className="pt-4">
                    <button
                      type="submit"
                      className="flex w-full items-center justify-center gap-2 rounded-xl py-4 font-bold text-white shadow-lg transition-all active:scale-[0.98]"
                      style={{ backgroundColor: theme.primary }}
                    >
                      <svg
                        className="h-5 w-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                        />
                      </svg>
                      Send Ticket
                    </button>
                  </div>
                </form>
              </div>
            ) : (
              <div className="space-y-4">
                {loadingTickets ? (
                  <div className="flex justify-center p-12">
                    <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div>
                  </div>
                ) : tickets.length === 0 ? (
                  <div className="rounded-2xl border border-gray-100 bg-white px-6 py-20 text-center shadow-lg">
                    <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-gray-50">
                      <svg
                        className="h-10 w-10 text-gray-300"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                        />
                      </svg>
                    </div>
                    <h3 className="mb-2 text-xl font-bold text-gray-900">No queries yet</h3>
                    <p className="mx-auto mb-8 max-w-xs text-gray-500">
                      You haven&apos;t submitted any support queries to our team.
                    </p>
                    <button
                      onClick={() => setActiveTab('submit')}
                      className="rounded-xl bg-indigo-600 px-8 py-3 font-bold text-white shadow-lg shadow-indigo-200 transition-all hover:bg-indigo-700"
                    >
                      Submit a Query
                    </button>
                  </div>
                ) : (
                  tickets.map((ticket) => (
                    <div
                      key={ticket._id}
                      className={`overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm transition-all duration-300 ${expandedTicket === ticket._id ? 'ring-2' : ''}`}
                      style={{ '--tw-ring-color': theme.primary } as any}
                    >
                      <div
                        onClick={() =>
                          setExpandedTicket(expandedTicket === ticket._id ? null : ticket._id)
                        }
                        className="flex cursor-pointer flex-col justify-between gap-4 p-6 hover:bg-gray-50/50 md:flex-row md:items-center"
                      >
                        <div className="min-w-0 flex-1">
                          <div className="mb-1 flex items-center gap-3">
                            <span className="text-[10px] font-black uppercase tracking-widest text-indigo-500">
                              {ticket.ticketNumber}
                            </span>
                            <span
                              className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${
                                ticket.status === 'open'
                                  ? 'bg-green-50 text-green-700'
                                  : ticket.status === 'closed'
                                    ? 'bg-gray-100 text-gray-700'
                                    : 'bg-blue-50 text-blue-700'
                              }`}
                            >
                              {ticket.status.replace('_', ' ')}
                            </span>
                          </div>
                          <h3 className="truncate text-lg font-bold text-gray-900">
                            {ticket.subject}
                          </h3>
                          <p className="text-xs font-medium text-gray-400">
                            {formatDateTimeIST(ticket.createdAt)}
                          </p>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="hidden text-right md:block">
                            <p className="mb-1 text-[10px] font-bold uppercase tracking-wider text-gray-400">
                              Category
                            </p>
                            <p className="text-sm font-bold capitalize text-gray-700">
                              {ticket.category}
                            </p>
                          </div>
                          <div
                            className={`flex h-10 w-10 items-center justify-center rounded-full transition-all ${expandedTicket === ticket._id ? 'rotate-180 bg-gray-900 text-white' : 'bg-gray-100 text-gray-400'}`}
                          >
                            <svg
                              className="h-5 w-5"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth="2"
                                d="M19 9l-7 7-7-7"
                              />
                            </svg>
                          </div>
                        </div>
                      </div>

                      {expandedTicket === ticket._id && (
                        <div className="animate-fade-in p-6 pt-0">
                          <div className="mb-6 h-px w-full bg-gray-100" />

                          <div className="space-y-6">
                            <div>
                              <h4 className="mb-4 text-[10px] font-bold uppercase tracking-widest text-gray-400">
                                Original Description
                              </h4>
                              <div className="rounded-2xl border border-gray-100 bg-gray-50 p-6 text-sm leading-relaxed text-gray-700">
                                {ticket.description}
                              </div>
                            </div>

                            {ticket.responses && ticket.responses.length > 0 && (
                              <div>
                                <h4 className="mb-4 text-[10px] font-bold uppercase tracking-widest text-gray-400">
                                  Conversation History
                                </h4>
                                <div className="space-y-4">
                                  {ticket.responses.map((resp, i) => (
                                    <div
                                      key={i}
                                      className={`flex ${resp.isAdminResponse ? 'justify-start' : 'justify-end'}`}
                                    >
                                      <div
                                        className={`max-w-[85%] rounded-2xl p-4 ${resp.isAdminResponse ? 'border border-indigo-100 bg-indigo-50' : 'bg-gray-900 text-white shadow-lg'}`}
                                      >
                                        <div className="mb-2 flex items-center justify-between gap-8">
                                          <span className="text-[10px] font-bold uppercase tracking-wider opacity-60">
                                            {resp.isAdminResponse ? 'Support Team' : 'You'}
                                          </span>
                                          <span className="text-[9px] opacity-40">
                                            {formatTimeIST(resp.createdAt)}
                                          </span>
                                        </div>
                                        <p className="text-sm leading-relaxed">{resp.message}</p>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {ticket.status !== 'closed' && (
                              <form
                                onSubmit={async (e) => {
                                  e.preventDefault();
                                  const message = (e.target as any).message.value;
                                  if (!message.trim()) return;
                                  try {
                                    await api.post(`/support-tickets/${ticket._id}/response/`, {
                                      message,
                                    });
                                    toast.success('Reply sent successfully');
                                    (e.target as any).message.value = '';
                                    fetchTickets();
                                  } catch (_error) {
                                    toast.error('Failed to send reply');
                                  }
                                }}
                                className="mt-8 border-t border-gray-100 pt-6"
                              >
                                <label className="mb-4 block text-[10px] font-bold uppercase tracking-widest text-gray-400">
                                  Reply to this ticket
                                </label>
                                <div className="relative">
                                  <textarea
                                    name="message"
                                    required
                                    rows={3}
                                    placeholder="Type your message here..."
                                    className="w-full resize-none rounded-2xl border border-gray-100 bg-gray-50 px-5 py-4 pr-16 text-sm outline-none transition-all focus:ring-2"
                                    style={{ '--tw-ring-color': theme.primary } as any}
                                  />
                                  <button
                                    type="submit"
                                    className="absolute bottom-3 right-3 flex h-10 w-10 items-center justify-center rounded-xl text-white shadow-lg shadow-indigo-200 transition-all active:scale-90"
                                    style={{ backgroundColor: theme.primary }}
                                  >
                                    <svg
                                      className="h-5 w-5"
                                      fill="none"
                                      stroke="currentColor"
                                      viewBox="0 0 24 24"
                                    >
                                      <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth="2"
                                        d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                                      />
                                    </svg>
                                  </button>
                                </div>
                              </form>
                            )}

                            {ticket.status === 'closed' && (
                              <div className="mt-6 rounded-xl bg-gray-100 p-4 text-center">
                                <p className="text-xs font-bold uppercase tracking-wide text-gray-500">
                                  This ticket has been marked as closed.
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {/* Contact Info Sidebar */}
          <div className="space-y-8">
            {/* Welcome Card */}
            <div className="rounded-2xl border border-gray-50 bg-white p-6 shadow-lg">
              <h2 className="mb-4 text-2xl font-bold text-gray-900">
                How can we <span style={{ color: theme.primary }}>help you?</span>
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed">
                Our support team is always ready to assist you. Submit a ticket or reach out to us
                directly through any of our channels.
              </p>
            </div>

            {/* Quick Contact Cards */}
            <div className="rounded-2xl border border-gray-50 bg-white p-6 shadow-lg">
              <h3 className="mb-6 flex items-center gap-2 text-lg font-bold text-gray-900">
                <span className="h-6 w-2 rounded-full" style={{ backgroundColor: theme.primary }} />
                Contact Info
              </h3>

              <div className="space-y-6">
                {contacts.length === 0 ? (
                  <p className="text-sm italic text-gray-400">Contact info coming soon...</p>
                ) : (
                  contacts.map((contact) => (
                    <div key={contact._id} className="space-y-4">
                      <h4 className="font-bold" style={{ color: theme.primary }}>
                        {contact.name}
                      </h4>

                      {contact.phoneNumbers?.map((phone, i) => (
                        <div
                          key={i}
                          className="group flex cursor-pointer items-center gap-3 text-gray-600 transition-colors"
                        >
                          <div
                            className="flex h-8 w-8 items-center justify-center rounded-full transition-colors"
                            style={{ backgroundColor: `${theme.primary}15`, color: theme.primary }}
                          >
                            <svg
                              className="h-4 w-4"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth="2"
                                d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                              />
                            </svg>
                          </div>
                          <span
                            className="text-sm font-medium group-hover:text-[var(--primary)]"
                            style={{ '--primary': theme.primary } as any}
                          >
                            {phone}
                          </span>
                        </div>
                      ))}

                      {contact.addresses?.map((addr, i) => (
                        <div key={i} className="flex items-start gap-3 text-gray-600">
                          <div
                            className="mt-1 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full"
                            style={{ backgroundColor: `${theme.primary}15`, color: theme.primary }}
                          >
                            <svg
                              className="h-4 w-4"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth="2"
                                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                              />
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth="2"
                                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                              />
                            </svg>
                          </div>
                          <div>
                            <p className="text-sm font-medium leading-relaxed">
                              {[addr.address, addr.city, addr.state].filter(Boolean).join(', ')}
                            </p>
                            {addr.googleLocation && (
                              <a
                                href={addr.googleLocation}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="mt-1 block text-xs font-bold hover:underline"
                                style={{ color: theme.primary }}
                              >
                                VIEW ON MAP
                              </a>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ))
                )}

                <div className="border-t pt-6">
                  <h4 className="mb-4 text-xs font-bold uppercase tracking-widest text-gray-400">
                    Social Media
                  </h4>
                  <div className="flex gap-4">
                    <a
                      href={
                        contacts.find((c) => c.socialMedia?.instagram)?.socialMedia?.instagram ||
                        'https://www.instagram.com/stationeryjunction_jamshedpur'
                      }
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex h-10 w-10 items-center justify-center rounded-full bg-pink-50 text-pink-600 shadow-sm transition-all hover:bg-pink-600 hover:text-white"
                    >
                      <svg
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect>
                        <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
                        <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line>
                      </svg>
                    </a>
                  </div>
                </div>
              </div>
            </div>

            {/* Support Hours */}
            <div className="rounded-2xl border border-gray-50 bg-white p-6 shadow-lg">
              <h3 className="mb-6 flex items-center gap-2 text-lg font-bold text-gray-900">
                <span className="h-6 w-2 rounded-full" style={{ backgroundColor: theme.primary }} />
                Support Hours
              </h3>
              <div className="space-y-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 font-medium">Mon - Sat</span>
                  <span className="font-bold" style={{ color: theme.primary }}>
                    10:00 AM - 08:00 PM
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 font-medium">Sunday</span>
                  <span className="font-bold text-gray-500">
                    Closed
                  </span>
                </div>
              </div>
              <div className="mt-6 rounded-xl border border-gray-100 bg-gray-50 p-4 text-xs italic leading-relaxed text-gray-500">
                Tickets submitted outside hours will be processed on the next business day.
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
