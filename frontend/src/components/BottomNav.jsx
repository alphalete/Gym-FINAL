import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { NavigationIcon } from './Icons';

const BottomNav = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const navItems = [
    { path: '/dashboard', icon: ChartBarIcon, label: 'Dashboard' },
    { path: '/members', icon: UserGroupIcon, label: 'Members' },
    { path: '/plans', icon: ClipboardDocumentListIcon, label: 'Plans' },
    { path: '/payments', icon: CreditCardIcon, label: 'Payments' },
    { path: '/settings', icon: Cog6ToothIcon, label: 'Settings' }
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="md:hidden fixed bottom-0 inset-x-0 z-50 h-16 bg-white/95 backdrop-blur border-t border-gray-200">
      <div className="flex">
        {navItems.map((item) => (
          <button
            key={item.path}
            type="button"
            onClick={() => navigate(item.path)}
            className={`flex flex-col items-center justify-center text-xs flex-1 h-16 px-1 transition-colors duration-200 ${
              isActive(item.path) 
                ? 'text-indigo-600 font-semibold' 
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            <div className="flex items-center justify-center w-6 h-6 mb-1">
              <NavigationIcon name={item.icon} isActive={isActive(item.path)} size="lg" />
            </div>
            <span className="font-medium text-xs leading-tight text-center">{item.label}</span>
          </button>
        ))}
      </div>
    </nav>
  );
};

export default BottomNav;