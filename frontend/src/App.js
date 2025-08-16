import React, { useEffect, useMemo, useState } from "react";
import { HashRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import "./App.css";
import ErrorBoundary from "./ErrorBoundary";
import DiagnosticApp from "./DiagnosticApp";
import gymStorage, * as storageNamed from "./storage";
import Components from "./Components";
import BottomNav from "./components/BottomNav";

const Fallback = () => (
  <div className="min-h-screen flex items-center justify-center text-gray-600">Loading…</div>
);

const safePick = (bag, key) => (bag && bag[key]) ? bag[key] : (() => <div className="p-4">Missing component: {key}</div>);

// Navigation wrapper component to expose navigation globally
const AppContent = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const C = Components || {};

  const safePick = (bag, key) => (bag && bag[key]) ? bag[key] : (() => <div className="p-4">No {key}</div>);
  
  // Add missing form components with fallback
  const AddMember     = C.AddMember     || (() => <div className="p-4">Add member form missing</div>);
  const RecordPayment = C.RecordPayment || (() => <div className="p-4">Record payment form missing</div>);

  // Expose navigation function globally for quick start links
  useEffect(() => {
    window.navigateToTab = (tab) => {
      const routes = {
        'dashboard': '/dashboard',
        'members': '/members', 
        'plans': '/plans',
        'payments': '/payments',
        'reports': '/reports',
        'settings': '/settings'
      };
      if (routes[tab]) {
        navigate(routes[tab]);
        // Scroll to top of the page
        window.scrollTo({ top: 0, behavior: 'smooth' });
        // Save the last selected tab
        try {
          localStorage.setItem('ui:lastTab', tab);
        } catch (e) {
          console.warn('Could not save last tab to localStorage:', e);
        }
      }
    };
    // Back-compat alias in case older code calls window.setActiveTab
    window.setActiveTab = window.navigateToTab;
    // Also expose direct navigate function
    window.navigateTo = navigate;
  }, [navigate]);

  // Persist last selected tab whenever route changes and scroll to top
  useEffect(() => {
    const currentPath = location.pathname;
    const tabMap = {
      '/dashboard': 'dashboard',
      '/members': 'members',
      '/plans': 'plans',
      '/payments': 'payments',
      '/reports': 'reports',
      '/settings': 'settings'
    };
    
    const currentTab = tabMap[currentPath];
    if (currentTab) {
      // Scroll to top when navigating between pages
      window.scrollTo({ top: 0, behavior: 'smooth' });
      try {
        localStorage.setItem('ui:lastTab', currentTab);
      } catch (e) {
        console.warn('Could not save last tab to localStorage:', e);
      }
    }
  }, [location.pathname]);

  // Restore last selected tab on app load
  useEffect(() => {
    try {
      const lastTab = localStorage.getItem('ui:lastTab');
      if (lastTab && location.pathname === '/') {
        // Only navigate if we're on the root path (to avoid overriding direct navigation)
        const routes = {
          'dashboard': '/dashboard',
          'members': '/members', 
          'plans': '/plans',
          'payments': '/payments',
          'reports': '/reports',
          'settings': '/settings'
        };
        
        if (routes[lastTab]) {
          navigate(routes[lastTab], { replace: true });
        }
      }
    } catch (e) {
      console.warn('Could not restore last tab from localStorage:', e);
    }
  }, []); // Run only once on mount

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {C.Sidebar ? <C.Sidebar /> : null}
      <main className="flex-1 min-w-0 pb-20 md:pb-4 md:ml-16">
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={C.Dashboard ? <C.Dashboard /> : <div className="p-4">No Dashboard</div>} />
          <Route path="/members" element={C.ClientManagement ? <C.ClientManagement /> : <div className="p-4">No Members</div>} />
          <Route path="/add-member" element={<AddMember />} />
          <Route path="/plans" element={C.MembershipManagement ? <C.MembershipManagement /> : <div className="p-4">No Plans</div>} />
          <Route path="/payments" element={C.PaymentTracking ? <C.PaymentTracking /> : <div className="p-4">No Payments</div>} />
          <Route path="/payments/new" element={<RecordPayment />} />
          <Route path="/reports" element={C.Reports ? <C.Reports /> : <div className="p-4">No Reports</div>} />
          <Route path="/settings" element={C.Settings ? <C.Settings /> : <div className="p-4">No Settings</div>} />
          <Route path="/__diag" element={<DiagnosticApp />} />
          <Route path="*" element={<div className="p-4">Not found</div>} />
        </Routes>
      </main>
      <BottomNav />
    </div>
  );
};

export default function App(){
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // Clear service workers and caches
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.getRegistrations?.().then(rs => rs.forEach(r => r.unregister())).catch(() => {});
      caches?.keys?.().then(keys => keys.forEach(k => caches.delete(k))).catch(() => {});
    }

    // CONSERVATIVE: Clear only specific storage items that might cache member data
    const clearMemberCache = () => {
      try {
        // Clear specific localStorage keys related to members
        const keysToRemove = [];
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i);
          if (key && (key.includes('member') || key.includes('client') || key.includes('gym'))) {
            keysToRemove.push(key);
          }
        }
        keysToRemove.forEach(key => localStorage.removeItem(key));
        console.log(`🧹 Cleared ${keysToRemove.length} member-related localStorage items`);
        
        // Clear sessionStorage completely (safer than localStorage full clear)
        sessionStorage.clear();
        console.log('🧹 Cleared sessionStorage');
        
      } catch (e) {
        console.warn('Warning: Could not clear member cache:', e);
      }
    };

    clearMemberCache();

    // CRITICAL: Dismiss loading screen when React app mounts
    const dismissLoadingScreen = () => {
      const loadingScreen = document.getElementById('loading-screen');
      if (loadingScreen) {
        loadingScreen.style.display = 'none';
        console.log('🚀 Loading screen dismissed by React App mount');
      }
    };

    // Dismiss loading screen immediately when React mounts
    dismissLoadingScreen();
    
    // Also call the global dismissal function if it exists
    if (window.dismissLoadingScreen) {
      window.dismissLoadingScreen();
    }

    setReady(true);
  }, []);

  return (
    <ErrorBoundary>
      <HashRouter>
        <AppContent />
      </HashRouter>
    </ErrorBoundary>
  );
}