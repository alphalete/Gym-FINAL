import { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Home/Dashboard Component
const Home = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(false);

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

  const sendBulkReminders = async () => {
    if (!window.confirm("Send payment reminders to all active clients?")) {
      return;
    }

    try {
      setLoading(true);
      const response = await axios.post(`${API}/email/payment-reminder/bulk`);
      alert(`Bulk reminders sent! Success: ${response.data.sent_successfully}, Failed: ${response.data.failed}`);
    } catch (error) {
      console.error("Error sending bulk reminders:", error);
      alert("Error sending bulk reminders");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gradient-to-r from-red-600 to-red-800 shadow-lg">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="text-3xl">🏋️‍♂️</div>
              <div>
                <h1 className="text-2xl font-bold">ALPHALETE ATHLETICS CLUB</h1>
                <p className="text-red-200">Elite Fitness Training & Membership</p>
              </div>
            </div>
            <Link 
              to="/add-client" 
              className="bg-white text-red-600 px-4 py-2 rounded-lg font-semibold hover:bg-red-50 transition"
            >
              + Add Client
            </Link>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">Client Management Dashboard</h2>
          <button
            onClick={sendBulkReminders}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg font-semibold disabled:opacity-50"
          >
            {loading ? "Sending..." : "📧 Send Bulk Reminders"}
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <h3 className="text-lg font-semibold text-gray-300">Total Clients</h3>
            <p className="text-3xl font-bold text-white">{clients.length}</p>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <h3 className="text-lg font-semibold text-gray-300">Active Members</h3>
            <p className="text-3xl font-bold text-green-400">
              {clients.filter(c => c.status === "Active").length}
            </p>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <h3 className="text-lg font-semibold text-gray-300">Monthly Revenue</h3>
            <p className="text-3xl font-bold text-blue-400">
              ${clients.filter(c => c.status === "Active").reduce((sum, c) => sum + c.monthly_fee, 0).toFixed(2)}
            </p>
          </div>
        </div>

        {/* Clients Table */}
        <div className="bg-gray-800 rounded-lg border border-gray-700">
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">All Clients</h3>
            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
                <p className="mt-4 text-gray-400">Loading clients...</p>
              </div>
            ) : clients.length === 0 ? (
              <div className="text-center py-8">
                <div className="text-6xl mb-4">💪</div>
                <p className="text-gray-400 text-lg mb-4">No clients yet</p>
                <Link 
                  to="/add-client"
                  className="bg-red-600 hover:bg-red-700 px-6 py-3 rounded-lg font-semibold inline-block"
                >
                  Add Your First Client
                </Link>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-700">
                    <tr>
                      <th className="text-left p-4">Name</th>
                      <th className="text-left p-4">Email</th>
                      <th className="text-left p-4">Membership</th>
                      <th className="text-left p-4">Monthly Fee</th>
                      <th className="text-left p-4">Next Payment</th>
                      <th className="text-left p-4">Status</th>
                      <th className="text-left p-4">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {clients.map((client) => (
                      <tr key={client.id} className="border-b border-gray-700 hover:bg-gray-750">
                        <td className="p-4 font-semibold">{client.name}</td>
                        <td className="p-4 text-gray-300">{client.email}</td>
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
                          <button
                            onClick={() => sendPaymentReminder(client.id)}
                            className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm font-semibold"
                          >
                            📧 Remind
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Add Client Component
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

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gradient-to-r from-red-600 to-red-800 shadow-lg">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="text-3xl">🏋️‍♂️</div>
              <div>
                <h1 className="text-2xl font-bold">ALPHALETE ATHLETICS CLUB</h1>
                <p className="text-red-200">Add New Client</p>
              </div>
            </div>
            <Link 
              to="/" 
              className="bg-white text-red-600 px-4 py-2 rounded-lg font-semibold hover:bg-red-50 transition"
            >
              ← Back to Dashboard
            </Link>
          </div>
        </div>
      </div>

      {/* Form */}
      <div className="container mx-auto px-6 py-8">
        <div className="max-w-2xl mx-auto">
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-8">
            <h2 className="text-2xl font-bold mb-6">Add New Client</h2>
            
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
                <label className="block text-sm font-medium mb-2">Membership Type</label>
                <select
                  name="membership_type"
                  value={formData.membership_type}
                  onChange={handleChange}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
                >
                  <option value="Standard">Standard</option>
                  <option value="Premium">Premium</option>
                  <option value="Elite">Elite</option>
                  <option value="VIP">VIP</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Monthly Fee ($)</label>
                <input
                  type="number"
                  name="monthly_fee"
                  value={formData.monthly_fee}
                  onChange={handleChange}
                  min="0"
                  step="0.01"
                  required
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
                  placeholder="50.00"
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
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/add-client" element={<AddClient />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;