import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal } from "../../components/ui/Modal";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { api, ApiError, type ResultatEncaissement } from "../../lib/api";
import { useTicketStore, totalTicket } from "../../stores/ticket";

const MODES = [
  { valeur: "especes", libelle: "Espèces" },
  { valeur: "momo", libelle: "MTN MoMo" },
  { valeur: "orange_money", libelle: "Orange Money" },
  { valeur: "credit", libelle: "Crédit" },
];

export function EncaissementModal({
  onFermer,
  onSucces,
}: {
  onFermer: () => void;
  onSucces: (resultat: ResultatEncaissement) => void;
}) {
  const lignes = useTicketStore((s) => s.lignes);
  const remise = useTicketStore((s) => s.remise);
  const vider = useTicketStore((s) => s.vider);
  const total = totalTicket(lignes, remise);
  const queryClient = useQueryClient();

  const [mode, setMode] = useState("especes");
  const [montantRecu, setMontantRecu] = useState<number>(total);
  const [nomClient, setNomClient] = useState("");

  const monnaie = mode === "especes" ? Math.max(0, montantRecu - total) : 0;
  const insuffisant = mode === "especes" && montantRecu < total;
  const clientManquant = mode === "credit" && nomClient.trim() === "";

  const encaisser = useMutation({
    mutationFn: () =>
      api.enregistrerPrestation({
        lignes: lignes.map((l) => ({
          service: l.serviceId,
          quantite: l.quantite,
          prix_unitaire: l.prix,
          recto_verso: l.rectoVerso,
        })),
        mode_paiement: mode,
        remise,
        montant_recu: mode === "especes" ? Number(montantRecu) : null,
        nom_client: mode === "credit" ? nomClient.trim() : "",
      }),
    onSuccess: async (resultat) => {
      vider();
      await queryClient.invalidateQueries({ queryKey: ["consommables"] });
      onSucces(resultat);
      onFermer();
    },
  });

  const erreur =
    encaisser.error instanceof ApiError
      ? (encaisser.error.corps as { detail?: string })?.detail ?? "Encaissement refusé."
      : encaisser.error
        ? "Encaissement impossible."
        : undefined;

  return (
    <Modal ouvert titre="Encaissement" onFermer={onFermer}>
      <div className="mb-4 flex items-end justify-between">
        <span className="text-encre-douce">Total à payer</span>
        <span className="tabular text-3xl">{total.toLocaleString("fr-FR")} F</span>
      </div>

      <div className="mb-4">
        <p className="mb-2 text-sm text-encre-douce">Mode de paiement</p>
        <div className="grid grid-cols-2 gap-2">
          {MODES.map((m) => (
            <button
              key={m.valeur}
              onClick={() => setMode(m.valeur)}
              className={[
                "h-11 rounded-xl border text-sm font-medium",
                mode === m.valeur
                  ? "border-cyan bg-cyan-clair text-cyan"
                  : "border-papier-creux text-encre-douce",
              ].join(" ")}
            >
              {m.libelle}
            </button>
          ))}
        </div>
      </div>

      {mode === "especes" && (
        <div className="mb-4">
          <Input
            label="Montant reçu (XAF)"
            type="number"
            min={0}
            value={montantRecu}
            onChange={(e) => setMontantRecu(Number(e.target.value))}
          />
          <div className="mt-2 flex items-center justify-between rounded-xl bg-valide-clair p-3">
            <span className="text-encre-douce">Monnaie à rendre</span>
            <span className="tabular text-xl text-valide">{monnaie.toLocaleString("fr-FR")} F</span>
          </div>
        </div>
      )}

      {mode === "credit" && (
        <div className="mb-4">
          <Input
            label="Nom du client (à crédit)"
            value={nomClient}
            onChange={(e) => setNomClient(e.target.value)}
            placeholder="ex. Awa Ngono"
            erreur={clientManquant ? "Le nom du client est requis pour un crédit." : undefined}
          />
        </div>
      )}

      {erreur && <p className="mb-3 text-sm text-magenta">{erreur}</p>}

      <div className="flex justify-end gap-2">
        <Button variante="secondaire" onClick={onFermer}>Annuler</Button>
        <Button
          variante="valide"
          taille="grand"
          onClick={() => encaisser.mutate()}
          disabled={encaisser.isPending || insuffisant || clientManquant || lignes.length === 0}
        >
          {encaisser.isPending ? "Encaissement…" : `Encaisser ${total.toLocaleString("fr-FR")} F`}
        </Button>
      </div>
    </Modal>
  );
}
