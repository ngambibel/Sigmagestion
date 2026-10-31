import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal } from "../../components/ui/Modal";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { api, ApiError, type Consommable } from "../../lib/api";

type Sens = "retirer" | "ajouter";

export function AjustementModal({ consommable, onFermer }: { consommable: Consommable; onFermer: () => void }) {
  const [sens, setSens] = useState<Sens>("retirer");
  const [quantite, setQuantite] = useState<number>(0);
  const [motif, setMotif] = useState("");
  const queryClient = useQueryClient();

  const stockActuel = Number(consommable.qte_stock);
  const delta = sens === "retirer" ? -Math.abs(quantite) : Math.abs(quantite);
  const stockApres = stockActuel + delta;

  const ajuster = useMutation({
    mutationFn: () => api.ajustementStock(consommable.id, { quantite_delta: delta, motif }),
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

  const boutonSens = (valeur: Sens, libelle: string) => (
    <button
      type="button"
      onClick={() => setSens(valeur)}
      className={[
        "h-12 flex-1 rounded-xl border text-sm font-medium",
        sens === valeur
          ? valeur === "retirer"
            ? "border-magenta bg-magenta-clair text-magenta"
            : "border-valide bg-valide-clair text-valide"
          : "border-papier-creux text-encre-douce",
      ].join(" ")}
    >
      {libelle}
    </button>
  );

  return (
    <Modal ouvert titre={`Ajuster le stock — ${consommable.nom}`} onFermer={onFermer}>
      <form onSubmit={soumettre} className="flex flex-col gap-4">
        <p className="text-sm text-encre-douce">
          Stock actuel : <span className="tabular font-medium">{stockActuel.toLocaleString("fr-FR")}</span> {consommable.unite_mesure}.
        </p>

        <div className="flex gap-2">
          {boutonSens("retirer", "➖ Retirer")}
          {boutonSens("ajouter", "➕ Ajouter")}
        </div>

        <Input
          label={`Quantité à ${sens} (${consommable.unite_mesure})`}
          type="number"
          min={0}
          value={quantite}
          onChange={(e) => setQuantite(Math.abs(Number(e.target.value)))}
          placeholder="ex. 10"
          required
        />
        <Input
          label="Motif (obligatoire)"
          value={motif}
          onChange={(e) => setMotif(e.target.value)}
          placeholder={sens === "retirer" ? "ex. feuilles abîmées, perte" : "ex. retour fournisseur"}
          required
        />

        <div className="rounded-xl bg-papier-creux p-3 text-sm">
          Nouveau stock : <span className="tabular font-medium">{stockApres.toLocaleString("fr-FR")}</span> {consommable.unite_mesure}
          {stockApres < 0 && <span className="text-magenta"> — impossible (négatif)</span>}
        </div>

        {erreurServeur && <p className="text-sm text-magenta">{erreurServeur}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variante="secondaire" onClick={onFermer}>Annuler</Button>
          <Button
            type="submit"
            variante={sens === "retirer" ? "danger" : "valide"}
            disabled={ajuster.isPending || quantite <= 0 || motif.trim() === "" || stockApres < 0}
          >
            {ajuster.isPending ? "Enregistrement…" : "Enregistrer l'ajustement"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
