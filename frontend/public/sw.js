const CACHE_NAME = 'alphalete-gym-v4';
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json',
  // Core PWA assets
  '/static/js/main.js',
  '/static/css/main.css',
  // PWA Icons - essential for offline installation
  '/icon-72x72.png',
  '/icon-96x96.png',
  '/icon-128x128.png',
  '/icon-144x144.png',
  '/icon-152x152.png',
  '/icon-192x192.png',
  '/icon-192x192-maskable.png',
  '/icon-384x384.png',
  '/icon-512x512.png',
  '/icon-512x512-maskable.png',
  '/favicon.ico',
  '/icon.svg',
  // Essential API endpoints for offline functionality
  '/api/clients',
  '/api/payments/stats',
  '/api/membership-types'
];

self.addEventListener('install', e => {
  console.log('[SW] Installing Alphalete Athletics PWA Service Worker v4');
  e.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('[SW] Precaching essential assets');
      return cache.addAll(urlsToCache.map(url => new Request(url, {cache: 'reload'})));
    }).catch(err => {
      console.warn('[SW] Precaching failed for some assets:', err);
      // Continue installation even if some assets fail to cache
      return caches.open(CACHE_NAME);
    })
  );
  self.skipWaiting(); // Force new SW to activate immediately
});

self.addEventListener('activate', e => {
  console.log('[SW] Activating Alphalete Athletics PWA Service Worker v4');
  e.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.map(key => {
          if (key !== CACHE_NAME) {
            console.log('[SW] Deleting old cache:', key);
            return caches.delete(key);
          }
        })
      );
    }).then(() => {
      console.log('[SW] Service Worker activated and ready');
      return self.clients.claim(); // Take control of all pages immediately
    })
  );
});

self.addEventListener('fetch', e => {
  e.respondWith(
    caches.match(e.request).then(resp => resp || fetch(e.request).catch(() => caches.match('/index.html')))
  );
});