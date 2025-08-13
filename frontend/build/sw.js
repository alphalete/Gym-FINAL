// Network-first service worker to fix caching issues
const CACHE_NAME = 'alphalete-app-v1';
const NETWORK_FIRST_RESOURCES = [
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/api/',
  '/clients',
  '/payments',
  '/settings'
];

// Install event - minimal caching
self.addEventListener('install', (event) => {
  console.log('SW: Installing network-first service worker');
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      // Only cache essential assets, not JS/CSS bundles
      return cache.addAll([
        '/',
        '/manifest.json'
      ]);
    })
  );
  self.skipWaiting();
});

// Activate event
self.addEventListener('activate', (event) => {
  console.log('SW: Activating');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('SW: Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      return self.clients.claim();
    })
  );
});

// Fetch event - network-first strategy
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip cross-origin requests
  if (url.origin !== location.origin) {
    return;
  }

  // Network-first for JS, CSS, API calls, and dynamic content
  const isNetworkFirst = NETWORK_FIRST_RESOURCES.some(resource => 
    url.pathname.includes(resource)
  );

  if (isNetworkFirst) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Don't cache failed responses or API calls
          if (!response.ok || url.pathname.includes('/api/')) {
            return response;
          }
          
          // Clone and cache successful responses
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseClone);
          });
          
          return response;
        })
        .catch(() => {
          // Fallback to cache only if network fails
          return caches.match(request);
        })
    );
  } else {
    // Cache-first for static assets
    event.respondWith(
      caches.match(request).then((response) => {
        return response || fetch(request);
      })
    );
  }
});

// Handle cache clearing messages
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'CLEAR_ALL_CACHES') {
    event.waitUntil(
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName))
        );
      }).then(() => {
        event.ports[0].postMessage({ success: true });
      })
    );
  }
});