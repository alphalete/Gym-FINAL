import React, { useState, useEffect } from 'react';
import { nextDueDateFromJoin, isOverdue } from './billing';
import { getDueSoonDays, formatMoney } from "./settings";
import { buildReminder, waLink } from "./reminders";

const Dashboard = () => {
  const [clients, setClients] = useState([]);
  const [stats, setStats] = useState({
    activeMembers: 0,
    overdueAccounts: 0,
    dueSoon: 0,
    totalRevenue: 0
  });
  const [loading, setLoading] = useState(true);

  // Get backend URL (same as existing system)
  const getBackendUrl = () => {
    return process.env.REACT_APP_BACKEND_URL || import.meta.env?.REACT_APP_BACKEND_URL || '';
  };

  // Get AST date (Atlantic Standard Time - same as existing system)
  const getASTDate = () => {
    const now = new Date();
    const utcTime = now.getTime() + (now.getTimezoneOffset() * 60000);
    const astOffset = -4; // AST is UTC-4
    return new Date(utcTime + (astOffset * 3600000));
  };

  // Get client payment status (same logic as existing system)
  const getClientPaymentStatus = (client) => {
    // Check if client has actually paid (amount_owed should be 0 or very small)
    if (client.amount_owed === 0 || client.amount_owed < 0.01) {
      return 'paid';
    }
    
    // If client owes money, check when their payment is due
    if (!client.next_payment_date) return 'overdue'; // No due date but owes money = overdue
    
    const today = getASTDate();
    today.setHours(0, 0, 0, 0);
    const paymentDate = new Date(client.next_payment_date);
    const daysDiff = Math.ceil((paymentDate - today) / (1000 * 60 * 60 * 24));
    
    if (daysDiff < 0) return 'overdue';    // Past due date
    if (daysDiff <= 7) return 'due-soon';  // Due within 7 days
    return 'due';                          // Due in the future
  };

  // Compute clients with billing info using the new billing logic
  const dueSoonDays = getDueSoonDays();
  const clientsWithBilling = clients.map(client => {
    const paymentStatus = getClientPaymentStatus(client);
    const dueDate = client.next_payment_date;
    const today = getASTDate();
    const due = dueDate ? new Date(dueDate) : null;
    const daysToDue = due ? Math.ceil((due - today) / (1000 * 60 * 60 * 24)) : null;
    
    let status = "Active";
    if (paymentStatus === 'overdue') {
      status = "Overdue";
    } else if (paymentStatus === 'due-soon' || (daysToDue !== null && daysToDue >= 0 && daysToDue <= dueSoonDays)) {
      status = "Due Soon";
    } else if (paymentStatus === 'paid') {
      status = "Paid";
    }
    
    return {
      ...client,
      _dueDate: dueDate,
      _status: status,
      _daysToDue: daysToDue,
      _paymentStatus: paymentStatus
    };
  });

  // Load data from API (same as existing system)
  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        const backendUrl = getBackendUrl();
        
        if (!backendUrl) {
          console.log('Dashboard: No backend URL configured');
          setLoading(false);
          return;
        }
        
        // Get clients and payment stats in parallel
        const [clientsResponse, paymentsResponse] = await Promise.all([
          fetch(`${backendUrl}/api/clients`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-cache' }
          }),
          fetch(`${backendUrl}/api/payments/stats`, {
            method: 'GET', 
            headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-cache' }
          })
        ]);
        
        if (clientsResponse.ok && paymentsResponse.ok) {
          const [clientsData, paymentStats] = await Promise.all([
            clientsResponse.json(),
            paymentsResponse.json()
          ]);
          
          setClients(clientsData);
          
          const activeClients = clientsData.filter(c => c.status === 'Active');
          const today = getASTDate();
          today.setHours(0, 0, 0, 0);
          
          // Calculate statistics using same logic as existing system
          const overdueCount = activeClients.filter(client => {
            if (client.amount_owed === 0 || client.amount_owed < 0.01) {
              return false; // Paid clients are not overdue
            }
            if (!client.next_payment_date) return true;
            const paymentDate = new Date(client.next_payment_date);
            return paymentDate < today;
          }).length;
          
          const dueSoonCount = activeClients.filter(client => {
            if (!client.next_payment_date) return false;
            const paymentDate = new Date(client.next_payment_date);
            const diffTime = paymentDate - today;
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            return diffDays >= 0 && diffDays <= getDueSoonDays();
          }).length;

          setStats({
            activeMembers: activeClients.length,
            overdueAccounts: overdueCount,
            dueSoon: dueSoonCount,
            totalRevenue: paymentStats.total_revenue || 0
          });
        }
      } catch (error) {
        console.error('Dashboard: Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case "Overdue":
        return "badge-danger";
      case "Due Soon":
        return "badge-warn";
      case "Paid":
        return "badge-success";
      case "Active":
        return "bg-blue-100 text-blue-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getDueDateColor = (daysToDue, status) => {
    if (status === "Overdue") return "text-red-600 font-semibold";
    if (daysToDue !== null && daysToDue <= getDueSoonDays()) return "text-orange-600 font-semibold";
    return "text-gray-600";
  };

  const formatDueDate = (dateStr, daysToDue, status) => {
    if (!dateStr) return "No due date";
    const date = new Date(dateStr);
    const formatted = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    
    if (status === "Overdue") {
      const overdueDays = Math.abs(daysToDue);
      return `${formatted} (${overdueDays} days overdue)`;
    } else if (daysToDue !== null && daysToDue <= 7 && daysToDue >= 0) {
      return `${formatted} (${daysToDue} days)`;
    }
    return formatted;
  };

  const handleWhatsApp = (client) => {
    const message = buildReminder({ 
      name: client.name, 
      dueISO: client._dueDate, 
      amount: client.amount_owed 
    });
    const phoneNumber = client.phone?.replace(/[^\d]/g, '') || '';
    if (phoneNumber) {
      const url = `https://wa.me/${phoneNumber}?text=${encodeURIComponent(message)}`;
      window.open(url, '_blank');
    } else {
      alert('No phone number available for this client.');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h1>
          <p className="text-gray-600">Member management overview</p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <h3 className="text-sm font-medium text-gray-500">Total Members</h3>
                <p className="text-2xl font-semibold text-gray-900">{stats.activeMembers}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-red-100 rounded-lg">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div className="ml-4">
                <h3 className="text-sm font-medium text-gray-500">Overdue</h3>
                <p className="text-2xl font-semibold text-red-600">{stats.overdueAccounts}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <h3 className="text-sm font-medium text-gray-500">Due Soon</h3>
                <p className="text-2xl font-semibold text-yellow-600">{stats.dueSoon}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
              <div className="ml-4">
                <h3 className="text-sm font-medium text-gray-500">Total Revenue</h3>
                <p className="text-2xl font-semibold text-brand-600">{formatMoney(stats.totalRevenue)}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Desktop Table View */}
        <div className="hidden lg:block">
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Members Overview</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Member</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Due Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount Owed</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {clientsWithBilling.map((client) => (
                    <tr key={client.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10">
                            <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                              <span className="text-sm font-medium text-gray-700">
                                {client.name ? client.name.split(' ').map(n => n[0]).join('').substring(0, 2) : '??'}
                              </span>
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">{client.name}</div>
                            <div className="text-sm text-gray-500">{client.email}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(client._status)}`}>
                          {client._status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className={`text-sm ${getDueDateColor(client._daysToDue, client._status)}`}>
                          {formatDueDate(client._dueDate, client._daysToDue, client._status)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatMoney(client.amount_owed)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        <button
                          onClick={() => handleWhatsApp(client)}
                          className="btn btn-primary"
                        >
                          WhatsApp
                        </button>
                        <button className="btn btn-outline">
                          Payment
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Mobile Card View */}
        <div className="lg:hidden">
          <div className="space-y-4">
            {clientsWithBilling.map((client) => (
              <div key={client.id} className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10">
                      <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                        <span className="text-sm font-medium text-gray-700">
                          {client.name ? client.name.split(' ').map(n => n[0]).join('').substring(0, 2) : '??'}
                        </span>
                      </div>
                    </div>
                    <div className="ml-3">
                      <div className="text-sm font-medium text-gray-900">{client.name}</div>
                      <div className="text-xs text-gray-500">{client.email}</div>
                    </div>
                  </div>
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(client._status)}`}>
                    {client._status}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <p className="text-xs text-gray-500">Due Date</p>
                    <p className={`text-sm ${getDueDateColor(client._daysToDue, client._status)}`}>
                      {formatDueDate(client._dueDate, client._daysToDue, client._status)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Amount Owed</p>
                    <p className="text-sm font-medium text-gray-900">{formatMoney(client.amount_owed)}</p>
                  </div>
                </div>

                <div className="flex space-x-2">
                  <button
                    onClick={() => handleWhatsApp(client)}
                    className="flex-1 bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-lg text-xs font-medium transition-colors"
                  >
                    WhatsApp
                  </button>
                  <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg text-xs font-medium transition-colors">
                    Payment
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Empty State */}
        {clientsWithBilling.length === 0 && (
          <div className="text-center py-12">
            <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-1">No members found</h3>
            <p className="text-gray-500">Get started by adding your first member.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;