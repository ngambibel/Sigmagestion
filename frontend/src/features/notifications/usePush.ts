import { useCallback, useEffect, useState } from "react";
import { api } from "../../lib/api";

/** Convertit la clé publique VAPID (base64url) en Uint8Array pour l'abonnement. */
function base64UrlVersUint8Array(base64: string): Uint8Array {
  const padding = "=".repeat((4 - (base64.length % 4)) % 4);
  const base64Std = (base64 + padding).replace(/-/g, "+").replace(/_/g, "/");
  const brut = atob(base64Std);
  return Uint8Array.from([...brut].map((c) => c.charCodeAt(0)));
}

type EtatPermission = "default" | "granted" | "denied";

export function usePush() {
  const supporte =
    typeof navigator !== "undefined" &&
    "serviceWorker" in navigator &&
    "PushManager" in window;

  const [permission, setPermission] = useState<EtatPermission>(
    supporte ? (Notification.permission as EtatPermission) : "denied",
  );
  const [abonne, setAbonne] = useState(false);
  const [enCours, setEnCours] = useState(false);

  useEffect(() => {
    if (!supporte) return;
    navigator.serviceWorker.ready
      .then((reg) => reg.pushManager.getSubscription())
      .then((sub) => setAbonne(Boolean(sub)))
      .catch(() => undefined);
  }, [supporte]);

  const activer = useCallback(async () => {
    if (!supporte) return;
    setEnCours(true);
    try {
      // Le service worker est enregistré au démarrage par le plugin PWA.
      const registration = await navigator.serviceWorker.ready;
      const perm = await Notification.requestPermission();
      setPermission(perm as EtatPermission);
      if (perm !== "granted") return;

      const { cle_publique } = await api.clePubliquePush();
      const abonnement = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: base64UrlVersUint8Array(cle_publique),
      });

      const brut = abonnement.toJSON() as { endpoint: string; keys: { p256dh: string; auth: string } };
      await api.abonnerPush({
        endpoint: brut.endpoint,
        keys: brut.keys,
        navigateur: navigator.userAgent.slice(0, 180),
      });
      setAbonne(true);
    } finally {
      setEnCours(false);
    }
  }, [supporte]);

  const desactiver = useCallback(async () => {
    if (!supporte) return;
    setEnCours(true);
    try {
      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.getSubscription();
      if (sub) {
        await api.desabonnerPush(sub.endpoint).catch(() => undefined);
        await sub.unsubscribe();
      }
      setAbonne(false);
    } finally {
      setEnCours(false);
    }
  }, [supporte]);

  const envoyerTest = useCallback(() => api.envoyerPushTest(), []);

  return { supporte, permission, abonne, enCours, activer, desactiver, envoyerTest };
}
