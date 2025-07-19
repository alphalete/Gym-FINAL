import React, { useState, useEffect } from 'react';

// Mock Data - Extended for 100+ clients
const generateMockClients = () => {
  const names = [
    'John Smith', 'Sarah Johnson', 'Mike Wilson', 'Emily Davis', 'David Brown',
    'Jessica Miller', 'Chris Garcia', 'Amanda Rodriguez', 'Ryan Martinez', 'Lisa Anderson',
    'Kevin Taylor', 'Maria Gonzalez', 'Brandon Lee', 'Nicole White', 'Tyler Harris',
    'Ashley Clark', 'Jonathan Lewis', 'Stephanie Robinson', 'Daniel Walker', 'Rachel Hall',
    'Anthony Young', 'Michelle Allen', 'Matthew King', 'Kimberly Wright', 'Joshua Lopez',
    'Amy Hill', 'Andrew Scott', 'Laura Green', 'Nicholas Adams', 'Christina Baker',
    'Joseph Nelson', 'Elizabeth Carter', 'Thomas Mitchell', 'Jennifer Perez', 'Brian Roberts',
    'Melissa Turner', 'Christopher Phillips', 'Susan Campbell', 'William Parker', 'Angela Evans',
    'James Edwards', 'Mary Collins', 'Robert Stewart', 'Patricia Sanchez', 'Michael Morris',
    'Linda Rogers', 'Richard Reed', 'Barbara Cook', 'Charles Bailey', 'Nancy Cooper',
    'Jason Richardson', 'Karen Cox', 'Paul Ward', 'Helen Torres', 'Mark Peterson',
    'Sandra Gray', 'Steven Ramirez', 'Donna James', 'Kenneth Watson', 'Carol Brooks',
    'Frank Kelly', 'Ruth Sanders', 'Gregory Price', 'Sharon Bennett', 'Raymond Wood',
    'Michelle Barnes', 'Samuel Ross', 'Betty Henderson', 'Peter Coleman', 'Alice Jenkins',
    'Harold Perry', 'Anna Powell', 'Douglas Long', 'Judith Patterson', 'Arthur Hughes',
    'Marie Flores', 'Jerry Washington', 'Gloria Butler', 'Carl Simmons', 'Teresa Foster',
    'Alan Gonzales', 'Frances Bryant', 'Henry Alexander', 'Diana Russell', 'Walter Griffin',
    'Julie Diaz', 'Ralph Hayes', 'Sara Myers', 'Gerald Ford', 'Janet Hamilton',
    'Howard Graham', 'Catherine Sullivan', 'Philip Wallace', 'Deborah Woods', 'Louis Knight',
    'Victoria McDonald', 'Scott Hunter', 'Carolyn Palmer', 'Albert Ellis', 'Jean Black'
  ];

  const membershipTypes = ['Student', 'Monthly', 'Custom'];
  const membershipPrices = { Student: 29, Monthly: 59, Custom: 99 };
  const domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'company.com'];

  return names.map((name, index) => {
    const membershipType = membershipTypes[index % 3];
    const isOverdue = Math.random() < 0.15; // 15% chance of being overdue
    const email = name.toLowerCase().replace(' ', '.') + '@' + domains[index % domains.length];
    const phone = `(555) ${String(Math.floor(Math.random() * 900) + 100)}-${String(Math.floor(Math.random() * 9000) + 1000)}`;
    
    // Generate random dates
    const joinDate = new Date(2024, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1);
    const lastPayment = isOverdue 
      ? new Date(Date.now() - (Math.floor(Math.random() * 30) + 10) * 24 * 60 * 60 * 1000)
      : new Date(Date.now() - Math.floor(Math.random() * 20) * 24 * 60 * 60 * 1000);
    
    const nextDue = new Date(lastPayment);
    nextDue.setMonth(nextDue.getMonth() + 1);
    
    return {
      id: index + 1,
      name,
      email,
      phone,
      membershipType,
      joinDate: joinDate.toISOString().split('T')[0],
      lastPayment: lastPayment.toISOString().split('T')[0],
      nextDue: nextDue.toISOString().split('T')[0],
      status: isOverdue ? 'Overdue' : 'Active',
      amount: membershipPrices[membershipType],
      overdue: isOverdue ? Math.floor(Math.random() * 20) + 1 : 0
    };
  });
};

const mockClients = generateMockClients();

