import { useMutation } from "@tanstack/react-query";
import { Button } from "../../components/ui/Button";
import { api, type Secretariat } from "../../lib/api";
import { useAuthStore } from "../../stores/auth";

const libellesRole: Record<string, string> = {
  super_admin: "Super-administrateur",
  proprietaire: "Propriétaire",
  gerant: "Gérant",
  employe: "Employé",
};

export function Accueil({ secretariat }: { secretariat?: Secretariat | null }) {
  const utilisateur = useAuthStore((s) => s.utilisateur);
  const refreshToken = useAuthStore((s) => s.refreshToken);
  const reinitialiser = useAuthStore((s) => s.reinitialiser);

  const deconnexion = useMutation({
    mutationFn: async () => {
      if (refreshToken) {
        await api.deconnexion(refreshToken).catch(() => undefined);
      }
    },
    onSettled: () => reinitialiser(),
  });

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-5">
      <div className="rounded-2xl bg-papier-surface p-8 shadow-sm">
        <p className="text-encre-pale">Bienvenue</p>
        <h1 className="mb-2 text-3xl">Bonjour, {utilisateur?.nom ?? "…"}</h1>
        {secretariat && (
          <div className="mb-4 rounded-xl bg-cyan-clair p-3">
            <p className="font-medium text-cyan">{secretariat.nom}</p>
            <p className="text-sm text-encre-douce">
              {secretariat.code}
              {secretariat.ville ? ` · ${secretariat.ville}` : ""}
            </p>
          </div>
        )}
        {utilisateur && (
          <dl className="mb-6 space-y-1 text-encre-douce">
            <div className="flex justify-between">
              <dt>Téléphone</dt>
              <dd className="tabular">{utilisateur.telephone}</dd>
            </div>
            <div className="flex justify-between">
              <dt>Rôle</dt>
              <dd>
                <span className="rounded-lg bg-cyan-clair px-2 py-0.5 text-sm text-cyan">
                  {libellesRole[utilisateur.role] ?? utilisateur.role}
                </span>
              </dd>
            </div>
          </dl>
        )}
        <Button
          variante="secondaire"
          onClick={() => deconnexion.mutate()}
          disabled={deconnexion.isPending}
          className="w-full"
        >
          {deconnexion.isPending ? "Déconnexion…" : "Se déconnecter"}
        </Button>
      </div>
    </div>
  );
}
