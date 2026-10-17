import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "../../components/ui/Button";
import { Select } from "../../components/ui/Select";
import { api, type ParametreNotification, type PlageHoraire } from "../../lib/api";
import { useSecretariats } from "../secretariats/useSecretariats";

const INTERVALLES = [
  { valeur: "60", libelle: "Toutes les heures" },
  { valeur: "120", libelle: "Toutes les 2 heures" },
  { valeur: "180", libelle: "Toutes les 3 heures" },
  { valeur: "240", libelle: "Toutes les 4 heures" },
];

/** "HH:MM:SS" ou "HH:MM" → "HH:MM" (valeur attendue par <input type="time">). */
function versHHMM(valeur: string): string {
  return valeur.slice(0, 5);
}

function Bascule({
  actif,
  onChange,
  children,
}: {
  actif: boolean;
  onChange: (v: boolean) => void;
  children: ReactNode;
}) {
  return (
    <label className="flex cursor-pointer items-center justify-between gap-3 py-2">
      <span className="text-encre-douce">{children}</span>
      <button
        type="button"
        role="switch"
        aria-checked={actif}
        onClick={() => onChange(!actif)}
        className={[
          "relative h-6 w-11 shrink-0 rounded-full transition-colors",
          actif ? "bg-cyan" : "bg-papier-creux",
        ].join(" ")}
      >
        <span
          className={[
            "absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform",
            actif ? "translate-x-5" : "translate-x-0.5",
          ].join(" ")}
        />
      </button>
    </label>
  );
}

