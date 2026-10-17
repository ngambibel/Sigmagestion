import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { EnTetePage } from "../../components/layout/EnTetePage";
import { api, type TableauDeBord } from "../../lib/api";
import { useAuthStore } from "../../stores/auth";
import BilanEmploye from "./BilanEmploye";

// Encres de la charte (quadrichromie) — utilisées comme couleurs de marque des graphiques.
const CYAN = "#0B7285";
const ENCRE_PALE = "#868D98";
const PAPIER_CREUX = "#ECECE6";

const fcfa = (n: number) => `${n.toLocaleString("fr-FR")} F`;
const jourMois = (iso: string) => {
  const d = new Date(iso);
  return `${d.getDate().toString().padStart(2, "0")}/${(d.getMonth() + 1).toString().padStart(2, "0")}`;
};

function Carte({ titre, children }: { titre: string; children: ReactNode }) {
  return (
    <section className="rounded-2xl bg-papier-surface p-5 shadow-sm">
      <h2 className="mb-3 text-base text-encre-douce">{titre}</h2>
      {children}
    </section>
  );
}

function InfoBulle({ actif, payload, label, suffixe }: any) {
  if (!actif || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-papier-creux bg-papier-surface px-3 py-2 text-sm shadow-md">
      {label && <p className="mb-0.5 text-encre-pale">{label}</p>}
      <p className="tabular font-medium text-encre">
        {fcfa(payload[0].value)}
        {suffixe}
      </p>
    </div>
  );
}

