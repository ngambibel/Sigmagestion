/**
 * Client API typé minimal pour SigmaGestion.
 * La couche complète (TanStack Query, refresh automatique) arrive à l'étape 0.6.
 */

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

async function requete<T>(chemin: string, options: RequestInit = {}): Promise<T> {
  const reponse = await fetch(`${BASE_URL}${chemin}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  const corps = reponse.status === 204 ? null : await reponse.json().catch(() => null);
  if (!reponse.ok) {
    throw new ApiError(reponse.status, corps);
  }
  return corps as T;
}

export interface Sante {
  base: string;
  redis: string;
}

export const api = {
  sante: () => requete<Sante>("/sante/"),
};
