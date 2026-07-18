'use client';

import { useState, useEffect, useMemo } from 'react';
import { useAuth } from '@/context/AuthContext';
import api from '@/utils/api';
import InfoButton from '@/components/InfoButton';
import { formatDateIST } from '@/utils/dateUtils';
import { toast } from 'react-toastify';
import RefreshButton from '@/components/Admin/RefreshButton';

export default function UserManagement() {
  const { user } = useAuth();
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [sortColumn, setSortColumn] = useState<string>('');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [pageInfo, setPageInfo] = useState<{
    page: { title?: string; description?: string } | null;
    columns: Record<string, string>;
  }>({ page: null, columns: {} });

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  const renderSortIcon = (column: string) => {
    if (sortColumn !== column) {
      return <span className="text-gray-300 ml-1 select-none">⇅</span>;
    }
    return sortDirection === 'asc' ? (
      <span className="text-indigo-600 ml-1 select-none">▲</span>
    ) : (
      <span className="text-indigo-600 ml-1 select-none">▼</span>
    );
  };

  useEffect(() => {
    if (user?.role === 'super_admin') {
      fetchUsers();
      fetchPageInfo();
    }
  }, [user]);

  const fetchPageInfo = async () => {
    try {
      const response = await api.get('/page-info/user-management');
      setPageInfo(response.data);
    } catch (error) {
      console.error('Failed to fetch page info:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await api.get('/users');
      setUsers(response.data || []);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch users', error);
      setLoading(false);
    }
  };

  const filteredUsers = useMemo(() => {
    return users.filter((userItem) => {
      const matchesSearch =
        userItem.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        userItem.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        userItem.phone?.includes(searchTerm) ||
        (userItem.userId || userItem._id || userItem.id)?.toString().includes(searchTerm);

      const matchesRole = roleFilter === 'all' || userItem.role === roleFilter;
      const matchesStatus =
        statusFilter === 'all' ||
        (statusFilter === 'active' && userItem.isActive) ||
        (statusFilter === 'inactive' && !userItem.isActive);

      return matchesSearch && matchesRole && matchesStatus;
    });
  }, [users, searchTerm, roleFilter, statusFilter]);

  const totalItems = filteredUsers.length;
  
  const sortedUsers = useMemo(() => {
    if (!sortColumn) return filteredUsers;
    return [...filteredUsers].sort((a, b) => {
      let valA: any = '';
      let valB: any = '';

      if (sortColumn === 'userId' || sortColumn === 'id' || sortColumn === '_id') {
        valA = a.userIdFormatted || `USER-${a.userId}` || a._id || a.id || '';
        valB = b.userIdFormatted || `USER-${b.userId}` || b._id || b.id || '';
      } else if (sortColumn === 'registrationDate' || sortColumn === 'createdAt') {
        valA = a.createdAt || '';
        valB = b.createdAt || '';
      } else if (sortColumn === 'company' || sortColumn === 'companyName') {
        valA = a.companyName || '';
        valB = b.companyName || '';
      } else {
        valA = a[sortColumn] ?? '';
        valB = b[sortColumn] ?? '';
      }

      if (typeof valA === 'string' && typeof valB === 'string') {
        return sortDirection === 'asc'
          ? valA.localeCompare(valB)
          : valB.localeCompare(valA);
      }

      if (typeof valA === 'number' && typeof valB === 'number') {
        return sortDirection === 'asc' ? valA - valB : valB - valA;
      }

      if (typeof valA === 'boolean' && typeof valB === 'boolean') {
        return sortDirection === 'asc'
          ? (valA === valB ? 0 : valA ? 1 : -1)
          : (valA === valB ? 0 : valA ? -1 : 1);
      }

      return sortDirection === 'asc'
        ? (valA > valB ? 1 : -1)
        : (valA < valB ? 1 : -1);
    });
  }, [filteredUsers, sortColumn, sortDirection]);

  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
  const paginatedUsers = sortedUsers.slice(startIndex, endIndex);

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

  const handleUpdateRole = async (userId: string, newRole: string) => {
    try {
      await api.put(`/users/${userId}/role`, { role: newRole, approvalStatus: 'approved' });
      toast.success('Role updated successfully');
      fetchUsers();
    } catch (error: any) {
      const errorMsg =
        error.response?.data?.message || error.response?.data?.detail || 'Failed to update role';
      toast.error(errorMsg);
    }
  };

  const handleUpdatePaymentTerms = async (userId: string, terms: number) => {
    try {
      await api.put(`/users/${userId}`, { paymentTerms: terms });
      toast.success('Payment terms updated successfully');
      fetchUsers();
    } catch (error: any) {
      const errorMsg =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        'Failed to update payment terms';
      toast.error(errorMsg);
    }
  };

  const getRoleBadgeClass = (role: string) => {
    switch (role) {
      case 'super_admin':
        return 'px-2 py-1 rounded text-xs bg-purple-100 text-purple-800';
      case 'wholesaler':
        return 'px-2 py-1 rounded text-xs bg-blue-100 text-blue-800';
      case 'customer':
        return 'px-2 py-1 rounded text-xs bg-gray-100 text-gray-800';
      case 'valet':
        return 'px-2 py-1 rounded text-xs bg-yellow-100 text-yellow-800';
      default:
        return 'px-2 py-1 rounded text-xs bg-gray-100 text-gray-800';
    }
  };

  const getDisplayRole = (role: string) => {
    const roleMap: { [key: string]: string } = {
      super_admin: 'Super Admin',
      wholesaler: 'Business Customer',
      customer: 'Retail Customer',
      valet: 'Delivery Valet',
    };
    return roleMap[role] || role;
  };

  if (user?.role !== 'super_admin') {
    return <div>Access Denied</div>;
  }

  if (loading)
    return (
      <div className="min-h-screen">
        <div>Loading...</div>
      </div>
    );

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="h-full flex flex-col min-h-0">
        <div className="rounded-lg bg-white p-6 shadow h-full flex flex-col min-h-0">
          <div className="mb-6 flex items-center justify-between">
            <h1 className="inline-flex items-center gap-3 text-3xl font-bold">
              <InfoButton
                info={
                  user?.role === 'super_admin' && pageInfo.page?.description
                    ? pageInfo.page.description
                    : undefined
                }
              >
                Individual Users
              </InfoButton>
              <RefreshButton onRefresh={fetchUsers} />
            </h1>
          </div>

          {/* Search and Filters */}
          <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3 flex-shrink-0">
            <div>
              <input
                type="text"
                placeholder="Search by name, email, phone, or ID"
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full rounded border border-gray-300 px-3 py-2"
              />
            </div>
            <div>
              <select
                value={roleFilter}
                onChange={(e) => {
                  setRoleFilter(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full rounded border border-gray-300 px-3 py-2"
              >
                <option value="all">All Roles</option>
                <option value="customer">Retail Customer</option>
                <option value="wholesaler">Business Customer</option>
                <option value="valet">Delivery Valet</option>
              </select>
            </div>
            <div>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full rounded border border-gray-300 px-3 py-2"
              >
                <option value="all">All Status</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
          </div>

          <div className="overflow-x-auto flex-1 min-h-0 border rounded border-gray-200">
            <table className="w-full border-collapse">
              <thead className="sticky top-0 z-10 bg-gray-50 shadow-sm">
                <tr className="bg-gray-50">
                  <th className="border border-gray-200 p-2 text-left">
                    <div className="flex items-center gap-1">
                      <span
                        onClick={() => handleSort('userId')}
                        className="inline-flex cursor-pointer items-center gap-0.5 hover:text-gray-700"
                      >
                        <InfoButton
                          info={
                            user?.role === 'super_admin' && pageInfo.columns?.userId
                              ? pageInfo.columns.userId
                              : undefined
                          }
                        >
                          User ID
                        </InfoButton>
                        {renderSortIcon('userId')}
                      </span>
                    </div>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <div className="flex items-center gap-1">
                      <span
                        onClick={() => handleSort('name')}
                        className="inline-flex cursor-pointer items-center gap-0.5 hover:text-gray-700"
                      >
                        <InfoButton
                          info={
                            user?.role === 'super_admin' && pageInfo.columns?.name
                              ? pageInfo.columns.name
                              : undefined
                          }
                        >
                          Name
                        </InfoButton>
                        {renderSortIcon('name')}
                      </span>
                    </div>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <div className="flex items-center gap-1">
                      <span
                        onClick={() => handleSort('email')}
                        className="inline-flex cursor-pointer items-center gap-0.5 hover:text-gray-700"
                      >
                        <InfoButton
                          info={
                            user?.role === 'super_admin' && pageInfo.columns?.email
                              ? pageInfo.columns.email
                              : undefined
                          }
                        >
                          Email
                        </InfoButton>
                        {renderSortIcon('email')}
                      </span>
                    </div>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <div className="flex items-center gap-1">
                      <span
                        onClick={() => handleSort('phone')}
                        className="inline-flex cursor-pointer items-center gap-0.5 hover:text-gray-700"
                      >
                        <InfoButton
                          info={
                            user?.role === 'super_admin' && pageInfo.columns?.phone
                              ? pageInfo.columns.phone
                              : undefined
                          }
                        >
                          Phone
                        </InfoButton>
                        {renderSortIcon('phone')}
                      </span>
                    </div>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <div className="flex items-center gap-1">
                      <span
                        onClick={() => handleSort('role')}
                        className="inline-flex cursor-pointer items-center gap-0.5 hover:text-gray-700"
                      >
                        <InfoButton
                          info={
                            user?.role === 'super_admin' && pageInfo.columns?.role
                              ? pageInfo.columns.role
                              : undefined
                          }
                        >
                          Role
                        </InfoButton>
                        {renderSortIcon('role')}
                      </span>
                    </div>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <div className="flex items-center gap-1">
                      <span
                        onClick={() => handleSort('registrationDate')}
                        className="inline-flex cursor-pointer items-center gap-0.5 hover:text-gray-700"
                      >
                        <InfoButton
                          info={
                            user?.role === 'super_admin' && pageInfo.columns?.registrationDate
                              ? pageInfo.columns.registrationDate
                              : undefined
                          }
                        >
                          Registration Date
                        </InfoButton>
                        {renderSortIcon('registrationDate')}
                      </span>
                    </div>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <div className="flex items-center gap-1">
                      <span
                        onClick={() => handleSort('company')}
                        className="inline-flex cursor-pointer items-center gap-0.5 hover:text-gray-700"
                      >
                        <InfoButton
                          info={
                            user?.role === 'super_admin' && pageInfo.columns?.company
                              ? pageInfo.columns.company
                              : undefined
                          }
                        >
                          Business Info
                        </InfoButton>
                        {renderSortIcon('company')}
                      </span>
                    </div>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <div className="flex items-center gap-1">
                      <span
                        onClick={() => handleSort('creditUsed')}
                        className="inline-flex cursor-pointer items-center gap-0.5 hover:text-gray-700"
                      >
                        <InfoButton
                          info={
                            user?.role === 'super_admin' && pageInfo.columns?.creditUsed
                              ? pageInfo.columns.creditUsed
                              : undefined
                          }
                        >
                          Credit Used
                        </InfoButton>
                        {renderSortIcon('creditUsed')}
                      </span>
                    </div>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <span
                      onClick={() => handleSort('paymentTerms')}
                      className="inline-flex cursor-pointer items-center gap-0.5 hover:text-gray-700"
                    >
                      Payment Terms {renderSortIcon('paymentTerms')}
                    </span>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <div className="flex items-center gap-1">
                      <span
                        onClick={() => handleSort('isActive')}
                        className="inline-flex cursor-pointer items-center gap-0.5 hover:text-gray-700"
                      >
                        <InfoButton
                          info={
                            user?.role === 'super_admin' && pageInfo.columns?.status
                              ? pageInfo.columns.status
                              : undefined
                          }
                        >
                          Status
                        </InfoButton>
                        {renderSortIcon('isActive')}
                      </span>
                    </div>
                  </th>
                  <th className="border border-gray-200 p-2 text-left">
                    <div className="flex items-center gap-1">
                      <InfoButton
                        info={
                          user?.role === 'super_admin' && pageInfo.columns?.actions
                            ? pageInfo.columns.actions
                            : undefined
                        }
                      >
                        Actions
                      </InfoButton>
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody>
                {paginatedUsers.length > 0 ? (
                  paginatedUsers.map((userItem: any) => (
                    <tr key={userItem._id || userItem.id} className="hover:bg-gray-50">
                      <td className="border border-gray-200 p-2">
                        {userItem.userIdFormatted ||
                          `USER-${userItem.userId}` ||
                          userItem._id ||
                          userItem.id ||
                          '-'}
                      </td>
                      <td className="border border-gray-200 p-2">{userItem.name}</td>
                      <td className="border border-gray-200 p-2">{userItem.email}</td>
                      <td className="border border-gray-200 p-2">{userItem.phone || '-'}</td>
                      <td className="border border-gray-200 p-2">
                        <span className={getRoleBadgeClass(userItem.role)}>
                          {getDisplayRole(userItem.role)}
                        </span>
                      </td>
                      <td className="border border-gray-200 p-2">
                        {userItem.createdAt ? formatDateIST(userItem.createdAt) : '-'}
                      </td>
                      <td className="border border-gray-200 p-2">
                        {userItem.companyName || '-'}
                        {userItem.gstin && (
                          <div className="mt-1 text-xs text-gray-500">GST: {userItem.gstin}</div>
                        )}
                      </td>
                      <td className="border border-gray-200 p-2">
                        {userItem.role === 'wholesaler'
                          ? `₹${(userItem.creditUsed || 0).toFixed(2)}`
                          : '-'}
                      </td>
                      <td className="border border-gray-200 p-2">
                        {userItem.role === 'wholesaler' ? (
                          <select
                            value={userItem.paymentTerms || 30}
                            onChange={(e) =>
                              handleUpdatePaymentTerms(
                                userItem._id || userItem.id,
                                parseInt(e.target.value)
                              )
                            }
                            className="rounded border border-gray-300 bg-white px-2 py-1 text-sm"
                          >
                            {[7, 15, 30, 45, 60, 90, 120].map((days) => (
                              <option key={days} value={days}>
                                {days} Days
                              </option>
                            ))}
                          </select>
                        ) : (
                          '-'
                        )}
                      </td>
                      <td className="border border-gray-200 p-2">
                        <span
                          className={`rounded px-2 py-1 text-xs ${
                            userItem.isActive
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {userItem.isActive ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="border border-gray-200 p-2">
                        {userItem.role !== 'super_admin' && (
                          <select
                            value={userItem.role}
                            onChange={(e) =>
                              handleUpdateRole(userItem._id || userItem.id, e.target.value)
                            }
                            className="rounded border border-gray-300 bg-white px-3 py-2 text-gray-900"
                            style={{
                              minWidth: '200px',
                              cursor: 'pointer',
                            }}
                          >
                            <option value="customer">Retail Customer</option>
                            <option value="wholesaler">Business Customer</option>
                            <option value="valet">Delivery Valet</option>
                          </select>
                        )}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td
                      colSpan={10}
                      className="border border-gray-200 p-4 text-center text-gray-600"
                    >
                      No users found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Premium Pagination Controls */}
          {filteredUsers.length > 0 && (
            <div className="mt-4 flex flex-shrink-0 flex-col items-center justify-between gap-4 border-t border-gray-200 pt-4 sm:flex-row">
              <div className="text-sm text-gray-700">
                Showing <span className="font-semibold">{totalItems === 0 ? 0 : startIndex + 1}</span> to{' '}
                <span className="font-semibold">{endIndex}</span> of{' '}
                <span className="font-semibold">{totalItems}</span> users
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
    </div>
  );
}
