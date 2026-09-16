import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Linking,
  TouchableOpacity,
  ScrollView,
  TextInput,
  ActivityIndicator,
  Animated,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, typography } from '../src/theme';
import api from '../src/api/client';
import { useAuth } from '../src/hooks/useAuth';
import { formatDateTimeIST, formatTimeIST } from '../src/utils/dateUtils';
import Toast from 'react-native-toast-message';
import SearchablePicker from '../src/components/SearchablePicker';

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

interface Ticket {
  _id: string;
  ticketNumber: string;
  subject: string;
  description: string;
  category: string;
  status: string;
  createdAt: string;
  responses?: Array<{
    user: { name: string; email: string; role: string };
    message: string;
    createdAt: string;
    isAdminResponse: boolean;
  }>;
}

interface User {
  name?: string;
  email?: string;
  companyName?: string;
  phone?: string;
}

const CATEGORY_MAP: Record<string, string> = {
  'General Inquiry': 'general',
  'Order Issues': 'order',
  'Payment & Billing': 'payment',
  'Product Information': 'product',
  'Technical Support': 'technical',
};

const REVERSE_CATEGORY_MAP: Record<string, string> = {
  general: 'General Inquiry',
  order: 'Order Issues',
  payment: 'Payment & Billing',
  product: 'Product Information',
  technical: 'Technical Support',
};

const CATEGORY_OPTIONS = Object.keys(CATEGORY_MAP);