// Login Form Component
const LoginForm = ({ onLogin }) => {
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    // Mock login - in real app this would validate against backend
    if (credentials.username && credentials.password) {
      onLogin({
        name: 'Admin User',
        username: credentials.username,
        role: 'Administrator'
      });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-black flex items-center justify-center">
      <div className="max-w-md w-full mx-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-gradient-to-r from-red-500 to-orange-500 rounded-xl flex items-center justify-center mx-auto mb-4">
              <span className="text-white font-bold text-2xl">A</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Alphalete Athletics</h1>
            <p className="text-gray-600">Management System</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Username
              </label>
              <input
                type="text"
                value={credentials.username}
                onChange={(e) => setCredentials({...credentials, username: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                placeholder="Enter your username"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <input
                type="password"
                value={credentials.password}
                onChange={(e) => setCredentials({...credentials, password: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                placeholder="Enter your password"
                required
              />
            </div>

            <button
              type="submit"
              className="w-full bg-gradient-to-r from-red-500 to-orange-500 text-white py-3 rounded-lg font-semibold hover:from-red-600 hover:to-orange-600 transition-all transform hover:scale-105"
            >
              Sign In
            </button>
          </form>

          <div className="text-center mt-6">
            <p className="text-gray-400">
              Don't have an account?{' '}
              <button onClick={onSwitchToSignup} className="text-red-500 hover:underline">
                Sign up
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Sidebar Component
const Sidebar = ({ activeTab, setActiveTab, user, onLogout, collapsed, onToggle }) => {
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'clients', label: 'Client Management', icon: '👥' },
    { id: 'payments', label: 'Payment Tracking', icon: '💳' },
    { id: 'memberships', label: 'Memberships', icon: '🎫' },
    { id: 'reports', label: 'Reports', icon: '📈' },
    { id: 'settings', label: 'Settings', icon: '⚙️' }
  ];

  // Close mobile menu when tab changes
  useEffect(() => {
    setIsMobileOpen(false);
  }, [activeTab]);

  return (
    <>
      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed lg:relative inset-y-0 left-0 z-50 bg-gray-900 text-white flex flex-col transition-all duration-300 ease-in-out
        ${collapsed ? 'w-16' : 'w-64'}
        ${isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        
        {/* Logo Section */}
        <div className={`p-6 border-b border-gray-700 ${collapsed ? 'px-4' : ''}`}>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-red-500 to-orange-500 rounded-lg flex items-center justify-center flex-shrink-0">
              <span className="text-white font-bold text-lg">A</span>
            </div>
            {!collapsed && (
              <div className="overflow-hidden">
                <h1 className="font-bold text-lg whitespace-nowrap">Alphalete Athletics</h1>
                <p className="text-gray-400 text-sm whitespace-nowrap">Management System</p>
              </div>
            )}
          </div>
          
          {/* Desktop Toggle Button */}
          <button
            onClick={onToggle}
            className={`hidden lg:block absolute top-6 -right-3 bg-gray-800 border border-gray-600 rounded-full p-1 hover:bg-gray-700 transition-colors ${
              collapsed ? 'rotate-180' : ''
            }`}
          >
            <svg className="w-4 h-4 text-white transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        </div>

        {/* User Info */}
        {!collapsed && (
          <div className="p-4 border-b border-gray-700">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-sm">👤</span>
              </div>
              <div className="overflow-hidden">
                <p className="font-medium whitespace-nowrap">{user?.name}</p>
                <p className="text-gray-400 text-sm whitespace-nowrap">{user?.role}</p>
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <nav className="flex-1 p-4 overflow-y-auto">
          <ul className="space-y-2">
            {menuItems.map((item) => (
              <li key={item.id}>
                <button
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center px-4 py-3 rounded-lg transition-colors group relative ${
                    activeTab === item.id
                      ? 'bg-red-500 text-white'
                      : 'text-gray-300 hover:bg-gray-800'
                  } ${collapsed ? 'justify-center' : 'space-x-3'}`}
                  title={collapsed ? item.label : ''}
                >
                  <span className="text-xl flex-shrink-0">{item.icon}</span>
                  {!collapsed && <span className="whitespace-nowrap">{item.label}</span>}
                  
                  {/* Tooltip for collapsed state */}
                  {collapsed && (
                    <div className="absolute left-full ml-2 px-2 py-1 bg-gray-800 text-white text-sm rounded-md opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 whitespace-nowrap z-50">
                      {item.label}
                    </div>
                  )}
                </button>
              </li>
            ))}
          </ul>
        </nav>

        {/* Logout */}
        <div className="p-4 border-t border-gray-700">
          <button
            onClick={onLogout}
            className={`w-full flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 rounded-lg transition-colors group relative ${
              collapsed ? 'justify-center' : 'space-x-3'
            }`}
            title={collapsed ? 'Logout' : ''}
          >
            <span className="text-xl flex-shrink-0">🚪</span>
            {!collapsed && <span className="whitespace-nowrap">Logout</span>}
            
            {/* Tooltip for collapsed state */}
            {collapsed && (
              <div className="absolute left-full ml-2 px-2 py-1 bg-gray-800 text-white text-sm rounded-md opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 whitespace-nowrap z-50">
                Logout
              </div>
            )}
          </button>
        </div>
      </div>

      {/* Mobile Toggle Button - Floating */}
      <button
        onClick={() => setIsMobileOpen(true)}
        className="lg:hidden fixed bottom-6 left-6 z-30 bg-red-500 text-white p-3 rounded-full shadow-lg hover:bg-red-600 transition-colors"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
    </>
  );
};

// Dashboard Component
const Dashboard = () => {
  const totalClients = mockClients.length;
  const activeClients = mockClients.filter(c => c.status === 'Active').length;
  const overdueClients = mockClients.filter(c => c.status === 'Overdue').length;
  const monthlyRevenue = mockClients.reduce((sum, client) => sum + client.amount, 0);
  const overdueAmount = mockClients.reduce((sum, client) => sum + client.overdue * client.amount, 0);

  const recentPayments = [
    { client: 'John Smith', amount: 59, date: '2025-01-20', status: 'Completed' },
    { client: 'David Brown', amount: 59, date: '2025-01-19', status: 'Completed' },
    { client: 'Mike Wilson', amount: 99, date: '2025-01-18', status: 'Completed' }
  ];

  const overduePayments = mockClients.filter(c => c.status === 'Overdue');

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-2">Welcome back! Here's what's happening at your gym.</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
        <div className="bg-white rounded-xl p-6 shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Clients</p>
              <p className="text-3xl font-bold text-gray-900">{totalClients}</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <span className="text-2xl">👥</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Members</p>
              <p className="text-3xl font-bold text-green-600">{activeClients}</p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <span className="text-2xl">✅</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Overdue Payments</p>
              <p className="text-3xl font-bold text-red-600">{overdueClients}</p>
            </div>
            <div className="p-3 bg-red-100 rounded-lg">
              <span className="text-2xl">⚠️</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Monthly Revenue</p>
              <p className="text-3xl font-bold text-blue-600">${monthlyRevenue}</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <span className="text-2xl">💰</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Overdue Amount</p>
              <p className="text-3xl font-bold text-orange-600">${overdueAmount}</p>
            </div>
            <div className="p-3 bg-orange-100 rounded-lg">
              <span className="text-2xl">💸</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Recent Payments */}
        <div className="bg-white rounded-xl shadow-sm border">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Recent Payments</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {recentPayments.map((payment, index) => (
                <div key={index} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-b-0">
                  <div>
                    <p className="font-medium text-gray-900">{payment.client}</p>
                    <p className="text-sm text-gray-500">{payment.date}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-green-600">${payment.amount}</p>
                    <p className="text-sm text-gray-500">{payment.status}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Overdue Payments Alert */}
        <div className="bg-white rounded-xl shadow-sm border">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <span className="mr-2">⚠️</span>
              Overdue Payments
            </h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {overduePayments.map((client) => (
                <div key={client.id} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-b-0">
                  <div>
                    <p className="font-medium text-gray-900">{client.name}</p>
                    <p className="text-sm text-gray-500">Due: {client.nextDue}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-red-600">${client.amount}</p>
                    <p className="text-sm text-red-500">{client.overdue} days overdue</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Client Management Component
const ClientManagement = () => {
  const [clients, setClients] = useState(mockClients);
  const [isAddingClient, setIsAddingClient] = useState(false);
  const [editingClient, setEditingClient] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('all');
  const [membershipFilter, setMembershipFilter] = useState('all');
  const clientsPerPage = 10;

  const [newClient, setNewClient] = useState({
    name: '',
    email: '',
    phone: '',
    membershipType: 'Monthly',
    amount: 59
  });

  const membershipPricing = {
    'Student': 29,
    'Monthly': 59,
    'Custom': 99
  };

  const filteredClients = clients.filter(client => {
    const matchesSearch = client.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         client.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         client.phone.includes(searchTerm);
    
    const matchesStatus = statusFilter === 'all' || client.status.toLowerCase() === statusFilter.toLowerCase();
    
    const matchesMembership = membershipFilter === 'all' || client.membershipType === membershipFilter;
    
    return matchesSearch && matchesStatus && matchesMembership;
  });

  // Pagination logic
  const totalPages = Math.ceil(filteredClients.length / clientsPerPage);
  const startIndex = (currentPage - 1) * clientsPerPage;
  const paginatedClients = filteredClients.slice(startIndex, startIndex + clientsPerPage);

  // Reset to first page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, statusFilter, membershipFilter]);

  const handleAddClient = (e) => {
    e.preventDefault();
    const client = {
      ...newClient,
      id: Date.now(),
      joinDate: new Date().toISOString().split('T')[0],
      lastPayment: new Date().toISOString().split('T')[0],
      nextDue: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      status: 'Active',
      overdue: 0,
      amount: membershipPricing[newClient.membershipType] || newClient.amount
    };
    setClients([...clients, client]);
    setNewClient({ name: '', email: '', phone: '', membershipType: 'Monthly', amount: 59 });
    setIsAddingClient(false);
  };

  const handleEditClient = (client) => {
    setEditingClient(client);
    setNewClient(client);
    setIsAddingClient(true);
  };

  const handleUpdateClient = (e) => {
    e.preventDefault();
    setClients(clients.map(c => c.id === editingClient.id ? { ...newClient, amount: membershipPricing[newClient.membershipType] || newClient.amount } : c));
    setNewClient({ name: '', email: '', phone: '', membershipType: 'Monthly', amount: 59 });
    setIsAddingClient(false);
    setEditingClient(null);
  };

  const handleDeleteClient = (clientId) => {
    if (window.confirm('Are you sure you want to delete this client?')) {
      setClients(clients.filter(c => c.id !== clientId));
    }
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Client Management</h1>
            <p className="text-gray-600 mt-2">Manage your gym members and their information</p>
          </div>
          <button
            onClick={() => setIsAddingClient(true)}
            className="bg-gradient-to-r from-red-500 to-orange-500 text-white px-6 py-3 rounded-lg font-semibold hover:from-red-600 hover:to-orange-600 transition-all"
          >
            + Add New Client
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="mb-6 grid md:grid-cols-4 gap-4">
        <div className="md:col-span-2">
          <input
            type="text"
            placeholder="Search by name, email, or phone..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
        >
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="overdue">Overdue</option>
        </select>
        <select
          value={membershipFilter}
          onChange={(e) => setMembershipFilter(e.target.value)}
          className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
        >
          <option value="all">All Memberships</option>
          <option value="Student">Student</option>
          <option value="Monthly">Monthly</option>
          <option value="Custom">Custom</option>
        </select>
      </div>

      {/* Results Summary */}
      <div className="mb-4 flex items-center justify-between">
        <p className="text-gray-600">
          Showing {paginatedClients.length} of {filteredClients.length} clients
          {searchTerm && ` matching "${searchTerm}"`}
        </p>
        <div className="text-sm text-gray-500">
          Page {currentPage} of {totalPages}
        </div>
      </div>

      {/* Add/Edit Client Modal */}
      {isAddingClient && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-8 w-full max-w-md mx-4">
            <h3 className="text-xl font-bold text-gray-900 mb-6">
              {editingClient ? 'Edit Client' : 'Add New Client'}
            </h3>
            <form onSubmit={editingClient ? handleUpdateClient : handleAddClient} className="space-y-4">
              <input
                type="text"
                placeholder="Full Name"
                value={newClient.name}
                onChange={(e) => setNewClient({...newClient, name: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                required
              />
              <input
                type="email"
                placeholder="Email"
                value={newClient.email}
                onChange={(e) => setNewClient({...newClient, email: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                required
              />
              <input
                type="tel"
                placeholder="Phone Number"
                value={newClient.phone}
                onChange={(e) => setNewClient({...newClient, phone: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                required
              />
              <select
                value={newClient.membershipType}
                onChange={(e) => setNewClient({
                  ...newClient, 
                  membershipType: e.target.value,
                  amount: membershipPricing[e.target.value] || newClient.amount
                })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
              >
                <option value="Student">Student - $29/month</option>
                <option value="Monthly">Monthly - $59/month</option>
                <option value="Custom">Custom - $99/month</option>
              </select>
              
              <div className="flex space-x-4">
                <button
                  type="submit"
                  className="flex-1 bg-gradient-to-r from-red-500 to-orange-500 text-white py-3 rounded-lg font-semibold hover:from-red-600 hover:to-orange-600 transition-all"
                >
                  {editingClient ? 'Update Client' : 'Add Client'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsAddingClient(false);
                    setEditingClient(null);
                    setNewClient({ name: '', email: '', phone: '', membershipType: 'Monthly', amount: 59 });
                  }}
                  className="flex-1 border border-gray-300 text-gray-700 py-3 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Clients Table */}
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Client</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Contact</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Membership</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Status</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Next Due</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {paginatedClients.map((client) => (
                <tr key={client.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div>
                      <p className="font-medium text-gray-900">{client.name}</p>
                      <p className="text-sm text-gray-500">Joined: {client.joinDate}</p>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div>
                      <p className="text-sm text-gray-900">{client.email}</p>
                      <p className="text-sm text-gray-500">{client.phone}</p>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div>
                      <p className="font-medium text-gray-900">{client.membershipType}</p>
                      <p className="text-sm text-gray-500">${client.amount}/month</p>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      client.status === 'Active' 
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {client.status}
                      {client.overdue > 0 && ` (${client.overdue} days)`}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <p className="text-sm text-gray-900">{client.nextDue}</p>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleEditClient(client)}
                        className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDeleteClient(client.id)}
                        className="text-red-600 hover:text-red-800 text-sm font-medium"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="mt-6 flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6">
            <div className="flex flex-1 justify-between sm:hidden">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className={`relative inline-flex items-center rounded-md px-4 py-2 text-sm font-medium ${
                  currentPage === 1
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
                }`}
              >
                Previous
              </button>
              <button
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className={`relative ml-3 inline-flex items-center rounded-md px-4 py-2 text-sm font-medium ${
                  currentPage === totalPages
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
                }`}
              >
                Next
              </button>
            </div>
            <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Showing <span className="font-medium">{startIndex + 1}</span> to{' '}
                  <span className="font-medium">
                    {Math.min(startIndex + clientsPerPage, filteredClients.length)}
                  </span>{' '}
                  of <span className="font-medium">{filteredClients.length}</span> results
                </p>
              </div>
              <div>
                <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span className="sr-only">Previous</span>
                    <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z" clipRule="evenodd" />
                    </svg>
                  </button>
                  
                  {[...Array(totalPages)].map((_, index) => {
                    const pageNumber = index + 1;
                    const isCurrentPage = pageNumber === currentPage;
                    const isVisible = pageNumber === 1 || pageNumber === totalPages || 
                                    Math.abs(pageNumber - currentPage) <= 2;
                    
                    if (!isVisible) {
                      if (pageNumber === currentPage - 3 || pageNumber === currentPage + 3) {
                        return (
                          <span key={pageNumber} className="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-700 ring-1 ring-inset ring-gray-300">
                            ...
                          </span>
                        );
                      }
                      return null;
                    }
                    
                    return (
                      <button
                        key={pageNumber}
                        onClick={() => setCurrentPage(pageNumber)}
                        className={`relative inline-flex items-center px-4 py-2 text-sm font-semibold ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 ${
                          isCurrentPage
                            ? 'z-10 bg-red-600 text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-600'
                            : 'text-gray-900'
                        }`}
                      >
                        {pageNumber}
                      </button>
                    );
                  })}
                  
                  <button
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                    className="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span className="sr-only">Next</span>
                    <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clipRule="evenodd" />
                    </svg>
                  </button>
                </nav>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Payment Tracking Component
const PaymentTracking = () => {
  const [clients, setClients] = useState(mockClients);
  const [selectedClient, setSelectedClient] = useState(null);
  const [isRecordingPayment, setIsRecordingPayment] = useState(false);
  const [paymentAmount, setPaymentAmount] = useState('');

  const overdueClients = clients.filter(c => c.status === 'Overdue');
  const upcomingDues = clients.filter(c => {
    const dueDate = new Date(c.nextDue);
    const today = new Date();
    const daysDiff = Math.ceil((dueDate - today) / (1000 * 60 * 60 * 24));
    return daysDiff <= 7 && daysDiff > 0;
  });

  const handleRecordPayment = (client) => {
    setSelectedClient(client);
    setPaymentAmount(client.amount.toString());
    setIsRecordingPayment(true);
  };

  const handleSubmitPayment = (e) => {
    e.preventDefault();
    const updatedClients = clients.map(c => {
      if (c.id === selectedClient.id) {
        const today = new Date();
        const nextDue = new Date(today);
        nextDue.setMonth(nextDue.getMonth() + 1);
        
        return {
          ...c,
          lastPayment: today.toISOString().split('T')[0],
          nextDue: nextDue.toISOString().split('T')[0],
          status: 'Active',
          overdue: 0
        };
      }
      return c;
    });
    
    setClients(updatedClients);
    setIsRecordingPayment(false);
    setSelectedClient(null);
    setPaymentAmount('');
  };

  const sendReminder = (client) => {
    // In a real app, this would send email/SMS
    alert(`Reminder sent to ${client.name} (${client.email})`);
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Payment Tracking</h1>
        <p className="text-gray-600 mt-2">Monitor payments and send reminders to clients</p>
      </div>

      {/* Payment Recording Modal */}
      {isRecordingPayment && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-8 w-full max-w-md mx-4">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Record Payment</h3>
            <form onSubmit={handleSubmitPayment} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Client</label>
                <input
                  type="text"
                  value={selectedClient?.name || ''}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg bg-gray-50"
                  disabled
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Payment Amount</label>
                <input
                  type="number"
                  value={paymentAmount}
                  onChange={(e) => setPaymentAmount(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Payment Date</label>
                <input
                  type="date"
                  defaultValue={new Date().toISOString().split('T')[0]}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  required
                />
              </div>
              
              <div className="flex space-x-4">
                <button
                  type="submit"
                  className="flex-1 bg-gradient-to-r from-red-500 to-orange-500 text-white py-3 rounded-lg font-semibold hover:from-red-600 hover:to-orange-600 transition-all"
                >
                  Record Payment
                </button>
                <button
                  type="button"
                  onClick={() => setIsRecordingPayment(false)}
                  className="flex-1 border border-gray-300 text-gray-700 py-3 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Overdue Payments */}
        <div className="bg-white rounded-xl shadow-sm border">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <span className="mr-2">🚨</span>
              Overdue Payments ({overdueClients.length})
            </h3>
          </div>
          <div className="p-6">
            {overdueClients.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No overdue payments! 🎉</p>
            ) : (
              <div className="space-y-4">
                {overdueClients.map((client) => (
                  <div key={client.id} className="border border-red-200 rounded-lg p-4 bg-red-50">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h4 className="font-medium text-gray-900">{client.name}</h4>
                        <p className="text-sm text-gray-600">{client.email}</p>
                        <p className="text-sm text-red-600 font-medium">
                          ${client.amount} - {client.overdue} days overdue
                        </p>
                      </div>
                      <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full">
                        Due: {client.nextDue}
                      </span>
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleRecordPayment(client)}
                        className="flex-1 bg-green-500 text-white py-2 px-4 rounded-lg text-sm font-medium hover:bg-green-600 transition-colors"
                      >
                        Record Payment
                      </button>
                      <button
                        onClick={() => sendReminder(client)}
                        className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors"
                      >
                        Send Reminder
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Upcoming Dues */}
        <div className="bg-white rounded-xl shadow-sm border">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <span className="mr-2">📅</span>
              Upcoming Dues (Next 7 Days)
            </h3>
          </div>
          <div className="p-6">
            {upcomingDues.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No upcoming dues in the next 7 days</p>
            ) : (
              <div className="space-y-4">
                {upcomingDues.map((client) => {
                  const dueDate = new Date(client.nextDue);
                  const today = new Date();
                  const daysDiff = Math.ceil((dueDate - today) / (1000 * 60 * 60 * 24));
                  
                  return (
                    <div key={client.id} className="border border-orange-200 rounded-lg p-4 bg-orange-50">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h4 className="font-medium text-gray-900">{client.name}</h4>
                          <p className="text-sm text-gray-600">{client.email}</p>
                          <p className="text-sm text-orange-600 font-medium">
                            ${client.amount} - Due in {daysDiff} day{daysDiff !== 1 ? 's' : ''}
                          </p>
                        </div>
                        <span className="px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded-full">
                          {client.nextDue}
                        </span>
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => sendReminder(client)}
                          className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors"
                        >
                          Send Reminder
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* All Clients Payment Status */}
      <div className="mt-8 bg-white rounded-xl shadow-sm border">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">All Clients Payment Status</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Client</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Last Payment</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Next Due</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Amount</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Status</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {clients.map((client) => (
                <tr key={client.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div>
                      <p className="font-medium text-gray-900">{client.name}</p>
                      <p className="text-sm text-gray-500">{client.email}</p>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">{client.lastPayment}</td>
                  <td className="px-6 py-4 text-sm text-gray-900">{client.nextDue}</td>
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">${client.amount}</td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      client.status === 'Active' 
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {client.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleRecordPayment(client)}
                        className="text-green-600 hover:text-green-800 text-sm font-medium"
                      >
                        Record Payment
                      </button>
                      <button
                        onClick={() => sendReminder(client)}
                        className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                      >
                        Send Reminder
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Membership Management Component
const MembershipManagement = () => {
  const [memberships, setMemberships] = useState([
    { id: 1, name: 'Student', price: 29, duration: 'Monthly', benefits: ['Access to all equipment', 'Basic group classes', 'Locker room access'] },
    { id: 2, name: 'Monthly', price: 59, duration: 'Monthly', benefits: ['All Student benefits', 'Premium group classes', '1 personal training session', 'Nutrition consultation'] },
    { id: 3, name: 'Custom', price: 99, duration: 'Monthly', benefits: ['All Monthly benefits', 'Unlimited personal training', 'Priority booking', 'Meal planning'] }
  ]);

  const [isEditing, setIsEditing] = useState(false);
  const [editingMembership, setEditingMembership] = useState(null);
  const [newMembership, setNewMembership] = useState({
    name: '',
    price: '',
    duration: 'Monthly',
    benefits: ['']
  });

  const handleEditMembership = (membership) => {
    setEditingMembership(membership);
    setNewMembership(membership);
    setIsEditing(true);
  };

  const handleUpdateMembership = (e) => {
    e.preventDefault();
    setMemberships(memberships.map(m => m.id === editingMembership.id ? { ...newMembership, id: editingMembership.id } : m));
    setIsEditing(false);
    setEditingMembership(null);
    setNewMembership({ name: '', price: '', duration: 'Monthly', benefits: [''] });
  };

  const addBenefit = () => {
    setNewMembership({
      ...newMembership,
      benefits: [...newMembership.benefits, '']
    });
  };

  const updateBenefit = (index, value) => {
    const updatedBenefits = [...newMembership.benefits];
    updatedBenefits[index] = value;
    setNewMembership({
      ...newMembership,
      benefits: updatedBenefits
    });
  };

  const removeBenefit = (index) => {
    setNewMembership({
      ...newMembership,
      benefits: newMembership.benefits.filter((_, i) => i !== index)
    });
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Membership Management</h1>
        <p className="text-gray-600 mt-2">Manage membership plans and pricing</p>
      </div>

      {/* Edit Membership Modal */}
      {isEditing && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-8 w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Edit Membership Plan</h3>
            <form onSubmit={handleUpdateMembership} className="space-y-4">
              <input
                type="text"
                placeholder="Membership Name"
                value={newMembership.name}
                onChange={(e) => setNewMembership({...newMembership, name: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                required
              />
              <input
                type="number"
                placeholder="Price"
                value={newMembership.price}
                onChange={(e) => setNewMembership({...newMembership, price: parseInt(e.target.value)})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                required
              />
              <select
                value={newMembership.duration}
                onChange={(e) => setNewMembership({...newMembership, duration: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
              >
                <option value="Monthly">Monthly</option>
                <option value="Quarterly">Quarterly</option>
                <option value="Annual">Annual</option>
              </select>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Benefits</label>
                {newMembership.benefits.map((benefit, index) => (
                  <div key={index} className="flex space-x-2 mb-2">
                    <input
                      type="text"
                      value={benefit}
                      onChange={(e) => updateBenefit(index, e.target.value)}
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                      placeholder="Enter benefit"
                    />
                    <button
                      type="button"
                      onClick={() => removeBenefit(index)}
                      className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg"
                    >
                      ✕
                    </button>
                  </div>
                ))}
                <button
                  type="button"
                  onClick={addBenefit}
                  className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                >
                  + Add Benefit
                </button>
              </div>
              
              <div className="flex space-x-4">
                <button
                  type="submit"
                  className="flex-1 bg-gradient-to-r from-red-500 to-orange-500 text-white py-3 rounded-lg font-semibold hover:from-red-600 hover:to-orange-600 transition-all"
                >
                  Update Plan
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsEditing(false);
                    setEditingMembership(null);
                    setNewMembership({ name: '', price: '', duration: 'Monthly', benefits: [''] });
                  }}
                  className="flex-1 border border-gray-300 text-gray-700 py-3 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Membership Plans */}
      <div className="grid lg:grid-cols-3 gap-8">
        {memberships.map((membership) => (
          <div key={membership.id} className="bg-white rounded-xl shadow-sm border p-6 hover:shadow-md transition-shadow">
            <div className="text-center mb-6">
              <h3 className="text-xl font-bold text-gray-900 mb-2">{membership.name}</h3>
              <div className="flex items-baseline justify-center mb-4">
                <span className="text-4xl font-bold text-gray-900">${membership.price}</span>
                <span className="text-gray-500 ml-1">/{membership.duration.toLowerCase()}</span>
              </div>
            </div>
            
            <ul className="space-y-3 mb-8">
              {membership.benefits.map((benefit, index) => (
                <li key={index} className="flex items-center text-gray-700">
                  <span className="text-green-500 mr-3">✓</span>
                  {benefit}
                </li>
              ))}
            </ul>
            
            <button
              onClick={() => handleEditMembership(membership)}
              className="w-full bg-gradient-to-r from-red-500 to-orange-500 text-white py-3 rounded-lg font-semibold hover:from-red-600 hover:to-orange-600 transition-all"
            >
              Edit Plan
            </button>
          </div>
        ))}
      </div>

      {/* Membership Statistics */}
      <div className="mt-12 bg-white rounded-xl shadow-sm border">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Membership Statistics</h3>
        </div>
        <div className="p-6">
          <div className="grid md:grid-cols-3 gap-6">
            {memberships.map((membership) => {
              const memberCount = mockClients.filter(c => c.membershipType === membership.name).length;
              const revenue = memberCount * membership.price;
              
              return (
                <div key={membership.id} className="text-center">
                  <h4 className="font-semibold text-gray-900 mb-2">{membership.name} Members</h4>
                  <p className="text-3xl font-bold text-blue-600 mb-1">{memberCount}</p>
                  <p className="text-sm text-gray-500">Monthly Revenue: ${revenue}</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

// Reports Component
const Reports = () => {
  const totalRevenue = mockClients.reduce((sum, client) => sum + client.amount, 0);
  const activeMembers = mockClients.filter(c => c.status === 'Active').length;
  const overdueAmount = mockClients.reduce((sum, client) => sum + (client.status === 'Overdue' ? client.amount * client.overdue : 0), 0);

  const membershipBreakdown = mockClients.reduce((acc, client) => {
    acc[client.membershipType] = (acc[client.membershipType] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Reports & Analytics</h1>
        <p className="text-gray-600 mt-2">Track your gym's performance and growth</p>
      </div>

      {/* Revenue Overview */}
      <div className="grid lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-xl p-6 shadow-sm border">
          <h3 className="text-sm font-medium text-gray-600 mb-2">Total Monthly Revenue</h3>
          <p className="text-3xl font-bold text-green-600">${totalRevenue}</p>
          <p className="text-sm text-gray-500 mt-1">+12% from last month</p>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-sm border">
          <h3 className="text-sm font-medium text-gray-600 mb-2">Active Members</h3>
          <p className="text-3xl font-bold text-blue-600">{activeMembers}</p>
          <p className="text-sm text-gray-500 mt-1">+3 new this month</p>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-sm border">
          <h3 className="text-sm font-medium text-gray-600 mb-2">Overdue Amount</h3>
          <p className="text-3xl font-bold text-red-600">${overdueAmount}</p>
          <p className="text-sm text-gray-500 mt-1">2 clients overdue</p>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-sm border">
          <h3 className="text-sm font-medium text-gray-600 mb-2">Collection Rate</h3>
          <p className="text-3xl font-bold text-purple-600">94%</p>
          <p className="text-sm text-gray-500 mt-1">Excellent performance</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Membership Breakdown */}
        <div className="bg-white rounded-xl shadow-sm border">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Membership Breakdown</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {Object.entries(membershipBreakdown).map(([type, count]) => {
                const percentage = ((count / mockClients.length) * 100).toFixed(1);
                return (
                  <div key={type} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className={`w-4 h-4 rounded mr-3 ${
                        type === 'Monthly' ? 'bg-blue-500' :
                        type === 'Student' ? 'bg-green-500' : 'bg-purple-500'
                      }`}></div>
                      <span className="font-medium text-gray-900">{type}</span>
                    </div>
                    <div className="text-right">
                      <span className="font-bold text-gray-900">{count}</span>
                      <span className="text-gray-500 ml-2">({percentage}%)</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-xl shadow-sm border">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
                <span className="text-green-600">💰</span>
                <div>
                  <p className="font-medium text-gray-900">Payment Received</p>
                  <p className="text-sm text-gray-500">John Smith paid $59 - 2 hours ago</p>
                </div>
              </div>
              <div className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
                <span className="text-blue-600">👤</span>
                <div>
                  <p className="font-medium text-gray-900">New Member</p>
                  <p className="text-sm text-gray-500">David Brown joined - 1 day ago</p>
                </div>
              </div>
              <div className="flex items-center space-x-3 p-3 bg-orange-50 rounded-lg">
                <span className="text-orange-600">📧</span>
                <div>
                  <p className="font-medium text-gray-900">Reminder Sent</p>
                  <p className="text-sm text-gray-500">Payment reminder to Sarah Johnson - 2 days ago</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Payment History Table */}
      <div className="mt-8 bg-white rounded-xl shadow-sm border">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Payment History</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Date</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Client</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Amount</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Type</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {mockClients.map((client) => (
                <tr key={client.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm text-gray-900">{client.lastPayment}</td>
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{client.name}</td>
                  <td className="px-6 py-4 text-sm text-gray-900">${client.amount}</td>
                  <td className="px-6 py-4 text-sm text-gray-900">{client.membershipType}</td>
                  <td className="px-6 py-4">
                    <span className="px-3 py-1 bg-green-100 text-green-800 text-sm rounded-full">
                      Completed
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Settings Component
const Settings = ({ user }) => {
  const [settings, setSettings] = useState({
    gymName: 'Alphalete Athletics Club',
    address: '123 Fitness Street, City, State 12345',
    phone: '(555) 123-4567',
    email: 'info@alphalete.com',
    reminderDays: 3,
    autoReminders: true,
    lateFeeDays: 7,
    lateFeeAmount: 10
  });

  const handleSaveSettings = (e) => {
    e.preventDefault();
    // In a real app, this would save to backend
    alert('Settings saved successfully!');
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-2">Manage your gym settings and preferences</p>
      </div>

      <div className="max-w-2xl">
        <form onSubmit={handleSaveSettings} className="space-y-8">
          {/* Gym Information */}
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Gym Information</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Gym Name</label>
                <input
                  type="text"
                  value={settings.gymName}
                  onChange={(e) => setSettings({...settings, gymName: e.target.value})}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Address</label>
                <input
                  type="text"
                  value={settings.address}
                  onChange={(e) => setSettings({...settings, address: e.target.value})}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Phone</label>
                  <input
                    type="tel"
                    value={settings.phone}
                    onChange={(e) => setSettings({...settings, phone: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                  <input
                    type="email"
                    value={settings.email}
                    onChange={(e) => setSettings({...settings, email: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Payment Settings */}
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Payment Settings</h3>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Reminder Days Before Due</label>
                  <input
                    type="number"
                    value={settings.reminderDays}
                    onChange={(e) => setSettings({...settings, reminderDays: parseInt(e.target.value)})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Late Fee After (days)</label>
                  <input
                    type="number"
                    value={settings.lateFeeDays}
                    onChange={(e) => setSettings({...settings, lateFeeDays: parseInt(e.target.value)})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Late Fee Amount ($)</label>
                <input
                  type="number"
                  value={settings.lateFeeAmount}
                  onChange={(e) => setSettings({...settings, lateFeeAmount: parseInt(e.target.value)})}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                />
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="autoReminders"
                  checked={settings.autoReminders}
                  onChange={(e) => setSettings({...settings, autoReminders: e.target.checked})}
                  className="w-4 h-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
                />
                <label htmlFor="autoReminders" className="ml-2 text-sm text-gray-700">
                  Enable automatic payment reminders
                </label>
              </div>
            </div>
          </div>

          <button
            type="submit"
            className="w-full bg-gradient-to-r from-red-500 to-orange-500 text-white py-3 rounded-lg font-semibold hover:from-red-600 hover:to-orange-600 transition-all"
          >
            Save Settings
          </button>
        </form>
      </div>
    </div>
  );
};

// Install Prompt Component
const InstallPrompt = ({ onInstall, onDismiss }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl p-6 max-w-sm w-full mx-4 text-center">
        <div className="w-16 h-16 bg-gradient-to-r from-red-500 to-orange-500 rounded-xl flex items-center justify-center mx-auto mb-4">
          <span className="text-white font-bold text-2xl">📱</span>
        </div>
        <h3 className="text-xl font-bold text-gray-900 mb-2">Install Gym Management App</h3>
        <p className="text-gray-600 mb-6">
          Add Alphalete Athletics to your home screen for quick access and a better experience!
        </p>
        <div className="flex space-x-3">
          <button
            onClick={onInstall}
            className="flex-1 bg-gradient-to-r from-red-500 to-orange-500 text-white py-3 rounded-lg font-semibold hover:from-red-600 hover:to-orange-600 transition-all"
          >
            Install App
          </button>
          <button
            onClick={onDismiss}
            className="flex-1 border border-gray-300 text-gray-700 py-3 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
          >
            Later
          </button>
        </div>
      </div>
    </div>
  );
};

const Components = {
  Sidebar,
  Dashboard,
  ClientManagement,
  PaymentTracking,
  MembershipManagement,
  Reports,
  Settings,
  LoginForm,
  InstallPrompt
};

export default Components;