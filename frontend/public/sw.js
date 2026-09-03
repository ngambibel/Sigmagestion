/* Service worker de SigmaGestion — réception des notifications push. */

self.addEventListener("push", (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (e) {
    data = { titre: "SigmaGestion", corps: event.data ? event.data.text() : "" };
  }
  const titre = data.titre || "SigmaGestion";
  const options = {
    body: data.corps || "",
    tag: data.tag || undefined,
    data: { url: data.url || "/" },
    badge: undefined,
  };
  event.waitUntil(self.registration.showNotification(titre, options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const cible = (event.notification.data && event.notification.data.url) || "/";
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((liste) => {
      for (const client of liste) {
        if ("focus" in client) return client.focus();
      }
      if (self.clients.openWindow) return self.clients.openWindow(cible);
    }),
  );
});
