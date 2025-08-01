import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

// Register service worker for PWA functionality and force cache clearing
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.log('📱 Service Worker registered successfully: ', registration);
        
        // Force update check for mobile
        registration.addEventListener('updatefound', () => {
          console.log('📱 New service worker available - forcing update');
          const newWorker = registration.installing;
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              console.log('📱 New service worker installed - reloading page');
              // Force reload to use new service worker
              window.location.reload();
            }
          });
        });
        
        // Check for updates immediately
        registration.update();
      })
      .catch((error) => {
        console.error('Service Worker registration failed: ', error);
      });
      
    // Listen for service worker messages
    navigator.serviceWorker.addEventListener('message', event => {
      if (event.data && event.data.type === 'FORCE_RELOAD_NEW_DATA') {
        console.log('📱 Received force reload message from service worker v4.0.0');
        console.log('📱 Message:', event.data.message);
        // Clear all caches and reload
        if ('caches' in window) {
          caches.keys().then(cacheNames => {
            return Promise.all(cacheNames.map(name => caches.delete(name)));
          }).then(() => {
            localStorage.clear();
            sessionStorage.clear();
            window.location.reload();
          });
        } else {
          window.location.reload();
        }
      }
    });
  });
}
