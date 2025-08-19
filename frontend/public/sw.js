const CACHE_NAME = 'alphalete-gym-v5'; // Increment version to force update
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
  console.log('[SW] Installing Alphalete Athletics PWA Service Worker v5');
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
  console.log('[SW] Activating Alphalete Athletics PWA Service Worker v5');
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
  // Skip chrome-extension requests but allow Google Apps Script requests
  if (e.request.url.includes('chrome-extension')) {
    return;
  }
  
  // Allow Google Apps Script requests to pass through without interception
  if (e.request.url.includes('script.google.com') || e.request.url.includes('script.googleusercontent.com')) {
    console.log('[SW] Allowing Google Apps Script request:', e.request.url);
    return; // Let the browser handle it directly
  }
  
  // Skip other cross-origin requests (but not Google Apps Script)
  if (!e.request.url.startsWith(self.location.origin)) {
    return;
  }

  e.respondWith(
    caches.match(e.request).then(cachedResponse => {
      if (cachedResponse) {
        console.log('[SW] Cache hit for:', e.request.url);
        return cachedResponse;
      }
      
      // Network first for API calls to ensure fresh data
      if (e.request.url.includes('/api/')) {
        return fetch(e.request).then(response => {
          if (response.ok) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then(cache => {
              cache.put(e.request, responseClone);
            });
          }
          return response;
        }).catch(() => {
          // Fallback to cached version if network fails
          return caches.match(e.request);
        });
      }
      
      // Cache first for static assets
      return fetch(e.request).then(response => {
        if (response.ok && response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(e.request, responseClone);
          });
        }
        return response;
      }).catch(() => {
        // Fallback to main app shell for navigation requests
        if (e.request.mode === 'navigate') {
          return caches.match('/index.html');
        }
        return new Response('Offline - Content not available', {
          status: 503,
          statusText: 'Service Unavailable'
        });
      });
    })
  );
});