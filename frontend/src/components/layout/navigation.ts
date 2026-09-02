export interface EntreeNav {
  chemin: string;
  libelle: string;
  icone: string;
  /** Rôles autorisés ; absent = tous les rôles connectés. */
  roles?: string[];
  /** Affiché dans la barre de navigation basse (mobile). */
  mobile?: boolean;
}

export const ENTREES_NAV: EntreeNav[] = [
  { chemin: "/", libelle: "Caisse", icone: "🧾", mobile: true },
  { chemin: "/stock", libelle: "Stock", icone: "📦", mobile: true },
  {
    chemin: "/bilan",
    libelle: "Bilan",
    icone: "📊",
    roles: ["proprietaire", "gerant", "super_admin"],
    mobile: true,
  },
  {
    chemin: "/catalogue",
    libelle: "Catalogue",
    icone: "🏷️",
    roles: ["proprietaire", "super_admin"],
  },
  {
    chemin: "/parametres",
    libelle: "Paramètres",
    icone: "⚙️",
    roles: ["proprietaire", "super_admin"],
  },
];

export function entreesVisibles(role: string | undefined): EntreeNav[] {
  return ENTREES_NAV.filter((e) => !e.roles || (role && e.roles.includes(role)));
}
