import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { EnTetePage } from "../../components/layout/EnTetePage";
import { Button } from "../../components/ui/Button";
import { api, telechargerRapportCsv, type Rapport, type TypeRapport } from "../../lib/api";

const ONGLETS: { cle: TypeRapport; libelle: string }[] = [
  { cle: "ventes", libelle: "Ventes" },
  { cle: "rentabilite", libelle: "Rentabilité" },
  { cle: "stock", libelle: "Stock" },
  { cle: "caisse", libelle: "Caisse" },
];

const MODES = [
  { valeur: "", libelle: "Tous les règlements" },
  { valeur: "especes", libelle: "Espèces" },
  { valeur: "momo", libelle: "MTN MoMo" },
  { valeur: "orange_money", libelle: "Orange Money" },
  { valeur: "credit", libelle: "Crédit" },
];

// Clés de colonnes dont la valeur est un montant en XAF (pour l'affichage « F »).
const COLONNES_MONTANT = new Set([
  "montant", "cout", "marge", "ca", "valorisation", "prix_achat",
  "fond_initial", "theorique", "compte", "ecart",
]);

function formate(cle: string, valeur: string | number): string {
  if (typeof valeur === "number") {
    const n = valeur.toLocaleString("fr-FR");
    if (COLONNES_MONTANT.has(cle)) return `${n} F`;
    if (cle === "marge_pct") return `${valeur} %`;
    return n;
  }
  return valeur;
}

function libelleTotal(cle: string): string {
  const map: Record<string, string> = {
    ca_total: "CA total",
    cout_total: "Coût total",
    marge_total: "Marge totale",
    nb_prestations: "Prestations",
    valorisation_totale: "Valorisation du stock",
    ecart_total: "Écart cumulé",
    depenses_total: "Dépenses",
    nb_sessions: "Sessions",
  };
  return map[cle] ?? cle.replace(/_/g, " ");
}

function imprimer(rapport: Rapport, periode: string) {
  const entetes = rapport.colonnes.map((c) => `<th>${c.libelle}</th>`).join("");
  const corps = rapport.lignes
    .map(
      (l) =>
        `<tr>${rapport.colonnes
          .map((c) => `<td>${formate(c.cle, l[c.cle] ?? "")}</td>`)
          .join("")}</tr>`,
    )
    .join("");
  const totaux = Object.entries(rapport.totaux)
    .filter(([, v]) => typeof v === "number")
    .map(([k, v]) => `<li><strong>${libelleTotal(k)} :</strong> ${formate(k, v as number)}</li>`)
    .join("");
  const html = `<!doctype html><html lang="fr"><head><meta charset="utf-8">
    <title>${rapport.titre}</title>
    <style>
      body{font-family:system-ui,Arial,sans-serif;color:#14161A;padding:24px;}
      h1{font-size:20px;margin:0 0 4px;}
      .periode{color:#4A4F58;margin:0 0 16px;}
      table{width:100%;border-collapse:collapse;font-size:12px;}
      th,td{border-bottom:1px solid #ECECE6;padding:6px 8px;text-align:left;}
      td:nth-child(n+2){text-align:right;}
      th:nth-child(n+2){text-align:right;}
      ul{margin-top:16px;padding-left:18px;}
    </style></head><body>
    <h1>${rapport.titre}</h1>
    <p class="periode">${periode}</p>
    <table><thead><tr>${entetes}</tr></thead><tbody>${corps}</tbody></table>
    <ul>${totaux}</ul>
    <script>window.onload=function(){window.print();}</script>
    </body></html>`;
  const fenetre = window.open("", "_blank", "width=900,height=700");
  if (fenetre) {
    fenetre.document.write(html);
    fenetre.document.close();
  }
}

