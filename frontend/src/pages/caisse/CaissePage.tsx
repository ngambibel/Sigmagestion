import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type ResultatEncaissement } from "../../lib/api";
import { EnTetePage } from "../../components/layout/EnTetePage";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { TuilesServices } from "../../features/caisse/TuilesServices";
import { TicketEnCours } from "../../features/caisse/TicketEnCours";

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

function RecuToast({ recu, onFermer }: { recu: ResultatEncaissement; onFermer: () => void }) {
  const p = recu.prestation;
  return (
    <div className="fixed inset-x-0 top-16 z-40 mx-auto max-w-md px-4">
      <div className="rounded-2xl bg-valide p-4 text-white shadow-lg">
        <div className="flex items-start justify-between">
          <div>
            <p className="font-medium">Encaissé — ticket {p.numero}</p>
            {p.monnaie_rendue != null && (
              <p className="tabular text-sm">Rendre {p.monnaie_rendue.toLocaleString("fr-FR")} F</p>
            )}
          </div>
          <button onClick={onFermer} className="text-white/80" aria-label="Fermer">✕</button>
        </div>
        {recu.alertes_stock.length > 0 && (
          <div className="mt-2 rounded-lg bg-white/15 p-2 text-sm">
            Stock bas : {recu.alertes_stock.map((a) => a.nom).join(", ")}
          </div>
        )}
      </div>
    </div>
  );
}

function SessionEnCours({ ouverteLe, fondInitial }: { ouverteLe: string; fondInitial: number }) {
  const [recu, setRecu] = useState<ResultatEncaissement | null>(null);

  const surSucces = (resultat: ResultatEncaissement) => {
    if ("vibrate" in navigator) navigator.vibrate?.(60);
    setRecu(resultat);
    window.setTimeout(() => setRecu(null), 6000);
  };

  return (
    <div>
      {recu && <RecuToast recu={recu} onFermer={() => setRecu(null)} />}

      <div className="mb-4 flex flex-wrap items-center gap-3 rounded-2xl bg-valide-clair p-3">
        <span className="rounded-lg bg-valide px-2 py-1 text-sm text-white">Caisse ouverte</span>
        <span className="text-encre-douce">
          Fond : <span className="tabular font-medium">{fondInitial.toLocaleString("fr-FR")} XAF</span>
        </span>
        <span className="text-encre-pale">
          depuis {new Date(ouverteLe).toLocaleString("fr-FR", { timeStyle: "short", dateStyle: "short" })}
        </span>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
        <TuilesServices />
        <div className="lg:sticky lg:top-16 lg:h-[calc(100vh-6rem)]">
          <TicketEnCours onSucces={surSucces} />
        </div>
      </div>
    </div>
  );
}

export default function CaissePage() {
  const session = useQuery({ queryKey: ["session-active"], queryFn: api.sessionActive });

  return (
    <div>
      <EnTetePage titre="Caisse" sousTitre="Enregistrez vos prestations et encaissez." />
      {session.isLoading ? (
        <p className="text-encre-pale">Chargement…</p>
      ) : session.data ? (
        <SessionEnCours ouverteLe={session.data.ouverte_le} fondInitial={session.data.fond_initial} />
      ) : (
        <OuvertureSession />
      )}
    </div>
  );
}
