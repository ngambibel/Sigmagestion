import { useSecretariats } from "../../features/secretariats/useSecretariats";
import { useAuthStore } from "../../stores/auth";
import { EnTetePage } from "../../components/layout/EnTetePage";
import { SectionNotifications } from "../../features/notifications/SectionNotifications";
import { SectionHoraires } from "../../features/notifications/SectionHoraires";
import { useThemeStore, type Theme } from "../../stores/theme";

const THEMES: { valeur: Theme; libelle: string; icone: string }[] = [
  { valeur: "systeme", libelle: "Système", icone: "🖥️" },
  { valeur: "clair", libelle: "Clair", icone: "☀️" },
  { valeur: "sombre", libelle: "Sombre", icone: "🌙" },
];

function SectionApparence() {
  const theme = useThemeStore((s) => s.theme);
  const definirTheme = useThemeStore((s) => s.definirTheme);
  return (
    <section className="mb-6 rounded-2xl bg-papier-surface p-5 shadow-sm">
      <h2 className="mb-1 text-lg">Apparence</h2>
      <p className="mb-3 text-sm text-encre-douce">
        Le thème sombre économise la batterie et repose les yeux en soirée.
      </p>
      <div role="radiogroup" aria-label="Thème" className="flex gap-2">
        {THEMES.map((t) => (
          <button
            key={t.valeur}
            role="radio"
            aria-checked={theme === t.valeur}
            onClick={() => definirTheme(t.valeur)}
            className={[
              "flex h-11 flex-1 items-center justify-center gap-2 rounded-xl border text-sm font-medium",
              theme === t.valeur
                ? "border-cyan bg-cyan-clair text-cyan"
                : "border-papier-creux text-encre-douce",
            ].join(" ")}
          >
            <span aria-hidden>{t.icone}</span>
            {t.libelle}
          </button>
        ))}
      </div>
    </section>
  );
}

const libellesRole: Record<string, string> = {
  super_admin: "Super-administrateur",
  proprietaire: "Propriétaire",
  gerant: "Gérant",
  employe: "Employé",
};

function Ligne({ cle, valeur }: { cle: string; valeur: string }) {
  return (
    <div className="flex justify-between border-t border-papier-creux py-2 first:border-t-0">
      <dt className="text-encre-douce">{cle}</dt>
      <dd className="tabular">{valeur}</dd>
    </div>
  );
}

export default function ParametresPage() {
  const utilisateur = useAuthStore((s) => s.utilisateur);
  const { secretariat } = useSecretariats();
  const estProprietaire = utilisateur?.role === "proprietaire" || utilisateur?.role === "super_admin";

  return (
    <div className="max-w-lg">
      <EnTetePage titre="Paramètres" sousTitre="Votre compte et votre secrétariat." />

      <SectionApparence />

      <SectionNotifications />

      {estProprietaire && <SectionHoraires />}

      <section className="mb-6 rounded-2xl bg-papier-surface p-5 shadow-sm">
        <h2 className="mb-2 text-lg">Compte</h2>
        <dl>
          <Ligne cle="Nom" valeur={utilisateur?.nom ?? "—"} />
          <Ligne cle="Téléphone" valeur={utilisateur?.telephone ?? "—"} />
          <Ligne cle="Rôle" valeur={libellesRole[utilisateur?.role ?? ""] ?? "—"} />
        </dl>
      </section>

      {secretariat && (
        <section className="rounded-2xl bg-papier-surface p-5 shadow-sm">
          <h2 className="mb-2 text-lg">Secrétariat</h2>
          <dl>
            <Ligne cle="Nom" valeur={secretariat.nom} />
            <Ligne cle="Code" valeur={secretariat.code} />
            <Ligne cle="Ville" valeur={secretariat.ville || "—"} />
            <Ligne cle="Devise" valeur={secretariat.devise} />
          </dl>
        </section>
      )}
    </div>
  );
}
