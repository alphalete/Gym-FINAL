import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";

// Unregister any existing service workers to avoid stale cache
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then(rs => rs.forEach(r => r.unregister()));
}

// Hide the HTML loading screen when React is ready
function hideLoadingScreen() {
  const loadingScreen = document.getElementById('loading-screen');
  if (loadingScreen) {
    loadingScreen.style.display = 'none';
    console.log('✅ Loading screen hidden - React app ready');
  }
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

// Hide loading screen after React render
setTimeout(hideLoadingScreen, 100);
