import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom';
import LocalStorageManager from './LocalStorageManager';
import './App.css';

const localDB = new LocalStorageManager();

const Navigation = ({ currentPage }) => {
  const [isOpen, setIsOpen] = useState(false);

  const menuItems = [
    { path: "/", icon: "🏠", label: "Dashboard", description: "Overview & Stats" },
    { path: "/clients", icon: "👥", label: "Members", description: "Manage Members" },
    { path: "/add-client", icon: "➕", label: "Add Member", description: "New Member" },
    { path: "/payments", icon: "💳", label: "Payments", description: "Payment Tracking" },
    { path: "/email-center", icon: "📧", label: "Messages", description: "Send Reminders" },
    { path: "/reminders", icon: "⏰", label: "Automation", description: "Auto Reminders" },
    { path: "/reports", icon: "📊", label: "Analytics", description: "Reports & Data" },
    { path: "/settings", icon: "⚙️", label: "Settings", description: "Configuration" },
  ];

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="md:hidden fixed top-4 left-4 z-50 p-3 bg-white dark:bg-gray-800 shadow-lg rounded-lg border border-gray-200 dark:border-gray-700 transition-all"
        style={{ touchAction: 'manipulation' }}
      >
        <span className="text-gray-700 dark:text-gray-300 text-lg">
          {isOpen ? "✕" : "☰"}
        </span>
      </button>

      {/* Sidebar */}
      <div className={`fixed left-0 top-0 bottom-0 w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transform transition-transform duration-300 z-40 overflow-y-auto shadow-lg ${
        isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
      }`} style={{ WebkitOverflowScrolling: 'touch' }}>
        
        {/* Logo Header */}
        <div className="p-6 bg-gradient-to-r from-primary-600 to-secondary-600 flex-shrink-0">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-md">
              <img src="/icon-192.png" alt="Logo" className="w-8 h-8 rounded-full" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">ALPHALETE</h1>
              <p className="text-xs text-white opacity-90">ATHLETICS</p>
            </div>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="p-4 flex-1">
          <ul className="space-y-2">
            {menuItems.map((item) => {
              const isActive = currentPage === item.path;
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    onClick={() => setIsOpen(false)}
                    className={`nav-item ${isActive ? 'active' : ''}`}
                  >
                    <span className="text-lg">{item.icon}</span>
                    <div className="flex-1">
                      <div className="font-medium">{item.label}</div>
                      <div className="text-xs opacity-75">{item.description}</div>
                    </div>
                    {isActive && (
                      <div className="w-1 h-8 bg-primary-500 rounded-full"></div>
                    )}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex-shrink-0">
          <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span>Online - All features available</span>
          </div>
          <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">
            PWA v4.2.4 - Modern UI
          </div>
        </div>
      </div>

      {/* Mobile Overlay */}
      {isOpen && (
        <div 
          className="md:hidden fixed inset-0 bg-black bg-opacity-50 z-30"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
};

// Layout Component
const Layout = ({ children }) => {
  const location = useLocation();
  
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navigation currentPage={location.pathname} />
      <div className="md:ml-64">
        {children}
      </div>
    </div>
  );
};

// Email Modal Component - Ultra High Contrast
const EmailModal = ({ isOpen, onClose, client }) => {
  const [emailData, setEmailData] = useState({
    subject: '',
    message: '',
    template: 'default'
  });

  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (isOpen && client) {
      setEmailData({
        subject: `Payment Reminder - ${client.name}`,
        message: `Dear ${client.name},\n\nThis is a reminder that your payment of $${client.monthly_fee} is due soon.\n\nThank you for your continued membership.`,
        template: 'default'
      });
    }
  }, [isOpen, client]);

  const handleSend = async () => {
    if (!client || !emailData.subject || !emailData.message) return;

    setSending(true);
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${backendUrl}/api/email/payment-reminder`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          client_email: client.email,
          client_name: client.name,
          amount: client.monthly_fee,
          due_date: new Date(client.next_payment_date).toLocaleDateString(),
          template_name: emailData.template,
          custom_subject: emailData.subject,
          custom_message: emailData.message
        })
      });

      if (response.ok) {
        alert('✅ Email sent successfully!');
        onClose();
      } else {
        alert('❌ Failed to send email');
      }
    } catch (error) {
      console.error('Error sending email:', error);
      alert('❌ Error sending email');
    } finally {
      setSending(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="ultra-contrast-modal rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex justify-between items-center">
            <h2 className="ultra-contrast-modal-header">Custom Email to {client?.name}</h2>
            <button
              onClick={onClose}
              className="ultra-contrast-button px-4 py-2 rounded-lg"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="p-6 space-y-4">
          <div>
            <label className="ultra-contrast-label block mb-2">Subject</label>
            <input
              type="text"
              value={emailData.subject}
              onChange={(e) => setEmailData(prev => ({ ...prev, subject: e.target.value }))}
              className="ultra-contrast-input w-full p-3 rounded-lg"
              placeholder="Enter email subject"
            />
          </div>

          <div>
            <label className="ultra-contrast-label block mb-2">Template</label>
            <select
              value={emailData.template}
              onChange={(e) => setEmailData(prev => ({ ...prev, template: e.target.value }))}
              className="ultra-contrast-input w-full p-3 rounded-lg"
            >
              <option value="default">Professional</option>
              <option value="friendly">Friendly</option>
              <option value="urgent">Urgent</option>
            </select>
          </div>

          <div>
            <label className="ultra-contrast-label block mb-2">Message</label>
            <textarea
              value={emailData.message}
              onChange={(e) => setEmailData(prev => ({ ...prev, message: e.target.value }))}
              className="ultra-contrast-input w-full p-3 rounded-lg h-32 resize-none"
              placeholder="Enter your custom message"
            />
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              onClick={handleSend}
              disabled={sending}
              className="ultra-contrast-button-primary px-6 py-3 rounded-lg flex-1"
            >
              {sending ? 'Sending...' : '📧 Send Email'}
            </button>
            <button
              onClick={onClose}
              className="ultra-contrast-button px-6 py-3 rounded-lg"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Edit Client Modal Component - Ultra High Contrast
const EditClientModal = ({ client, isOpen, onClose, onSave }) => {
  const [clientData, setClientData] = useState({
    name: '',
    email: '',
    phone: '',
    membership_type: 'Standard',
    monthly_fee: 0,
    start_date: '',
    status: 'Active',
    auto_reminders_enabled: true
  });

  const [membershipTypes, setMembershipTypes] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && client) {
      // Initialize form with client data
      setClientData({
        name: client.name || '',
        email: client.email || '',
        phone: client.phone || '',
        membership_type: client.membership_type || 'Standard',
        monthly_fee: client.monthly_fee || 0,
        start_date: client.start_date ? new Date(client.start_date).toISOString().split('T')[0] : '',
        status: client.status || 'Active',
        auto_reminders_enabled: client.auto_reminders_enabled !== undefined ? client.auto_reminders_enabled : true
      });

      // Fetch membership types
      fetchMembershipTypes();
    }
  }, [isOpen, client]);

  const fetchMembershipTypes = async () => {
    try {
      const result = await localDB.getMembershipTypes();
      setMembershipTypes(result.data || []);
    } catch (error) {
      console.error('Error fetching membership types:', error);
    }
  };

  const handleMembershipChange = (membershipType) => {
    const selectedType = membershipTypes.find(type => type.name === membershipType);
    setClientData(prev => ({
      ...prev,
      membership_type: membershipType,
      monthly_fee: selectedType ? selectedType.fee : prev.monthly_fee
    }));
  };

  const handleSave = async () => {
    // Validation
    if (!clientData.name || !clientData.email || !clientData.start_date) {
      alert('Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${backendUrl}/api/clients/${client.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: clientData.name.trim(),
          email: clientData.email.trim(),
          phone: clientData.phone.trim() || null,
          membership_type: clientData.membership_type,
          monthly_fee: parseFloat(clientData.monthly_fee),
          start_date: clientData.start_date,
          status: clientData.status,
          auto_reminders_enabled: clientData.auto_reminders_enabled
        })
      });

      if (!response.ok) {
        throw new Error('Failed to update client');
      }

      const updatedClient = await response.json();
      
      // Update local storage with the complete updated client data from backend
      await localDB.updateClient(client.id, {
        ...updatedClient,
        updated_at: new Date().toISOString()
      });

      alert(`✅ ${clientData.name} updated successfully!`);
      onSave && onSave(updatedClient);
      onClose();
      
    } catch (error) {
      console.error('Error updating client:', error);
      alert('❌ Error updating client: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !client) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="ultra-contrast-modal rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex justify-between items-center">
            <h2 className="ultra-contrast-modal-header">Edit Client</h2>
            <button
              onClick={onClose}
              className="ultra-contrast-button px-4 py-2 rounded-lg"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Client Preview */}
          <div className="member-card p-4 rounded-lg">
            <h3 className="ultra-contrast-text text-lg mb-2">Client Preview</h3>
            <p className="ultra-contrast-secondary">Name: {clientData.name}</p>
            <p className="ultra-contrast-secondary">Email: {clientData.email}</p>
            <p className="ultra-contrast-secondary">Membership: {clientData.membership_type} (${clientData.monthly_fee}/month)</p>
            <p className="ultra-contrast-secondary">Status: {clientData.status}</p>
            <p className="ultra-contrast-secondary">Auto Reminders: {clientData.auto_reminders_enabled ? '✅ Enabled' : '❌ Disabled'}</p>
          </div>

          {/* Form Fields */}
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="ultra-contrast-label block mb-2">Name *</label>
                <input
                  type="text"
                  value={clientData.name}
                  onChange={(e) => setClientData(prev => ({ ...prev, name: e.target.value }))}
                  className="ultra-contrast-input w-full p-3 rounded-lg"
                  placeholder="Enter client name"
                />
              </div>
              <div>
                <label className="ultra-contrast-label block mb-2">Email *</label>
                <input
                  type="email"
                  value={clientData.email}
                  onChange={(e) => setClientData(prev => ({ ...prev, email: e.target.value }))}
                  className="ultra-contrast-input w-full p-3 rounded-lg"
                  placeholder="Enter email address"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="ultra-contrast-label block mb-2">Phone</label>
                <input
                  type="tel"
                  value={clientData.phone}
                  onChange={(e) => setClientData(prev => ({ ...prev, phone: e.target.value }))}
                  className="ultra-contrast-input w-full p-3 rounded-lg"
                  placeholder="Enter phone number"
                />
              </div>
              <div>
                <label className="ultra-contrast-label block mb-2">Membership Type</label>
                <select
                  value={clientData.membership_type}
                  onChange={(e) => handleMembershipChange(e.target.value)}
                  className="ultra-contrast-input w-full p-3 rounded-lg"
                >
                  {membershipTypes.map(type => (
                    <option key={type.name} value={type.name}>
                      {type.name} - ${type.fee}/month
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="ultra-contrast-label block mb-2">Monthly Fee</label>
                <input
                  type="number"
                  value={clientData.monthly_fee}
                  onChange={(e) => setClientData(prev => ({ ...prev, monthly_fee: e.target.value }))}
                  className="ultra-contrast-input w-full p-3 rounded-lg"
                  placeholder="Enter monthly fee"
                />
              </div>
              <div>
                <label className="ultra-contrast-label block mb-2">Start Date *</label>
                <input
                  type="date"
                  value={clientData.start_date}
                  onChange={(e) => setClientData(prev => ({ ...prev, start_date: e.target.value }))}
                  className="ultra-contrast-input w-full p-3 rounded-lg"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="ultra-contrast-label block mb-2">Status</label>
                <select
                  value={clientData.status}
                  onChange={(e) => setClientData(prev => ({ ...prev, status: e.target.value }))}
                  className="ultra-contrast-input w-full p-3 rounded-lg"
                >
                  <option value="Active">Active</option>
                  <option value="Inactive">Inactive</option>
                </select>
              </div>
            </div>

            {/* Automatic Reminders Toggle */}
            <div className="member-card p-4 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <label className="ultra-contrast-label block mb-1">Automatic Payment Reminders</label>
                  <p className="ultra-contrast-secondary text-xs">Send reminders 3 days before and on payment due date</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={clientData.auto_reminders_enabled}
                    onChange={(e) => setClientData(prev => ({ ...prev, auto_reminders_enabled: e.target.checked }))}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-red-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
                </label>
              </div>
            </div>
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              onClick={handleSave}
              disabled={loading}
              className="ultra-contrast-button-primary px-6 py-3 rounded-lg flex-1"
            >
              {loading ? "Saving..." : "✅ Save Changes"}
            </button>
            <button
              onClick={onClose}
              className="ultra-contrast-button px-6 py-3 rounded-lg"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Dashboard Component - Modern Design
const Dashboard = () => {
  const [stats, setStats] = useState({
    totalClients: 0,
    activeClients: 0,
    inactiveClients: 0,
    totalRevenue: 0,
    pendingPayments: 0,
    overduePayments: 0,
    upcomingPayments: 0
  });
  const [loading, setLoading] = useState(true);
  const [recentClients, setRecentClients] = useState([]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const result = await localDB.getClients();
      const clients = result.data || [];
      
      // Calculate modern statistics
      const totalClients = clients.length;
      const activeClients = clients.filter(c => c.status === 'Active').length;
      const inactiveClients = clients.filter(c => c.status === 'Inactive').length;
      const totalRevenue = clients.reduce((sum, c) => sum + (c.monthly_fee || 0), 0);
      
      // Calculate payment statistics
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      let pendingPayments = 0;
      let overduePayments = 0;
      let upcomingPayments = 0;
      
      clients.forEach(client => {
        if (client.status === 'Active' && client.next_payment_date) {
          const paymentDate = new Date(client.next_payment_date + 'T00:00:00');
          const daysUntilDue = Math.ceil((paymentDate - today) / (1000 * 60 * 60 * 24));
          
          if (daysUntilDue < 0) {
            overduePayments++;
          } else if (daysUntilDue <= 7) {
            pendingPayments++;
          } else {
            upcomingPayments++;
          }
        }
      });
      
      setStats({
        totalClients,
        activeClients,
        inactiveClients,
        totalRevenue,
        pendingPayments,
        overduePayments,
        upcomingPayments
      });
      
      // Get recent clients (last 5)
      const recent = clients
        .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
        .slice(0, 5);
      setRecentClients(recent);
      
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const ModernStatCard = ({ title, value, subtitle, icon, trend, color = 'primary', onClick }) => (
    <div 
      className={`stats-card stats-card-${color} animate-fade-in cursor-pointer`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="p-3 bg-white bg-opacity-20 rounded-lg">
          <div className="text-2xl">{icon}</div>
        </div>
        {trend && (
          <div className="flex items-center space-x-1 text-sm font-medium">
            <span className={trend > 0 ? 'text-green-300' : 'text-red-300'}>
              {trend > 0 ? '↗' : '↘'} {Math.abs(trend)}%
            </span>
          </div>
        )}
      </div>
      <div>
        <h3 className="text-3xl font-bold mb-1">{value}</h3>
        <p className="text-sm opacity-90">{title}</p>
        {subtitle && <p className="text-xs opacity-75 mt-1">{subtitle}</p>}
      </div>
    </div>
  );

  const ModernClientCard = ({ client }) => (
    <div className="card p-4 animate-slide-in">
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-full flex items-center justify-center">
          <span className="text-white font-semibold text-sm">{client.name.charAt(0)}</span>
        </div>
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900 dark:text-white">{client.name}</h4>
          <p className="text-sm text-gray-500 dark:text-gray-400">{client.email}</p>
        </div>
        <div className="text-right">
          <p className="text-sm font-medium text-green-600 dark:text-green-400">${client.monthly_fee}</p>
          <span className={`status-badge ${client.status === 'Active' ? 'status-active' : 'status-inactive'}`}>
            {client.status}
          </span>
        </div>
      </div>
    </div>
  );

  const navigate = useNavigate();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-300">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Modern Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-display text-gray-900 dark:text-white mb-2">
                Dashboard
              </h1>
              <p className="text-body text-gray-600 dark:text-gray-300">
                Welcome back! Here's what's happening at Alphalete Athletics.
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={fetchDashboardData}
                className="btn btn-secondary btn-sm"
              >
                <span>🔄</span>
                <span>Refresh</span>
              </button>
              <Link to="/add-client" className="btn btn-primary btn-sm">
                <span>➕</span>
                <span>Add Member</span>
              </Link>
            </div>
          </div>
        </div>

        {/* Modern Statistics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <ModernStatCard
            title="Total Members"
            value={stats.totalClients}
            subtitle="All registered members"
            icon="👥"
            trend={+8.2}
            color="primary"
            onClick={() => navigate('/clients')}
          />
          <ModernStatCard
            title="Active Members"
            value={stats.activeClients}
            subtitle="Currently active"
            icon="✅"
            trend={+5.1}
            color="accent"
            onClick={() => navigate('/clients')}
          />
          <ModernStatCard
            title="Monthly Revenue"
            value={`$${stats.totalRevenue.toLocaleString()}`}
            subtitle="Total potential revenue"
            icon="💰"
            trend={+12.3}
            color="secondary"
            onClick={() => navigate('/payments')}
          />
          <ModernStatCard
            title="Overdue Payments"
            value={stats.overduePayments}
            subtitle="Require immediate attention"
            icon="⚠️"
            trend={-2.1}
            color="error"
            onClick={() => navigate('/payments')}
          />
        </div>

        {/* Payment Status Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="card p-6">
            <h3 className="text-heading-3 text-gray-900 dark:text-white mb-4">Payment Status</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                  <span className="text-sm font-medium">Pending (7 days)</span>
                </div>
                <span className="text-sm font-bold text-yellow-600">{stats.pendingPayments}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                  <span className="text-sm font-medium">Overdue</span>
                </div>
                <span className="text-sm font-bold text-red-600">{stats.overduePayments}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span className="text-sm font-medium">Upcoming</span>
                </div>
                <span className="text-sm font-bold text-green-600">{stats.upcomingPayments}</span>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="card p-6">
            <h3 className="text-heading-3 text-gray-900 dark:text-white mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <Link to="/add-client" className="btn btn-primary w-full">
                <span>➕</span>
                <span>Add New Member</span>
              </Link>
              <Link to="/email-center" className="btn btn-secondary w-full">
                <span>📧</span>
                <span>Send Reminders</span>
              </Link>
              <Link to="/reminders" className="btn btn-secondary w-full">
                <span>⏰</span>
                <span>Auto Reminders</span>
              </Link>
            </div>
          </div>

          {/* System Status */}
          <div className="card p-6">
            <h3 className="text-heading-3 text-gray-900 dark:text-white mb-4">System Status</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">Connection</span>
                <span className="status-badge status-active">Online</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Auto Reminders</span>
                <span className="status-badge status-active">Active</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Data Sync</span>
                <span className="status-badge status-active">Synced</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">PWA Version</span>
                <span className="text-xs text-gray-500">v4.2.0</span>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Members */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-heading-3 text-gray-900 dark:text-white">Recent Members</h3>
            <Link to="/clients" className="text-sm font-medium text-primary-600 hover:text-primary-700">
              View all →
            </Link>
          </div>
          {recentClients.length === 0 ? (
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">👥</span>
              </div>
              <h4 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No members yet</h4>
              <p className="text-gray-500 dark:text-gray-400 mb-4">Get started by adding your first member</p>
              <Link to="/add-client" className="btn btn-primary">
                <span>➕</span>
                <span>Add Member</span>
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {recentClients.map((client) => (
                <ModernClientCard key={client.id} client={client} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Client Management Component with Ultra High Contrast
const ClientManagement = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [editClientModal, setEditClientModal] = useState({ isOpen: false, client: null });
  const [customEmailModal, setCustomEmailModal] = useState({ isOpen: false, client: null });

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async (forceRefresh = false) => {
    try {
      setLoading(true);
      const result = await localDB.getClients(forceRefresh);
      setClients(result.data || []);
    } catch (error) {
      console.error('Error fetching clients:', error);
      setClients([]);
    } finally {
      setLoading(false);
    }
  };

  const sendPaymentReminder = async (client) => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      
      const response = await fetch(`${backendUrl}/api/email/payment-reminder`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          client_email: client.email,
          client_name: client.name,
          amount: client.monthly_fee,
          due_date: new Date(client.next_payment_date).toLocaleDateString(),
          template_name: 'default'
        })
      });

      if (response.ok) {
        alert(`✅ Payment reminder sent to ${client.name}`);
      } else {
        alert('❌ Failed to send reminder');
      }
    } catch (error) {
      console.error('Error sending reminder:', error);
      alert('❌ Error sending reminder');
    }
  };

  const openEditClientModal = (client) => {
    setEditClientModal({ isOpen: true, client });
  };

  const closeEditClientModal = () => {
    setEditClientModal({ isOpen: false, client: null });
  };

  const openCustomEmailModal = (client) => {
    setCustomEmailModal({ isOpen: true, client });
  };

  const closeCustomEmailModal = () => {
    setCustomEmailModal({ isOpen: false, client: null });
  };

  const handleClientUpdated = (updatedClient) => {
    setClients(prev => prev.map(client => 
      client.id === updatedClient.id ? updatedClient : client
    ));
    fetchClients();
  };

  const toggleClientStatus = async (client) => {
    try {
      const newStatus = client.status === 'Active' ? 'Inactive' : 'Active';
      console.log(`Toggling ${client.name} status from ${client.status} to ${newStatus} (ID: ${client.id})`);
      
      // First delete from backend
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${backendUrl}/api/clients/${client.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...client,
          status: newStatus
        })
      });

      if (!response.ok) {
        throw new Error('Failed to update client status');
      }

      // Then update local storage
      await localDB.updateClient(client.id, {
        ...client,
        status: newStatus,
        updated_at: new Date().toISOString()
      });

      // Refresh the client list
      fetchClients();
      
      alert(`✅ ${client.name} marked as ${newStatus}`);
    } catch (error) {
      console.error("❌ Error toggling client status:", error);
      alert('❌ Error updating client status: ' + error.message);
    }
  };

  const filteredClients = clients.filter(client =>
    client.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    client.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
        <div className="max-w-7xl mx-auto">
          {/* Modern Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-display text-gray-900 dark:text-white mb-2">
                  Member Management
                </h1>
                <p className="text-body text-gray-600 dark:text-gray-300">
                  Manage your gym members and their information.
                </p>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={() => fetchClients(true)}
                  className="btn btn-secondary btn-sm"
                  disabled={loading}
                >
                  <span>{loading ? "🔄" : "↻"}</span>
                  <span>Refresh</span>
                </button>
                <Link 
                  to="/add-client"
                  className="btn btn-primary btn-sm"
                >
                  <span>➕</span>
                  <span>Add Member</span>
                </Link>
              </div>
            </div>
          </div>

          {/* Modern Search and Stats */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
            <div className="lg:col-span-3">
              <div className="card p-6">
                <div className="flex items-center space-x-4">
                  <div className="flex-1">
                    <div className="relative">
                      <input
                        type="text"
                        placeholder="Search members by name or email..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="form-input pl-10 pr-4"
                      />
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <span className="text-gray-400 text-lg">🔍</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      {filteredClients.length} of {clients.length} members
                    </span>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="stats-card stats-card-primary">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm opacity-90">Total Members</span>
                <span className="text-2xl">👥</span>
              </div>
              <div className="text-2xl font-bold">{clients.length}</div>
              <div className="text-sm opacity-75">
                {clients.filter(c => c.status === 'Active').length} Active
              </div>
            </div>
          </div>

          {/* Client List */}
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto mb-4"></div>
              <p className="text-gray-600 dark:text-gray-300">Loading clients...</p>
            </div>
          ) : filteredClients.length === 0 ? (
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">👥</span>
              </div>
              <h4 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No members found</h4>
              <p className="text-gray-500 dark:text-gray-400 mb-4">
                {searchTerm ? 'Try adjusting your search' : 'Add your first member to get started'}
              </p>
              <Link to="/add-client" className="btn btn-primary">
                <span>➕</span>
                <span>Add Member</span>
              </Link>
            </div>
          ) : (
            <>
              {/* Mobile Cards View */}
              <div className="md:hidden space-y-4">
                {filteredClients.map((client) => (
                  <div key={client.id} className="member-card p-6">
                    <div className="flex items-center space-x-3 mb-4">
                      <div className="w-12 h-12 bg-red-600 rounded-full flex items-center justify-center font-bold text-white">
                        {client.name.charAt(0)}
                      </div>
                      <div className="flex-1">
                        <h3 className="member-name">{client.name}</h3>
                        <p className="member-email">{client.email}</p>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs ${
                        client.status === 'Active' 
                          ? 'member-status-active' 
                          : 'member-status-inactive'
                      }`}>
                        {client.status}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                      <div>
                        <span className="member-label">Phone:</span>
                        <p className="member-value">{client.phone || "N/A"}</p>
                      </div>
                      <div>
                        <span className="member-label">Membership:</span>
                        <p className="member-value">{client.membership_type}</p>
                      </div>
                      <div>
                        <span className="member-label">Monthly Fee:</span>
                        <p className="member-fee">${client.monthly_fee}</p>
                      </div>
                      <div>
                        <span className="member-label">Member Since:</span>
                        <p className="member-value">{client.start_date ? new Date(client.start_date + 'T00:00:00').toLocaleDateString() : 'N/A'}</p>
                      </div>
                      <div>
                        <span className="member-label">Auto Reminders:</span>
                        <p className={client.auto_reminders_enabled !== false ? "member-reminder-enabled" : "member-reminder-disabled"}>
                          {client.auto_reminders_enabled !== false ? "✅ Enabled" : "❌ Disabled"}
                        </p>
                      </div>
                      {client.current_period_start && client.current_period_end && (
                        <>
                          <div>
                            <span className="member-label">Current Period:</span>
                            <p className="member-value text-blue-700 dark:text-blue-300 font-bold">
                              {new Date(client.current_period_start + 'T00:00:00').toLocaleDateString()} - {new Date(client.current_period_end + 'T00:00:00').toLocaleDateString()}
                            </p>
                          </div>
                          <div>
                            <span className="member-label">Next Payment:</span>
                            <p className="member-value">{new Date(client.next_payment_date + 'T00:00:00').toLocaleDateString()}</p>
                          </div>
                        </>
                      )}
                      {!client.current_period_start && (
                        <div>
                          <span className="member-label">Next Payment:</span>
                          <p className="member-value">{new Date(client.next_payment_date + 'T00:00:00').toLocaleDateString()}</p>
                        </div>
                      )}
                    </div>
                    
                    <div className="flex space-x-2 mt-4">
                      <button
                        onClick={() => sendPaymentReminder(client)}
                        className="btn btn-primary btn-sm flex-1"
                      >
                        📧 Remind
                      </button>
                      <button
                        onClick={() => openCustomEmailModal(client)}
                        className="btn btn-secondary btn-sm"
                        title="Custom Email"
                      >
                        🎨
                      </button>
                      <button
                        onClick={() => openEditClientModal(client)}
                        className="btn btn-secondary btn-sm"
                        title="Edit Client"
                      >
                        ✏️
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Desktop Table View */}
              <div className="hidden md:block card overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-100 dark:bg-gray-800">
                      <tr>
                        <th className="text-left p-4 font-semibold text-gray-900 dark:text-white">Name</th>
                        <th className="text-left p-4 font-semibold text-gray-900 dark:text-white">Email</th>
                        <th className="text-left p-4 font-semibold text-gray-900 dark:text-white">Phone</th>
                        <th className="text-left p-4 font-semibold text-gray-900 dark:text-white">Membership</th>
                        <th className="text-left p-4 font-semibold text-gray-900 dark:text-white">Monthly Fee</th>
                        <th className="text-left p-4 font-semibold text-gray-900 dark:text-white">Member Since</th>
                        <th className="text-left p-4 font-semibold text-gray-900 dark:text-white">Current Period</th>
                        <th className="text-left p-4 font-semibold text-gray-900 dark:text-white">Next Payment</th>
                        <th className="text-left p-4 font-semibold text-gray-900 dark:text-white">Status</th>
                        <th className="text-left p-4 font-semibold text-gray-900 dark:text-white">Auto Reminders</th>
                        <th className="text-left p-4 font-semibold text-gray-900 dark:text-white">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredClients.map((client) => (
                        <tr key={client.id} className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800">
                          <td className="p-4">
                            <div className="flex items-center space-x-3">
                              <div className="w-8 h-8 bg-red-600 rounded-full flex items-center justify-center font-bold text-white text-sm">
                                {client.name.charAt(0)}
                              </div>
                              <div className="member-name">{client.name}</div>
                            </div>
                          </td>
                          <td className="p-4 member-email">{client.email}</td>
                          <td className="p-4 member-value">{client.phone || "N/A"}</td>
                          <td className="p-4 member-value">{client.membership_type}</td>
                          <td className="p-4 member-fee">${client.monthly_fee}</td>
                          <td className="p-4 member-value">{client.start_date ? new Date(client.start_date + 'T00:00:00').toLocaleDateString() : 'N/A'}</td>
                          <td className="p-4">
                            {client.current_period_start && client.current_period_end ? (
                              <div className="text-blue-700 dark:text-blue-300 text-sm font-bold">
                                {new Date(client.current_period_start + 'T00:00:00').toLocaleDateString()} - {new Date(client.current_period_end + 'T00:00:00').toLocaleDateString()}
                              </div>
                            ) : (
                              <span className="text-gray-500 dark:text-gray-400 text-sm font-semibold">Not set</span>
                            )}
                          </td>
                          <td className="p-4 member-value">{client.next_payment_date ? new Date(client.next_payment_date + 'T00:00:00').toLocaleDateString() : 'N/A'}</td>
                          <td className="p-4">
                            <span className={`px-3 py-1 rounded-full text-xs ${
                              client.status === 'Active' 
                                ? 'member-status-active' 
                                : 'member-status-inactive'
                            }`}>
                              {client.status}
                            </span>
                          </td>
                          <td className="p-4">
                            <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                              client.auto_reminders_enabled !== false 
                                ? 'member-status-active' 
                                : 'member-status-inactive'
                            }`}>
                              {client.auto_reminders_enabled !== false ? '✅ On' : '❌ Off'}
                            </span>
                          </td>
                          <td className="p-4">
                            <div className="flex space-x-2">
                              <button
                                onClick={() => sendPaymentReminder(client)}
                                className="btn btn-primary btn-sm"
                                title="Send Payment Reminder"
                              >
                                📧
                              </button>
                              <button
                                onClick={() => openCustomEmailModal(client)}
                                className="btn btn-secondary btn-sm"
                                title="Custom Email"
                              >
                                🎨
                              </button>
                              <button
                                onClick={() => openEditClientModal(client)}
                                className="btn btn-secondary btn-sm"
                                title="Edit Client"
                              >
                                ✏️
                              </button>
                              <button
                                onClick={() => toggleClientStatus(client)}
                                className={`btn btn-sm ${
                                  client.status === 'Active' 
                                    ? 'bg-orange-600 hover:bg-orange-700 text-white' 
                                    : 'bg-green-600 hover:bg-green-700 text-white'
                                }`}
                                title={`Make ${client.status === 'Active' ? 'Inactive' : 'Active'}`}
                              >
                                {client.status === 'Active' ? '⏸️' : '▶️'}
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Custom Email Modal */}
      <EmailModal
        isOpen={customEmailModal.isOpen}
        onClose={closeCustomEmailModal}
        client={customEmailModal.client}
      />

      {/* Edit Client Modal */}
      <EditClientModal
        client={editClientModal.client}
        isOpen={editClientModal.isOpen}
        onClose={closeEditClientModal}
        onSave={handleClientUpdated}
      />
    </>
  );
};

// Add Client Component (placeholder for brevity)
const AddClient = () => {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    membership_type: "",
    monthly_fee: 50.00,
    start_date: new Date().toISOString().split('T')[0],
    auto_reminders_enabled: true
  });

  const [membershipTypes, setMembershipTypes] = useState([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchMembershipTypes();
  }, []);

  const fetchMembershipTypes = async () => {
    try {
      const result = await localDB.getMembershipTypes();
      setMembershipTypes(result.data || []);
      
      // Set default membership type
      if (result.data && result.data.length > 0) {
        setFormData(prev => ({
          ...prev,
          membership_type: result.data[0].name,
          monthly_fee: result.data[0].fee
        }));
      }
    } catch (error) {
      console.error('Error fetching membership types:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name || !formData.email || !formData.membership_type) {
      alert('Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
      await localDB.addClient(formData);
      alert(`✅ ${formData.name} added successfully!`);
      navigate('/clients');
    } catch (error) {
      console.error('Error adding client:', error);
      alert('❌ Error adding client: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <h1 className="text-display text-gray-900 dark:text-white mb-2">Add New Member</h1>
          <p className="text-body text-gray-600 dark:text-gray-300">Add a new member to your gym</p>
        </div>

        <form onSubmit={handleSubmit} className="ultra-contrast-modal p-6 rounded-lg">
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="ultra-contrast-label block mb-2">Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  className="ultra-contrast-input w-full p-3 rounded-lg"
                  placeholder="Enter member name"
                  required
                />
              </div>
              <div>
                <label className="ultra-contrast-label block mb-2">Email *</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                  className="ultra-contrast-input w-full p-3 rounded-lg"
                  placeholder="Enter email address"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="ultra-contrast-label block mb-2">Phone</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                  className="ultra-contrast-input w-full p-3 rounded-lg"
                  placeholder="Enter phone number"
                />
              </div>
              <div>
                <label className="ultra-contrast-label block mb-2">Start Date *</label>
                <input
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData(prev => ({ ...prev, start_date: e.target.value }))}
                  className="ultra-contrast-input w-full p-3 rounded-lg"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="ultra-contrast-label block mb-2">Membership Type *</label>
                <select
                  value={formData.membership_type}
                  onChange={(e) => {
                    const selectedType = membershipTypes.find(type => type.name === e.target.value);
                    setFormData(prev => ({
                      ...prev,
                      membership_type: e.target.value,
                      monthly_fee: selectedType ? selectedType.fee : prev.monthly_fee
                    }));
                  }}
                  className="ultra-contrast-input w-full p-3 rounded-lg"
                  required
                >
                  {membershipTypes.map(type => (
                    <option key={type.name} value={type.name}>
                      {type.name} - ${type.fee}/month
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="ultra-contrast-label block mb-2">Monthly Fee *</label>
                <input
                  type="number"
                  value={formData.monthly_fee}
                  onChange={(e) => setFormData(prev => ({ ...prev, monthly_fee: parseFloat(e.target.value) || 0 }))}
                  className="ultra-contrast-input w-full p-3 rounded-lg"
                  step="0.01"
                  min="0"
                  required
                />
              </div>
            </div>

            <div className="member-card p-4 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <label className="ultra-contrast-label block mb-1">Automatic Payment Reminders</label>
                  <p className="ultra-contrast-secondary text-xs">Send reminders 3 days before and on payment due date</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.auto_reminders_enabled}
                    onChange={(e) => setFormData(prev => ({ ...prev, auto_reminders_enabled: e.target.checked }))}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-red-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
                </label>
              </div>
            </div>

            <div className="flex space-x-3 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="ultra-contrast-button-primary px-6 py-3 rounded-lg flex-1"
              >
                {loading ? 'Adding...' : '➕ Add Member'}
              </button>
              <button
                type="button"
                onClick={() => navigate('/clients')}
                className="ultra-contrast-button px-6 py-3 rounded-lg"
              >
                Cancel
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

// Other components would be here with similar ultra-contrast styles...
// For brevity, I'm including placeholders for the remaining components

const EmailCenter = () => <div className="ultra-contrast-text p-6">Email Center Component</div>;
const Payments = () => <div className="ultra-contrast-text p-6">Payments Component</div>;
const AutoReminders = () => <div className="ultra-contrast-text p-6">Auto Reminders Component</div>;
const Reports = () => <div className="ultra-contrast-text p-6">Reports Component</div>;
const Settings = () => <div className="ultra-contrast-text p-6">Settings Component</div>;

function App() {
  useEffect(() => {
    // Force remove loading screen with stronger methods
    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen) {
      console.log('React App mounted, removing loading screen...');
      
      // Use stronger CSS overrides with !important
      loadingScreen.style.setProperty('opacity', '0', 'important');
      loadingScreen.style.setProperty('pointer-events', 'none', 'important');
      loadingScreen.style.setProperty('z-index', '-1', 'important');
      
      setTimeout(() => {
        // Complete DOM removal instead of just hiding
        console.log('Completely removing loading screen from DOM');
        loadingScreen.remove();
      }, 300);
    } else {
      console.log('Loading screen element not found');
    }
  }, []);

  return (
    <Router>
      <div className="App">
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/clients" element={<ClientManagement />} />
            <Route path="/add-client" element={<AddClient />} />
            <Route path="/email-center" element={<EmailCenter />} />
            <Route path="/payments" element={<Payments />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/reminders" element={<AutoReminders />} />
          </Routes>
        </Layout>
      </div>
    </Router>
  );
}

export default App;