import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Theme = "systeme" | "clair" | "sombre";

const COULEUR_BARRE: Record<"clair" | "sombre", string> = {
  clair: "#0B7285",
  sombre: "#101215",
};

/** Applique le thème au document (attribut data-theme + couleur de la barre d'état). */
export function appliquerTheme(theme: Theme) {
  const racine = document.documentElement;
  if (theme === "systeme") {
    racine.removeAttribute("data-theme");
  } else {
    racine.setAttribute("data-theme", theme);
  }
  const sombreEffectif =
    theme === "sombre" ||
    (theme === "systeme" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute("content", sombreEffectif ? COULEUR_BARRE.sombre : COULEUR_BARRE.clair);
}

interface ThemeState {
  theme: Theme;
  definirTheme: (t: Theme) => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: "systeme",
      definirTheme: (theme) => {
        appliquerTheme(theme);
        set({ theme });
      },
    }),
    { name: "sigma-theme" },
  ),
);
