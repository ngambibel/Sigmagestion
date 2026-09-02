import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal } from "../../components/ui/Modal";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { api, ApiError, type Consommable } from "../../lib/api";

export function AjustementModal({ consommable, onFermer }: { consommable: Consommable; onFermer: () => void }) {
  const [delta, setDelta] = useState<number>(0);
  const [motif, setMotif] = useState("");
  const queryClient = useQueryClient();

  const stockApres = Number(consommable.qte_stock) + delta;

  const ajuster = useMutation({
    mutationFn: () => api.ajustementStock(consommable.id, { quantite_delta: Number(delta), motif }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["consommables"] });
      await queryClient.invalidateQueries({ queryKey: ["mouvements"] });
      onFermer();
    },
  });

  const soumettre = (e: FormEvent) => {
    e.preventDefault();
    ajuster.mutate();
  };

  const erreurServeur =
    ajuster.error instanceof ApiError
      ? (ajuster.error.corps as { detail?: string })?.detail ?? "Ajustement refusé."
      : ajuster.error
        ? "Enregistrement impossible."
        : undefined;

  return (
    <Modal ouvert titre={`Ajuster le stock — ${consommable.nom}`} onFermer={onFermer}>
      <form onSubmit={soumettre} className="flex flex-col gap-4">
        <p className="text-sm text-encre-douce">
          Stock actuel : <span className="tabular">{Number(consommable.qte_stock)}</span> {consommable.unite_mesure}.
          Utilisez un nombre négatif pour une perte (casse, vol).
        </p>
        <Input
          label={`Variation (${consommable.unite_mesure})`}
          type="number"
          value={delta}
          onChange={(e) => setDelta(Number(e.target.value))}
          placeholder="ex. -10"
          required
        />
        <Input label="Motif (obligatoire)" value={motif} onChange={(e) => setMotif(e.target.value)} placeholder="ex. 10 feuilles abîmées" required />

        <div className="rounded-xl bg-papier-creux p-3 text-sm">
          Nouveau stock : <span className="tabular font-medium">{stockApres}</span> {consommable.unite_mesure}
          {stockApres < 0 && <span className="text-magenta"> — impossible (négatif)</span>}
        </div>

        {erreurServeur && <p className="text-sm text-magenta">{erreurServeur}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variante="secondaire" onClick={onFermer}>Annuler</Button>
          <Button type="submit" variante="danger" disabled={ajuster.isPending || delta === 0 || stockApres < 0}>
            {ajuster.isPending ? "Enregistrement…" : "Enregistrer l'ajustement"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
