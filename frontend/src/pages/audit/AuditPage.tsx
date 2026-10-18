import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { EnTetePage } from "../../components/layout/EnTetePage";
import { api } from "../../lib/api";

const FILTRES = [
  { valeur: "", libelle: "Toutes" },
  { valeur: "prix_modifie", libelle: "Prix" },
  { valeur: "stock_ajuste", libelle: "Stock" },
  { valeur: "prestation_annulee", libelle: "Annulations" },
  { valeur: "compte_desactive", libelle: "Comptes" },
];

function resume(valeurs: Record<string, unknown> | null): string {
  if (!valeurs) return "—";
  return Object.entries(valeurs)
    .map(([k, v]) => `${k}: ${v}`)
    .join(", ");
}

export default function AuditPage() {
  const [action, setAction] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["audit", action],
    queryFn: () => api.listerAudit(action || undefined),
  });

  return (
    <div>
      <EnTetePage titre="Journal d'audit" sousTitre="Traçabilité des opérations sensibles." />

      <div className="mb-4 flex flex-wrap gap-2">
        {FILTRES.map((f) => (
          <button
            key={f.valeur}
            onClick={() => setAction(f.valeur)}
            className={[
              "h-9 rounded-xl border px-3 text-sm font-medium",
              action === f.valeur
                ? "border-cyan bg-cyan-clair text-cyan"
                : "border-papier-creux text-encre-douce",
            ].join(" ")}
          >
            {f.libelle}
          </button>
        ))}
      </div>

      <div className="overflow-x-auto rounded-2xl bg-papier-surface p-4 shadow-sm">
        {isLoading ? (
          <p className="text-encre-pale">Chargement…</p>
        ) : !data || data.length === 0 ? (
          <p className="text-encre-pale">Aucune opération enregistrée.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-encre-pale">
                <th className="py-2 font-normal">Date</th>
                <th className="py-2 font-normal">Action</th>
                <th className="py-2 font-normal">Objet</th>
                <th className="py-2 font-normal">Avant → Après</th>
                <th className="py-2 font-normal">Auteur</th>
              </tr>
            </thead>
            <tbody>
              {data.map((e) => (
                <tr key={e.id} className="border-t border-papier-creux align-top">
                  <td className="tabular py-2 text-encre-pale">
                    {new Date(e.cree_le).toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "short" })}
                  </td>
                  <td className="py-2 text-encre">{e.action_libelle}</td>
                  <td className="py-2 text-encre-douce">{e.objet_repr}</td>
                  <td className="py-2 text-encre-douce">
                    <span className="text-encre-pale">{resume(e.valeurs_avant)}</span>
                    {" → "}
                    <span className="text-encre">{resume(e.valeurs_apres)}</span>
                  </td>
                  <td className="py-2 text-encre-douce">{e.auteur_nom}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
