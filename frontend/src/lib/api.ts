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

export const api = {
  sante: () => requete<Sante>("/sante/", { publique: true }),

  connexion: (telephone: string, password: string) =>
    requete<ReponseConnexion>("/auth/connexion/", {
      method: "POST",
      publique: true,
      body: JSON.stringify({ telephone, password }),
    }),

  moi: () => requete<Utilisateur>("/moi/"),

  deconnexion: (refresh: string) =>
    requete<null>("/auth/deconnexion/", {
      method: "POST",
      body: JSON.stringify({ refresh }),
    }),
};
