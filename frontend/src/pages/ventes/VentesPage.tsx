import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Prestation } from "../../lib/api";
import { EnTetePage, EtatVide } from "../../components/layout/EnTetePage";

const modesLibelle: Record<string, string> = {
  especes: "Espèces",
  momo: "MoMo",
  orange_money: "Orange",
  credit: "Crédit",
};

function formaterHeure(iso: string) {
  return new Date(iso).toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "short" });
}

export default function VentesPage() {
  const prestations = useQuery({ queryKey: ["prestations"], queryFn: api.listerPrestations });
  const queryClient = useQueryClient();

  const annuler = useMutation({
    mutationFn: ({ id, motif }: { id: number; motif: string }) => api.annulerPrestation(id, motif),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["prestations"] });
      queryClient.invalidateQueries({ queryKey: ["consommables"] });
    },
  });

  const demanderAnnulation = (p: Prestation) => {
    const motif = window.prompt(`Annuler le ticket ${p.numero} ? Indiquez le motif :`);
    if (motif && motif.trim()) annuler.mutate({ id: p.id, motif: motif.trim() });
  };

  return (
    <div>
      <div className="flex items-start justify-between">
        <EnTetePage titre="Ventes" sousTitre="Historique des prestations. L'annulation ré-injecte le stock." />
        <Link to="/" className="text-sm font-medium text-cyan underline">← Caisse</Link>
      </div>

      {prestations.isLoading ? (
        <p className="text-encre-pale">Chargement…</p>
      ) : !prestations.data || prestations.data.length === 0 ? (
        <EtatVide message="Aucune vente enregistrée pour le moment." />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-papier-creux bg-papier-surface">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-papier-creux text-left text-encre-pale">
                <th className="p-3">Ticket</th>
                <th className="p-3">Heure</th>
                <th className="p-3 text-right">Montant</th>
                <th className="p-3">Paiement</th>
                <th className="p-3">Statut</th>
                <th className="p-3"></th>
              </tr>
            </thead>
            <tbody>
              {prestations.data.map((p) => {
                const annulee = p.statut === "annulee";
                return (
                  <tr key={p.id} className={`border-t border-papier-creux ${annulee ? "opacity-60" : ""}`}>
                    <td className="p-3 font-medium">{p.numero}</td>
                    <td className="whitespace-nowrap p-3 text-encre-pale">{formaterHeure(p.cree_le)}</td>
                    <td className="tabular p-3 text-right">{p.montant_total.toLocaleString("fr-FR")} F</td>
                    <td className="p-3">
                      {modesLibelle[p.mode_paiement] ?? p.mode_paiement}
                      {p.mode_paiement === "credit" && p.nom_client ? ` · ${p.nom_client}` : ""}
                    </td>
                    <td className="p-3">
                      {annulee ? (
                        <span className="rounded bg-magenta-clair px-1.5 py-0.5 text-xs text-magenta">annulée</span>
                      ) : (
                        <span className="rounded bg-valide-clair px-1.5 py-0.5 text-xs text-valide">validée</span>
                      )}
                    </td>
                    <td className="p-3 text-right">
                      {!annulee && (
                        <button
                          onClick={() => demanderAnnulation(p)}
                          className="text-sm font-medium text-magenta underline"
                          disabled={annuler.isPending}
                        >
                          Annuler
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
