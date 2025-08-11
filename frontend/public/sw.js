const CACHE_VERSION = 'v3';
const CACHE_NAME = `alphalete-cache-${CACHE_VERSION}`;

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll([
      '/', '/index.html', '/manifest.json'
    ]))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter(k => k.startsWith('alphalete-cache-') && k !== CACHE_NAME)
        .map(k => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Only handle same-origin
  if (url.origin !== location.origin) return;

  if (req.destination === 'document' || req.destination === 'script' || req.destination === 'style') {
    event.respondWith((async () => {
      const cache = await caches.open(CACHE_NAME);
      const cached = await cache.match(req);
      const network = fetch(req).then(res => { cache.put(req, res.clone()); return res; });
      return cached || network;
    })());
  } else {
    event.respondWith(caches.match(req).then(resp => resp || fetch(req)));
  }
});

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