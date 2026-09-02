import { useSecretariats } from "../../features/secretariats/useSecretariats";
import { useAuthStore } from "../../stores/auth";
import { EnTetePage } from "../../components/layout/EnTetePage";

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

  return (
    <div className="max-w-lg">
      <EnTetePage titre="Paramètres" sousTitre="Votre compte et votre secrétariat." />

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
