import { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import LocalStorageManager from "./LocalStorageManager";

// Initialize local storage manager
const localDB = new LocalStorageManager();

// PWA Status Component
const PWAStatus = () => {
  const [connectionStatus, setConnectionStatus] = useState({ 
    online: navigator.onLine, 
    message: navigator.onLine ? 'Connected - All features available' : 'Offline - Local data only' 
  });
  
  useEffect(() => {
    const updateStatus = async () => {
      // Enhanced online detection for mobile PWA
      let isOnline = navigator.onLine;
      
      // Additional connectivity check for mobile devices
      if (isOnline) {
        try {
          // Try to fetch a small resource to verify actual connectivity
          const controller = new AbortController();
          const timeout = setTimeout(() => controller.abort(), 5000);
          
          await fetch('/manifest.json', {
            method: 'HEAD',
            signal: controller.signal,
            cache: 'no-cache'
          });
          
          clearTimeout(timeout);
          isOnline = true;
        } catch (error) {
          console.log('PWA Status: Connectivity test failed:', error.message);
          isOnline = false;
        }
      }
      
      setConnectionStatus({
        online: isOnline,
        message: isOnline ? 'Connected - All features available' : 'Offline - Local data only'
      });
    };
    
    // Update status immediately
    updateStatus();
    
    // Listen for online/offline events
    const handleOnline = () => {
      console.log('PWA Status: Online event triggered');
      updateStatus();
    };
    
    const handleOffline = () => {
      console.log('PWA Status: Offline event triggered');
      setConnectionStatus({
        online: false,
        message: 'Offline - Local data only'
      });
    };
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    // Enhanced check every 10 seconds for mobile devices
    const interval = setInterval(updateStatus, 10000);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(interval);
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

// Custom Email Template Modal Component
const CustomEmailModal = ({ client, isOpen, onClose, onSend }) => {
  const [emailData, setEmailData] = useState({
    template_name: 'default',
    custom_subject: '',
    custom_message: '',
    custom_amount: client?.monthly_fee || 0,
    custom_due_date: ''
  });
  const [templates, setTemplates] = useState({});
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (isOpen && client) {
      // Reset form when modal opens
      setEmailData({
        template_name: 'default',
        custom_subject: '',
        custom_message: '',
        custom_amount: client.monthly_fee || 0,
        custom_due_date: client.next_payment_date || ''
      });
      
      // Fetch available templates
      fetchTemplates();
    }
  }, [isOpen, client]);

  const fetchTemplates = async () => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${backendUrl}/api/email/templates`);
      const data = await response.json();
      setTemplates(data.templates || {});
    } catch (error) {
      console.error("Error fetching templates:", error);
    }
  };

  const handleSend = async () => {
    setSending(true);
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      
      const response = await fetch(`${backendUrl}/api/email/custom-reminder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_id: client.id,
          ...emailData
        })
      });
      
      const result = await response.json();
      
      if (response.ok && result.success) {
        alert(`✅ Custom email sent successfully to ${result.client_email}`);
        onSend && onSend();
        onClose();
      } else {
        alert(`❌ Failed to send custom email: ${result.message}`);
      }
    } catch (error) {
      console.error("Error sending custom email:", error);
      alert(`❌ Error sending custom email: ${error.message}`);
    } finally {
      setSending(false);
    }
  };

  if (!isOpen || !client) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-gray-800 rounded-lg border border-gray-700 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-semibold">Customize Email for {client.name}</h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-200 text-2xl"
            >
              ✕
            </button>
          </div>
          <p className="text-gray-400 text-sm mt-1">Send a personalized payment reminder</p>
        </div>
        
        <div className="p-6 space-y-4">
          {/* Template Selection */}
          <div>
            <label className="block text-sm font-medium mb-2">Email Template</label>
            <select
              value={emailData.template_name}
              onChange={(e) => setEmailData(prev => ({ ...prev, template_name: e.target.value }))}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
            >
              {Object.entries(templates).map(([value, template]) => (
                <option key={value} value={value}>
                  {template.name} - {template.description}
                </option>
              ))}
            </select>
          </div>

          {/* Custom Subject */}
          <div>
            <label className="block text-sm font-medium mb-2">Custom Subject (Optional)</label>
            <input
              type="text"
              value={emailData.custom_subject}
              onChange={(e) => setEmailData(prev => ({ ...prev, custom_subject: e.target.value }))}
              placeholder="Leave empty to use template default"
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
            />
          </div>

          {/* Custom Message */}
          <div>
            <label className="block text-sm font-medium mb-2">Custom Message (Optional)</label>
            <textarea
              value={emailData.custom_message}
              onChange={(e) => setEmailData(prev => ({ ...prev, custom_message: e.target.value }))}
              placeholder="Add a personal message to include in the email"
              rows="3"
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
            />
          </div>

          {/* Custom Amount */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Amount</label>
              <input
                type="number"
                value={emailData.custom_amount}
                onChange={(e) => setEmailData(prev => ({ ...prev, custom_amount: parseFloat(e.target.value) || 0 }))}
                min="0"
                step="0.01"
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
              />
            </div>

            {/* Custom Due Date */}
            <div>
              <label className="block text-sm font-medium mb-2">Due Date</label>
              <input
                type="date"
                value={emailData.custom_due_date}
                onChange={(e) => setEmailData(prev => ({ ...prev, custom_due_date: e.target.value }))}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
              />
            </div>
          </div>

          {/* Preview Info */}
          <div className="bg-gray-900 p-4 rounded-lg border border-gray-600">
            <h4 className="font-semibold mb-2">Email Preview Info:</h4>
            <p className="text-sm text-gray-300">To: {client.email}</p>
            <p className="text-sm text-gray-300">Template: {templates[emailData.template_name]?.name || 'Default'}</p>
            <p className="text-sm text-gray-300">Amount: ${emailData.custom_amount}</p>
          </div>
        </div>

        <div className="p-6 border-t border-gray-700 flex space-x-4">
          <button
            onClick={onClose}
            className="flex-1 bg-gray-600 hover:bg-gray-700 px-6 py-3 rounded-lg font-semibold"
          >
            Cancel
          </button>
          <button
            onClick={handleSend}
            disabled={sending}
            className="flex-1 bg-red-600 hover:bg-red-700 disabled:opacity-50 px-6 py-3 rounded-lg font-semibold"
          >
            {sending ? "Sending..." : "Send Custom Email"}
          </button>
        </div>
      </div>
    </div>
  );
};

