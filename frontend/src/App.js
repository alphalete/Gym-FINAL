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
          />
          <div className="flex-1 overflow-hidden">
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