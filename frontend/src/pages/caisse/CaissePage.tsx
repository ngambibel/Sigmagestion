import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../lib/api";
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

function SessionEnCours({ ouverteLe, fondInitial }: { ouverteLe: string; fondInitial: number }) {
  return (
    <div>
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
          <TicketEnCours />
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
