import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  ChartBarIcon,
  UserGroupIcon, 
  ClipboardDocumentListIcon,
  CreditCardIcon,
  Cog6ToothIcon,
  ChartPieIcon
} from '@heroicons/react/24/outline';
import { 
  ChartBarIcon as ChartBarIconSolid,
  UserGroupIcon as UserGroupIconSolid,
  ClipboardDocumentListIcon as ClipboardDocumentListIconSolid,
  CreditCardIcon as CreditCardIconSolid,
  Cog6ToothIcon as Cog6ToothIconSolid,
  ChartPieIcon as ChartPieIconSolid
} from '@heroicons/react/24/solid';

const BottomNav = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const navItems = [
    { path: '/dashboard', icon: ChartBarIcon, label: 'Dashboard' },
    { path: '/members', icon: UserGroupIcon, label: 'Members' },
    { path: '/plans', icon: ClipboardDocumentListIcon, label: 'Plans' },
    { path: '/payments', icon: CreditCardIcon, label: 'Payments' },
    { path: '/reports', icon: ChartPieIcon, label: 'Reports' },
    { path: '/settings', icon: Cog6ToothIcon, label: 'Settings' }
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="md:hidden fixed bottom-0 inset-x-0 z-50 h-16 bg-white/95 backdrop-blur border-t border-gray-200">
      <div className="flex h-full">
        {navItems.map((item) => (
          <button
            key={item.path}
            type="button"
            onClick={() => navigate(item.path)}
            className={`flex flex-col items-center justify-center flex-1 h-full px-1 py-2 transition-colors duration-200 ${
              isActive(item.path) 
                ? 'text-indigo-600 font-semibold' 
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            <div className="flex items-center justify-center mb-1">
              {React.createElement(
                isActive(item.path) 
                  ? {
                      '/dashboard': ChartBarIconSolid,
                      '/members': UserGroupIconSolid,
                      '/plans': ClipboardDocumentListIconSolid,
                      '/payments': CreditCardIconSolid,
                      '/settings': Cog6ToothIconSolid
                    }[item.path] || item.icon
                  : item.icon,
                { className: "w-5 h-5 flex-shrink-0" }
              )}
            </div>
            <span className="text-xs leading-none font-medium text-center">{item.label}</span>
          </button>
        ))}
      </div>
    </nav>
  );
};

export default BottomNav;