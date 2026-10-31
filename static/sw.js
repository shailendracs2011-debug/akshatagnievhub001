/* Akshat Agni EV Motors — Service Worker */
const CACHE_NAME = 'aaev-v1';
const ASSETS = [
  '/',
  '/static/css/site.css',
  '/static/css/fonts.css',
  '/static/js/site.js',
  '/static/manifest.json',
  '/static/images/favicon.svg',
  '/static/images/akshat-agni-logo.jpg',
  '/static/images/scooter-placeholder.svg',
  '/static/images/showroom-banner.jpg',
  '/static/fonts/noto-sans-latin.woff2',
  '/static/fonts/noto-sans-devanagari.woff2'
];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (!url.protocol.startsWith('http')) return;
  if (url.pathname.startsWith('/erp/') || url.pathname.startsWith('/admin/') || url.pathname.startsWith('/invoice/')) return;
  if (url.origin === self.location.origin && (url.pathname.startsWith('/static/') || url.pathname.endsWith('.svg') || url.pathname.endsWith('.woff2') || url.pathname.endsWith('.jpg') || url.pathname.endsWith('.webp') || url.pathname.endsWith('.png'))) {
    event.respondWith(caches.match(event.request).then((cached) => cached || fetch(event.request).then((resp) => { const copy = resp.clone(); caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy)); return resp; })));
    return;
  }
  event.respondWith(fetch(event.request).then((resp) => { const copy = resp.clone(); caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy)); return resp; }).catch(() => caches.match(event.request).then((cached) => cached || caches.match('/'))));
});
