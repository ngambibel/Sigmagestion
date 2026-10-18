/** Helpers hors ligne : cache de lecture et file de ventes en attente. */
import { db, type VentePayload } from "./db";

const EVT_QUEUE = "sigma:ventes-maj";

/** Prévient l'UI (badge, bandeau) qu'une évolution a eu lieu dans la file. */
export function notifierQueue() {
  window.dispatchEvent(new Event(EVT_QUEUE));
}

export function ecouterQueue(cb: () => void): () => void {
  window.addEventListener(EVT_QUEUE, cb);
  return () => window.removeEventListener(EVT_QUEUE, cb);
}

/**
 * Exécute `fn` (appel réseau) ; en cas de succès, met en cache le résultat ;
 * en cas d'échec (hors ligne), renvoie la dernière valeur connue si elle existe.
 */
export async function chargerAvecCache<T>(cle: string, fn: () => Promise<T>): Promise<T> {
  try {
    const data = await fn();
    await db.cache.put({ cle, data });
    return data;
  } catch (erreur) {
    const entree = await db.cache.get(cle);
    if (entree !== undefined) return entree.data as T;
    throw erreur;
  }
}

/** Ajoute une vente à la file hors ligne et renvoie son client_uuid. */
export async function enfilerVente(
  base: Omit<VentePayload, "client_uuid">,
  resume: { total: number; nb_lignes: number; mode: string },
): Promise<string> {
  const client_uuid =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  await db.ventesEnAttente.add({
    client_uuid,
    payload: { ...base, client_uuid },
    cree_le: new Date().toISOString(),
    resume,
  });
  notifierQueue();
  return client_uuid;
}

export function compterVentesEnAttente(): Promise<number> {
  return db.ventesEnAttente.count();
}

export function listerVentesEnAttente() {
  return db.ventesEnAttente.orderBy("cree_le").toArray();
}

export async function retirerVente(client_uuid: string) {
  await db.ventesEnAttente.delete(client_uuid);
  notifierQueue();
}