function BilanProprietaire() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["tableau-de-bord"],
    queryFn: api.tableauDeBord,
    refetchInterval: 60_000,
  });

  if (isLoading) {
    return (
      <div>
        <EnTetePage titre="Bilan" sousTitre="Votre chiffre d'affaires et vos indicateurs." />
        <p className="text-encre-pale">Chargement du tableau de bord…</p>
      </div>
    );
  }
  if (isError || !data) {
    return (
      <div>
        <EnTetePage titre="Bilan" sousTitre="Votre chiffre d'affaires et vos indicateurs." />
        <p className="text-magenta">Impossible de charger le tableau de bord.</p>
      </div>
    );
  }

  const d: TableauDeBord = data;
  const variation = d.variation_pct;
  const hausse = (variation ?? 0) >= 0;

  return (
    <div>
      <EnTetePage titre="Bilan" sousTitre="Votre chiffre d'affaires et vos indicateurs." />

      <div className="grid gap-4 md:grid-cols-3">
        {/* Hero : CA du jour */}
        <section className="rounded-2xl bg-papier-surface p-5 shadow-sm md:col-span-3">
          <p className="text-encre-douce">Chiffre d'affaires du jour</p>
          <p className="tabular font-display text-5xl text-encre" aria-live="polite">
            {fcfa(d.ca_jour)}
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-x-5 gap-y-1 text-sm">
            {variation === null ? (
              <span className="text-encre-pale">Pas de vente hier à cette heure</span>
            ) : (
              <span className={hausse ? "text-valide" : "text-magenta"}>
                {hausse ? "↑" : "↓"} {Math.abs(variation)} % vs hier
              </span>
            )}
            <span className="text-encre-douce">
              {d.nb_prestations_jour} prestation{d.nb_prestations_jour > 1 ? "s" : ""}
            </span>
            <span className="text-encre-douce">
              Marge estimée <span className="tabular text-encre">{fcfa(d.marge_jour)}</span>
            </span>
          </div>
        </section>

        {/* Courbe CA 30 jours */}
        <div className="md:col-span-2">
          <Carte titre="Chiffre d'affaires — 30 derniers jours">
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={d.serie_30j} margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
                <CartesianGrid stroke={PAPIER_CREUX} vertical={false} />
                <XAxis
                  dataKey="date"
                  tickFormatter={jourMois}
                  tick={{ fill: ENCRE_PALE, fontSize: 11 }}
                  interval="preserveStartEnd"
                  minTickGap={24}
                  axisLine={{ stroke: PAPIER_CREUX }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: ENCRE_PALE, fontSize: 11 }}
                  tickFormatter={(v) => (v >= 1000 ? `${v / 1000}k` : `${v}`)}
                  axisLine={false}
                  tickLine={false}
                  width={34}
                />
                <Tooltip
                  content={(p) => <InfoBulle {...p} label={jourMois((p.label as string) ?? "")} />}
                />
                <Line
                  type="monotone"
                  dataKey="ca"
                  stroke={CYAN}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </Carte>
        </div>

        {/* Consommables sous seuil */}
        <Carte titre="Stock sous le seuil">
          {d.consommables_sous_seuil.length === 0 ? (
            <p className="text-encre-pale">Aucun consommable sous le seuil. 👍</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {d.consommables_sous_seuil.map((c) => (
                <li
                  key={c.id}
                  className="flex items-center justify-between gap-2 rounded-lg bg-jaune-clair px-3 py-2 text-sm"
                >
                  <span className="flex items-center gap-2 text-encre">
                    <span aria-hidden>⚠️</span>
                    {c.nom}
                  </span>
                  <span className="tabular text-jaune">
                    {Number(c.qte_stock)} / {Number(c.seuil_alerte)} {c.unite_mesure}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Carte>

        {/* Répartition par service (barres horizontales) */}
        <div className="md:col-span-2">
          <Carte titre="Répartition par service — 30 jours">
            {d.par_service.length === 0 ? (
              <p className="text-encre-pale">Aucune vente sur la période.</p>
            ) : (
              <ResponsiveContainer width="100%" height={Math.max(160, d.par_service.length * 40)}>
                <BarChart
                  data={d.par_service}
                  layout="vertical"
                  margin={{ top: 4, right: 16, bottom: 4, left: 8 }}
                >
                  <CartesianGrid stroke={PAPIER_CREUX} horizontal={false} />
                  <XAxis
                    type="number"
                    tick={{ fill: ENCRE_PALE, fontSize: 11 }}
                    tickFormatter={(v) => (v >= 1000 ? `${v / 1000}k` : `${v}`)}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    type="category"
                    dataKey="nom_service"
                    tick={{ fill: "#4A4F58", fontSize: 12 }}
                    width={110}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip cursor={{ fill: "transparent" }} content={(p) => <InfoBulle {...p} />} />
                  <Bar dataKey="ca" fill={CYAN} radius={[0, 4, 4, 0]} maxBarSize={22} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </Carte>
        </div>

        {/* Top 5 services */}
        <Carte titre="Top 5 des services">
          {d.top_services.length === 0 ? (
            <p className="text-encre-pale">—</p>
          ) : (
            <ol className="flex flex-col gap-2">
              {d.top_services.map((s, i) => (
                <li key={s.nom_service} className="flex items-center justify-between gap-2 text-sm">
                  <span className="flex items-center gap-2 text-encre">
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-cyan-clair text-xs text-cyan">
                      {i + 1}
                    </span>
                    {s.nom_service}
                  </span>
                  <span className="tabular text-encre-douce">{fcfa(s.ca)}</span>
                </li>
              ))}
            </ol>
          )}
        </Carte>

        {/* Performance par employé */}
        <div className="md:col-span-3">
          <Carte titre="Performance par employé — 30 jours">
            {d.par_employe.length === 0 ? (
              <p className="text-encre-pale">Aucune vente sur la période.</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-encre-pale">
                    <th className="py-1 font-normal">Employé</th>
                    <th className="py-1 text-right font-normal">Prestations</th>
                    <th className="py-1 text-right font-normal">CA généré</th>
                  </tr>
                </thead>
                <tbody>
                  {d.par_employe.map((e) => (
                    <tr key={e.employe} className="border-t border-papier-creux">
                      <td className="py-1.5 text-encre">{e.employe}</td>
                      <td className="tabular py-1.5 text-right text-encre-douce">{e.nb}</td>
                      <td className="tabular py-1.5 text-right text-encre">{fcfa(e.ca)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Carte>
        </div>
      </div>
    </div>
  );
}

export default function BilanPage() {
  const role = useAuthStore((s) => s.utilisateur?.role);
  if (role === "employe") return <BilanEmploye />;
  return <BilanProprietaire />;
}
