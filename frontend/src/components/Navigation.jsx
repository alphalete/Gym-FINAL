import React, { useState, useEffect } from 'react';

// Simple icons (we'll use emojis initially, can replace with Heroicons later)
const Icons = {
  home: '🏠',
  users: '👥',
  creditCard: '💳',
  calendar: '📅',
  settings: '⚙️',
  menu: '☰',
  x: '✕',
  dashboard: '📊',
  members: '👤',
  plans: '📋',
  payments: '💰'
};

const NavItem = ({ icon, label, isActive, onClick, className = '' }) => (
  <button
    type="button"
    onClick={onClick}
    className={`nav-bottom-item ${isActive ? 'active' : ''} ${className} transition-colors duration-200`}
  >
    <span className="text-xl mb-1">{Icons[icon] || icon}</span>
    <span className="font-medium">{label}</span>
  </button>
);

const SidebarNavItem = ({ icon, label, isActive, onClick, className = '' }) => (
  <button
    type="button"
    onClick={onClick}
    className={`nav-sidebar-item ${isActive ? 'active' : ''} ${className} transition-all duration-200 group`}
  >
    <span className="text-xl mr-3 group-hover:scale-110 transition-transform duration-200">
      {Icons[icon] || icon}
    </span>
    <span className="font-medium">{label}</span>
  </button>
);

// Mobile Bottom Navigation
export const MobileBottomNavigation = ({ activeTab, onNavigate }) => {
  const navItems = [
    { id: 'dashboard', icon: 'dashboard', label: 'Dashboard' },
    { id: 'clients', icon: 'members', label: 'Members' },
    { id: 'plans', icon: 'plans', label: 'Plans' },
    { id: 'payments', icon: 'payments', label: 'Payments' },
    { id: 'settings', icon: 'settings', label: 'Settings' }
  ];

  return (
    <nav className="nav-bottom md:hidden">
      <div className="flex">
        {navItems.map((item) => (
          <NavItem
            key={item.id}
            icon={item.icon}
            label={item.label}
            isActive={activeTab === item.id}
            onClick={() => onNavigate(item.id)}
          />
        ))}
      </div>
    </nav>
  );
};

// Desktop Sidebar Navigation
export const DesktopSidebarNavigation = ({ activeTab, onNavigate }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isHovering, setIsHovering] = useState(false);

  const navItems = [
    { id: 'dashboard', icon: 'dashboard', label: 'Dashboard' },
    { id: 'clients', icon: 'members', label: 'Members' },
    { id: 'plans', icon: 'plans', label: 'Plans' },
    { id: 'payments', icon: 'payments', label: 'Payments' },
    { id: 'settings', icon: 'settings', label: 'Settings' }
  ];

  const shouldShowLabels = !isCollapsed || isHovering;
  const sidebarWidth = shouldShowLabels ? 'w-64' : 'w-16';

  return (
    <nav 
      className={`nav-sidebar hidden md:flex flex-col ${sidebarWidth} transition-all duration-300`}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          {shouldShowLabels && (
            <h1 className="text-xl font-bold text-primary">GoGym4U</h1>
          )}
          <button
            type="button"
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <span className="text-lg">{isCollapsed ? '☰' : '✕'}</span>
          </button>
        </div>
      </div>

      {/* Navigation Items */}
      <div className="flex-1 py-6">
        <ul className="space-y-2 px-3">
          {navItems.map((item) => (
            <li key={item.id}>
              <SidebarNavItem
                icon={item.icon}
                label={shouldShowLabels ? item.label : ''}
                isActive={activeTab === item.id}
                onClick={() => onNavigate(item.id)}
                className={`${!shouldShowLabels ? 'justify-center' : ''}`}
              />
            </li>
          ))}
        </ul>
      </div>

      {/* Footer */}
      {shouldShowLabels && (
        <div className="p-6 border-t border-gray-200">
          <div className="text-xs text-gray-500 text-center">
            GoGym4U v2.0
          </div>
        </div>
      )}
    </nav>
  );
};

// Main Navigation Provider
export const Navigation = ({ children }) => {
  const [activeTab, setActiveTab] = useState('dashboard');

  useEffect(() => {
    // Get initial tab from hash
    const hash = window.location.hash;
    if (hash.includes('tab=')) {
      const tab = hash.split('tab=')[1];
      setActiveTab(tab);
    }

    // Listen for hash changes
    const handleHashChange = () => {
      const hash = window.location.hash;
      if (hash.includes('tab=')) {
        const tab = hash.split('tab=')[1];
        setActiveTab(tab);
      }
    };

    // Listen for custom navigation events
    const handleNavigate = (event) => {
      setActiveTab(event.detail);
    };

    window.addEventListener('hashchange', handleHashChange);
    window.addEventListener('NAVIGATE', handleNavigate);

    return () => {
      window.removeEventListener('hashchange', handleHashChange);
      window.removeEventListener('NAVIGATE', handleNavigate);
    };
  }, []);

  const handleNavigate = (tab) => {
    setActiveTab(tab);
    window.location.hash = `#tab=${tab}`;
    
    // Dispatch custom event for backward compatibility
    try {
      window.dispatchEvent(new CustomEvent('NAVIGATE', { detail: tab }));
    } catch (e) {
      console.warn('Could not dispatch NAVIGATE event:', e);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Desktop Sidebar */}
      <DesktopSidebarNavigation activeTab={activeTab} onNavigate={handleNavigate} />
      
      {/* Main Content */}
      <div className="content-padding">
        {children}
      </div>
      
      {/* Mobile Bottom Navigation */}
      <MobileBottomNavigation activeTab={activeTab} onNavigate={handleNavigate} />
    </div>
  );
};