export function SectionHoraires() {
  const { secretariat } = useSecretariats();
  const secretariatId = secretariat?.id;
  const queryClient = useQueryClient();

  const plagesQuery = useQuery({
    queryKey: ["plages-horaires", secretariatId],
    queryFn: () => api.getPlagesHoraires(secretariatId!),
    enabled: !!secretariatId,
  });
  const parametresQuery = useQuery({
    queryKey: ["parametres-notification", secretariatId],
    queryFn: () => api.getParametresNotification(secretariatId!),
    enabled: !!secretariatId,
  });

  const [plages, setPlages] = useState<PlageHoraire[]>([]);
  const [parametres, setParametres] = useState<ParametreNotification | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (plagesQuery.data) setPlages(plagesQuery.data);
  }, [plagesQuery.data]);
  useEffect(() => {
    if (parametresQuery.data) setParametres(parametresQuery.data);
  }, [parametresQuery.data]);

  const enregistrer = useMutation({
    mutationFn: async () => {
      if (!secretariatId || !parametres) return;
      await api.putPlagesHoraires(
        secretariatId,
        plages.map((p) => ({
          jour: p.jour,
          ouvert: p.ouvert,
          heure_debut: versHHMM(p.heure_debut),
          heure_fin: versHHMM(p.heure_fin),
        })),
      );
      await api.patchParametresNotification(secretariatId, {
        intervalle_ca_min: parametres.intervalle_ca_min,
        alerte_ca_on: parametres.alerte_ca_on,
        alerte_stock_on: parametres.alerte_stock_on,
        bilan_jour_on: parametres.bilan_jour_on,
        alerte_ecart_caisse_on: parametres.alerte_ecart_caisse_on,
        alerte_annulation_on: parametres.alerte_annulation_on,
        alerte_session_on: parametres.alerte_session_on,
        ne_pas_deranger: parametres.ne_pas_deranger,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plages-horaires", secretariatId] });
      queryClient.invalidateQueries({ queryKey: ["parametres-notification", secretariatId] });
      setMessage("Horaires et notifications enregistrés.");
    },
    onError: () => setMessage("Échec de l'enregistrement. Réessayez."),
  });

  if (!secretariatId) return null;
  if (plagesQuery.isLoading || parametresQuery.isLoading || !parametres) {
    return (
      <section className="mb-6 rounded-2xl bg-papier-surface p-5 shadow-sm">
        <h2 className="mb-2 text-lg">Horaires et bilan de CA</h2>
        <p className="text-encre-douce">Chargement…</p>
      </section>
    );
  }

  function majPlage(jour: number, champ: keyof PlageHoraire, valeur: string | boolean) {
    setPlages((liste) =>
      liste.map((p) => (p.jour === jour ? { ...p, [champ]: valeur } : p)),
    );
  }

  return (
    <section className="mb-6 rounded-2xl bg-papier-surface p-5 shadow-sm">
      <h2 className="mb-1 text-lg">Horaires et bilan de CA</h2>
      <p className="mb-4 text-sm text-encre-douce">
        Vous recevez votre chiffre d'affaires par notification uniquement pendant vos horaires
        d'ouverture, à l'intervalle choisi.
      </p>

      <Select
        label="Fréquence du bilan de CA"
        options={INTERVALLES}
        value={String(parametres.intervalle_ca_min)}
        onChange={(e) =>
          setParametres({ ...parametres, intervalle_ca_min: Number(e.target.value) })
        }
        className="mb-4 w-full"
      />

      <div className="mb-4 border-t border-papier-creux pt-2">
        <Bascule
          actif={parametres.ne_pas_deranger}
          onChange={(v) => setParametres({ ...parametres, ne_pas_deranger: v })}
        >
          Ne pas déranger (les notifications restent dans l'app, sans push)
        </Bascule>
      </div>

      <div className="mb-4 border-t border-papier-creux pt-2">
        <h3 className="mb-1 text-sm font-medium text-encre">Types de notification</h3>
        <Bascule
          actif={parametres.alerte_ca_on}
          onChange={(v) => setParametres({ ...parametres, alerte_ca_on: v })}
        >
          Bilan de CA pendant les horaires
        </Bascule>
        <Bascule
          actif={parametres.bilan_jour_on}
          onChange={(v) => setParametres({ ...parametres, bilan_jour_on: v })}
        >
          Récapitulatif de fin de journée
        </Bascule>
        <Bascule
          actif={parametres.alerte_stock_on}
          onChange={(v) => setParametres({ ...parametres, alerte_stock_on: v })}
        >
          Alerte de stock faible
        </Bascule>
        <Bascule
          actif={parametres.alerte_ecart_caisse_on}
          onChange={(v) => setParametres({ ...parametres, alerte_ecart_caisse_on: v })}
        >
          Écart de caisse à la clôture
        </Bascule>
        <Bascule
          actif={parametres.alerte_annulation_on}
          onChange={(v) => setParametres({ ...parametres, alerte_annulation_on: v })}
        >
          Annulation d'une prestation
        </Bascule>
        <Bascule
          actif={parametres.alerte_session_on}
          onChange={(v) => setParametres({ ...parametres, alerte_session_on: v })}
        >
          Ouverture / clôture de session
        </Bascule>
      </div>

      <div className="mb-4 border-t border-papier-creux pt-3">
        <h3 className="mb-2 text-sm font-medium text-encre">Horaires d'ouverture</h3>
        <div className="flex flex-col gap-2">
          {plages.map((p) => (
            <div key={p.jour} className="flex items-center gap-2">
              <label className="flex w-28 items-center gap-2">
                <input
                  type="checkbox"
                  checked={p.ouvert}
                  onChange={(e) => majPlage(p.jour, "ouvert", e.target.checked)}
                  className="h-4 w-4 accent-cyan"
                />
                <span className="text-sm text-encre">{p.jour_libelle}</span>
              </label>
              {p.ouvert ? (
                <div className="flex items-center gap-1.5">
                  <input
                    type="time"
                    value={versHHMM(p.heure_debut)}
                    onChange={(e) => majPlage(p.jour, "heure_debut", e.target.value)}
                    className="h-10 rounded-lg border border-papier-creux bg-papier-surface px-2 text-sm tabular"
                  />
                  <span className="text-encre-pale">→</span>
                  <input
                    type="time"
                    value={versHHMM(p.heure_fin)}
                    onChange={(e) => majPlage(p.jour, "heure_fin", e.target.value)}
                    className="h-10 rounded-lg border border-papier-creux bg-papier-surface px-2 text-sm tabular"
                  />
                </div>
              ) : (
                <span className="text-sm text-encre-pale">Fermé</span>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Button onClick={() => enregistrer.mutate()} disabled={enregistrer.isPending}>
          {enregistrer.isPending ? "Enregistrement…" : "Enregistrer"}
        </Button>
        {message && <span className="text-sm text-encre-douce">{message}</span>}
      </div>
    </section>
  );
}
