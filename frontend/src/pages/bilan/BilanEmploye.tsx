import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { EnTetePage } from "../../components/layout/EnTetePage";
import { api } from "../../lib/api";

const fcfa = (n: number) => `${n.toLocaleString("fr-FR")} F`;
const MODE_LIBELLE: Record<string, string> = {
  especes: "Espèces",
  momo: "MTN MoMo",
  orange_money: "Orange Money",
  credit: "Crédit",
};

function Carte({ titre, children }: { titre: string; children: ReactNode }) {
  return (
    <section className="rounded-2xl bg-papier-surface p-5 shadow-sm">
      <h2 className="mb-3 text-base text-encre-douce">{titre}</h2>
      {children}
    </section>
  );
}

export default function BilanEmploye() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["tableau-de-bord-employe"],
    queryFn: api.tableauDeBordEmploye,
    refetchInterval: 60_000,
  });

  if (isLoading) {
    return (
      <div>
        <EnTetePage titre="Ma journée" sousTitre="Votre session et vos ventes." />
        <p className="text-encre-pale">Chargement…</p>
      </div>
    );
  }
  if (isError || !data) {
    return (
      <div>
        <EnTetePage titre="Ma journée" sousTitre="Votre session et vos ventes." />
        <p className="text-magenta">Impossible de charger votre bilan.</p>
      </div>
    );
  }

  const s = data.session;

  return (
    <div>
      <EnTetePage titre="Ma journée" sousTitre="Votre session et vos ventes." />

      <div className="grid gap-4 md:grid-cols-3">
        {/* Hero : total encaissé de la session */}
        <section className="rounded-2xl bg-papier-surface p-5 shadow-sm md:col-span-3">
          {s ? (
            <>
              <p className="text-encre-douce">Encaissé dans ma session</p>
              <p className="tabular font-display text-5xl text-encre">{fcfa(s.total_encaisse)}</p>
              <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-sm text-encre-douce">
                <span>
                  {s.nb_prestations} prestation{s.nb_prestations > 1 ? "s" : ""}
                </span>
                <span>Fond de caisse <span className="tabular text-encre">{fcfa(s.fond_initial)}</span></span>
                <span>
                  Attendu en espèces{" "}
                  <span className="tabular text-encre">{fcfa(s.montant_theorique_estime)}</span>
                </span>
              </div>
            </>
          ) : (
            <p className="text-encre-pale">
              Aucune session ouverte. Ouvrez une session depuis la Caisse pour commencer.
            </p>
          )}
        </section>

        {/* Détail par mode de règlement */}
        {s && (
          <Carte titre="Par mode de règlement">
            <dl className="flex flex-col gap-1.5 text-sm">
              {[
                ["Espèces", s.especes],
                ["MTN MoMo", s.momo],
                ["Orange Money", s.orange],
                ["Crédit", s.credit],
              ].map(([libelle, montant]) => (
                <div key={libelle as string} className="flex justify-between">
                  <dt className="text-encre-douce">{libelle}</dt>
                  <dd className="tabular text-encre">{fcfa(montant as number)}</dd>
                </div>
              ))}
            </dl>
          </Carte>
        )}

        {/* Dernières prestations */}
        <div className={s ? "md:col-span-2" : "md:col-span-3"}>
          <Carte titre="Mes dernières prestations">
            {data.mes_prestations.length === 0 ? (
              <p className="text-encre-pale">Aucune prestation pour le moment.</p>
            ) : (
              <ul className="divide-y divide-papier-creux">
                {data.mes_prestations.map((p) => (
                  <li key={p.id} className="flex items-center justify-between gap-2 py-2 text-sm">
                    <div className="min-w-0">
                      <p className="truncate text-encre">{p.numero}</p>
                      <p className="text-encre-pale">
                        {MODE_LIBELLE[p.mode_paiement] ?? p.mode_paiement}
                        {p.statut === "annulee" && " · annulée"}
                      </p>
                    </div>
                    <span
                      className={[
                        "tabular font-medium",
                        p.statut === "annulee" ? "text-encre-pale line-through" : "text-encre",
                      ].join(" ")}
                    >
                      {fcfa(p.montant_total)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </Carte>
        </div>

        {/* État du stock (sans prix d'achat) */}
        <Carte titre="Stock sous le seuil">
          {data.consommables_sous_seuil.length === 0 ? (
            <p className="text-encre-pale">Aucun consommable sous le seuil. 👍</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {data.consommables_sous_seuil.map((c) => (
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
      </div>
    </div>
  );
}
