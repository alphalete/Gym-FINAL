import { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

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
        className="md:hidden fixed top-4 left-4 z-50 bg-red-600 text-white p-2 rounded-lg"
      >
        {isOpen ? "✕" : "☰"}
      </button>

      {/* Sidebar */}
      <div className={`fixed left-0 top-0 h-full w-64 bg-gray-900 border-r border-gray-700 transform transition-transform duration-300 z-40 ${
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
            <div className="text-xs text-gray-400">Gym Management System</div>
            <div className="text-xs text-red-400 font-semibold">v1.0.0</div>
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
    <div className="min-h-screen bg-gray-900 text-white">
      <Navigation currentPage={location.pathname} />
      <div className="md:ml-64">
        {children}
      </div>
    </div>
  );
};

// Dashboard Component (Enhanced)
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
      const response = await axios.get(`${API}/clients`);
      setClients(response.data);
      
      // Calculate stats
      const activeMembers = response.data.filter(c => c.status === "Active");
      const monthlyRevenue = activeMembers.reduce((sum, c) => sum + c.monthly_fee, 0);
      
      setStats({
        totalClients: response.data.length,
        activeMembers: activeMembers.length,
        monthlyRevenue: monthlyRevenue,
        pendingPayments: activeMembers.length // Assuming all active members have pending payments
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
        
        <Link to="/reports" className="bg-gray-800 p-6 rounded-lg border border-gray-700 hover:border-red-600 transition-all">
          <div className="text-4xl mb-4">📈</div>
          <h3 className="text-xl font-semibold mb-2">View Reports</h3>
          <p className="text-gray-400">Analytics and performance metrics</p>
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

// Client Management Component
const ClientManagement = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  const fetchClients = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/clients`);
      setClients(response.data);
    } catch (error) {
      console.error("Error fetching clients:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClients();
  }, []);

  const sendPaymentReminder = async (clientId) => {
    try {
      const response = await axios.post(`${API}/email/payment-reminder`, {
        client_id: clientId
      });
      
      if (response.data.success) {
        alert(`Payment reminder sent successfully to ${response.data.client_email}`);
      } else {
        alert(`Failed to send payment reminder: ${response.data.message}`);
      }
    } catch (error) {
      console.error("Error sending payment reminder:", error);
      alert("Error sending payment reminder");
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
                          onClick={() => sendPaymentReminder(client.id)}
                          className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm font-semibold"
                          title="Send Payment Reminder"
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

// Add Client Component (Enhanced)
const AddClient = () => {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    membership_type: "Standard",
    monthly_fee: 50.00,
    next_payment_date: ""
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(`${API}/clients`, formData);
      alert("Client added successfully!");
      setFormData({
        name: "",
        email: "",
        phone: "",
        membership_type: "Standard",
        monthly_fee: 50.00,
        next_payment_date: ""
      });
    } catch (error) {
      console.error("Error adding client:", error);
      alert("Error adding client: " + (error.response?.data?.detail || error.message));
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

  const membershipPlans = [
    { type: "Standard", fee: 50.00, description: "Basic gym access" },
    { type: "Premium", fee: 75.00, description: "Gym + Group classes" },
    { type: "Elite", fee: 100.00, description: "Premium + Personal training" },
    { type: "VIP", fee: 150.00, description: "All access + Nutrition consultation" }
  ];

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Add New Client</h1>
        <p className="text-gray-400">Register a new member to your gym.</p>
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
              <label className="block text-sm font-medium mb-3">Membership Type</label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {membershipPlans.map((plan) => (
                  <label key={plan.type} className={`cursor-pointer border-2 rounded-lg p-4 transition-all ${
                    formData.membership_type === plan.type
                      ? 'border-red-600 bg-red-600/10'
                      : 'border-gray-600 hover:border-gray-500'
                  }`}>
                    <input
                      type="radio"
                      name="membership_type"
                      value={plan.type}
                      checked={formData.membership_type === plan.type}
                      onChange={(e) => {
                        setFormData(prev => ({
                          ...prev,
                          membership_type: e.target.value,
                          monthly_fee: plan.fee
                        }));
                      }}
                      className="sr-only"
                    />
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-semibold">{plan.type}</h4>
                        <p className="text-sm text-gray-400">{plan.description}</p>
                      </div>
                      <div className="text-lg font-bold text-green-400">${plan.fee}</div>
                    </div>
                  </label>
                ))}
              </div>
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
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Next Payment Date *</label>
              <input
                type="date"
                name="next_payment_date"
                value={formData.next_payment_date}
                onChange={handleChange}
                required
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
              />
            </div>

            <div className="pt-4">
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-red-600 hover:bg-red-700 disabled:opacity-50 px-6 py-3 rounded-lg font-semibold text-lg transition"
              >
                {loading ? "Adding Client..." : "Add Client"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

// Email Center Component
const EmailCenter = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [bulkLoading, setBulkLoading] = useState(false);

  const fetchClients = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/clients`);
      setClients(response.data);
    } catch (error) {
      console.error("Error fetching clients:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClients();
  }, []);

  const sendBulkReminders = async () => {
    if (!window.confirm("Send payment reminders to all active clients?")) {
      return;
    }

    try {
      setBulkLoading(true);
      const response = await axios.post(`${API}/email/payment-reminder/bulk`);
      alert(`Bulk reminders sent! Success: ${response.data.sent_successfully}, Failed: ${response.data.failed}`);
    } catch (error) {
      console.error("Error sending bulk reminders:", error);
      alert("Error sending bulk reminders");
    } finally {
      setBulkLoading(false);
    }
  };

  const sendIndividualReminder = async (clientId) => {
    try {
      const response = await axios.post(`${API}/email/payment-reminder`, {
        client_id: clientId
      });
      
      if (response.data.success) {
        alert(`Payment reminder sent successfully to ${response.data.client_email}`);
      } else {
        alert(`Failed to send payment reminder: ${response.data.message}`);
      }
    } catch (error) {
      console.error("Error sending payment reminder:", error);
      alert("Error sending payment reminder");
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Email Center</h1>
        <p className="text-gray-400">Send payment reminders and manage email communications.</p>
      </div>

      {/* Bulk Actions */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 mb-6">
        <h3 className="text-xl font-semibold mb-4">Bulk Actions</h3>
        <div className="flex items-center justify-between">
          <div>
            <p className="font-semibold">Send payment reminders to all active clients</p>
            <p className="text-sm text-gray-400">This will send reminder emails to {clients.filter(c => c.status === 'Active').length} active members</p>
          </div>
          <button
            onClick={sendBulkReminders}
            disabled={bulkLoading}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 px-6 py-3 rounded-lg font-semibold flex items-center space-x-2"
          >
            <span>📧</span>
            <span>{bulkLoading ? "Sending..." : "Send Bulk Reminders"}</span>
          </button>
        </div>
      </div>

      {/* Individual Client Actions */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
        <h3 className="text-xl font-semibold mb-4">Individual Reminders</h3>
        
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600 mx-auto"></div>
            <p className="mt-2 text-gray-400">Loading clients...</p>
          </div>
        ) : clients.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-4">📧</div>
            <p className="text-gray-400">No clients available for email reminders.</p>
            <Link to="/add-client" className="text-red-400 hover:text-red-300 underline">Add clients first</Link>
          </div>
        ) : (
          <div className="space-y-4">
            {clients.map((client) => (
              <div key={client.id} className="flex items-center justify-between p-4 bg-gray-700 rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className="w-10 h-10 bg-red-600 rounded-full flex items-center justify-center font-semibold">
                    {client.name.charAt(0)}
                  </div>
                  <div>
                    <p className="font-semibold">{client.name}</p>
                    <p className="text-sm text-gray-400">{client.email} • ${client.monthly_fee}/month</p>
                    <p className="text-xs text-gray-500">Next payment: {new Date(client.next_payment_date).toLocaleDateString()}</p>
                  </div>
                </div>
                <button
                  onClick={() => sendIndividualReminder(client.id)}
                  className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg font-semibold flex items-center space-x-2"
                >
                  <span>📧</span>
                  <span>Send Reminder</span>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Placeholder Components for other pages
const Payments = () => (
  <div className="p-6">
    <div className="mb-6">
      <h1 className="text-3xl font-bold mb-2">Payment Tracking</h1>
      <p className="text-gray-400">Monitor client payments and outstanding balances.</p>
    </div>
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
      <div className="text-6xl mb-4">💳</div>
      <p className="text-xl text-gray-400">Payment tracking features coming soon!</p>
    </div>
  </div>
);

const Reports = () => (
  <div className="p-6">
    <div className="mb-6">
      <h1 className="text-3xl font-bold mb-2">Reports & Analytics</h1>
      <p className="text-gray-400">View detailed reports and business insights.</p>
    </div>
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
      <div className="text-6xl mb-4">📈</div>
      <p className="text-xl text-gray-400">Detailed analytics coming soon!</p>
    </div>
  </div>
);

const Settings = () => (
  <div className="p-6">
    <div className="mb-6">
      <h1 className="text-3xl font-bold mb-2">Settings</h1>
      <p className="text-gray-400">Configure your gym management system.</p>
    </div>
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
      <div className="text-6xl mb-4">⚙️</div>
      <p className="text-xl text-gray-400">Settings panel coming soon!</p>
    </div>
  </div>
);

function App() {
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