/**
 * Base locale (IndexedDB via Dexie) pour le fonctionnement hors ligne (étape 7.2).
 * - `cache` : dernières données serveur connues (catalogue, session…) pour la lecture.
 * - `ventesEnAttente` : file des ventes saisies hors ligne, à synchroniser (idempotence
 *   garantie par `client_uuid`).
 */
import Dexie, { type Table } from "dexie";
import type { SaisieLigne } from "./api";

export interface EntreeCache {
  cle: string;
  data: unknown;
}

export interface VentePayload {
  lignes: SaisieLigne[];
  mode_paiement: string;
  remise: number;
  montant_recu?: number | null;
  client?: number | null;
  client_uuid: string;
}

export interface VenteEnAttente {
  client_uuid: string;
  payload: VentePayload;
  cree_le: string;
  resume: { total: number; nb_lignes: number; mode: string };
}

class SigmaDB extends Dexie {
  cache!: Table<EntreeCache, string>;
  ventesEnAttente!: Table<VenteEnAttente, string>;

  constructor() {
    super("sigmagestion");
    this.version(1).stores({
      cache: "cle",
      ventesEnAttente: "client_uuid, cree_le",
    });
  }
}

export const db = new SigmaDB();
