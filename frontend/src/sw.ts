/// <reference lib="webworker" />
/* Service worker SigmaGestion : précache du shell (PWA installable, étape 7.1)
   + mise en cache réseau du catalogue et des polices + réception des push (4.2).
   Stratégie injectManifest : ce fichier source est conservé, Workbox y injecte
   le manifeste de précache (self.__WB_MANIFEST). */
import { clientsClaim } from "workbox-core";
import { precacheAndRoute, cleanupOutdatedCaches } from "workbox-precaching";
import { registerRoute, NavigationRoute } from "workbox-routing";
import { NetworkFirst, StaleWhileRevalidate, CacheFirst } from "workbox-strategies";
import { ExpirationPlugin } from "workbox-expiration";

declare const self: ServiceWorkerGlobalScope & { __WB_MANIFEST: unknown[] };

self.skipWaiting();
clientsClaim();

// --- Précache du shell applicatif (généré au build) ---
cleanupOutdatedCaches();
precacheAndRoute(self.__WB_MANIFEST);

// Navigation (SPA) : on sert index.html depuis le cache, réseau en secours.
const handlerNavigation = new NetworkFirst({
  cacheName: "shell",
  networkTimeoutSeconds: 3,
});
registerRoute(new NavigationRoute(handlerNavigation, { denylist: [/^\/api\//, /^\/admin\//] }));

// Catalogue et consommables : lecture rapide depuis le cache, revalidation en fond.
registerRoute(
  ({ url }) => /\/api\/v1\/(services|consommables|secretariats|onboarding)/.test(url.pathname),
  new StaleWhileRevalidate({
    cacheName: "api-catalogue",
    plugins: [new ExpirationPlugin({ maxEntries: 60, maxAgeSeconds: 24 * 3600 })],
  }),
);

// Polices (Fontsource importées dans le bundle restent précachées ; au cas où).
registerRoute(
  ({ request }) => request.destination === "font",
  new CacheFirst({
    cacheName: "polices",
    plugins: [new ExpirationPlugin({ maxEntries: 20, maxAgeSeconds: 365 * 24 * 3600 })],
  }),
);

// --- Background Sync : au retour du réseau, on réveille l'app pour qu'elle vide
//     la file (le JWT vit côté fenêtre, la fenêtre fait donc l'envoi). ---
self.addEventListener("sync", (event: Event) => {
  const e = event as Event & { tag: string; waitUntil: (p: Promise<unknown>) => void };
  if (e.tag === "sigma-sync-ventes") {
    e.waitUntil(
      self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((liste) => {
        liste.forEach((c) => c.postMessage({ type: "sigma-sync" }));
      }),
    );
  }
});

// --- Notifications push (repris de l'étape 4.2) ---
self.addEventListener("push", (event) => {
  let data: { titre?: string; corps?: string; url?: string; tag?: string } = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch {
    data = { titre: "SigmaGestion", corps: event.data ? event.data.text() : "" };
  }
  const titre = data.titre || "SigmaGestion";
  event.waitUntil(
    self.registration.showNotification(titre, {
      body: data.corps || "",
      tag: data.tag || undefined,
      data: { url: data.url || "/" },
    }),
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const cible = (event.notification.data && event.notification.data.url) || "/";
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((liste) => {
      for (const client of liste) {
        if ("focus" in client) return client.focus();
      }
      return self.clients.openWindow ? self.clients.openWindow(cible) : undefined;
    }),
  );
});
