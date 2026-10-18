import { useCallback, useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { synchroniserFile } from "../../lib/sync";
import { compterVentesEnAttente } from "../../lib/offline";

/**
 * Synchronise la file hors ligne : automatiquement au retour du réseau et au
 * montage (si des ventes sont en attente), et manuellement via `synchroniser`.
 * Rafraîchit les données serveur impactées après un envoi.
 */
export function useSynchro() {
  const queryClient = useQueryClient();
  const [enCours, setEnCours] = useState(false);

  const synchroniser = useCallback(async () => {
    setEnCours(true);
    try {
      const resultat = await synchroniserFile();
      if (resultat.envoyees > 0) {
        queryClient.invalidateQueries({ queryKey: ["session-active"] });
        queryClient.invalidateQueries({ queryKey: ["consommables"] });
        queryClient.invalidateQueries({ queryKey: ["prestations"] });
        queryClient.invalidateQueries({ queryKey: ["tableau-de-bord"] });
      }
      return resultat;
    } finally {
      setEnCours(false);
    }
  }, [queryClient]);

  useEffect(() => {
    const auRetour = () => {
      void synchroniser();
    };
    window.addEventListener("online", auRetour);
    // Message du service worker (Background Sync) → on vide la file.
    const surMessage = (e: MessageEvent) => {
      if (e.data?.type === "sigma-sync") void synchroniser();
    };
    navigator.serviceWorker?.addEventListener("message", surMessage);
    // Au montage, s'il reste des ventes et qu'on est en ligne, on tente.
    compterVentesEnAttente().then((n) => {
      if (n > 0 && navigator.onLine) void synchroniser();
    });
    return () => {
      window.removeEventListener("online", auRetour);
      navigator.serviceWorker?.removeEventListener("message", surMessage);
    };
  }, [synchroniser]);

  return { enCours, synchroniser };
}
