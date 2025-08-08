// PWABuilder specific service worker for enhanced standalone mode
const CACHE_NAME = 'alphalete-pwa-standalone-v1';

// Force PWA installation and standalone mode
self.addEventListener('install', event => {
  console.log('PWABuilder SW: Installing for standalone mode');
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll([
        '/',
        '/clients',
        '/add-client', 
        '/manifest.json'
      ]);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  console.log('PWABuilder SW: Activated for standalone mode');
  event.waitUntil(self.clients.claim());
});

// Enhanced fetch for standalone mode
self.addEventListener('fetch', event => {
  if (event.request.mode === 'navigate') {
    event.respondWith(
      caches.match('/').then(response => {
        return response || fetch('/');
      })
    );
  }
});