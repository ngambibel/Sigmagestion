/** Drainage de la file de ventes hors ligne vers le serveur (étape 7.3).
 * Idempotent : chaque vente porte un client_uuid ; un rejeu ne crée pas de doublon. */
import { api, ApiError } from "./api";
import { listerVentesEnAttente, retirerVente } from "./offline";

let enCours = false;

export interface ResultatSynchro {
  envoyees: number;
  restantes: number;
  erreurs: number;
}

/**
 * Envoie toutes les ventes en attente. Retire de la file celles acceptées
 * (ok/doublon). Garde celles en erreur (ex. plus de session ouverte → 400 global).
 * Protégé contre les exécutions concurrentes.
 */
export async function synchroniserFile(): Promise<ResultatSynchro> {
  if (enCours || !navigator.onLine) return { envoyees: 0, restantes: 0, erreurs: 0 };
  enCours = true;
  try {
    const file = await listerVentesEnAttente();
    if (file.length === 0) return { envoyees: 0, restantes: 0, erreurs: 0 };

    let envoyees = 0;
    let erreurs = 0;
    try {
      const { resultats } = await api.synchroniserPrestations(file.map((v) => v.payload));
      const parUuid = new Map(resultats.map((r) => [r.client_uuid, r.statut]));
      for (const v of file) {
        const statut = parUuid.get(v.client_uuid);
        if (statut === "ok" || statut === "doublon") {
          await retirerVente(v.client_uuid);
          envoyees += 1;
        } else if (statut === "erreur") {
          erreurs += 1;
        }
      }
    } catch (e) {
      // 400 global (pas de session ouverte) ou panne réseau : on garde la file.
      if (!(e instanceof ApiError)) throw e;
    }

    const restantes = (await listerVentesEnAttente()).length;
    return { envoyees, restantes, erreurs };
  } finally {
    enCours = false;
  }
}
