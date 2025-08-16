import React, { useEffect, useMemo, useState } from "react";
import { HashRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import "./App.css";
import ErrorBoundary from "./ErrorBoundary";
import DiagnosticApp from "./DiagnosticApp";
import gymStorage, * as storageNamed from "./storage";
import Components from "./Components";
import BottomNav from "./components/BottomNav";
import Dashboard from "./Dashboard"; // Import the new Dashboard component

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
        // Use comprehensive scroll function
        scrollToTop();
        
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

  // Helper function to scroll to top with comprehensive approach
  const scrollToTop = () => {
    // Method 1: Scroll to specific page element if available
    requestAnimationFrame(() => {
      // Try to find the current page header by ID first
      const pageHeaders = [
        '#settings-header',
        '#members-header', 
        '#dashboard-header',
        '#reports-header',
        '#payments-header',
        '#plans-header'
      ];
      
      let headerFound = false;
      for (const headerSelector of pageHeaders) {
        const header = document.querySelector(headerSelector);
        if (header) {
          header.scrollIntoView({ behavior: 'instant', block: 'start', inline: 'nearest' });
          headerFound = true;
          break;
        }
      }
      
      // Fallback: Try to find any main page header
      if (!headerFound) {
        const anyHeader = document.querySelector('main h1, h1, [class*="text-2xl"]');
        if (anyHeader) {
          anyHeader.scrollIntoView({ behavior: 'instant', block: 'start', inline: 'nearest' });
        }
      }
      
      // Method 2: Window scroll (always do this too)
      window.scrollTo({ top: 0, behavior: 'instant' });
      
      // Method 3: Document elements
      if (document.documentElement) {
        document.documentElement.scrollTop = 0;
      }
      if (document.body) {
        document.body.scrollTop = 0;
      }
      
      // Method 4: Scroll main container
      const mainElement = document.querySelector('main');
      if (mainElement) {
        mainElement.scrollTop = 0;
        if (mainElement.scrollTo) {
          mainElement.scrollTo({ top: 0, behavior: 'instant' });
        }
      }
    });
  };

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
      // Immediate scroll
      scrollToTop();
      
      // Also scroll after DOM updates
      setTimeout(() => {
        scrollToTop();
      }, 50);
      
      // And again after component renders and content loads
      setTimeout(() => {
        scrollToTop();
      }, 200);
      
      // Final scroll to ensure we're at the top
      setTimeout(() => {
        scrollToTop();
      }, 500);
      
      try {
        localStorage.setItem('ui:lastTab', currentTab);
      } catch (e) {
        console.warn('Could not save last tab to localStorage:', e);
      }
    }
  }, [location.pathname]);

  // Always start with Dashboard on app load
  useEffect(() => {
    try {
      // Always navigate to dashboard when the app loads, regardless of current path
      navigate('/dashboard', { replace: true });
    } catch (e) {
      console.warn('Could not navigate to dashboard on load:', e);
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