/* Trendo: pamięć podręczna, żeby aplikacja startowała szybko i bez sieci */
const WERSJA = 'trendo-0.4.0';
const PLIKI = ['./', 'index.html', 'styles.css?v=0.4.0', 'js/wzorce.js?v=0.4.0', 'js/demo.js?v=0.4.0', 'js/grafika.js?v=0.4.0', 'js/app.js?v=0.4.0', 'manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png', 'icons/apple-touch-icon.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(WERSJA).then((c) => c.addAll(PLIKI)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((k) => Promise.all(k.filter((x) => x !== WERSJA).map((x) => caches.delete(x)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  if (u.origin !== location.origin) {
    if (u.host.includes('fonts.g')) {
      e.respondWith(caches.open(WERSJA).then((c) => c.match(e.request).then((r) => r || fetch(e.request).then((n) => { c.put(e.request, n.clone()); return n; }))));
    }
    return;
  }
  // własne pliki: najpierw sieć (świeże wersje), przy braku sieci pamięć
  e.respondWith(fetch(e.request).then((n) => {
    if (n.ok) { const k = n.clone(); caches.open(WERSJA).then((c) => c.put(e.request, k)); }
    return n;
  }).catch(() => caches.match(e.request).then((r) => r || caches.match('index.html'))));
});