export default function Support() {
  const router = useRouter();
  const { user } = useAuth() as { user: User | null };
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loadingContacts, setLoadingContacts] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    name: '',
    company: '',
    email: '',
    phone: '',
    subject: '',
    description: '',
    category: 'general',
  });
  const [activeTab, setActiveTab] = useState<'submit' | 'history'>('submit');
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loadingTickets, setLoadingTickets] = useState(false);
  const [ticketError, setTicketError] = useState(false);
  const [expandedTicket, setExpandedTicket] = useState<string | null>(null);
  const [replyText, setReplyText] = useState('');
  const [submittingReply, setSubmittingReply] = useState(false);
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    fetchContacts();
    if (user) {
      fetchTickets();
    }
  }, [user]);

  useEffect(() => {
    Animated.timing(fadeAnim, { toValue: 1, duration: 280, useNativeDriver: true }).start();
  }, [fadeAnim]);

  useEffect(() => {
    if (user) {
      setForm((prev) => ({
        ...prev,
        name: user.name || prev.name,
        company: user.companyName || prev.company,
        email: user.email || prev.email,
        phone: user.phone || prev.phone,
      }));
    }
  }, [user]);

  const fetchContacts = async () => {
    try {
      const res = await api.get('/contacts/public');
      setContacts(res.data || []);
    } catch (e) {
      setContacts([]);
    } finally {
      setLoadingContacts(false);
    }
  };

  const fetchTickets = async () => {
    if (!user) return;
    try {
      setLoadingTickets(true);
      setTicketError(false);
      const res = await api.get('/support-tickets');
      setTickets(res.data || []);
    } catch {
      setTicketError(true);
    } finally {
      setLoadingTickets(false);
    }
  };

  const submitSupport = async () => {
    if (!form.name || !form.email || !form.phone || !form.subject || !form.description) {
      Toast.show({
        type: 'error',
        text1: 'Missing info',
        text2: 'Please fill all required fields.',
      });
      return;
    }
    try {
      setSubmitting(true);
      const config = !user ? ({ skipAccessToken: true } as any) : undefined;
      await api.post('/support-tickets', {
        name: form.name,
        company: form.company,
        email: form.email,
        phone: form.phone,
        subject: form.subject,
        description: form.description,
        category: form.category,
        priority: 'medium',
      }, config);
      Toast.show({
        type: 'success',
        text1: 'Submitted',
        text2: 'Support query submitted successfully',
      });
      fetchTickets();
      setForm({
        name: user?.name || '',
        company: user?.companyName || '',
        email: user?.email || '',
        phone: user?.phone || '',
        subject: '',
        description: '',
        category: 'general',
      });
    } catch (e: any) {
      Toast.show({
        type: 'error',
        text1: 'Error',
        text2: e?.response?.data?.message || 'Failed to submit query',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const submitReply = async (ticketId: string) => {
    if (!replyText.trim()) return;
    try {
      setSubmittingReply(true);
      await api.post(`/support-tickets/${ticketId}/response`, {
        message: replyText,
      });
      Toast.show({
        type: 'success',
        text1: 'Reply sent',
        text2: 'Your response has been added to the ticket.',
      });
      setReplyText('');
      fetchTickets();
    } catch (err: any) {
      Toast.show({
        type: 'error',
        text1: 'Error',
        text2: err?.response?.data?.message || 'Failed to send reply',
      });
    } finally {
      setSubmittingReply(false);
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.background }}>
      {/* Header with Back Button */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={22} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Customer Support</Text>
      </View>

      <ScrollView contentContainerStyle={styles.container}>
        <Animated.View style={[styles.hero, { opacity: fadeAnim }]}>
          <Text style={styles.subtitle}>
            We're here to help with orders, returns, and anything in between.
          </Text>
        </Animated.View>

        {user && (
          <View style={styles.tabsContainer}>
            <TouchableOpacity
              style={[styles.tab, activeTab === 'submit' && styles.activeTab]}
              onPress={() => setActiveTab('submit')}
            >
              <Text style={[styles.tabText, activeTab === 'submit' && styles.activeTabText]}>
                Submit Query
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.tab, activeTab === 'history' && styles.activeTab]}
              onPress={() => setActiveTab('history')}
            >
              <Text style={[styles.tabText, activeTab === 'history' && styles.activeTabText]}>
                My Queries
              </Text>
            </TouchableOpacity>
          </View>
        )}

        {contacts.length > 0 && (
          <Animated.View style={[styles.quickRow, { opacity: fadeAnim }]}>
            {contacts[0]?.phoneNumbers?.[0] && (
              <TouchableOpacity
                style={styles.quickBtn}
                onPress={() => Linking.openURL(`tel:${contacts[0].phoneNumbers?.[0]}`)}
              >
                <Text style={styles.quickText}>Call Us</Text>
                <Text style={styles.quickMeta}>{contacts[0].phoneNumbers[0]}</Text>
              </TouchableOpacity>
            )}
            {contacts[0]?.email && (
              <TouchableOpacity
                style={styles.quickBtn}
                onPress={() => Linking.openURL(`mailto:${contacts[0].email}`)}
              >
                <Text style={styles.quickText}>Email Us</Text>
                <Text style={styles.quickMeta}>{contacts[0].email}</Text>
              </TouchableOpacity>
            )}
          </Animated.View>
        )}

        {activeTab === 'submit' ? (
          <Animated.View style={[styles.card, { opacity: fadeAnim }]}>
            <Text style={styles.cardTitle}>Submit Your Query</Text>
            <View style={styles.row}>
              <View style={styles.half}>
                <Text style={styles.label}>Name *</Text>
                <TextInput
                  style={styles.input}
                  value={form.name}
                  onChangeText={(t) => setForm({ ...form, name: t })}
                />
              </View>
              <View style={styles.half}>
                <Text style={styles.label}>Company</Text>
                <TextInput
                  style={styles.input}
                  value={form.company}
                  onChangeText={(t) => setForm({ ...form, company: t })}
                />
              </View>
            </View>
            <View style={styles.row}>
              <View style={styles.half}>
                <Text style={styles.label}>Email *</Text>
                <TextInput
                  style={styles.input}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  value={form.email}
                  onChangeText={(t) => setForm({ ...form, email: t })}
                />
              </View>
              <View style={styles.half}>
                <Text style={styles.label}>Phone *</Text>
                <TextInput
                  style={styles.input}
                  keyboardType="phone-pad"
                  value={form.phone}
                  onChangeText={(t) => setForm({ ...form, phone: t })}
                />
              </View>
            </View>
            <SearchablePicker
              label="Category *"
              options={CATEGORY_OPTIONS}
              value={REVERSE_CATEGORY_MAP[form.category] || 'General Inquiry'}
              onChange={(label) => {
                const key = CATEGORY_MAP[label] || 'general';
                setForm((prev) => ({ ...prev, category: key }));
              }}
              placeholder="Select Category"
              icon="grid-outline"
            />
            <Text style={styles.label}>Subject *</Text>
            <TextInput
              style={styles.input}
              value={form.subject}
              onChangeText={(t) => setForm({ ...form, subject: t })}
            />
            <Text style={styles.label}>Description of Query *</Text>
            <TextInput
              style={[styles.input, { height: 120, textAlignVertical: 'top' }]}
              multiline
              value={form.description}
              onChangeText={(t) => setForm({ ...form, description: t })}
            />
            <TouchableOpacity
              style={styles.primaryBtn}
              onPress={submitSupport}
              disabled={submitting}
            >
              {submitting ? (
                <ActivityIndicator color={colors.textOnPrimary} />
              ) : (
                <Text style={styles.primaryText}>Submit Query</Text>
              )}
            </TouchableOpacity>
          </Animated.View>
        ) : (
          <Animated.View
            style={[
              styles.card,
              {
                opacity: fadeAnim,
                padding: 0,
                backgroundColor: 'transparent',
                shadowOpacity: 0,
                elevation: 0,
              },
            ]}
          >
            {loadingTickets ? (
              <ActivityIndicator color={colors.primary} style={{ marginTop: 20 }} />
            ) : ticketError ? (
              <View style={[styles.card, { alignItems: 'center', paddingVertical: 40 }]}>
                <Ionicons name="cloud-offline-outline" size={48} color={colors.neutral[300]} />
                <Text style={[styles.text, { marginTop: 12, textAlign: 'center' }]}>
                  Could not load support history.
                </Text>
                <TouchableOpacity
                  style={[styles.primaryBtn, { paddingHorizontal: 32, marginTop: 16 }]}
                  onPress={fetchTickets}
                >
                  <Text style={styles.primaryText}>Retry</Text>
                </TouchableOpacity>
              </View>
            ) : tickets.length === 0 ? (
              <View style={[styles.card, { alignItems: 'center', paddingVertical: 40 }]}>
                <Ionicons name="chatbox-ellipses-outline" size={48} color={colors.neutral[300]} />
                <Text style={[styles.text, { marginTop: 12, textAlign: 'center' }]}>
                  You haven't submitted any queries yet.
                </Text>
                <TouchableOpacity
                  style={[styles.primaryBtn, { paddingHorizontal: 32 }]}
                  onPress={() => setActiveTab('submit')}
                >
                  <Text style={styles.primaryText}>Submit a Query</Text>
                </TouchableOpacity>
              </View>
            ) : (
              tickets.map((ticket) => (
                <View key={ticket._id} style={[styles.card, { marginBottom: 12 }]}>
                  <TouchableOpacity
                    onPress={() => {
                      setExpandedTicket(expandedTicket === ticket._id ? null : ticket._id);
                      setReplyText('');
                    }}
                    style={styles.ticketHeader}
                  >
                    <View style={{ flex: 1 }}>
                      <View style={styles.ticketMeta}>
                        <Text style={styles.ticketNumber}>{ticket.ticketNumber}</Text>
                        <View
                          style={[
                            styles.statusBadge,
                            { backgroundColor: getStatusColor(ticket.status) + '20' },
                          ]}
                        >
                          <Text
                            style={[styles.statusText, { color: getStatusColor(ticket.status) }]}
                          >
                            {ticket.status.replace('_', ' ').toUpperCase()}
                          </Text>
                        </View>
                        {ticket.category && (
                          <View style={styles.categoryBadge}>
                            <Text style={styles.categoryBadgeText}>
                              {REVERSE_CATEGORY_MAP[ticket.category] || ticket.category}
                            </Text>
                          </View>
                        )}
                      </View>
                      <Text style={styles.ticketSubject}>{ticket.subject}</Text>
                      <Text style={styles.ticketDate}>{formatDateTimeIST(ticket.createdAt)}</Text>
                    </View>
                    <Ionicons
                      name={expandedTicket === ticket._id ? 'chevron-up' : 'chevron-down'}
                      size={20}
                      color={colors.neutral[400]}
                    />
                  </TouchableOpacity>

                  {expandedTicket === ticket._id && (
                    <View style={styles.ticketDetails}>
                      <View style={styles.divider} />
                      <Text style={styles.sectionLabel}>Your Description:</Text>
                      <Text style={styles.descriptionText}>{ticket.description}</Text>

                      {ticket.responses && ticket.responses.length > 0 && (
                        <View style={{ marginTop: 16 }}>
                          <Text style={styles.sectionLabel}>Conversation:</Text>
                          {ticket.responses.map((resp, idx) => (
                            <View
                              key={idx}
                              style={[
                                styles.responseBubble,
                                resp.isAdminResponse ? styles.adminResponse : styles.userResponse,
                              ]}
                            >
                              <View style={styles.responseHeader}>
                                <Text style={styles.responseUser}>
                                  {resp.isAdminResponse ? 'Support Team' : 'You'}
                                </Text>
                                <Text style={styles.responseTime}>
                                  {formatTimeIST(resp.createdAt)}
                                </Text>
                              </View>
                              <Text style={styles.responseMessage}>{resp.message}</Text>
                            </View>
                          ))}
                        </View>
                      )}

                      {ticket.status !== 'closed' && (
                        <View style={styles.replyFormContainer}>
                          <View style={styles.divider} />
                          <Text style={styles.sectionLabel}>Reply to this ticket</Text>
                          <View style={styles.replyInputRow}>
                            <TextInput
                              style={styles.replyInput}
                              placeholder="Type your message here..."
                              placeholderTextColor={colors.textMuted}
                              value={replyText}
                              onChangeText={setReplyText}
                              multiline
                            />
                            <TouchableOpacity
                              style={styles.replySendBtn}
                              onPress={() => submitReply(ticket._id)}
                              disabled={submittingReply || !replyText.trim()}
                            >
                              {submittingReply ? (
                                <ActivityIndicator size="small" color={colors.surface} />
                              ) : (
                                <Ionicons name="send" size={18} color={colors.surface} />
                              )}
                            </TouchableOpacity>
                          </View>
                        </View>
                      )}
                    </View>
                  )}
                </View>
              ))
            )}
          </Animated.View>
        )}

        <Animated.View style={[styles.card, { opacity: fadeAnim }]}>
          <Text style={styles.cardTitle}>Contact Us</Text>
          {loadingContacts ? (
            <View style={styles.loader}>
              <ActivityIndicator size="small" color={colors.primary} />
            </View>
          ) : contacts.length === 0 ? (
            <Text style={styles.text}>No contact information available.</Text>
          ) : (
            contacts.map((c) => (
              <View key={c._id} style={styles.contactCard}>
                <Text style={styles.contactName}>{c.name}</Text>
                {c.phoneNumbers?.length ? (
                  <View style={styles.contactBlock}>
                    <Text style={styles.contactLabel}>Phone</Text>
                    {c.phoneNumbers.map((p, idx) => {
                      if (!p) return null;
                      return (
                        <TouchableOpacity key={idx} onPress={() => Linking.openURL(`tel:${p}`)}>
                          <Text style={styles.contactValue}>{p}</Text>
                        </TouchableOpacity>
                      );
                    })}
                  </View>
                ) : null}
                {c.email ? (
                  <View style={styles.contactBlock}>
                    <Text style={styles.contactLabel}>Email</Text>
                    <TouchableOpacity onPress={() => Linking.openURL(`mailto:${c.email}`)}>
                      <Text style={styles.contactValue}>{c.email}</Text>
                    </TouchableOpacity>
                  </View>
                ) : null}
                {c.addresses?.length ? (
                  <View style={styles.contactBlock}>
                    <Text style={styles.contactLabel}>Address</Text>
                    {c.addresses.map((a, idx) => (
                      <View key={idx} style={{ marginTop: 2 }}>
                        <Text style={styles.contactValue}>
                          {[a.address, a.city, a.district, a.state].filter(Boolean).join(', ')}
                          {a.zipCode ? ` - ${a.zipCode}` : ''}
                        </Text>
                        {a.googleLocation ? (
                          <TouchableOpacity
                            onPress={() => a.googleLocation && Linking.openURL(a.googleLocation)}
                          >
                            <Text style={styles.mapLink}>Open in Google Maps</Text>
                          </TouchableOpacity>
                        ) : null}
                      </View>
                    ))}
                  </View>
                ) : null}
                {c.description ? <Text style={styles.contactDesc}>{c.description}</Text> : null}
                
                {/* Social Media links */}
                <View style={styles.socialContainer}>
                  <Text style={styles.socialLabel}>Social Media</Text>
                  <View style={styles.socialIcons}>
                    <TouchableOpacity
                      style={[styles.socialIconBtn, { backgroundColor: '#FDF2F8' }]}
                      onPress={() =>
                        Linking.openURL(
                          c.socialMedia?.instagram ||
                            'https://www.instagram.com/stationeryjunction_jamshedpur'
                        )
                      }
                    >
                      <Ionicons name="logo-instagram" size={20} color="#DB2777" />
                    </TouchableOpacity>
                    {c.socialMedia?.facebook ? (
                      <TouchableOpacity
                        style={[styles.socialIconBtn, { backgroundColor: '#EFF6FF' }]}
                        onPress={() => Linking.openURL(c.socialMedia?.facebook || '')}
                      >
                        <Ionicons name="logo-facebook" size={20} color="#2563EB" />
                      </TouchableOpacity>
                    ) : null}
                    {c.socialMedia?.twitter ? (
                      <TouchableOpacity
                        style={[styles.socialIconBtn, { backgroundColor: '#F8FAFC' }]}
                        onPress={() => Linking.openURL(c.socialMedia?.twitter || '')}
                      >
                        <Ionicons name="logo-twitter" size={20} color="#0F172A" />
                      </TouchableOpacity>
                    ) : null}
                    {c.socialMedia?.whatsapp ? (
                      <TouchableOpacity
                        style={[styles.socialIconBtn, { backgroundColor: '#ECFDF5' }]}
                        onPress={() => Linking.openURL(`https://wa.me/${c.socialMedia?.whatsapp}`)}
                      >
                        <Ionicons name="logo-whatsapp" size={20} color={colors.success} />
                      </TouchableOpacity>
                    ) : null}
                    {c.socialMedia?.youtube ? (
                      <TouchableOpacity
                        style={[styles.socialIconBtn, { backgroundColor: '#FEF2F2' }]}
                        onPress={() => Linking.openURL(c.socialMedia?.youtube || '')}
                      >
                        <Ionicons name="logo-youtube" size={20} color={colors.error} />
                      </TouchableOpacity>
                    ) : null}
                    {c.socialMedia?.linkedin ? (
                      <TouchableOpacity
                        style={[styles.socialIconBtn, { backgroundColor: '#F0F9FF' }]}
                        onPress={() => Linking.openURL(c.socialMedia?.linkedin || '')}
                      >
                        <Ionicons name="logo-linkedin" size={20} color="#0284C7" />
                      </TouchableOpacity>
                    ) : null}
                  </View>
                </View>
              </View>
            ))
          )}
        </Animated.View>
      </ScrollView>
    </SafeAreaView>
  );
}

const getStatusColor = (status: string = '') => {
  switch ((status || '').toLowerCase()) {
    case 'open':
      return colors.info;
    case 'in_progress':
      return colors.warning;
    case 'resolved':
      return colors.success;
    case 'closed':
      return '#8E8E93';
    default:
      return colors.neutral[500];
  }
};

const styles = StyleSheet.create({
  container: { flexGrow: 1, backgroundColor: colors.background, padding: spacing.md },
  hero: { marginBottom: spacing.sm },
  title: { ...typography.h2, marginBottom: spacing.xs, color: colors.textPrimary },
  subtitle: { ...typography.body, color: colors.textSecondary },
  quickRow: { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.md },
  quickBtn: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
    shadowColor: colors.textPrimary,
    shadowOpacity: 0.06,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  quickText: { ...typography.body, color: colors.textPrimary, fontWeight: '700' },
  quickMeta: { ...typography.caption, color: colors.textSecondary, marginTop: 2 },
  text: { ...typography.body, color: colors.textSecondary, marginBottom: spacing.xs },
  card: {
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: 12,
    marginBottom: spacing.md,
    shadowColor: colors.textPrimary,
    shadowOpacity: 0.08,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 3 },
    elevation: 3,
  },
  cardTitle: { ...typography.h3, color: colors.textPrimary, marginBottom: spacing.sm },
  row: { flexDirection: 'row', gap: spacing.sm },
  half: { flex: 1 },
  label: { ...typography.caption, color: colors.textSecondary, marginBottom: 4 },
  input: {
    backgroundColor: colors.background,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.sm,
    marginBottom: spacing.sm,
  },
  primaryBtn: {
    backgroundColor: colors.primary,
    padding: spacing.md,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: spacing.sm,
  },
  primaryText: { color: colors.textOnPrimary, fontWeight: '700' },
  loader: { paddingVertical: spacing.sm, alignItems: 'center' },
  contactCard: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    padding: spacing.sm,
    marginBottom: spacing.sm,
  },
  contactName: { ...typography.h3, color: colors.textPrimary, marginBottom: 4 },
  contactBlock: { marginTop: spacing.xs },
  contactLabel: { ...typography.caption, color: colors.textSecondary },
  contactValue: { ...typography.body, color: colors.textPrimary },
  contactDesc: { ...typography.body, color: colors.textSecondary, marginTop: spacing.xs },
  mapLink: { color: colors.primary, ...typography.caption },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    backgroundColor: colors.surface,
  },
  backBtn: { padding: spacing.xs, marginRight: spacing.sm, marginLeft: -spacing.xs },
  headerTitle: { ...typography.h3, color: colors.textPrimary },
  tabsContainer: {
    flexDirection: 'row',
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 4,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  tab: { flex: 1, paddingVertical: 10, alignItems: 'center', borderRadius: 10 },
  activeTab: { backgroundColor: colors.primary },
  tabText: { ...typography.bodySmall, fontWeight: '600', color: colors.textSecondary },
  activeTabText: { color: colors.surface },
  ticketHeader: { flexDirection: 'row', alignItems: 'center' },
  ticketMeta: { flexDirection: 'row', alignItems: 'center', marginBottom: 4, gap: 8 },
  ticketNumber: { ...typography.tiny, color: colors.primary, fontWeight: '700' },
  statusBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 4 },
  statusText: { fontSize: 10, fontWeight: '800' },
  ticketSubject: {
    ...typography.body,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: 2,
  },
  ticketDate: { ...typography.caption, color: colors.textMuted },
  ticketDetails: { marginTop: 12 },
  divider: { height: 1, backgroundColor: colors.border, marginBottom: 12 },
  sectionLabel: {
    ...typography.tiny,
    textTransform: 'uppercase',
    color: colors.textMuted,
    fontWeight: '700',
    marginBottom: 6,
  },
  descriptionText: { ...typography.bodySmall, color: colors.textSecondary, lineHeight: 20 },
  responseBubble: { padding: 12, borderRadius: 12, marginBottom: 8, maxWidth: '90%' },
  userResponse: {
    backgroundColor: colors.backgroundAlt,
    alignSelf: 'flex-end',
    borderBottomRightRadius: 4,
  },
  adminResponse: { backgroundColor: '#F0F7F4', alignSelf: 'flex-start', borderBottomLeftRadius: 4 },
  responseHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
    gap: 12,
  },
  responseUser: { fontSize: 11, fontWeight: '700', color: colors.textPrimary },
  responseTime: { fontSize: 10, color: colors.textMuted },
  responseMessage: { ...typography.bodySmall, color: colors.textPrimary, lineHeight: 18 },
  replyFormContainer: {
    marginTop: spacing.md,
  },
  replyInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginTop: spacing.xs,
  },
  replyInput: {
    flex: 1,
    backgroundColor: colors.background,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    minHeight: 50,
    maxHeight: 100,
    color: colors.textPrimary,
  },
  replySendBtn: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  categoryBadge: {
    backgroundColor: '#F1F5F9',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  categoryBadgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  socialContainer: {
    marginTop: spacing.md,
    paddingTop: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  socialLabel: {
    ...typography.caption,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  socialIcons: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  socialIconBtn: {
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: colors.textPrimary,
    shadowOpacity: 0.05,
    shadowRadius: 2,
    shadowOffset: { width: 0, height: 1 },
    elevation: 1,
  },
});