export default function RapportsPage() {
  const [type, setType] = useState<TypeRapport>("ventes");
  const [debut, setDebut] = useState("");
  const [fin, setFin] = useState("");
  const [mode, setMode] = useState("");

  const params = new URLSearchParams();
  if (debut) params.set("date_debut", debut);
  if (fin) params.set("date_fin", fin);
  if (mode && type === "ventes") params.set("mode_reglement", mode);
  const qs = params.toString();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["rapport", type, qs],
    queryFn: () => api.getRapport(type, qs),
  });

  const periodeLisible =
    debut || fin ? `Période : ${debut || "…"} → ${fin || "…"}` : "Toutes périodes";

  return (
    <div>
      <EnTetePage titre="Rapports" sousTitre="Ventes, rentabilité, stock et caisse." />

      {/* Onglets */}
      <div className="mb-4 flex flex-wrap gap-2">
        {ONGLETS.map((o) => (
          <button
            key={o.cle}
            onClick={() => setType(o.cle)}
            className={[
              "h-10 rounded-xl border px-4 text-sm font-medium",
              type === o.cle
                ? "border-cyan bg-cyan-clair text-cyan"
                : "border-papier-creux text-encre-douce",
            ].join(" ")}
          >
            {o.libelle}
          </button>
        ))}
      </div>

      {/* Filtres */}
      <div className="mb-4 flex flex-wrap items-end gap-3 rounded-2xl bg-papier-surface p-4 shadow-sm">
        <label className="flex flex-col gap-1 text-sm text-encre-douce">
          Du
          <input type="date" value={debut} onChange={(e) => setDebut(e.target.value)}
            className="h-10 rounded-lg border border-papier-creux bg-papier-surface px-2 text-encre" />
        </label>
        <label className="flex flex-col gap-1 text-sm text-encre-douce">
          Au
          <input type="date" value={fin} onChange={(e) => setFin(e.target.value)}
            className="h-10 rounded-lg border border-papier-creux bg-papier-surface px-2 text-encre" />
        </label>
        {type === "ventes" && (
          <label className="flex flex-col gap-1 text-sm text-encre-douce">
            Règlement
            <select value={mode} onChange={(e) => setMode(e.target.value)}
              className="h-10 rounded-lg border border-papier-creux bg-papier-surface px-2 text-encre">
              {MODES.map((m) => <option key={m.valeur} value={m.valeur}>{m.libelle}</option>)}
            </select>
          </label>
        )}
        <div className="ml-auto flex gap-2">
          <Button
            variante="secondaire"
            onClick={() => telechargerRapportCsv(type, qs, `${type}`)}
            disabled={!data}
          >
            Exporter CSV
          </Button>
          <Button onClick={() => data && imprimer(data, periodeLisible)} disabled={!data}>
            Imprimer / PDF
          </Button>
        </div>
      </div>

      {/* Tableau */}
      <div className="overflow-x-auto rounded-2xl bg-papier-surface p-4 shadow-sm">
        {isLoading ? (
          <p className="text-encre-pale">Chargement…</p>
        ) : isError || !data ? (
          <p className="text-magenta">Impossible de charger le rapport.</p>
        ) : data.lignes.length === 0 ? (
          <p className="text-encre-pale">Aucune donnée sur cette période.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-encre-pale">
                {data.colonnes.map((c, i) => (
                  <th key={c.cle} className={i === 0 ? "py-2 text-left font-normal" : "py-2 text-right font-normal"}>
                    {c.libelle}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.lignes.map((l, idx) => (
                <tr key={idx} className="border-t border-papier-creux">
                  {data.colonnes.map((c, i) => (
                    <td key={c.cle} className={[
                      "py-1.5",
                      i === 0 ? "text-left text-encre" : "tabular text-right text-encre-douce",
                    ].join(" ")}>
                      {formate(c.cle, l[c.cle] ?? "")}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Totaux */}
      {data && (
        <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 rounded-2xl bg-papier-surface p-4 text-sm shadow-sm">
          {Object.entries(data.totaux)
            .filter(([, v]) => typeof v === "number")
            .map(([k, v]) => (
              <span key={k} className="text-encre-douce">
                {libelleTotal(k)} : <span className="tabular font-medium text-encre">{formate(k, v as number)}</span>
              </span>
            ))}
        </div>
      )}
    </div>
  );
}