// Edit Client Modal Component
const EditClientModal = ({ client, isOpen, onClose, onSave }) => {
  const [clientData, setClientData] = useState({
    name: '',
    email: '',
    phone: '',
    membership_type: 'Standard',
    monthly_fee: 0,
    start_date: '',
    status: 'Active'
  });
  const [membershipTypes, setMembershipTypes] = useState([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isOpen && client) {
      // Initialize form with client data
      setClientData({
        name: client.name || '',
        email: client.email || '',
        phone: client.phone || '',
        membership_type: client.membership_type || 'Standard',
        monthly_fee: client.monthly_fee || 0,
        start_date: client.start_date || '',
        status: client.status || 'Active'
      });
      
      // Fetch membership types
      fetchMembershipTypes();
    }
  }, [isOpen, client]);

  const fetchMembershipTypes = async () => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${backendUrl}/api/membership-types`);
      const data = await response.json();
      setMembershipTypes(data || []);
    } catch (error) {
      console.error("Error fetching membership types:", error);
      // Use default types if API fails
      setMembershipTypes([
        { name: 'Standard', monthly_fee: 50.00 },
        { name: 'Premium', monthly_fee: 75.00 },
        { name: 'Elite', monthly_fee: 100.00 }
      ]);
    }
  };

  const handleMembershipTypeChange = (membershipType) => {
    const selectedType = membershipTypes.find(type => type.name === membershipType);
    setClientData(prev => ({
      ...prev,
      membership_type: membershipType,
      monthly_fee: selectedType ? selectedType.monthly_fee : prev.monthly_fee
    }));
  };

  const handleSave = async () => {
    // Validation
    if (!clientData.name.trim()) {
      alert('❌ Please enter client name');
      return;
    }
    if (!clientData.email.trim()) {
      alert('❌ Please enter client email');
      return;
    }
    if (!clientData.start_date) {
      alert('❌ Please enter start date');
      return;
    }

    setSaving(true);
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      
      // Update via backend API
      const response = await fetch(`${backendUrl}/api/clients/${client.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: clientData.name.trim(),
          email: clientData.email.trim(),
          phone: clientData.phone.trim() || null,
          membership_type: clientData.membership_type,
          monthly_fee: parseFloat(clientData.monthly_fee),
          start_date: clientData.start_date,
          status: clientData.status
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to update client: ${response.status} - ${errorText}`);
      }

      const updatedClient = await response.json();
      
      // Also update local storage
      await localDB.updateClient(client.id, {
        name: clientData.name.trim(),
        email: clientData.email.trim(),
        phone: clientData.phone.trim() || null,
        membership_type: clientData.membership_type,
        monthly_fee: parseFloat(clientData.monthly_fee),
        start_date: clientData.start_date,
        status: clientData.status,
        updated_at: new Date().toISOString()
      });

      alert(`✅ ${clientData.name} updated successfully!`);
      onSave && onSave(updatedClient);
      onClose();
      
    } catch (error) {
      console.error("Error updating client:", error);
      alert(`❌ Error updating client: ${error.message}`);
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen || !client) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-gray-800 rounded-lg border border-gray-700 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-semibold">Edit Client: {client.name}</h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-200 text-2xl"
            >
              ✕
            </button>
          </div>
          <p className="text-gray-400 text-sm mt-1">Update client information</p>
        </div>
        
        <div className="p-6 space-y-4">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium mb-2">Full Name *</label>
            <input
              type="text"
              value={clientData.name}
              onChange={(e) => setClientData(prev => ({ ...prev, name: e.target.value }))}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
              placeholder="Enter full name"
            />
          </div>

          {/* Email */}
          <div>
            <label className="block text-sm font-medium mb-2">Email Address *</label>
            <input
              type="email"
              value={clientData.email}
              onChange={(e) => setClientData(prev => ({ ...prev, email: e.target.value }))}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
              placeholder="Enter email address"
            />
          </div>

          {/* Phone */}
          <div>
            <label className="block text-sm font-medium mb-2">Phone Number</label>
            <input
              type="tel"
              value={clientData.phone}
              onChange={(e) => setClientData(prev => ({ ...prev, phone: e.target.value }))}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
              placeholder="Enter phone number (optional)"
            />
          </div>

          {/* Membership Type and Monthly Fee */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Membership Type</label>
              <select
                value={clientData.membership_type}
                onChange={(e) => handleMembershipTypeChange(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
              >
                {membershipTypes.map((type) => (
                  <option key={type.name} value={type.name}>
                    {type.name} - ${type.monthly_fee}/month
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Monthly Fee</label>
              <input
                type="number"
                value={clientData.monthly_fee}
                onChange={(e) => setClientData(prev => ({ ...prev, monthly_fee: parseFloat(e.target.value) || 0 }))}
                min="0"
                step="0.01"
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
              />
            </div>
          </div>

          {/* Start Date and Status */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Start Date *</label>
              <input
                type="date"
                value={clientData.start_date}
                onChange={(e) => setClientData(prev => ({ ...prev, start_date: e.target.value }))}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Status</label>
              <select
                value={clientData.status}
                onChange={(e) => setClientData(prev => ({ ...prev, status: e.target.value }))}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
              >
                <option value="Active">Active</option>
                <option value="Inactive">Inactive</option>
              </select>
            </div>
          </div>

          {/* Client Info Preview */}
          <div className="bg-gray-900 p-4 rounded-lg border border-gray-600">
            <h4 className="font-semibold mb-2">Updated Client Info:</h4>
            <p className="text-sm text-gray-300">Name: {clientData.name}</p>
            <p className="text-sm text-gray-300">Email: {clientData.email}</p>
            <p className="text-sm text-gray-300">Membership: {clientData.membership_type} (${clientData.monthly_fee}/month)</p>
            <p className="text-sm text-gray-300">Status: {clientData.status}</p>
          </div>
        </div>

        <div className="p-6 border-t border-gray-700 flex space-x-4">
          <button
            onClick={onClose}
            className="flex-1 bg-gray-600 hover:bg-gray-700 px-6 py-3 rounded-lg font-semibold"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex-1 bg-red-600 hover:bg-red-700 disabled:opacity-50 px-6 py-3 rounded-lg font-semibold"
          >
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>
    </div>
  );
};
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
        className="md:hidden fixed top-16 left-4 z-50 bg-red-600 text-white p-3 rounded-lg shadow-lg"
        style={{ touchAction: 'manipulation' }}
      >
        {isOpen ? "✕" : "☰"}
      </button>

      {/* Sidebar */}
      <div className={`fixed left-0 top-12 bottom-0 w-64 bg-gray-900 border-r border-gray-700 transform transition-transform duration-300 z-40 overflow-y-auto ${
        isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
      }`} style={{ WebkitOverflowScrolling: 'touch' }}>
        {/* Logo Header */}
        <div className="p-6 border-b border-gray-700 flex-shrink-0">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-black rounded-full flex items-center justify-center">
              <img src="/icon-192.png" alt="Wolf Logo" className="w-8 h-8 rounded-full" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">ALPHALETE</h1>
              <p className="text-xs text-red-400">ATHLETICS CLUB</p>
            </div>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="p-4 flex-1">
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
                  style={{ touchAction: 'manipulation', minHeight: '48px' }}
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
        <div className="p-4 flex-shrink-0">
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
          style={{ touchAction: 'manipulation' }}
        />
      )}
    </>
  );
};

// Main Layout Component with Scroll Fix
const Layout = ({ children }) => {
  const location = useLocation();
  
  return (
    <div className="pwa-container">
      <PWAStatus />
      <Navigation currentPage={location.pathname} />
      <div className="pwa-main-content">
        <div className="pwa-scrollable-content">
          {children}
        </div>
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

  // Initialize with sample data if no clients exist
  const initializeSampleData = async () => {
    try {
      const result = await localDB.getClients();
      console.log("🔍 Debug - Current clients count:", result.data.length);
      
      if (result.data.length === 0) {
        // Add sample clients for testing
        const sampleClients = [
          {
            name: "John Smith",
            email: "john.smith@example.com",
            phone: "(555) 123-4567",
            membership_type: "Premium",
            monthly_fee: 99.99,
            start_date: "2025-07-01",
            status: "Active"
          },
          {
            name: "Sarah Johnson",
            email: "sarah.johnson@example.com", 
            phone: "(555) 234-5678",
            membership_type: "Basic",
            monthly_fee: 59.99,
            start_date: "2025-07-15",
            status: "Active"
          },
          {
            name: "Mike Davis",
            email: "mike.davis@example.com",
            phone: "(555) 345-6789", 
            membership_type: "Premium",
            monthly_fee: 99.99,
            start_date: "2025-06-20",
            status: "Active"
          }
        ];

        console.log("🔍 Debug - Adding sample clients for testing...");
        for (const client of sampleClients) {
          const addedClient = await localDB.addClient(client);
          console.log(`✅ Added sample client: ${client.name}`, addedClient);
        }
        
        alert("🎯 Sample clients added for testing!\n\n✅ John Smith (Premium - $99.99)\n✅ Sarah Johnson (Basic - $59.99)\n✅ Mike Davis (Premium - $99.99)\n\nYou can now test email and payment features!");
        
        // Refresh the dashboard data
        fetchClients();
        return true;
      } else {
        console.log("🔍 Debug - Existing clients found:", result.data.map(c => ({ name: c.name, status: c.status })));
      }
      return false;
    } catch (error) {
      console.error("Error initializing sample data:", error);
      return false;
    }
  };

  // Debug function to clear all data and reinitialize
  const resetData = async () => {
    if (confirm("⚠️ This will delete all client data and add fresh sample clients. Continue?")) {
      try {
        // Clear all clients
        const clients = await localDB.getClients();
        for (const client of clients.data) {
          await localDB.deleteClient(client.id);
        }
        console.log("🔍 Debug - All clients cleared");
        
        // Re-initialize sample data
        await initializeSampleData();
        
        alert("✅ Data reset complete! Fresh sample clients added.");
      } catch (error) {
        console.error("Error resetting data:", error);
        alert("❌ Error resetting data: " + error.message);
      }
    }
  };

  useEffect(() => {
    fetchClients();
    // Initialize sample data if needed
    setTimeout(() => initializeSampleData(), 1000);
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

      {/* Debug section - can be removed in production */}
      <div className="mt-8 p-4 bg-gray-800 rounded-lg border border-gray-700">
        <h3 className="text-lg font-semibold mb-2">🔧 Debug Tools</h3>
        <div className="flex space-x-4">
          <button
            onClick={resetData}
            className="bg-yellow-600 hover:bg-yellow-700 px-4 py-2 rounded-lg font-semibold text-sm"
          >
            🔄 Reset Sample Data
          </button>
          <button
            onClick={() => console.log("Current clients:", clients)}
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg font-semibold text-sm"
          >
            📊 Log Client Data
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-2">Use these tools to test and debug the application</p>
      </div>
    </div>
  );
};

// Client Management Component (Fixed Scrolling)
const ClientManagement = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [customEmailModal, setCustomEmailModal] = useState({ isOpen: false, client: null });
  const [editClientModal, setEditClientModal] = useState({ isOpen: false, client: null });

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
    // Initialize sample data if needed (for Client Management)
    setTimeout(async () => {
      const result = await localDB.getClients();
      if (result.data.length === 0) {
        console.log("🔍 Client Management - No clients found, sample data may be loading...");
      } else {
        // Force sync existing clients to backend if online
        if (navigator.onLine) {
          try {
            console.log("🔄 Syncing existing clients to backend...");
            await localDB.forceSyncAllData();
            console.log("✅ Client sync completed");
          } catch (error) {
            console.error("❌ Client sync failed:", error);
          }
        }
      }
    }, 1000);
  }, []);

  const sendPaymentReminder = async (client) => {
    // Force check online status
    const isOnline = navigator.onLine && window.navigator.onLine;
    
    if (!isOnline) {
      alert("Email functionality requires an internet connection. Please check your connection and try again.");
      return;
    }

    try {
      // Get backend URL from environment
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      
      if (!backendUrl) {
        throw new Error('Backend URL not configured. Please set REACT_APP_BACKEND_URL environment variable.');
      }
      
      console.log("🔍 Debug - Backend URL from env:", backendUrl);
      console.log("🔍 Debug - Sending payment reminder to:", client.email, "Client ID:", client.id);
      
      const requestBody = { client_id: client.id };
      console.log("🔍 Debug - Request body:", requestBody);
      console.log("🔍 Debug - API URL:", `${backendUrl}/api/email/payment-reminder`);
      
      const response = await fetch(`${backendUrl}/api/email/payment-reminder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });
      
      console.log("🔍 Debug - Response status:", response.status);
      console.log("🔍 Debug - Response ok:", response.ok);
      console.log("🔍 Debug - Response headers:", Object.fromEntries(response.headers.entries()));
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("🔍 Debug - Error response text:", errorText);
        throw new Error(`HTTP ${response.status}: ${errorText || 'Unknown server error'}`);
      }
      
      const result = await response.json();
      console.log("🔍 Debug - Response data:", result);
      
      if (result.success) {
        alert(`✅ Payment reminder sent successfully to ${result.client_email || client.email}`);
      } else {
        console.error("❌ Failed to send email:", result);
        alert(`❌ Failed to send payment reminder: ${result.message || 'Unknown error'}\n\nDebug info:\n- Status: ${response.status}\n- Client ID: ${client.id}\n- Backend URL: ${backendUrl}`);
      }
    } catch (error) {
      console.error("❌ Error sending payment reminder:", error);
      alert(`❌ Error sending payment reminder: ${error.message}\n\nDebug info:\n- Client ID: ${client.id}\n- Please check browser console for more details`);
    }
  };

  const openCustomEmailModal = (client) => {
    setCustomEmailModal({ isOpen: true, client });
  };

  const closeCustomEmailModal = () => {
    setCustomEmailModal({ isOpen: false, client: null });
  };

  const openEditClientModal = (client) => {
    setEditClientModal({ isOpen: true, client });
  };

  const closeEditClientModal = () => {
    setEditClientModal({ isOpen: false, client: null });
  };

  const handleClientUpdated = (updatedClient) => {
    // Refresh the client list after successful update
    fetchClients();
  };

  const deleteClient = async (client) => {
    if (!confirm(`⚠️ Are you sure you want to delete ${client.name}?\n\nThis action cannot be undone and will remove all client data including payment history.`)) {
      return;
    }
    
    try {
      console.log(`🔍 Debug - Deleting client: ${client.name} (ID: ${client.id})`);
      
      // First delete from backend
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      
      if (backendUrl && navigator.onLine) {
        console.log("🔄 Deleting client from backend first...");
        const response = await fetch(`${backendUrl}/api/clients/${client.id}`, {
          method: 'DELETE',
          headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Backend delete failed: ${response.status} - ${errorText}`);
        }
        
        console.log("✅ Client deleted from backend successfully");
      }
      
      // Then delete from local storage
      await localDB.deleteClient(client.id);
      console.log("✅ Client deleted from local storage");
      
      alert(`✅ ${client.name} has been deleted successfully.`);
      fetchClients(); // Refresh the client list
      
    } catch (error) {
      console.error("❌ Error deleting client:", error);
      alert(`❌ Error deleting client: ${error.message}`);
    }
  };

  const toggleClientStatus = async (client) => {
    try {
      const newStatus = client.status === 'Active' ? 'Inactive' : 'Active';
      console.log(`🔍 Debug - Toggling ${client.name} status from ${client.status} to ${newStatus}`);
      
      await localDB.updateClient(client.id, {
        status: newStatus,
        updated_at: new Date().toISOString()
      });
      
      alert(`✅ ${client.name} status changed to: ${newStatus}`);
      fetchClients(); // Refresh data
      
    } catch (error) {
      console.error("❌ Error toggling client status:", error);
      alert(`❌ Error updating client status: ${error.message}`);
    }
  };

  const filteredClients = clients.filter(client =>
    client.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    client.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <>
      <div className="pwa-page-container">
        <div className="pwa-page-header">
          <h1 className="text-3xl font-bold mb-2">Client Management</h1>
          <p className="text-gray-400">Manage your gym members and their information.</p>
        </div>

        {/* Search and Actions */}
        <div className="pwa-search-section">
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

        {/* Client Cards for Mobile, Table for Desktop */}
        <div className="pwa-scrollable-section">
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
            <>
              {/* Mobile Cards View */}
              <div className="block md:hidden space-y-4">
                {filteredClients.map((client) => (
                  <div key={client.id} className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                    <div className="flex items-center space-x-3 mb-3">
                      <div className="w-12 h-12 bg-red-600 rounded-full flex items-center justify-center font-semibold">
                        {client.name.charAt(0)}
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold text-lg">{client.name}</h3>
                        <p className="text-gray-400 text-sm">{client.email}</p>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                        client.status === 'Active' 
                          ? 'bg-green-900 text-green-300' 
                          : 'bg-red-900 text-red-300'
                      }`}>
                        {client.status}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                      <div>
                        <span className="text-gray-400">Phone:</span>
                        <p>{client.phone || "N/A"}</p>
                      </div>
                      <div>
                        <span className="text-gray-400">Membership:</span>
                        <p>{client.membership_type}</p>
                      </div>
                      <div>
                        <span className="text-gray-400">Monthly Fee:</span>
                        <p className="text-green-400 font-semibold">${client.monthly_fee}</p>
                      </div>
                      <div>
                        <span className="text-gray-400">Next Payment:</span>
                        <p>{new Date(client.next_payment_date).toLocaleDateString()}</p>
                      </div>
                    </div>
                    
                    <div className="flex space-x-2">
                      <button
                        onClick={() => sendPaymentReminder(client)}
                        className="flex-1 bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg font-semibold flex items-center justify-center space-x-2"
                      >
                        <span>📧</span>
                        <span>Quick Send</span>
                      </button>
                      <button
                        onClick={() => openCustomEmailModal(client)}
                        className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg font-semibold"
                        title="Custom Email"
                      >
                        🎨
                      </button>
                      <button
                        onClick={() => openEditClientModal(client)}
                        className="bg-yellow-600 hover:bg-yellow-700 px-4 py-2 rounded-lg font-semibold"
                        title="Edit Client"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => toggleClientStatus(client)}
                        className={`px-4 py-2 rounded-lg font-semibold ${
                          client.status === 'Active' 
                            ? 'bg-orange-600 hover:bg-orange-700' 
                            : 'bg-green-600 hover:bg-green-700'
                        }`}
                        title={`Make ${client.status === 'Active' ? 'Inactive' : 'Active'}`}
                      >
                        {client.status === 'Active' ? '⏸️' : '▶️'}
                      </button>
                      <button
                        onClick={() => deleteClient(client)}
                        className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg font-semibold"
                        title="Delete Client"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Desktop Table View */}
              <div className="hidden md:block bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
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
                                className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm font-semibold"
                                title="Send Payment Reminder"
                              >
                                📧
                              </button>
                              <button
                                onClick={() => openCustomEmailModal(client)}
                                className="bg-purple-600 hover:bg-purple-700 px-3 py-1 rounded text-sm font-semibold"
                                title="Custom Email"
                              >
                                🎨
                              </button>
                              <button
                                onClick={() => toggleClientStatus(client)}
                                className={`px-3 py-1 rounded text-sm font-semibold ${
                                  client.status === 'Active' 
                                    ? 'bg-orange-600 hover:bg-orange-700' 
                                    : 'bg-green-600 hover:bg-green-700'
                                }`}
                                title={`Make ${client.status === 'Active' ? 'Inactive' : 'Active'}`}
                              >
                                {client.status === 'Active' ? '⏸️' : '▶️'}
                              </button>
                              <button
                                onClick={() => deleteClient(client)}
                                className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-sm font-semibold"
                                title="Delete Client"
                              >
                                🗑️
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
      <CustomEmailModal
        client={customEmailModal.client}
        isOpen={customEmailModal.isOpen}
        onClose={closeCustomEmailModal}
        onSend={fetchClients}
      />
    </>
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

// Payment Management Component - Full Implementation
const Payments = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [paymentStats, setPaymentStats] = useState({
    totalRevenue: 0,
    pendingPayments: 0,
    overduePayments: 0,
    thisMonthRevenue: 0
  });

  const fetchPaymentData = async () => {
    try {
      setLoading(true);
      const result = await localDB.getClients();
      // Show ALL clients, not just active ones - so you can see inactive clients and reactivate them
      const allClients = result.data;
      setClients(allClients);
      
      // Calculate payment statistics (only from active clients for stats)
      const activeClients = allClients.filter(client => client.status === 'Active');
      const today = new Date();
      const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
      
      let totalRevenue = 0;
      let pendingPayments = 0;
      let overduePayments = 0;
      let thisMonthRevenue = 0;
      
      activeClients.forEach(client => {
        const nextPaymentDate = new Date(client.next_payment_date);
        const fee = client.monthly_fee || 0;
        
        totalRevenue += fee;
        
        // Check if payment is due this month
        if (nextPaymentDate >= startOfMonth && nextPaymentDate <= today) {
          thisMonthRevenue += fee;
        }
        
        // Check if payment is pending (due in next 7 days)
        const daysUntilDue = Math.ceil((nextPaymentDate - today) / (1000 * 60 * 60 * 24));
        if (daysUntilDue <= 7 && daysUntilDue >= 0) {
          pendingPayments += 1;
        }
        
        // Check if payment is overdue
        if (nextPaymentDate < today) {
          overduePayments += 1;
        }
      });
      
      setPaymentStats({
        totalRevenue,
        pendingPayments,
        overduePayments,
        thisMonthRevenue
      });
      
    } catch (error) {
      console.error("Error fetching payment data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPaymentData();
    // Initialize sample data if needed (for Payment Management)
    setTimeout(async () => {
      const result = await localDB.getClients();
      if (result.data.length === 0) {
        console.log("🔍 Payment Management - No clients found, sample data may be loading...");
      }
    }, 1000);
  }, []);

  const getPaymentStatus = (nextPaymentDate) => {
    const today = new Date();
    const paymentDate = new Date(nextPaymentDate);
    const daysUntilDue = Math.ceil((paymentDate - today) / (1000 * 60 * 60 * 24));
    
    if (daysUntilDue < 0) {
      return { status: 'overdue', label: 'Overdue', class: 'bg-red-900 text-red-300' };
    } else if (daysUntilDue <= 7) {
      return { status: 'due-soon', label: 'Due Soon', class: 'bg-orange-900 text-orange-300' };
    } else {
      return { status: 'upcoming', label: 'Upcoming', class: 'bg-green-900 text-green-300' };
    }
  };

  const sendPaymentReminder = async (client) => {
    const isOnline = navigator.onLine;
    
    if (!isOnline) {
      alert("Email functionality requires an internet connection. Please check your connection and try again.");
      return;
    }

    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      console.log("🔍 Debug - Payment Mgmt - Backend URL:", backendUrl);
      console.log("🔍 Debug - Payment Mgmt - Sending payment reminder to:", client.email, "Client ID:", client.id);
      
      const requestBody = { client_id: client.id };
      console.log("🔍 Debug - Payment Mgmt - Request body:", requestBody);
      
      const response = await fetch(`${backendUrl}/api/email/payment-reminder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });
      
      console.log("🔍 Debug - Payment Mgmt - Response status:", response.status);
      console.log("🔍 Debug - Payment Mgmt - Response ok:", response.ok);
      
      const result = await response.json();
      console.log("🔍 Debug - Payment Mgmt - Response data:", result);
      
      if (response.ok && result.success) {
        alert(`✅ Payment reminder sent successfully to ${result.client_email || client.email}`);
      } else {
        console.error("❌ Payment Mgmt - Failed to send email:", result);
        alert(`❌ Failed to send payment reminder: ${result.message || 'Unknown error'}\n\nDebug info:\n- Status: ${response.status}\n- Client ID: ${client.id}\n- Backend URL: ${backendUrl}`);
      }
    } catch (error) {
      console.error("❌ Payment Mgmt - Error sending payment reminder:", error);
      alert(`❌ Error sending payment reminder: ${error.message}\n\nDebug info:\n- Client ID: ${client.id}\n- Check browser console for details`);
    }
  };

  const markAsPaid = async (client) => {
    try {
      console.log("🔍 Debug - Recording payment for client:", client.name, "ID:", client.id, "Current Status:", client.status);
      
      // Calculate next payment date (30 days from today)
      const today = new Date();
      const nextPaymentDate = new Date(today);
      nextPaymentDate.setDate(today.getDate() + 30);
      
      console.log("🔍 Debug - Next payment date calculated:", nextPaymentDate.toLocaleDateString());
      
      // Update local storage first - including setting status to Active
      const updateData = {
        next_payment_date: nextPaymentDate.toISOString().split('T')[0],
        status: "Active", // Always set to Active when payment is recorded
        updated_at: new Date().toISOString()
      };
      
      await localDB.updateClient(client.id, updateData);
      console.log("🔍 Debug - Local storage updated successfully with Active status");
      
      // If online, also update the backend
      const isOnline = navigator.onLine;
      console.log("🔍 Debug - Online status:", isOnline);
      
      if (isOnline) {
        try {
          const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
          console.log("🔍 Debug - Backend URL:", backendUrl);
          
          const paymentData = {
            client_id: client.id,
            amount_paid: client.monthly_fee,
            payment_date: today.toISOString().split('T')[0],
            payment_method: "Manual Entry",
            notes: `Payment recorded via PWA - Client reactivated from ${client.status || 'Unknown'} to Active`
          };
          console.log("🔍 Debug - Payment data:", paymentData);
          
          const response = await fetch(`${backendUrl}/api/payments/record`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(paymentData)
          });
          
          console.log("🔍 Debug - Payment record response status:", response.status);
          
          if (response.ok) {
            const result = await response.json();
            console.log("🔍 Debug - Payment recorded on server:", result);
          } else {
            console.warn("❌ Failed to record payment on server, but saved locally");
            const errorText = await response.text();
            console.warn("Server error:", errorText);
          }
        } catch (error) {
          console.warn("❌ Could not sync payment to server:", error.message);
        }
      }
      
      alert(`✅ Payment recorded for ${client.name}!\n\n💳 Amount: $${client.monthly_fee}\n📅 Next payment due: ${nextPaymentDate.toLocaleDateString()}\n🎯 Status: ACTIVE\n${isOnline ? '🌐 Synced to server' : '📱 Saved locally (will sync when online)'}`);
      fetchPaymentData(); // Refresh data
      
    } catch (error) {
      console.error("❌ Error marking payment as paid:", error);
      alert(`❌ Error updating payment status: ${error.message}\n\nDebug info:\n- Client ID: ${client.id}\n- Check browser console for details`);
    }
  };

  const filteredClients = clients.filter(client =>
    client.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    client.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="pwa-page-container">
      <div className="pwa-page-header">
        <h1 className="text-3xl font-bold mb-2">Payment Management</h1>
        <p className="text-gray-400">Track payments, send reminders, and manage billing.</p>
      </div>

      <div className="pwa-scrollable-section">
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
            <p className="mt-4 text-gray-400">Loading payment data...</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Payment Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-gradient-to-r from-green-600 to-green-700 p-6 rounded-lg">
                <h3 className="text-green-200 text-sm font-semibold">Total Monthly Revenue</h3>
                <p className="text-3xl font-bold text-white">${paymentStats.totalRevenue.toFixed(2)}</p>
                <p className="text-green-200 text-sm mt-2">From {clients.length} active members</p>
              </div>
              
              <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-6 rounded-lg">
                <h3 className="text-blue-200 text-sm font-semibold">This Month Revenue</h3>
                <p className="text-3xl font-bold text-white">${paymentStats.thisMonthRevenue.toFixed(2)}</p>
                <p className="text-blue-200 text-sm mt-2">Payments due this month</p>
              </div>
              
              <div className="bg-gradient-to-r from-orange-600 to-orange-700 p-6 rounded-lg">
                <h3 className="text-orange-200 text-sm font-semibold">Pending Payments</h3>
                <p className="text-3xl font-bold text-white">{paymentStats.pendingPayments}</p>
                <p className="text-orange-200 text-sm mt-2">Due within 7 days</p>
              </div>
              
              <div className="bg-gradient-to-r from-red-600 to-red-700 p-6 rounded-lg">
                <h3 className="text-red-200 text-sm font-semibold">Overdue Payments</h3>
                <p className="text-3xl font-bold text-white">{paymentStats.overduePayments}</p>
                <p className="text-red-200 text-sm mt-2">Past due date</p>
              </div>
            </div>

            {/* Search */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
              <input
                type="text"
                placeholder="Search clients by name or email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent"
              />
            </div>

            {/* Payment List */}
            <div className="bg-gray-800 rounded-lg border border-gray-700">
              <div className="p-4 border-b border-gray-700">
                <h3 className="text-xl font-semibold">All Client Payments</h3>
                <p className="text-gray-400 text-sm">Manage payments for all clients - Record payments to reactivate inactive clients</p>
              </div>
              
              {filteredClients.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-6xl mb-4">💳</div>
                  <p className="text-gray-400 text-lg">
                    {searchTerm ? "No clients found matching your search" : "No clients found"}
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <div className="min-w-full divide-y divide-gray-700" style={{ minWidth: '800px' }}>
                    {filteredClients.map((client) => {
                      const paymentStatus = getPaymentStatus(client.next_payment_date);
                      const nextPaymentDate = new Date(client.next_payment_date);
                      const daysUntilDue = Math.ceil((nextPaymentDate - new Date()) / (1000 * 60 * 60 * 24));
                      const isInactive = client.status !== 'Active';
                      
                      return (
                        <div key={client.id} className={`p-4 hover:bg-gray-750 flex items-center justify-between ${isInactive ? 'bg-gray-900 border-l-4 border-l-red-500' : ''}`} style={{ minWidth: '800px' }}>
                          <div className="flex items-center space-x-4 flex-shrink-0" style={{ minWidth: '300px' }}>
                            <div className={`w-12 h-12 rounded-full flex items-center justify-center font-semibold ${
                              isInactive ? 'bg-gray-600' : 'bg-red-600'
                            }`}>
                              {client.name.charAt(0)}
                            </div>
                            <div>
                              <div className="flex items-center space-x-2">
                                <h4 className={`font-semibold text-lg ${isInactive ? 'text-gray-400' : ''}`}>
                                  {client.name}
                                </h4>
                                {isInactive && (
                                  <span className="px-2 py-1 bg-red-900 text-red-300 text-xs rounded-full font-semibold">
                                    INACTIVE
                                  </span>
                                )}
                              </div>
                              <p className="text-gray-400 text-sm">{client.email}</p>
                              <p className="text-gray-500 text-xs">{client.membership_type} • ${client.monthly_fee}/month</p>
                            </div>
                          </div>
                          
                          <div className="flex items-center space-x-4 flex-shrink-0">
                            <div className="text-right" style={{ minWidth: '120px' }}>
                              <p className={`font-semibold text-lg ${isInactive ? 'text-gray-400' : ''}`}>
                                ${client.monthly_fee}
                              </p>
                              <p className="text-sm text-gray-400">
                                Due: {nextPaymentDate.toLocaleDateString()}
                              </p>
                              <p className="text-xs text-gray-500">
                                {daysUntilDue < 0 
                                  ? `${Math.abs(daysUntilDue)} days overdue`
                                  : daysUntilDue === 0 
                                    ? 'Due today'
                                    : `${daysUntilDue} days remaining`
                                }
                              </p>
                            </div>
                            
                            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                              isInactive ? 'bg-gray-800 text-gray-400' : paymentStatus.class
                            }`} style={{ minWidth: '80px', textAlign: 'center' }}>
                              {isInactive ? 'Inactive' : paymentStatus.label}
                            </span>
                            
                            <div className="flex space-x-2 flex-shrink-0" style={{ minWidth: '200px' }}>
                              <button
                                onClick={() => sendPaymentReminder(client)}
                                className={`px-3 py-2 rounded text-sm font-semibold whitespace-nowrap ${
                                  isInactive 
                                    ? 'bg-gray-600 hover:bg-gray-700 text-gray-300' 
                                    : 'bg-blue-600 hover:bg-blue-700'
                                }`}
                                title={isInactive ? "Reactivate client first to send reminder" : "Send Payment Reminder"}
                                disabled={isInactive}
                              >
                                📧 Remind
                              </button>
                              <button
                                onClick={() => markAsPaid(client)}
                                className={`px-3 py-2 rounded text-sm font-semibold whitespace-nowrap ${
                                  isInactive 
                                    ? 'bg-green-600 hover:bg-green-700 text-white font-bold' 
                                    : 'bg-green-600 hover:bg-green-700'
                                }`}
                                title={isInactive ? "Record Payment & Reactivate Client" : "Mark as Paid"}
                              >
                                ✅ {isInactive ? 'Reactivate' : 'Mark Paid'}
                              </button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Link to="/clients" className="bg-gray-800 p-6 rounded-lg border border-gray-700 hover:border-red-600 transition-all text-center">
                <div className="text-4xl mb-4">👥</div>
                <h3 className="text-xl font-semibold mb-2">Manage Clients</h3>
                <p className="text-gray-400">View and edit client information</p>
              </Link>
              
              <Link to="/reports" className="bg-gray-800 p-6 rounded-lg border border-gray-700 hover:border-red-600 transition-all text-center">
                <div className="text-4xl mb-4">📈</div>
                <h3 className="text-xl font-semibold mb-2">View Reports</h3>
                <p className="text-gray-400">Detailed payment analytics</p>
              </Link>
              
              <Link to="/settings" className="bg-gray-800 p-6 rounded-lg border border-gray-700 hover:border-red-600 transition-all text-center">
                <div className="text-4xl mb-4">⚙️</div>
                <h3 className="text-xl font-semibold mb-2">Settings</h3>
                <p className="text-gray-400">Configure membership types</p>
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Reports Component - Full Implementation
const Reports = () => {
  const [clients, setClients] = useState([]);
  const [membershipTypes, setMembershipTypes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [reportData, setReportData] = useState({
    totalRevenue: 0,
    avgMembershipFee: 0,
    membershipDistribution: {},
    monthlyGrowth: [],
    topMemberships: []
  });

  const fetchReportData = async () => {
    try {
      setLoading(true);
      const clientsResult = await localDB.getClients();
      const typesResult = await localDB.getMembershipTypes();
      
      setClients(clientsResult.data);
      setMembershipTypes(typesResult.data);
      
      // Calculate report metrics
      const activeClients = clientsResult.data.filter(c => c.status === 'Active');
      const totalRevenue = activeClients.reduce((sum, c) => sum + c.monthly_fee, 0);
      const avgFee = activeClients.length > 0 ? totalRevenue / activeClients.length : 0;
      
      // Membership distribution
      const distribution = {};
      activeClients.forEach(client => {
        distribution[client.membership_type] = (distribution[client.membership_type] || 0) + 1;
      });
      
      // Top memberships by revenue
      const membershipRevenue = {};
      activeClients.forEach(client => {
        membershipRevenue[client.membership_type] = (membershipRevenue[client.membership_type] || 0) + client.monthly_fee;
      });
      
      const topMemberships = Object.entries(membershipRevenue)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 5);
      
      setReportData({
        totalRevenue,
        avgMembershipFee: avgFee,
        membershipDistribution: distribution,
        topMemberships
      });
      
    } catch (error) {
      console.error("Error fetching report data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReportData();
  }, []);

  return (
    <div className="pwa-page-container">
      <div className="pwa-page-header">
        <h1 className="text-3xl font-bold mb-2">Reports & Analytics</h1>
        <p className="text-gray-400">View detailed reports and business insights from your local data.</p>
      </div>

      <div className="pwa-scrollable-section">
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
            <p className="mt-4 text-gray-400">Generating reports...</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Revenue Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-gradient-to-r from-green-600 to-green-700 p-6 rounded-lg">
                <h3 className="text-green-200 text-sm font-semibold">Total Monthly Revenue</h3>
                <p className="text-3xl font-bold text-white">${reportData.totalRevenue.toFixed(2)}</p>
                <p className="text-green-200 text-sm mt-2">From {clients.filter(c => c.status === 'Active').length} active members</p>
              </div>
              
              <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-6 rounded-lg">
                <h3 className="text-blue-200 text-sm font-semibold">Average Membership Fee</h3>
                <p className="text-3xl font-bold text-white">${reportData.avgMembershipFee.toFixed(2)}</p>
                <p className="text-blue-200 text-sm mt-2">Per member per month</p>
              </div>
              
              <div className="bg-gradient-to-r from-purple-600 to-purple-700 p-6 rounded-lg">
                <h3 className="text-purple-200 text-sm font-semibold">Total Members</h3>
                <p className="text-3xl font-bold text-white">{clients.length}</p>
                <p className="text-purple-200 text-sm mt-2">{clients.filter(c => c.status === 'Active').length} active, {clients.filter(c => c.status !== 'Active').length} inactive</p>
              </div>
            </div>

            {/* Membership Distribution */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
              <h3 className="text-xl font-semibold mb-4">Membership Distribution</h3>
              {Object.keys(reportData.membershipDistribution).length === 0 ? (
                <p className="text-gray-400">No membership data available</p>
              ) : (
                <div className="space-y-4">
                  {Object.entries(reportData.membershipDistribution).map(([type, count]) => {
                    const percentage = ((count / clients.filter(c => c.status === 'Active').length) * 100).toFixed(1);
                    return (
                      <div key={type} className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="w-4 h-4 bg-red-600 rounded"></div>
                          <span className="font-semibold">{type}</span>
                        </div>
                        <div className="flex items-center space-x-4">
                          <div className="w-32 bg-gray-700 rounded-full h-2">
                            <div 
                              className="bg-red-600 h-2 rounded-full"
                              style={{ width: `${percentage}%` }}
                            ></div>
                          </div>
                          <span className="text-sm font-semibold w-16">{count} ({percentage}%)</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Top Revenue Memberships */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
              <h3 className="text-xl font-semibold mb-4">Top Revenue Memberships</h3>
              {reportData.topMemberships.length === 0 ? (
                <p className="text-gray-400">No revenue data available</p>
              ) : (
                <div className="space-y-3">
                  {reportData.topMemberships.map(([type, revenue], index) => (
                    <div key={type} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <span className="text-2xl">{index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '🏅'}</span>
                        <div>
                          <p className="font-semibold">{type}</p>
                          <p className="text-sm text-gray-400">{reportData.membershipDistribution[type] || 0} members</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-green-400">${revenue.toFixed(2)}</p>
                        <p className="text-sm text-gray-400">monthly</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Client Status Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
                <h3 className="text-xl font-semibold mb-4">Client Status</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-green-400">● Active Members</span>
                    <span className="font-bold">{clients.filter(c => c.status === 'Active').length}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-red-400">● Inactive Members</span>
                    <span className="font-bold">{clients.filter(c => c.status !== 'Active').length}</span>
                  </div>
                  <div className="flex justify-between items-center border-t border-gray-700 pt-3">
                    <span className="text-white font-semibold">Total</span>
                    <span className="font-bold">{clients.length}</span>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
                <h3 className="text-xl font-semibold mb-4">Quick Actions</h3>
                <div className="space-y-3">
                  <Link to="/clients" className="block w-full bg-blue-600 hover:bg-blue-700 px-4 py-3 rounded-lg text-center font-semibold transition">
                    📊 View All Clients
                  </Link>
                  <Link to="/add-client" className="block w-full bg-green-600 hover:bg-green-700 px-4 py-3 rounded-lg text-center font-semibold transition">
                    ➕ Add New Client
                  </Link>
                  <Link to="/settings" className="block w-full bg-purple-600 hover:bg-purple-700 px-4 py-3 rounded-lg text-center font-semibold transition">
                    ⚙️ Manage Memberships
                  </Link>
                </div>
              </div>
            </div>

            {/* Data Export */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
              <h3 className="text-xl font-semibold mb-4">Export Data</h3>
              <p className="text-gray-400 mb-4">Export your data for backup or external analysis</p>
              <div className="flex flex-col sm:flex-row gap-3">
                <button 
                  onClick={() => alert('CSV export feature coming soon!')}
                  className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded-lg font-semibold"
                >
                  📄 Export to CSV
                </button>
                <button 
                  onClick={() => alert('JSON export feature coming soon!')}
                  className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded-lg font-semibold"
                >
                  📋 Export to JSON
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const EmailCenter = () => {
  const [connectionStatus, setConnectionStatus] = useState({
    online: navigator.onLine,
    message: navigator.onLine ? 'Connected - All features available' : 'Offline - Local data only'
  });
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sendingBulk, setSendingBulk] = useState(false);

  // Initialize local storage manager
  const localDB = new LocalStorageManager();

  useEffect(() => {
    const updateStatus = async () => {
      let isOnline = navigator.onLine;
      
      if (isOnline) {
        try {
          const controller = new AbortController();
          const timeout = setTimeout(() => controller.abort(), 5000);
          
          await fetch('/manifest.json', {
            method: 'HEAD',
            signal: controller.signal,
            cache: 'no-cache'
          });
          
          clearTimeout(timeout);
          isOnline = true;
        } catch (error) {
          console.log('Email Center: Connectivity test failed:', error.message);
          isOnline = false;
        }
      }
      
      setConnectionStatus({
        online: isOnline,
        message: isOnline ? 'Connected - All features available' : 'Offline - Local data only'
      });
    };
    
    // Update status immediately and every 10 seconds
    updateStatus();
    const interval = setInterval(updateStatus, 10000);
    
    // Listen for online/offline events
    const handleOnline = () => updateStatus();
    const handleOffline = () => setConnectionStatus({
      online: false,
      message: 'Offline - Local data only'
    });
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(interval);
    };
  }, []);

  // Fetch clients
  const fetchClients = async () => {
    try {
      setLoading(true);
      const result = await localDB.getClients();
      setClients(result.data.filter(c => c.status === 'Active'));
    } catch (error) {
      console.error("Error fetching clients:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClients();
  }, []);

  // Send bulk payment reminders
  const sendBulkReminders = async () => {
    if (!connectionStatus.online) {
      alert("❌ Bulk email requires an internet connection. Please check your connection and try again.");
      return;
    }

    if (clients.length === 0) {
      alert("❌ No active clients found to send reminders to.");
      return;
    }

    if (!confirm(`📧 Send payment reminders to all ${clients.length} active clients?`)) {
      return;
    }

    try {
      setSendingBulk(true);
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      
      console.log("🔄 Sending bulk payment reminders...");
      
      const response = await fetch(`${backendUrl}/api/email/payment-reminder/bulk`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }
      
      const result = await response.json();
      console.log("✅ Bulk reminders result:", result);
      
      alert(`✅ Bulk payment reminders completed!\n\n📊 Results:\n• Total clients: ${result.total_clients}\n• Sent successfully: ${result.sent_successfully}\n• Failed: ${result.failed}`);
      
    } catch (error) {
      console.error("❌ Error sending bulk reminders:", error);
      alert(`❌ Error sending bulk reminders: ${error.message}`);
    } finally {
      setSendingBulk(false);
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Email Center</h1>
        <p className="text-gray-400">Send payment reminders to clients.</p>
      </div>

      {/* Connection Status */}
      <div className={`mb-6 p-4 rounded-lg border ${
        connectionStatus.online 
          ? 'bg-green-900 border-green-600' 
          : 'bg-orange-900 border-orange-600'
      }`}>
        <div className="flex items-center">
          <div className="text-2xl mr-3">
            {connectionStatus.online ? '🌐' : '📱'}
          </div>
          <div>
            <h3 className="font-bold">
              {connectionStatus.online ? 'Online' : 'Offline'} - {connectionStatus.message}
            </h3>
            <p className="text-sm opacity-75">
              {connectionStatus.online 
                ? 'All email features are available' 
                : 'Email features require internet connection'}
            </p>
          </div>
        </div>
      </div>

      {connectionStatus.online ? (
        <>
          {/* Bulk Email Section */}
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-xl font-bold">📧 Bulk Payment Reminders</h2>
                <p className="text-gray-400">Send payment reminders to all active clients</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-green-400">{clients.length}</p>
                <p className="text-sm text-gray-500">Active Clients</p>
              </div>
            </div>
            
            <button
              onClick={sendBulkReminders}
              disabled={sendingBulk || clients.length === 0}
              className={`w-full py-3 px-6 rounded-lg font-bold text-white transition-colors ${
                sendingBulk || clients.length === 0
                  ? 'bg-gray-600 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {sendingBulk ? '📧 Sending Reminders...' : `📧 Send Reminders to All ${clients.length} Clients`}
            </button>
          </div>

          {/* Client List */}
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
            <h3 className="text-lg font-bold mb-4">👥 Active Clients</h3>
            {loading ? (
              <p className="text-center text-gray-400">Loading clients...</p>
            ) : clients.length > 0 ? (
              <div className="space-y-2">
                {clients.map((client, index) => (
                  <div key={client.id || index} className="flex justify-between items-center p-3 bg-gray-700 rounded">
                    <div>
                      <p className="font-semibold">{client.name}</p>
                      <p className="text-sm text-gray-400">{client.email}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-green-400 font-bold">${client.monthly_fee}</p>
                      <p className="text-xs text-gray-500">{client.membership_type}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="text-4xl mb-4">👥</div>
                <p className="text-gray-400">No active clients found</p>
                <p className="text-sm text-gray-500 mt-2">Add clients in Client Management</p>
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
          <div className="text-6xl mb-4">📧</div>
          <p className="text-xl text-gray-400">Email functionality requires internet connection.</p>
          <p className="text-sm text-gray-500 mt-2">Use individual email buttons in Client Management when online</p>
        </div>
      )}
    </div>
  );
};

function App() {
  useEffect(() => {
    // Initialize PWA
    console.log('Alphalete PWA initialized');
    
    // CRITICAL: Hide loading screen when React app mounts
    const hideLoadingScreen = () => {
      console.log("🔍 App: Hiding loading screen...");
      const loadingScreen = document.getElementById('loading-screen');
      if (loadingScreen) {
        loadingScreen.style.opacity = '0';
        loadingScreen.style.transition = 'opacity 0.3s ease';
        setTimeout(() => {
          loadingScreen.style.display = 'none';
          console.log("✅ App: Loading screen hidden successfully");
        }, 300);
      } else {
        console.log("⚠️ App: Loading screen element not found");
      }
    };
    
    // Hide loading screen immediately
    hideLoadingScreen();
    
    // Force scroll behavior fix for PWA
    const fixScrolling = () => {
      // Enable scrolling on body and document
      document.body.style.overflow = 'auto';
      document.body.style.webkitOverflowScrolling = 'touch';
      document.body.style.height = 'auto';
      document.body.style.minHeight = '100vh';
      
      // Fix for iOS Safari
      document.body.style.touchAction = 'pan-y pinch-zoom';
      
      // Find the main scrollable content
      const scrollableContent = document.querySelector('.pwa-scrollable-content');
      if (scrollableContent) {
        scrollableContent.style.overflowY = 'auto';
        scrollableContent.style.webkitOverflowScrolling = 'touch';
        scrollableContent.style.touchAction = 'pan-y';
      }
      
      // Fix any tables
      const tables = document.querySelectorAll('.overflow-x-auto');
      tables.forEach(table => {
        table.style.overflowX = 'auto';
        table.style.webkitOverflowScrolling = 'touch';
        table.style.touchAction = 'pan-x pan-y';
      });
    };
    
    // Apply fixes immediately and after a delay
    fixScrolling();
    setTimeout(fixScrolling, 100);
    setTimeout(fixScrolling, 500);
    
    // Remove loading screen after app loads
    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen) {
      setTimeout(() => {
        loadingScreen.style.opacity = '0';
        setTimeout(() => {
          loadingScreen.style.display = 'none';
          // Apply scroll fixes again after loading screen is removed
          fixScrolling();
        }, 500);
      }, 1000);
    }
    
    // Add event listener for orientation changes
    const handleOrientationChange = () => {
      setTimeout(fixScrolling, 100);
    };
    
    window.addEventListener('orientationchange', handleOrientationChange);
    window.addEventListener('resize', handleOrientationChange);
    
    // Cleanup
    return () => {
      window.removeEventListener('orientationchange', handleOrientationChange);
      window.removeEventListener('resize', handleOrientationChange);
    };
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