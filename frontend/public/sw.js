const CACHE_VERSION = 'v4.0.0';
const CACHE_NAME = `alphalete-cache-${CACHE_VERSION}`;

// Essential app shell assets to pre-cache
const APP_SHELL_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/static/css/main.css',
  '/static/js/main.js'
];

self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker v4.0.0');
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Pre-caching app shell assets');
      return cache.addAll(APP_SHELL_ASSETS);
    }).catch(error => {
      console.warn('[SW] Failed to pre-cache some assets:', error);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker v4.0.0');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      console.log('[SW] Found caches:', cacheNames);
      return Promise.all(
        cacheNames
          .filter(cacheName => cacheName.startsWith('alphalete-cache-') && cacheName !== CACHE_NAME)
          .map(cacheName => {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Only handle same-origin requests
  if (url.origin !== location.origin) return;

  // Skip non-GET requests
  if (req.method !== 'GET') return;

  // Determine if this is a critical resource (HTML, JS, CSS)
  const isCriticalResource = req.destination === 'document' || 
                           req.destination === 'script' || 
                           req.destination === 'style' ||
                           url.pathname.endsWith('.html') ||
                           url.pathname.endsWith('.js') ||
                           url.pathname.endsWith('.css');

  if (isCriticalResource) {
    // Stale-while-revalidate strategy for critical resources
    event.respondWith(staleWhileRevalidate(req));
  } else {
    // Cache-first strategy for other resources
    event.respondWith(cacheFirst(req));
  }
});

// Stale-while-revalidate strategy
async function staleWhileRevalidate(request) {
  const cache = await caches.open(CACHE_NAME);
  const cachedResponse = await cache.match(request);
  
  // Fetch from network and update cache in the background
  const fetchAndCache = async () => {
    try {
      const networkResponse = await fetch(request);
      if (networkResponse.ok) {
        cache.put(request, networkResponse.clone());
      }
      return networkResponse;
    } catch (error) {
      console.warn('[SW] Network fetch failed:', error);
      throw error;
    }
  };

  // If we have a cached response, return it immediately and update in background
  if (cachedResponse) {
    fetchAndCache().catch(() => {}); // Update cache silently
    return cachedResponse;
  }

  // No cached response, wait for network
  return fetchAndCache();
}

// Cache-first strategy
async function cacheFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  const cachedResponse = await cache.match(request);
  
  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.warn('[SW] Cache-first fetch failed:', error);
    throw error;
  }
}

// Handle cache management messages
self.addEventListener('message', event => {
  const { type } = event.data || {};
  
  switch (type) {
    case 'CLEAR_ALL_CACHES':
      caches.keys().then(keys => 
        Promise.all(keys.map(k => caches.delete(k)))
      ).then(() => {
        event.ports[0]?.postMessage({ success: true, message: 'All caches cleared' });
      });
      break;
      
    case 'GET_CACHE_INFO':
      caches.has(CACHE_NAME).then(exists => {
        event.ports[0]?.postMessage({
          success: true,
          caches: { [CACHE_NAME]: exists },
          version: CACHE_VERSION
        });
      });
      break;
  }
});