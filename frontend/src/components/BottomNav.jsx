import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  ChartBarIcon,
  UserGroupIcon, 
  ClipboardDocumentListIcon,
  CreditCardIcon,
  Cog6ToothIcon,
  ChartPieIcon,
  ArrowPathIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { 
  ChartBarIcon as ChartBarIconSolid,
  UserGroupIcon as UserGroupIconSolid,
  ClipboardDocumentListIcon as ClipboardDocumentListIconSolid,
  CreditCardIcon as CreditCardIconSolid,
  Cog6ToothIcon as Cog6ToothIconSolid,
  ChartPieIcon as ChartPieIconSolid,
  ArrowPathIcon as ArrowPathIconSolid,
  XMarkIcon as XMarkIconSolid
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
      <div className="flex h-full overflow-x-auto scrollbar-hide px-2">
        
        {navItems.map((item) => (
          <button
            key={item.path}
            type="button"
            onClick={() => {
              navigate(item.path);
              // Force immediate scroll to top with multiple approaches
              window.scrollTo(0, 0);
              document.documentElement.scrollTop = 0;
              document.body.scrollTop = 0;
              
              // Also set it again after navigation
              setTimeout(() => {
                window.scrollTo(0, 0);
                document.documentElement.scrollTop = 0;
                document.body.scrollTop = 0;
              }, 10);
            }}
            className={`flex flex-col items-center justify-center min-w-[64px] h-full px-2 py-2 transition-colors duration-200 flex-shrink-0 ${
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
                      '/reports': ChartPieIconSolid,
                      '/settings': Cog6ToothIconSolid
                    }[item.path] || item.icon
                  : item.icon,
                { className: "w-5 h-5 flex-shrink-0" }
              )}
            </div>
            <span className="text-xs leading-none font-medium text-center whitespace-nowrap">{item.label}</span>
          </button>
        ))}
        
        {/* Separator */}
        <div className="flex items-center px-1">
          <div className="w-px h-8 bg-gray-300"></div>
        </div>
        
        {/* App Control Buttons */}
        <button
          type="button"
          onClick={() => window.location.reload()}
          className="flex flex-col items-center justify-center min-w-[64px] h-full px-2 py-2 text-blue-600 hover:text-blue-700 transition-colors duration-200 flex-shrink-0"
          title="Refresh App"
        >
          <div className="flex items-center justify-center mb-1">
            <ArrowPathIcon className="w-5 h-5 flex-shrink-0" />
          </div>
          <span className="text-xs leading-none font-medium text-center whitespace-nowrap">Refresh</span>
        </button>
        
        <button
          type="button"
          onClick={() => {
            if (confirm('Close Alphalete Athletics? This will navigate away from the app.')) {
              // Try multiple methods to close/exit the app
              try {
                // Method 1: Try window.close() (works for popups)
                window.close();
                
                // Method 2: If window.close() doesn't work, navigate to a goodbye page
                setTimeout(() => {
                  // Check if window is still open (window.close() failed)
                  if (!window.closed) {
                    // Create a goodbye screen
                    document.body.innerHTML = `
                      <div style="
                        display: flex; 
                        flex-direction: column; 
                        justify-content: center; 
                        align-items: center; 
                        height: 100vh; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        text-align: center;
                      ">
                        <div style="max-width: 400px; padding: 2rem;">
                          <h1 style="font-size: 2.5rem; margin-bottom: 1rem; font-weight: bold;">
                            👋 Goodbye!
                          </h1>
                          <p style="font-size: 1.2rem; margin-bottom: 2rem; opacity: 0.9;">
                            Thank you for using Alphalete Athletics Club
                          </p>
                          <p style="font-size: 1rem; opacity: 0.7; margin-bottom: 2rem;">
                            You can close this browser tab manually or click the button below to return to the app.
                          </p>
                          <button onclick="window.location.reload()" style="
                            background: rgba(255,255,255,0.2);
                            border: 2px solid rgba(255,255,255,0.3);
                            color: white;
                            padding: 12px 24px;
                            border-radius: 25px;
                            font-size: 1rem;
                            cursor: pointer;
                            transition: all 0.3s ease;
                          " onmouseover="this.style.background='rgba(255,255,255,0.3)'" onmouseout="this.style.background='rgba(255,255,255,0.2)'">
                            🔄 Return to App
                          </button>
                        </div>
                      </div>
                    `;
                  }
                }, 100);
                
              } catch (error) {
                console.log('Close methods not available - displaying goodbye message');
                alert('Please close this browser tab manually to exit the app.');
              }
            }
          }}
          className="flex flex-col items-center justify-center min-w-[64px] h-full px-2 py-2 text-red-600 hover:text-red-700 transition-colors duration-200 flex-shrink-0"
          title="Close App"
        >
          <div className="flex items-center justify-center mb-1">
            <XMarkIcon className="w-5 h-5 flex-shrink-0" />
          </div>
          <span className="text-xs leading-none font-medium text-center whitespace-nowrap">Close</span>
        </button>
      </div>
    </nav>
  );
};

export default BottomNav;