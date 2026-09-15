'use strict';

/* Service worker NIMM ePub — strategie network-first.
   Garantit que le navigateur (surtout une PWA installee) revalide
   toujours le document et les ressources aupres du serveur, au lieu
   de servir des versions perimees depuis son cache agressif. */

const CACHE_NAME = 'nimm-epub-v1';

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // API : TOUJOURS le reseau, JAMAIS le cache -- meme si le reseau echoue.
  // Pourquoi (constat de Laurent, 15/09/2026) : les voix castees d'un livre
  // sont des DONNEES. L'ancien code faisait `fetch(req).catch(() => caches.match(req))` :
  // comme aucune reponse d'API n'est mise en cache ici, ce repli ne renvoyait
  // rien du tout -- une promesse sans reponse, donc une erreur de fetch
  // incomprehensible cote page, au lieu d'un echec clair. On renvoie
  // maintenant une erreur explicite : le lecteur possede deja sa mecanique de
  // reprise reseau, et il vaut mieux une erreur lisible qu'une donnee douteuse.
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(req).catch(() => new Response(
        JSON.stringify({ detail: 'reseau indisponible (les donnees ne sont pas mises en cache)' }),
        {
          status: 503,
          statusText: 'Reseau indisponible',
          headers: { 'Content-Type': 'application/json' },
        }))
    );
    return;
  }

  // Document + assets versionnes : reseau d'abord, mise en cache
  // dynamique des reponses OK, cache en secours si hors-ligne.
  event.respondWith((async () => {
    try {
      const fresh = await fetch(req);
      if (fresh.ok) {
        const cache = await caches.open(CACHE_NAME);
        cache.put(req, fresh.clone());
      }
      return fresh;
    } catch (e) {
      const cached = await caches.match(req);
      if (cached) return cached;
      return new Response('Hors ligne', { status: 503, statusText: 'Offline' });
    }
  })());
});
