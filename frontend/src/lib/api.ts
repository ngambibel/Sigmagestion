/**
 * Client API typé pour SigmaGestion.
 * Injecte le token d'accès, rafraîchit automatiquement sur 401 une fois.
 */
import { useAuthStore, type Utilisateur } from "../stores/auth";

export const BASE_URL =
  import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  constructor(
    public statut: number,
    public corps: unknown,
  ) {
    super(`Erreur API ${statut}`);
    this.name = "ApiError";
  }
}

interface Options extends RequestInit {
  /** Requête publique : n'ajoute pas le header d'autorisation. */
  publique?: boolean;
  /** Interne : empêche une seconde tentative de refresh. */
  _reessaye?: boolean;
}

async function rafraichirAcces(): Promise<boolean> {
  const { refreshToken, definirAcces, reinitialiser } = useAuthStore.getState();
  if (!refreshToken) return false;
  const reponse = await fetch(`${BASE_URL}/auth/rafraichir/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: refreshToken }),
  });
  if (!reponse.ok) {
    reinitialiser();
    return false;
  }
  const corps = (await reponse.json()) as { access: string };
  definirAcces(corps.access);
  return true;
}

async function requete<T>(chemin: string, options: Options = {}): Promise<T> {
  const { publique, _reessaye, headers, ...reste } = options;
  const token = useAuthStore.getState().accessToken;
  const entetes: Record<string, string> = {
    "Content-Type": "application/json",
    ...(headers as Record<string, string>),
  };
  if (!publique && token) entetes.Authorization = `Bearer ${token}`;

  const reponse = await fetch(`${BASE_URL}${chemin}`, { headers: entetes, ...reste });

  // 401 → tentative unique de rafraîchissement puis nouvel essai.
  if (reponse.status === 401 && !publique && !_reessaye) {
    if (await rafraichirAcces()) {
      return requete<T>(chemin, { ...options, _reessaye: true });
    }
  }

  const corps =
    reponse.status === 204 || reponse.status === 205
      ? null
      : await reponse.json().catch(() => null);
  if (!reponse.ok) throw new ApiError(reponse.status, corps);
  return corps as T;
}

export interface Sante {
  base: string;
  redis: string;
}

export interface ReponseConnexion {
  access: string;
  refresh: string;
  role: string;
  nom: string;
  doit_changer_mdp: boolean;
}

export interface DonneesInscription {
  nom: string;
  telephone: string;
  email?: string;
  password: string;
}

export interface Secretariat {
  id: number;
  nom: string;
  code: string;
  ville: string;
  quartier: string;
  telephone: string;
  devise: string;
  onboarding_termine: boolean;
  proprietaire: number;
  cree_le: string;
}

export interface ServiceModele {
  nom: string;
  categorie: string;
  unite_facturation: string;
  prix: number;
  consomme_stock: boolean;
}

export interface ConsommableModele {
  nom: string;
  unite_mesure: string;
  prix_achat: number;
  seuil_alerte: number;
}

export interface ModelesOnboarding {
  services: ServiceModele[];
  consommables: ConsommableModele[];
}

export interface Service {
  id: number;
  nom: string;
  categorie: string;
  unite_facturation: string;
  prix: number;
  consomme_stock: boolean;
  actif: boolean;
  couleur: string;
  icone: string;
  ordre: number;
}

export interface Consommable {
  id: number;
  nom: string;
  unite_mesure: string;
  prix_achat: number;
  qte_stock: string;
  seuil_alerte: string;
  seuil_critique: string | null;
  fournisseur: string;
  actif: boolean;
  sous_seuil: boolean;
}

export const api = {
  sante: () => requete<Sante>("/sante/", { publique: true }),

  connexion: (telephone: string, password: string) =>
    requete<ReponseConnexion>("/auth/connexion/", {
      method: "POST",
      publique: true,
      body: JSON.stringify({ telephone, password }),
    }),

  inscription: (donnees: DonneesInscription) =>
    requete<ReponseConnexion>("/auth/inscription/", {
      method: "POST",
      publique: true,
      body: JSON.stringify(donnees),
    }),

  moi: () => requete<Utilisateur>("/moi/"),

  deconnexion: (refresh: string) =>
    requete<null>("/auth/deconnexion/", {
      method: "POST",
      body: JSON.stringify({ refresh }),
    }),

  // --- Secrétariats ---
  listerSecretariats: () => requete<Secretariat[]>("/secretariats/"),

  creerSecretariat: (donnees: Partial<Secretariat>) =>
    requete<Secretariat>("/secretariats/", {
      method: "POST",
      body: JSON.stringify(donnees),
    }),

  modifierSecretariat: (id: number, donnees: Partial<Secretariat>) =>
    requete<Secretariat>(`/secretariats/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(donnees),
    }),

  // --- Onboarding ---
  modelesOnboarding: () => requete<ModelesOnboarding>("/onboarding/modeles/"),

  // --- Catalogue ---
  listerServices: () => requete<Service[]>("/services/"),
  creerService: (donnees: Partial<Service>) =>
    requete<Service>("/services/", { method: "POST", body: JSON.stringify(donnees) }),
  modifierService: (id: number, donnees: Partial<Service>) =>
    requete<Service>(`/services/${id}/`, { method: "PATCH", body: JSON.stringify(donnees) }),
  supprimerService: (id: number) =>
    requete<null>(`/services/${id}/`, { method: "DELETE" }),

  // --- Stocks ---
  listerConsommables: () => requete<Consommable[]>("/consommables/"),
  creerConsommable: (donnees: Record<string, unknown>) =>
    requete<Consommable>("/consommables/", {
      method: "POST",
      body: JSON.stringify(donnees),
    }),
  modifierConsommable: (id: number, donnees: Record<string, unknown>) =>
    requete<Consommable>(`/consommables/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(donnees),
    }),
  supprimerConsommable: (id: number) =>
    requete<null>(`/consommables/${id}/`, { method: "DELETE" }),
};
