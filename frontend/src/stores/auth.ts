import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface Utilisateur {
  id: number;
  telephone: string;
  nom: string;
  email: string;
  role: string;
  doit_changer_mdp: boolean;
  is_active: boolean;
  date_joined: string;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  utilisateur: Utilisateur | null;
  estConnecte: () => boolean;
  definirSession: (acces: string, refresh: string) => void;
  definirAcces: (acces: string) => void;
  definirUtilisateur: (u: Utilisateur) => void;
  reinitialiser: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      utilisateur: null,
      estConnecte: () => Boolean(get().accessToken),
      definirSession: (acces, refresh) =>
        set({ accessToken: acces, refreshToken: refresh }),
      definirAcces: (acces) => set({ accessToken: acces }),
      definirUtilisateur: (utilisateur) => set({ utilisateur }),
      reinitialiser: () =>
        set({ accessToken: null, refreshToken: null, utilisateur: null }),
    }),
    { name: "sigma-auth" },
  ),
);
