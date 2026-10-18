import { useEffect, useState } from "react";
import { compterVentesEnAttente, ecouterQueue } from "../../lib/offline";

/** État de connexion réseau (navigator.onLine + événements). */
export function useOnline(): boolean {
  const [enLigne, setEnLigne] = useState(
    typeof navigator === "undefined" ? true : navigator.onLine,
  );
  useEffect(() => {
    const maj = () => setEnLigne(navigator.onLine);
    window.addEventListener("online", maj);
    window.addEventListener("offline", maj);
    return () => {
      window.removeEventListener("online", maj);
      window.removeEventListener("offline", maj);
    };
  }, []);
  return enLigne;
}

/** Nombre de ventes en attente de synchronisation (réactif aux évolutions de la file). */
export function useVentesEnAttente(): number {
  const [nb, setNb] = useState(0);
  useEffect(() => {
    let actif = true;
    const rafraichir = () => compterVentesEnAttente().then((n) => actif && setNb(n));
    rafraichir();
    const stop = ecouterQueue(rafraichir);
    window.addEventListener("online", rafraichir);
    return () => {
      actif = false;
      stop();
      window.removeEventListener("online", rafraichir);
    };
  }, []);
  return nb;
}
