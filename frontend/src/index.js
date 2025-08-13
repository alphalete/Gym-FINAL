import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";

// Unregister any existing service workers to avoid stale cache
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then(rs => rs.forEach(r => r.unregister()));
}

// Aggressive loading screen dismissal
function forceHideLoadingScreen() {
  try {
    // Method 1: Direct style manipulation
    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen) {
      loadingScreen.style.display = 'none';
      loadingScreen.style.visibility = 'hidden';
      loadingScreen.style.opacity = '0';
      loadingScreen.style.zIndex = '-1';
      console.log('✅ React: Loading screen forcibly hidden');
    }
    
    // Method 2: Use global dismissal function if available
    if (typeof window.dismissLoadingScreen === 'function') {
      window.dismissLoadingScreen();
    }
    
    // Method 3: Remove the element entirely
    setTimeout(() => {
      const screen = document.getElementById('loading-screen');
      if (screen) {
        screen.remove();
        console.log('✅ React: Loading screen element removed');
      }
    }, 1000);
    
  } catch (error) {
    console.warn('Loading screen dismissal error:', error);
  }
}

const root = ReactDOM.createRoot(document.getElementById("root"));

// Hide loading screen immediately when React starts
forceHideLoadingScreen();

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

// Multiple fallback attempts to hide loading screen
setTimeout(forceHideLoadingScreen, 100);
setTimeout(forceHideLoadingScreen, 500);
setTimeout(forceHideLoadingScreen, 1000);
setTimeout(forceHideLoadingScreen, 2000);
