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
  e.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache)));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.map(k => k !== CACHE_NAME && caches.delete(k)))));
});

self.addEventListener('fetch', e => {
  e.respondWith(
    caches.match(e.request).then(resp => resp || fetch(e.request).catch(() => caches.match('/index.html')))
  );
});