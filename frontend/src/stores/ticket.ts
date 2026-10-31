import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Service } from "../lib/api";

export interface ConsommableChoisi {
  consommableId: number;
  nom: string;
  quantite: number;
  prixAchat: number; // coût de revient unitaire (CUMP) figé à l'affichage
}

export interface LigneTicket {
  serviceId: number;
  nom: string;
  prix: number; // prix unitaire appliqué (modifiable)
  prixCatalogue: number; // prix de référence du service
  quantite: number;
  rectoVerso: boolean;
  rectoVersoPossible: boolean;
  // Consommables choisis librement à la vente ; s'ils sont présents, ils
  // remplacent la recette du service (coût + déduction du stock).
  consommables?: ConsommableChoisi[];
}

interface TicketState {
  lignes: LigneTicket[];
  remise: number;
  ajouter: (service: Service) => void;
  changerQuantite: (serviceId: number, quantite: number) => void;
  changerPrix: (serviceId: number, prix: number) => void;
  basculerRectoVerso: (serviceId: number) => void;
  definirConsommables: (serviceId: number, consommables: ConsommableChoisi[]) => void;
  retirer: (serviceId: number) => void;
  definirRemise: (montant: number) => void;
  vider: () => void;
}

export const useTicketStore = create<TicketState>()(
  persist(
    (set) => ({
      lignes: [],
      remise: 0,
      ajouter: (service) =>
        set((etat) => {
          const existante = etat.lignes.find((l) => l.serviceId === service.id);
          if (existante) {
            return {
              lignes: etat.lignes.map((l) =>
                l.serviceId === service.id ? { ...l, quantite: l.quantite + 1 } : l,
              ),
            };
          }
          // Pré-remplissage depuis la recette du service (quantités PAR UNITÉ vendue).
          const consommables = (service.nomenclature ?? []).map((n) => ({
            consommableId: n.consommable,
            nom: n.consommable_nom,
            quantite: Number(n.qte_par_unite),
            prixAchat: Number(n.prix_achat),
          }));
          return {
            lignes: [
              ...etat.lignes,
              {
                serviceId: service.id,
                nom: service.nom,
                prix: service.prix,
                prixCatalogue: service.prix,
                quantite: 1,
                rectoVerso: false,
                rectoVersoPossible: service.recto_verso_possible,
                consommables: consommables.length ? consommables : undefined,
              },
            ],
          };
        }),
      changerQuantite: (serviceId, quantite) =>
        set((etat) => ({
          lignes:
            quantite <= 0
              ? etat.lignes.filter((l) => l.serviceId !== serviceId)
              : etat.lignes.map((l) =>
                  l.serviceId === serviceId ? { ...l, quantite } : l,
                ),
        })),
      changerPrix: (serviceId, prix) =>
        set((etat) => ({
          lignes: etat.lignes.map((l) =>
            l.serviceId === serviceId ? { ...l, prix: Math.max(0, prix) } : l,
          ),
        })),
      basculerRectoVerso: (serviceId) =>
        set((etat) => ({
          lignes: etat.lignes.map((l) =>
            l.serviceId === serviceId ? { ...l, rectoVerso: !l.rectoVerso } : l,
          ),
        })),
      definirConsommables: (serviceId, consommables) =>
        set((etat) => ({
          lignes: etat.lignes.map((l) =>
            l.serviceId === serviceId
              ? { ...l, consommables: consommables.length ? consommables : undefined }
              : l,
          ),
        })),
      retirer: (serviceId) =>
        set((etat) => ({ lignes: etat.lignes.filter((l) => l.serviceId !== serviceId) })),
      definirRemise: (montant) => set({ remise: Math.max(0, montant) }),
      vider: () => set({ lignes: [], remise: 0 }),
    }),
    { name: "sigma-ticket" },
  ),
);

/** Sous-total (avant remise). */
export function sousTotal(lignes: LigneTicket[]): number {
  return lignes.reduce((somme, l) => somme + l.prix * l.quantite, 0);
}

/** Total à payer (après remise, jamais négatif). */
export function totalTicket(lignes: LigneTicket[], remise: number): number {
  return Math.max(0, sousTotal(lignes) - remise);
}

/** Coût matière d'une ligne : coût par unité (consommables choisis) × quantité vendue. */
export function coutMatiereLigne(l: LigneTicket): number {
  const parUnite = (l.consommables ?? []).reduce((s, c) => s + c.quantite * c.prixAchat, 0);
  return parUnite * l.quantite;
}

/** Coût matière total des consommables choisis sur le ticket. */
export function coutMatiereTicket(lignes: LigneTicket[]): number {
  return lignes.reduce((s, l) => s + coutMatiereLigne(l), 0);
}
