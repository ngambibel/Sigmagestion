import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { EnTetePage, EtatVide } from "../../components/layout/EnTetePage";

const TYPES = [
  { valeur: "", libelle: "Tous les types" },
  { valeur: "entree", libelle: "Entrées" },
  { valeur: "sortie_vente", libelle: "Sorties (vente)" },
  { valeur: "ajustement", libelle: "Ajustements" },
  { valeur: "annulation", libelle: "Annulations" },
];

const couleursType: Record<string, string> = {
  entree: "text-valide",
  sortie_vente: "text-magenta",
  ajustement: "text-jaune",
  annulation: "text-encre-pale",
};

function formaterDate(iso: string) {
  return new Date(iso).toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "short" });
}

export default function MouvementsPage() {
  const [type, setType] = useState("");
  const mouvements = useQuery({
    queryKey: ["mouvements", type],
    queryFn: () => api.listerMouvements(type ? { type } : undefined),
  });

  return (
    <div>
      <div className="flex items-start justify-between">
        <EnTetePage titre="Journal des mouvements" sousTitre="Historique horodaté de vos stocks." />
        <Link to="/stock" className="text-sm font-medium text-cyan underline">← Retour au stock</Link>
      </div>

      <div className="mb-4">
        <select
          className="h-10 rounded-lg border border-papier-creux bg-papier-surface px-2"
          value={type}
          onChange={(e) => setType(e.target.value)}
        >
          {TYPES.map((t) => (
            <option key={t.valeur} value={t.valeur}>{t.libelle}</option>
          ))}
        </select>
      </div>

      {mouvements.isLoading ? (
        <p className="text-encre-pale">Chargement…</p>
      ) : !mouvements.data || mouvements.data.length === 0 ? (
        <EtatVide message="Aucun mouvement enregistré pour ce filtre." />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-papier-creux bg-papier-surface">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-papier-creux text-left text-encre-pale">
                <th className="p-3">Date</th>
                <th className="p-3">Consommable</th>
                <th className="p-3">Type</th>
                <th className="p-3 text-right">Quantité</th>
                <th className="p-3 text-right">Stock après</th>
                <th className="p-3">Motif</th>
                <th className="p-3">Auteur</th>
              </tr>
            </thead>
            <tbody>
              {mouvements.data.map((m) => (
                <tr key={m.id} className="border-t border-papier-creux">
                  <td className="whitespace-nowrap p-3 text-encre-pale">{formaterDate(m.cree_le)}</td>
                  <td className="p-3">{m.consommable_nom}</td>
                  <td className={`p-3 font-medium ${couleursType[m.type] ?? ""}`}>{m.type_libelle}</td>
                  <td className="tabular p-3 text-right">{Number(m.quantite) > 0 ? "+" : ""}{Number(m.quantite)}</td>
                  <td className="tabular p-3 text-right">{Number(m.stock_apres)}</td>
                  <td className="p-3 text-encre-douce">{m.motif || "—"}</td>
                  <td className="p-3 text-encre-pale">{m.auteur_nom || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
