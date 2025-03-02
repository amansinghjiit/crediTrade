const CACHE_NAME = 'creditrade-cache-v1';
const urlsToCache = [
  '/',
  '/static/css/styles.css',
  '/static/css/orders.css',
  '/static/css/analytics.css',
  '/static/js/scripts.js',
  '/static/images/3_dots.svg',
  '/static/images/copy.svg',
  '/static/images/ddfavicon.png',
  '/static/images/delete.svg',
  '/static/images/edit.svg',
  '/static/images/eye.svg',
  '/static/images/fbgroup.png',
  '/static/images/logo.png',
  '/static/images/upload.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});