import React, { useState, useEffect } from 'react';
import './App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Components from './Components';

const {
  Sidebar,
  Dashboard,
  ClientManagement,
  PaymentTracking,
  MembershipManagement,
  Reports,
  Settings,
  LoginForm
} = Components;

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [user, setUser] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Mock login check
  useEffect(() => {
    const savedUser = localStorage.getItem('gymAdminUser');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
      setIsLoggedIn(true);
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    setIsLoggedIn(true);
    localStorage.setItem('gymAdminUser', JSON.stringify(userData));
  };

  const handleLogout = () => {
    setUser(null);
    setIsLoggedIn(false);
    localStorage.removeItem('gymAdminUser');
    setActiveTab('dashboard');
  };

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  if (!isLoggedIn) {
    return <LoginForm onLogin={handleLogin} />;
  }

  const renderActiveComponent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'clients':
        return <ClientManagement />;
      case 'payments':
        return <PaymentTracking />;
      case 'memberships':
        return <MembershipManagement />;
      case 'reports':
        return <Reports />;
      case 'settings':
        return <Settings user={user} />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="App">
      <BrowserRouter>
        <div className="flex h-screen bg-gray-100">
          <Sidebar 
            activeTab={activeTab} 
            setActiveTab={setActiveTab}
            user={user}
            onLogout={handleLogout}
            collapsed={sidebarCollapsed}
            onToggle={toggleSidebar}
          />
          <div className={`flex-1 overflow-hidden transition-all duration-300 ${
            sidebarCollapsed ? 'ml-0' : 'ml-0'
          }`}>
            {/* Mobile Header */}
            <div className="lg:hidden bg-white border-b border-gray-200 p-4 flex items-center justify-between">
              <button
                onClick={toggleSidebar}
                className="p-2 rounded-md text-gray-600 hover:bg-gray-100"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              <h1 className="text-lg font-semibold text-gray-900">Alphalete Athletics</h1>
              <div className="w-10"></div>
            </div>
            
            <main className="h-full overflow-y-auto">
              {renderActiveComponent()}
            </main>
          </div>
        </div>
      </BrowserRouter>
    </div>
  );
}

export default App;