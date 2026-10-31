import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type ResultatEncaissement } from "../../lib/api";
import { chargerAvecCache } from "../../lib/offline";
import { EnTetePage } from "../../components/layout/EnTetePage";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { TuilesServices } from "../../features/caisse/TuilesServices";
import { TicketEnCours } from "../../features/caisse/TicketEnCours";
import { DepenseModal } from "../../features/caisse/DepenseModal";
import { ClotureModal } from "../../features/caisse/ClotureModal";
import { RecuModal } from "../../features/ventes/RecuModal";
import { useSecretariats } from "../../features/secretariats/useSecretariats";
import { useAuthStore } from "../../stores/auth";
import type { Prestation, SessionCaisse } from "../../lib/api";

function OuvertureSession() {
  const [fond, setFond] = useState<number>(0);
  const queryClient = useQueryClient();

  const ouvrir = useMutation({
    mutationFn: () => api.ouvrirSession(Number(fond)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["session-active"] }),
  });

  return (
    <div className="mx-auto max-w-sm rounded-2xl bg-papier-surface p-6 shadow-sm">
      <h2 className="text-xl">Ouvrir la caisse</h2>
      <p className="mb-5 text-encre-douce">
        Déclarez le fond de caisse avec lequel vous démarrez.
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          ouvrir.mutate();
        }}
        className="flex flex-col gap-4"
      >
        <Input
          label="Fond de caisse (XAF)"
          type="number"
          min={0}
          value={fond}
          onChange={(e) => setFond(Number(e.target.value))}
          required
        />
        <Button type="submit" taille="grand" variante="valide" disabled={ouvrir.isPending}>
          {ouvrir.isPending ? "Ouverture…" : "Ouvrir la session"}
        </Button>
      </form>
    </div>
  );
}

function RecuToast({
  recu,
  onFermer,
  onVoirRecu,
}: {
  recu: ResultatEncaissement;
  onFermer: () => void;
  onVoirRecu: () => void;
}) {
  const p = recu.prestation;
  const couleur = recu.hors_ligne ? "bg-jaune" : "bg-valide";
  return (
    <div className="fixed inset-x-0 top-16 z-40 mx-auto max-w-md px-4">
      <div className={`rounded-2xl ${couleur} p-4 text-white shadow-lg`}>
        <div className="flex items-start justify-between">
          <div>
            {recu.hors_ligne ? (
              <>
                <p className="font-medium">Vente enregistrée hors ligne</p>
                <p className="tabular text-sm">
                  {p.montant_total.toLocaleString("fr-FR")} F · en attente de synchronisation
                </p>
              </>
            ) : (
              <>
                <p className="font-medium">Encaissé — ticket {p.numero}</p>
                {p.monnaie_rendue != null && (
                  <p className="tabular text-sm">Rendre {p.monnaie_rendue.toLocaleString("fr-FR")} F</p>
                )}
                {p.mode_paiement === "credit" && p.nom_client && (
                  <p className="text-sm">Crédit — {p.nom_client}</p>
                )}
              </>
            )}
          </div>
          <button onClick={onFermer} className="text-white/80" aria-label="Fermer">✕</button>
        </div>
        {recu.alertes_stock.length > 0 && (
          <div className="mt-2 rounded-lg bg-white/15 p-2 text-sm">
            Stock bas : {recu.alertes_stock.map((a) => a.nom).join(", ")}
          </div>
        )}
        {!recu.hors_ligne && (
          <button onClick={onVoirRecu} className="mt-2 text-sm font-medium text-white underline">
            Voir le reçu
          </button>
        )}
      </div>
    </div>
  );
}

function TuileChiffre({
  libelle,
  valeur,
  couleur,
}: {
  libelle: string;
  valeur: number;
  couleur?: "magenta" | "valide";
}) {
  const teinte =
    couleur === "magenta" ? "text-magenta" : couleur === "valide" ? "text-valide" : "text-encre";
  return (
    <div className="rounded-2xl bg-papier-surface p-3 shadow-sm">
      <p className="text-xs text-encre-pale">{libelle}</p>
      <p className={`tabular text-lg font-semibold ${teinte}`}>
        {valeur.toLocaleString("fr-FR")} <span className="text-sm font-normal text-encre-pale">XAF</span>
      </p>
    </div>
  );
}

