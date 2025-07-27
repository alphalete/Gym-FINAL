const CACHE_NAME = 'alphalete-v4.4.0-final-changes';

console.log('Service Worker: Starting minimal version');

// Install event - minimal setup
self.addEventListener('install', event => {
  console.log('Service Worker: Install - forcing activation');
  self.skipWaiting();
});

// Activate event - clean old caches
self.addEventListener('activate', event => {
  console.log('Service Worker: Activate - cleaning caches');
  
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Service Worker: Deleting cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      self.clients.claim();
    })
  );
});

// Fetch event - network first, minimal caching
self.addEventListener('fetch', event => {
  event.respondWith(
    fetch(event.request)
      .then(response => {
        console.log('Service Worker: Network success for:', event.request.url);
        return response;
      })
      .catch(error => {
        console.log('Service Worker: Network failed for:', event.request.url);
        return caches.match(event.request).then(cachedResponse => {
          return cachedResponse || new Response('Offline', { status: 503 });
        });
      })
  );
});

console.log('Service Worker: Minimal version loaded');