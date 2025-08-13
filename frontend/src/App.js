// frontend/src/App.js — GoGym4U Theme Integration
import React, { useEffect, useState } from "react";
import Components from "./Components";
import gymStorage from "./storage";
import { Navigation } from "./components/Navigation";
import "./App.css";

// Error Boundary
function ErrorBoundary({ children }) {
  const [err, setErr] = useState(null);
  
  useEffect(() => {
    const handleError = (event) => {
      setErr(event.error);
    };
    
    window.addEventListener('error', handleError);
    return () => window.removeEventListener('error', handleError);
  }, []);
  
  if (err) {
    return (
      <div className="p-4 text-sm">
        <div className="font-semibold mb-2">Something went wrong.</div>
        <pre className="text-xs whitespace-pre-wrap bg-gray-100 p-2 rounded">{String(err?.stack || err)}</pre>
        <button 
          type="button" 
          className="mt-2 btn btn-outline" 
          onClick={() => location.reload()}
        >
          Reload
        </button>
      </div>
    );
  }
  
  return children;
}

// Main App Component with GoGym4U Navigation
function App() {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize storage and set up app
  useEffect(() => {
    const initializeApp = async () => {
      try {
        console.log('[App] Initializing storage...');
        await gymStorage.init();
        await gymStorage.persistHint();
        
        // Run self-test to ensure storage works
        try {
          await gymStorage.__storageSelfTest?.();
        } catch (testError) {
          console.warn('[App] Storage self-test failed:', testError);
        }
        
        console.log('[App] Storage initialized successfully');
        setIsInitialized(true);
        
        // Ensure loading screen is hidden when app is ready
        setTimeout(() => {
          const loadingScreen = document.getElementById('loading-screen');
          if (loadingScreen) {
            loadingScreen.style.display = 'none';
            console.log('[App] ✅ Loading screen dismissed - App fully ready');
          }
        }, 100);
        
      } catch (error) {
        console.error('[App] Failed to initialize storage:', error);
        setIsInitialized(true); // Continue even if storage fails
        
        // Hide loading screen even on error
        setTimeout(() => {
          const loadingScreen = document.getElementById('loading-screen');
          if (loadingScreen) {
            loadingScreen.style.display = 'none';
            console.log('[App] Loading screen dismissed (with error)');
          }
        }, 100);
      }
    };

    initializeApp();
  }, []);

  // Handle navigation
  useEffect(() => {
    // Get initial tab from hash
    const hash = window.location.hash;
    if (hash.includes('tab=')) {
      const tab = hash.split('tab=')[1];
      setCurrentTab(tab);
    }

    // Listen for navigation events
    const handleNavigate = (event) => {
      const tab = event.detail;
      setCurrentTab(tab);
      window.location.hash = `#tab=${tab}`;
    };

    window.addEventListener('NAVIGATE', handleNavigate);
    return () => window.removeEventListener('NAVIGATE', handleNavigate);
  }, []);

  // Render loading state while initializing
  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <div className="text-gray-600">Initializing GoGym4U...</div>
        </div>
      </div>
    );
  }

  // Map tab names to components
  const renderCurrentComponent = () => {
    switch (currentTab) {
      case 'dashboard':
      case 'home':
        return <Components.Dashboard />;
      case 'clients':
      case 'members':
        return <Components.ClientManagement />;
      case 'payments':
        return <Components.PaymentTracking />;
      case 'plans':
        return <Components.MembershipManagement />;
      case 'settings':
        return <Components.Settings />;
      case 'reports':
        return <Components.Reports />;
      default:
        return <Components.Dashboard />;
    }
  };

  return (
    <ErrorBoundary>
      <div className="App">
        <Navigation>
          <div className="min-h-screen bg-gray-50">
            {renderCurrentComponent()}
          </div>
        </Navigation>
      </div>
    </ErrorBoundary>
  );
}

export default App;