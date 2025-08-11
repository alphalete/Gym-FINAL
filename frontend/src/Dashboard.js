import React, { useState, useEffect } from 'react';
import { nextDueDateFromJoin, isOverdue } from './billing';

const Dashboard = () => {
  // Mock data - will be replaced with real data
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);

  // Mock clients data for demo (replace with real clientsWithBilling)
  const mockClients = [
    {
      id: 1,
      name: "Alice Johnson",
      joinDate: "2025-07-15",
      email: "alice@example.com",
      phone: "+1234567890",
      monthlyFee: 55,
      status: "Active",
      lastPayment: "2025-07-15"
    },
    {
      id: 2,
      name: "Bob Smith",
      joinDate: "2025-06-01",
      email: "bob@example.com",
      phone: "+1234567891",
      monthlyFee: 75,
      status: "Overdue", 
      lastPayment: "2025-06-01"
    },
    {
      id: 3,
      name: "Carol White",
      joinDate: "2025-07-25",
      email: "carol@example.com",
      phone: "+1234567892",
      monthlyFee: 65,
      status: "Active",
      lastPayment: "2025-07-25"
    },
    {
      id: 4,
      name: "David Brown",
      joinDate: "2025-05-15",
      email: "david@example.com", 
      phone: "+1234567893",
      monthlyFee: 85,
      status: "Due Soon",
      lastPayment: "2025-06-15"
    }
  ];

  // Compute clients with billing info
  const clientsWithBilling = mockClients.map(client => {
    const dueDate = client.joinDate ? nextDueDateFromJoin(client.joinDate) : null;
    const overdue = client.joinDate ? isOverdue(client.joinDate) : false;
    const today = new Date();
    const due = dueDate ? new Date(dueDate) : null;
    const daysToDue = due ? Math.ceil((due - today) / (1000 * 60 * 60 * 24)) : null;
    
    let status = "Active";
    if (overdue) {
      status = "Overdue";
    } else if (daysToDue !== null && daysToDue <= 7 && daysToDue > 0) {
      status = "Due Soon";
    }
    
    return {
      ...client,
      _dueDate: dueDate ? new Date(dueDate).toISOString().slice(0, 10) : null,
      _status: status,
      _daysToDue: daysToDue
    };
  });

  // Calculate summary stats
  const totalClients = clientsWithBilling.length;
  const overdueClients = clientsWithBilling.filter(c => c._status === "Overdue").length;
  const dueSoonClients = clientsWithBilling.filter(c => c._status === "Due Soon").length;
  const monthlyRevenue = clientsWithBilling.reduce((sum, client) => sum + (client.monthlyFee || 0), 0);

  useEffect(() => {
    // Simulate loading
    setTimeout(() => setLoading(false), 1000);
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case "Overdue":
        return "bg-red-100 text-red-800";
      case "Due Soon":
        return "bg-yellow-100 text-yellow-800";
      case "Active":
        return "bg-green-100 text-green-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getDueDateColor = (daysToDue, status) => {
    if (status === "Overdue") return "text-red-600 font-semibold";
    if (daysToDue !== null && daysToDue <= 7) return "text-yellow-600 font-semibold";
    return "text-gray-600";
  };

  const formatDueDate = (dateStr, daysToDue, status) => {
    if (!dateStr) return "No due date";
    const date = new Date(dateStr);
    const formatted = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    
    if (status === "Overdue") {
      return `${formatted} (${Math.abs(daysToDue)} days overdue)`;
    } else if (daysToDue !== null && daysToDue <= 7 && daysToDue > 0) {
      return `${formatted} (${daysToDue} days)`;
    }
    return formatted;
  };

  const handleWhatsApp = (client) => {
    const message = `Hi ${client.name}, this is a reminder about your membership payment.`;
    const url = `https://wa.me/${client.phone?.replace(/[^\d]/g, '')}?text=${encodeURIComponent(message)}`;
    window.open(url, '_blank');
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
                <p className="text-2xl font-semibold text-gray-900">{totalClients}</p>
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
                <p className="text-2xl font-semibold text-red-600">{overdueClients}</p>
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
                <p className="text-2xl font-semibold text-yellow-600">{dueSoonClients}</p>
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
                <h3 className="text-sm font-medium text-gray-500">Monthly Revenue</h3>
                <p className="text-2xl font-semibold text-green-600">TTD {monthlyRevenue}</p>
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
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Monthly Fee</th>
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
                                {client.name.split(' ').map(n => n[0]).join('').substring(0, 2)}
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
                        TTD {client.monthlyFee}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        <button
                          onClick={() => handleWhatsApp(client)}
                          className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded-lg text-xs font-medium transition-colors"
                        >
                          WhatsApp
                        </button>
                        <button className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded-lg text-xs font-medium transition-colors">
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
                          {client.name.split(' ').map(n => n[0]).join('').substring(0, 2)}
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
                    <p className="text-xs text-gray-500">Monthly Fee</p>
                    <p className="text-sm font-medium text-gray-900">TTD {client.monthlyFee}</p>
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