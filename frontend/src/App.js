import { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import LocalStorageManager from "./LocalStorageManager";

// Initialize local storage manager
const localDB = new LocalStorageManager();

// PWA Status Component
const PWAStatus = () => {
  const [connectionStatus, setConnectionStatus] = useState({ online: navigator.onLine, message: '' });
  
  useEffect(() => {
    const updateStatus = () => {
      const status = localDB.getConnectionStatus();
      setConnectionStatus(status);
    };
    
    window.addEventListener('online', updateStatus);
    window.addEventListener('offline', updateStatus);
    updateStatus();
    
    return () => {
      window.removeEventListener('online', updateStatus);
      window.removeEventListener('offline', updateStatus);
    };
  }, []);
  
  return (
    <div className={`fixed top-0 left-0 right-0 z-50 px-4 py-2 text-center text-sm font-medium ${
      connectionStatus.online 
        ? 'bg-green-600 text-white' 
        : 'bg-orange-500 text-white'
    }`}>
      {connectionStatus.online ? '🌐 Online' : '📱 Offline'} - {connectionStatus.message}
    </div>
  );
};

// Navigation Component
const Navigation = ({ currentPage }) => {
  const [isOpen, setIsOpen] = useState(false);

  const menuItems = [
    { path: "/", icon: "📊", label: "Dashboard", description: "Overview & Stats" },
    { path: "/clients", icon: "👥", label: "Client Management", description: "Manage Members" },
    { path: "/add-client", icon: "➕", label: "Add Client", description: "New Member" },
    { path: "/payments", icon: "💳", label: "Payments", description: "Payment Tracking" },
    { path: "/email-center", icon: "📧", label: "Email Center", description: "Send Reminders" },
    { path: "/reports", icon: "📈", label: "Reports", description: "Analytics" },
    { path: "/settings", icon: "⚙️", label: "Settings", description: "Configuration" },
  ];

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="md:hidden fixed top-14 left-4 z-50 bg-red-600 text-white p-2 rounded-lg"
      >
        {isOpen ? "✕" : "☰"}
      </button>

      {/* Sidebar */}
      <div className={`fixed left-0 top-12 h-full w-64 bg-gray-900 border-r border-gray-700 transform transition-transform duration-300 z-40 ${
        isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
      }`}>
        {/* Logo Header */}
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="text-2xl">🏋️‍♂️</div>
            <div>
              <h1 className="text-lg font-bold text-white">ALPHALETE</h1>
              <p className="text-xs text-red-400">ATHLETICS CLUB</p>
            </div>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="p-4">
          <ul className="space-y-2">
            {menuItems.map((item) => (
              <li key={item.path}>
                <Link
                  to={item.path}
                  onClick={() => setIsOpen(false)}
                  className={`flex items-center space-x-3 p-3 rounded-lg transition-all duration-200 ${
                    currentPage === item.path
                      ? "bg-red-600 text-white shadow-lg"
                      : "text-gray-300 hover:bg-gray-800 hover:text-white"
                  }`}
                >
                  <span className="text-xl">{item.icon}</span>
                  <div>
                    <div className="font-semibold">{item.label}</div>
                    <div className="text-xs opacity-75">{item.description}</div>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        {/* Footer */}
        <div className="absolute bottom-4 left-4 right-4">
          <div className="bg-gray-800 p-3 rounded-lg text-center">
            <div className="text-xs text-gray-400">PWA - Offline Ready</div>
            <div className="text-xs text-red-400 font-semibold">v2.1.0</div>
          </div>
        </div>
      </div>

      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-30 md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
};

// Main Layout Component
const Layout = ({ children }) => {
  const location = useLocation();
  
  return (
    <div className="min-h-screen bg-gray-900 text-white pt-12">
      <PWAStatus />
      <Navigation currentPage={location.pathname} />
      <div className="md:ml-64">
        {children}
      </div>
    </div>
  );
};

// Dashboard Component (Using Local Storage)
const Dashboard = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({
    totalClients: 0,
    activeMembers: 0,
    monthlyRevenue: 0,
    pendingPayments: 0
  });

  const fetchClients = async () => {
    try {
      setLoading(true);
      const result = await localDB.getClients();
      setClients(result.data);
      
      // Calculate stats
      const activeMembers = result.data.filter(c => c.status === "Active");
      const monthlyRevenue = activeMembers.reduce((sum, c) => sum + c.monthly_fee, 0);
      
      setStats({
        totalClients: result.data.length,
        activeMembers: activeMembers.length,
        monthlyRevenue: monthlyRevenue,
        pendingPayments: activeMembers.length
      });
    } catch (error) {
      console.error("Error fetching clients:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClients();
  }, []);

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
        <p className="text-gray-400">Welcome back! Here's what's happening at your gym.</p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-6 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-200">Total Clients</p>
              <p className="text-3xl font-bold text-white">{stats.totalClients}</p>
            </div>
            <div className="text-4xl text-blue-200">👥</div>
          </div>
        </div>
        
        <div className="bg-gradient-to-r from-green-600 to-green-700 p-6 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-200">Active Members</p>
              <p className="text-3xl font-bold text-white">{stats.activeMembers}</p>
            </div>
            <div className="text-4xl text-green-200">💪</div>
          </div>
        </div>
        
        <div className="bg-gradient-to-r from-purple-600 to-purple-700 p-6 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-200">Monthly Revenue</p>
              <p className="text-3xl font-bold text-white">${stats.monthlyRevenue.toFixed(2)}</p>
            </div>
            <div className="text-4xl text-purple-200">💰</div>
          </div>
        </div>
        
        <div className="bg-gradient-to-r from-orange-600 to-orange-700 p-6 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-orange-200">Pending Payments</p>
              <p className="text-3xl font-bold text-white">{stats.pendingPayments}</p>
            </div>
            <div className="text-4xl text-orange-200">⏰</div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Link to="/add-client" className="bg-gray-800 p-6 rounded-lg border border-gray-700 hover:border-red-600 transition-all">
          <div className="text-4xl mb-4">➕</div>
          <h3 className="text-xl font-semibold mb-2">Add New Client</h3>
          <p className="text-gray-400">Register a new gym member</p>
        </Link>
        
        <Link to="/email-center" className="bg-gray-800 p-6 rounded-lg border border-gray-700 hover:border-red-600 transition-all">
          <div className="text-4xl mb-4">📧</div>
          <h3 className="text-xl font-semibold mb-2">Send Reminders</h3>
          <p className="text-gray-400">Email payment reminders to clients</p>
        </Link>
        
        <Link to="/settings" className="bg-gray-800 p-6 rounded-lg border border-gray-700 hover:border-red-600 transition-all">
          <div className="text-4xl mb-4">⚙️</div>
          <h3 className="text-xl font-semibold mb-2">Manage Settings</h3>
          <p className="text-gray-400">Configure membership types</p>
        </Link>
      </div>

      {/* Recent Activity */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
        <h3 className="text-xl font-semibold mb-4">Recent Clients</h3>
        {loading ? (
          <div className="text-center py-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600 mx-auto"></div>
            <p className="mt-2 text-gray-400">Loading...</p>
          </div>
        ) : clients.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-4">👋</div>
            <p className="text-gray-400">No clients yet. Add your first client to get started!</p>
          </div>
        ) : (
          <div className="space-y-4">
            {clients.slice(0, 5).map((client) => (
              <div key={client.id} className="flex items-center justify-between py-2 border-b border-gray-700 last:border-b-0">
                <div className="flex items-center space-x-4">
                  <div className="w-10 h-10 bg-red-600 rounded-full flex items-center justify-center font-semibold">
                    {client.name.charAt(0)}
                  </div>
                  <div>
                    <p className="font-semibold">{client.name}</p>
                    <p className="text-sm text-gray-400">{client.membership_type} • ${client.monthly_fee}/month</p>
                    <p className="text-xs text-gray-500">Started: {new Date(client.start_date).toLocaleDateString()}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                  client.status === 'Active' 
                    ? 'bg-green-900 text-green-300' 
                    : 'bg-red-900 text-red-300'
                }`}>
                  {client.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Client Management Component (Using Local Storage)
const ClientManagement = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  const fetchClients = async () => {
    try {
      setLoading(true);
      const result = await localDB.getClients();
      setClients(result.data);
    } catch (error) {
      console.error("Error fetching clients:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClients();
  }, []);

  const sendPaymentReminder = async (client) => {
    if (!navigator.onLine) {
      alert("Email functionality requires an internet connection.");
      return;
    }

    try {
      // This would be handled by the service worker
      const response = await fetch('/api/email/payment-reminder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_id: client.id })
      });
      
      const result = await response.json();
      
      if (result.offline) {
        alert("You're offline. Email functionality requires an internet connection.");
      } else if (result.success) {
        alert(`Payment reminder sent successfully to ${result.client_email || client.email}`);
      } else {
        alert(`Failed to send payment reminder: ${result.message}`);
      }
    } catch (error) {
      console.error("Error sending payment reminder:", error);
      alert("Error sending payment reminder. Check your internet connection.");
    }
  };

  const filteredClients = clients.filter(client =>
    client.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    client.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Client Management</h1>
        <p className="text-gray-400">Manage your gym members and their information.</p>
      </div>

      {/* Search and Actions */}
      <div className="mb-6 flex flex-col md:flex-row gap-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search clients by name or email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
          />
        </div>
        <Link
          to="/add-client"
          className="bg-red-600 hover:bg-red-700 px-6 py-3 rounded-lg font-semibold whitespace-nowrap"
        >
          ➕ Add Client
        </Link>
      </div>

      {/* Client Table */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
            <p className="mt-4 text-gray-400">Loading clients...</p>
          </div>
        ) : filteredClients.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-6xl mb-4">💪</div>
            <p className="text-gray-400 text-lg mb-4">
              {searchTerm ? "No clients found matching your search" : "No clients yet"}
            </p>
            {!searchTerm && (
              <Link 
                to="/add-client"
                className="bg-red-600 hover:bg-red-700 px-6 py-3 rounded-lg font-semibold inline-block"
              >
                Add Your First Client
              </Link>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-700">
                <tr>
                  <th className="text-left p-4">Name</th>
                  <th className="text-left p-4">Email</th>
                  <th className="text-left p-4">Phone</th>
                  <th className="text-left p-4">Membership</th>
                  <th className="text-left p-4">Monthly Fee</th>
                  <th className="text-left p-4">Start Date</th>
                  <th className="text-left p-4">Next Payment</th>
                  <th className="text-left p-4">Status</th>
                  <th className="text-left p-4">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredClients.map((client) => (
                  <tr key={client.id} className="border-b border-gray-700 hover:bg-gray-750">
                    <td className="p-4">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-red-600 rounded-full flex items-center justify-center font-semibold text-sm">
                          {client.name.charAt(0)}
                        </div>
                        <div className="font-semibold">{client.name}</div>
                      </div>
                    </td>
                    <td className="p-4 text-gray-300">{client.email}</td>
                    <td className="p-4 text-gray-300">{client.phone || "N/A"}</td>
                    <td className="p-4">{client.membership_type}</td>
                    <td className="p-4 font-semibold text-green-400">${client.monthly_fee}</td>
                    <td className="p-4">{new Date(client.start_date).toLocaleDateString()}</td>
                    <td className="p-4">{new Date(client.next_payment_date).toLocaleDateString()}</td>
                    <td className="p-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                        client.status === 'Active' 
                          ? 'bg-green-900 text-green-300' 
                          : 'bg-red-900 text-red-300'
                      }`}>
                        {client.status}
                      </span>
                    </td>
                    <td className="p-4">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => sendPaymentReminder(client)}
                          className={`px-3 py-1 rounded text-sm font-semibold ${
                            navigator.onLine 
                              ? 'bg-blue-600 hover:bg-blue-700' 
                              : 'bg-gray-600 cursor-not-allowed'
                          }`}
                          disabled={!navigator.onLine}
                          title={navigator.onLine ? "Send Payment Reminder" : "Requires internet connection"}
                        >
                          📧
                        </button>
                        <button
                          className="bg-gray-600 hover:bg-gray-700 px-3 py-1 rounded text-sm font-semibold"
                          title="Edit Client"
                        >
                          ✏️
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

// Add Client Component (Using Local Storage)
const AddClient = () => {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    membership_type: "",
    monthly_fee: 50.00,
    start_date: ""
  });
  const [membershipTypes, setMembershipTypes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [typesLoading, setTypesLoading] = useState(false);

  // Fetch membership types from local storage
  const fetchMembershipTypes = async () => {
    try {
      setTypesLoading(true);
      const result = await localDB.getMembershipTypes();
      setMembershipTypes(result.data.filter(type => type.is_active));
      
      // Set first membership type as default if available
      const activeTypes = result.data.filter(type => type.is_active);
      if (activeTypes.length > 0) {
        setFormData(prev => ({
          ...prev,
          membership_type: activeTypes[0].name,
          monthly_fee: activeTypes[0].monthly_fee
        }));
      }
    } catch (error) {
      console.error("Error fetching membership types:", error);
    } finally {
      setTypesLoading(false);
    }
  };

  useEffect(() => {
    fetchMembershipTypes();
    
    // Set default start date to today
    const today = new Date().toISOString().split('T')[0];
    setFormData(prev => ({ ...prev, start_date: today }));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await localDB.addClient(formData);
      alert("Client added successfully! Next payment date automatically calculated for 30 days from start date. Data saved locally and will sync when online.");
      setFormData({
        name: "",
        email: "",
        phone: "",
        membership_type: membershipTypes.length > 0 ? membershipTypes[0].name : "",
        monthly_fee: membershipTypes.length > 0 ? membershipTypes[0].monthly_fee : 50.00,
        start_date: new Date().toISOString().split('T')[0]
      });
    } catch (error) {
      console.error("Error adding client:", error);
      alert("Error adding client: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'monthly_fee' ? parseFloat(value) || 0 : value
    }));
  };

  const handleMembershipChange = (selectedType) => {
    const selectedMembership = membershipTypes.find(m => m.name === selectedType.name);
    if (selectedMembership) {
      setFormData(prev => ({
        ...prev,
        membership_type: selectedMembership.name,
        monthly_fee: selectedMembership.monthly_fee
      }));
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Add New Client</h1>
        <p className="text-gray-400">Register a new member to your gym. Payment date will be automatically set to 30 days from start date.</p>
      </div>

      <div className="max-w-2xl">
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2">Client Name *</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
                placeholder="Enter client's full name"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Email Address *</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
                placeholder="client@example.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Phone Number</label>
              <input
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
                placeholder="(555) 123-4567"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Start Date *</label>
              <input
                type="date"
                name="start_date"
                value={formData.start_date}
                onChange={handleChange}
                required
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
              />
              <p className="text-sm text-gray-400 mt-1">Next payment date will be automatically set to 30 days from this date</p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-3">Membership Type</label>
              {typesLoading ? (
                <div className="text-center py-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-red-600 mx-auto"></div>
                  <p className="mt-2 text-gray-400 text-sm">Loading membership types...</p>
                </div>
              ) : membershipTypes.length === 0 ? (
                <div className="text-center py-4">
                  <p className="text-gray-400">No membership types available. Please configure them in Settings.</p>
                  <Link to="/settings" className="text-red-400 hover:text-red-300 underline text-sm">Go to Settings</Link>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {membershipTypes.map((plan) => (
                    <label key={plan.id} className={`cursor-pointer border-2 rounded-lg p-4 transition-all ${
                      formData.membership_type === plan.name
                        ? 'border-red-600 bg-red-600/10'
                        : 'border-gray-600 hover:border-gray-500'
                    }`}>
                      <input
                        type="radio"
                        name="membership_type"
                        value={plan.name}
                        checked={formData.membership_type === plan.name}
                        onChange={(e) => {
                          handleMembershipChange(plan);
                        }}
                        className="sr-only"
                      />
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h4 className="font-semibold">{plan.name}</h4>
                          <p className="text-sm text-gray-400">{plan.description}</p>
                        </div>
                        <div className="text-lg font-bold text-green-400">${plan.monthly_fee}</div>
                      </div>
                      {plan.features && plan.features.length > 0 && (
                        <div className="mt-2">
                          <ul className="text-xs text-gray-300 space-y-1">
                            {plan.features.slice(0, 3).map((feature, index) => (
                              <li key={index}>• {feature}</li>
                            ))}
                            {plan.features.length > 3 && (
                              <li className="text-gray-400">• +{plan.features.length - 3} more features</li>
                            )}
                          </ul>
                        </div>
                      )}
                    </label>
                  ))}
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Custom Monthly Fee ($)</label>
              <input
                type="number"
                name="monthly_fee"
                value={formData.monthly_fee}
                onChange={handleChange}
                min="0"
                step="0.01"
                required
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
              />
              <p className="text-sm text-gray-400 mt-1">Override the default fee for this membership type if needed</p>
            </div>

            <div className="pt-4">
              <button
                type="submit"
                disabled={loading || membershipTypes.length === 0}
                className="w-full bg-red-600 hover:bg-red-700 disabled:opacity-50 px-6 py-3 rounded-lg font-semibold text-lg transition"
              >
                {loading ? "Adding Client..." : "Add Client"}
              </button>
              <p className="text-xs text-gray-400 text-center mt-2">Data will be saved locally and sync when online</p>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

// PWA Settings Component with Offline Membership Types Management
const Settings = () => {
  const [membershipTypes, setMembershipTypes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editingType, setEditingType] = useState(null);
  const [isAddingNew, setIsAddingNew] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    monthly_fee: 0,
    description: "",
    features: []
  });

  const fetchMembershipTypes = async () => {
    try {
      setLoading(true);
      const result = await localDB.getMembershipTypes();
      setMembershipTypes(result.data.filter(type => type.is_active));
    } catch (error) {
      console.error("Error fetching membership types:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMembershipTypes();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    
    try {
      if (editingType) {
        await localDB.updateMembershipType(editingType.id, formData);
        alert("Membership type updated successfully! Changes saved locally and will sync when online.");
      } else {
        await localDB.addMembershipType(formData);
        alert("Membership type created successfully! Changes saved locally and will sync when online.");
      }
      
      setFormData({ name: "", monthly_fee: 0, description: "", features: [] });
      setEditingType(null);
      setIsAddingNew(false);
      fetchMembershipTypes();
    } catch (error) {
      console.error("Error saving membership type:", error);
      alert("Error saving membership type: " + error.message);
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (membershipType) => {
    setEditingType(membershipType);
    setFormData({
      name: membershipType.name,
      monthly_fee: membershipType.monthly_fee,
      description: membershipType.description,
      features: [...(membershipType.features || [])]
    });
    setIsAddingNew(false);
  };

  const startAddNew = () => {
    setIsAddingNew(true);
    setEditingType(null);
    setFormData({ name: "", monthly_fee: 0, description: "", features: [] });
  };

  const cancelEdit = () => {
    setEditingType(null);
    setIsAddingNew(false);
    setFormData({ name: "", monthly_fee: 0, description: "", features: [] });
  };

  const deleteMembershipType = async (id, name) => {
    if (window.confirm(`Are you sure you want to delete the "${name}" membership type? This will deactivate it.`)) {
      try {
        await localDB.deleteMembershipType(id);
        alert("Membership type deactivated successfully! Changes saved locally and will sync when online.");
        fetchMembershipTypes();
      } catch (error) {
        console.error("Error deleting membership type:", error);
        alert("Error deleting membership type");
      }
    }
  };

  const addFeature = () => {
    setFormData(prev => ({
      ...prev,
      features: [...prev.features, ""]
    }));
  };

  const updateFeature = (index, value) => {
    setFormData(prev => ({
      ...prev,
      features: prev.features.map((feature, i) => i === index ? value : feature)
    }));
  };

  const removeFeature = (index) => {
    setFormData(prev => ({
      ...prev,
      features: prev.features.filter((_, i) => i !== index)
    }));
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Settings</h1>
        <p className="text-gray-400">Configure your gym management system and membership types (works offline).</p>
      </div>

      <div className="max-w-6xl mx-auto">
        {/* Header with Add Button */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-semibold">Membership Types Management</h2>
            <p className="text-gray-400 text-sm">Create, edit, and manage your gym membership plans</p>
          </div>
          <button
            onClick={startAddNew}
            className="bg-red-600 hover:bg-red-700 px-6 py-3 rounded-lg font-semibold flex items-center space-x-2"
          >
            <span>➕</span>
            <span>Add New Type</span>
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Membership Types List */}
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
            <h3 className="text-lg font-semibold mb-4">Current Membership Types</h3>

            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600 mx-auto"></div>
                <p className="mt-2 text-gray-400">Loading...</p>
              </div>
            ) : membershipTypes.length === 0 ? (
              <div className="text-center py-8">
                <div className="text-4xl mb-4">📝</div>
                <p className="text-gray-400 mb-4">No membership types configured yet.</p>
                <button
                  onClick={startAddNew}
                  className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg font-semibold"
                >
                  Add Your First Type
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {membershipTypes.map((type) => (
                  <div key={type.id} className={`border rounded-lg p-4 transition-all ${
                    editingType && editingType.id === type.id 
                      ? 'border-red-600 bg-red-600/5' 
                      : 'border-gray-600'
                  }`}>
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h4 className="font-semibold text-lg">{type.name}</h4>
                          <span className="text-green-400 font-bold text-lg">${type.monthly_fee}/month</span>
                        </div>
                        <p className="text-gray-400 text-sm mb-2">{type.description}</p>
                        {type.features && type.features.length > 0 && (
                          <div className="text-xs text-gray-300">
                            <div className="font-semibold mb-1">Features:</div>
                            <ul className="list-disc list-inside space-y-1">
                              {type.features.slice(0, 4).map((feature, index) => (
                                <li key={index}>{feature}</li>
                              ))}
                              {type.features.length > 4 && (
                                <li className="text-gray-400">... and {type.features.length - 4} more features</li>
                              )}
                            </ul>
                          </div>
                        )}
                      </div>
                      <div className="flex space-x-2 ml-4">
                        <button
                          onClick={() => startEdit(type)}
                          className="bg-blue-600 hover:bg-blue-700 px-3 py-2 rounded text-sm font-semibold"
                          title="Edit Membership Type"
                        >
                          ✏️ Edit
                        </button>
                        <button
                          onClick={() => deleteMembershipType(type.id, type.name)}
                          className="bg-red-600 hover:bg-red-700 px-3 py-2 rounded text-sm font-semibold"
                          title="Delete Membership Type"
                        >
                          🗑️ Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Add/Edit Form */}
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold">
                {editingType ? `Edit "${editingType.name}" Membership` : isAddingNew ? "Add New Membership Type" : "Membership Type Editor"}
              </h3>
              {(editingType || isAddingNew) && (
                <button
                  onClick={cancelEdit}
                  className="text-gray-400 hover:text-gray-200 text-xl"
                  title="Cancel"
                >
                  ✕
                </button>
              )}
            </div>

            {(editingType || isAddingNew) ? (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Membership Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    required
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
                    placeholder="e.g., Premium, Elite, VIP"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Monthly Fee ($) *</label>
                  <input
                    type="number"
                    value={formData.monthly_fee}
                    onChange={(e) => setFormData(prev => ({ ...prev, monthly_fee: parseFloat(e.target.value) || 0 }))}
                    required
                    min="0"
                    step="0.01"
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
                    placeholder="75.00"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Description *</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    required
                    rows="3"
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
                    placeholder="Brief description of this membership type..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Features & Benefits</label>
                  <div className="space-y-2">
                    {formData.features.map((feature, index) => (
                      <div key={index} className="flex items-center space-x-2">
                        <input
                          type="text"
                          value={feature}
                          onChange={(e) => updateFeature(index, e.target.value)}
                          className="flex-1 bg-gray-700 border border-gray-600 rounded px-3 py-2 focus:ring-2 focus:ring-red-600 focus:border-transparent"
                          placeholder="Enter feature or benefit"
                        />
                        <button
                          type="button"
                          onClick={() => removeFeature(index)}
                          className="bg-red-600 hover:bg-red-700 px-3 py-2 rounded text-sm font-semibold"
                          title="Remove Feature"
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                    <button
                      type="button"
                      onClick={addFeature}
                      className="bg-blue-600 hover:bg-blue-700 px-3 py-2 rounded text-sm font-semibold"
                    >
                      ➕ Add Feature
                    </button>
                  </div>
                  <p className="text-xs text-gray-400 mt-1">Add features and benefits that come with this membership</p>
                </div>

                <div className="flex space-x-4 pt-6">
                  <button
                    type="submit"
                    disabled={saving}
                    className="flex-1 bg-green-600 hover:bg-green-700 disabled:opacity-50 px-6 py-3 rounded-lg font-semibold"
                  >
                    {saving ? (editingType ? "Updating..." : "Creating...") : (editingType ? "Update Membership Type" : "Create Membership Type")}
                  </button>
                  <button
                    type="button"
                    onClick={cancelEdit}
                    className="bg-gray-600 hover:bg-gray-700 px-6 py-3 rounded-lg font-semibold"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">⚙️</div>
                <p className="text-gray-400 text-lg mb-4">Select a membership type to edit</p>
                <p className="text-gray-500 text-sm mb-6">Or click "Add New Type" to create a new membership plan</p>
                <button
                  onClick={startAddNew}
                  className="bg-red-600 hover:bg-red-700 px-6 py-3 rounded-lg font-semibold"
                >
                  ➕ Add New Membership Type
                </button>
              </div>
            )}
          </div>
        </div>

        {/* PWA Info */}
        <div className="mt-8 bg-gray-800 rounded-lg border border-gray-700 p-6">
          <h3 className="text-lg font-semibold mb-4">📱 PWA Features</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-700 p-4 rounded-lg">
              <h4 className="font-semibold mb-2">🔄 Offline Mode</h4>
              <p className="text-sm text-gray-400 mb-3">All data stored locally. Works without internet!</p>
            </div>
            <div className="bg-gray-700 p-4 rounded-lg">
              <h4 className="font-semibold mb-2">🌐 Auto Sync</h4>
              <p className="text-sm text-gray-400 mb-3">Data syncs automatically when online</p>
            </div>
            <div className="bg-gray-700 p-4 rounded-lg">
              <h4 className="font-semibold mb-2">📧 Email Online</h4>
              <p className="text-sm text-gray-400 mb-3">Email reminders work when connected</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Placeholder Components
const Payments = () => (
  <div className="p-6">
    <div className="mb-6">
      <h1 className="text-3xl font-bold mb-2">Payment Tracking</h1>
      <p className="text-gray-400">Monitor client payments and outstanding balances (offline ready).</p>
    </div>
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
      <div className="text-6xl mb-4">💳</div>
      <p className="text-xl text-gray-400">Payment tracking features coming soon!</p>
      <p className="text-sm text-gray-500 mt-2">Will work offline and sync when online</p>
    </div>
  </div>
);

const Reports = () => (
  <div className="p-6">
    <div className="mb-6">
      <h1 className="text-3xl font-bold mb-2">Reports & Analytics</h1>
      <p className="text-gray-400">View detailed reports and business insights (offline ready).</p>
    </div>
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
      <div className="text-6xl mb-4">📈</div>
      <p className="text-xl text-gray-400">Detailed analytics coming soon!</p>
      <p className="text-sm text-gray-500 mt-2">Will generate reports from local data</p>
    </div>
  </div>
);

const EmailCenter = () => (
  <div className="p-6">
    <div className="mb-6">
      <h1 className="text-3xl font-bold mb-2">Email Center</h1>
      <p className="text-gray-400">Send payment reminders (requires internet connection).</p>
    </div>
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
      <div className="text-6xl mb-4">📧</div>
      <p className="text-xl text-gray-400">Email functionality requires internet connection.</p>
      <p className="text-sm text-gray-500 mt-2">Use individual email buttons in Client Management when online</p>
    </div>
  </div>
);

function App() {
  useEffect(() => {
    // Initialize PWA
    console.log('Alphalete PWA initialized');
    
    // Remove loading screen after app loads
    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen) {
      setTimeout(() => {
        loadingScreen.style.opacity = '0';
        setTimeout(() => {
          loadingScreen.style.display = 'none';
        }, 500);
      }, 1000);
    }
  }, []);

  return (
    <div className="App">
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/clients" element={<ClientManagement />} />
            <Route path="/add-client" element={<AddClient />} />
            <Route path="/email-center" element={<EmailCenter />} />
            <Route path="/payments" element={<Payments />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </div>
  );
}

export default App;