function SessionEnCours({ session }: { session: SessionCaisse }) {
  const [recu, setRecu] = useState<ResultatEncaissement | null>(null);
  const [recuAffiche, setRecuAffiche] = useState<Prestation | null>(null);
  const [depenseOuverte, setDepenseOuverte] = useState(false);
  const [clotureOuverte, setClotureOuverte] = useState(false);
  const { secretariat } = useSecretariats();
  const role = useAuthStore((s) => s.utilisateur?.role);
  const peutVoirVentes = role === "proprietaire" || role === "gerant" || role === "super_admin";
  const peutDepenser = role === "proprietaire" || role === "gerant" || role === "super_admin";

  const surSucces = (resultat: ResultatEncaissement) => {
    if ("vibrate" in navigator) navigator.vibrate?.(60);
    setRecu(resultat);
    window.setTimeout(() => setRecu(null), 6000);
  };

  return (
    <div className="flex flex-col lg:min-h-0 lg:flex-1 lg:overflow-hidden">
      {recu && (
        <RecuToast
          recu={recu}
          onFermer={() => setRecu(null)}
          onVoirRecu={() => {
            setRecuAffiche(recu.prestation);
            setRecu(null);
          }}
        />
      )}

      <div className="mb-4 flex shrink-0 flex-wrap items-center gap-3 rounded-2xl bg-valide-clair p-3">
        <span className="rounded-lg bg-valide px-2 py-1 text-sm text-white">Caisse ouverte</span>
        <span className="flex items-baseline gap-1.5">
          <span className="text-encre-douce">En caisse (espèces) :</span>
          <span className="tabular text-xl font-semibold text-valide">
            {(session.montant_theorique_estime ?? session.fond_initial).toLocaleString("fr-FR")} XAF
          </span>
        </span>
        <span className="text-encre-pale">
          fond {session.fond_initial.toLocaleString("fr-FR")} · depuis{" "}
          {new Date(session.ouverte_le).toLocaleString("fr-FR", { timeStyle: "short", dateStyle: "short" })}
        </span>
        <div className="ml-auto flex items-center gap-3">
          {peutVoirVentes && (
            <Link to="/ventes" className="text-sm font-medium text-cyan underline">Ventes</Link>
          )}
          {peutDepenser && (
            <button onClick={() => setDepenseOuverte(true)} className="text-sm font-medium text-magenta underline">
              Dépense
            </button>
          )}
          <button onClick={() => setClotureOuverte(true)} className="text-sm font-medium text-encre underline">
            Clôturer
          </button>
        </div>
      </div>

      {peutVoirVentes && (
        <div className="mb-4 grid shrink-0 grid-cols-3 gap-3">
          <TuileChiffre libelle="Chiffre d'affaires" valeur={session.chiffre_affaires_estime ?? 0} />
          <TuileChiffre libelle="Coût consommables" valeur={session.cout_consommables_estime ?? 0} couleur="magenta" />
          <TuileChiffre
            libelle="Marge"
            valeur={(session.chiffre_affaires_estime ?? 0) - (session.cout_consommables_estime ?? 0)}
            couleur="valide"
          />
        </div>
      )}

      <div className="grid gap-4 lg:min-h-0 lg:flex-1 lg:grid-cols-[1fr_360px]">
        <div className="lg:min-h-0">
          <TuilesServices />
        </div>
        <div className="lg:min-h-0 lg:overflow-y-auto">
          <TicketEnCours onSucces={surSucces} />
        </div>
      </div>

      {depenseOuverte && <DepenseModal onFermer={() => setDepenseOuverte(false)} />}
      {clotureOuverte && <ClotureModal session={session} onFermer={() => setClotureOuverte(false)} />}
      {recuAffiche && (
        <RecuModal prestation={recuAffiche} secretariat={secretariat} onFermer={() => setRecuAffiche(null)} />
      )}
    </div>
  );
}

export default function CaissePage() {
  const session = useQuery({
    queryKey: ["session-active"],
    queryFn: () => chargerAvecCache("session-active", api.sessionActive),
  });

  return (
    <div className="flex h-full flex-col">
      <div className="shrink-0">
        <EnTetePage titre="Caisse" sousTitre="Enregistrez vos prestations et encaissez." />
      </div>
      {session.isLoading ? (
        <p className="text-encre-pale">Chargement…</p>
      ) : session.data ? (
        <SessionEnCours session={session.data} />
      ) : (
        <OuvertureSession />
      )}
    </div>
  );
}
