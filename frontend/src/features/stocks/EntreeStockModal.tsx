import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal } from "../../components/ui/Modal";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { api, ApiError, type Consommable } from "../../lib/api";

export function EntreeStockModal({ consommable, onFermer }: { consommable: Consommable; onFermer: () => void }) {
  const [quantite, setQuantite] = useState<number>(0);
  const [prixTotal, setPrixTotal] = useState<number>(0);
  const [fournisseur, setFournisseur] = useState(consommable.fournisseur ?? "");
  const queryClient = useQueryClient();

  const prixUnitaire = quantite > 0 ? Math.round(prixTotal / quantite) : 0;

  const entree = useMutation({
    mutationFn: () =>
      api.entreeStock(consommable.id, {
        quantite: Number(quantite),
        prix_total_lot: Number(prixTotal),
        fournisseur,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["consommables"] });
      onFermer();
    },
  });

  const soumettre = (e: FormEvent) => {
    e.preventDefault();
    entree.mutate();
  };

  const erreur =
    entree.error instanceof ApiError
      ? "Vérifiez la quantité (> 0) et le prix."
      : entree.error
        ? "Enregistrement impossible."
        : undefined;

  return (
    <Modal ouvert titre={`Entrée de stock — ${consommable.nom}`} onFermer={onFermer}>
      <form onSubmit={soumettre} className="flex flex-col gap-4">
        <p className="text-sm text-encre-douce">
          Stock actuel : <span className="tabular">{Number(consommable.qte_stock)}</span> {consommable.unite_mesure} ·
          prix d'achat moyen : <span className="tabular">{consommable.prix_achat} XAF</span>
        </p>
        <div className="grid grid-cols-2 gap-3">
          <Input label={`Quantité entrante (${consommable.unite_mesure})`} type="number" min={0} step="0.01"
            value={quantite} onChange={(e) => setQuantite(Number(e.target.value))} required />
          <Input label="Prix total du lot (XAF)" type="number" min={0}
            value={prixTotal} onChange={(e) => setPrixTotal(Number(e.target.value))} required />
        </div>
        <Input label="Fournisseur (facultatif)" value={fournisseur} onChange={(e) => setFournisseur(e.target.value)} />

        <div className="rounded-xl bg-cyan-clair p-3 text-sm">
          Prix unitaire de ce lot : <span className="tabular font-medium">{prixUnitaire} XAF</span>
          <span className="text-encre-douce"> — le prix d'achat moyen (CUMP) sera recalculé.</span>
        </div>

        {erreur && <p className="text-sm text-magenta">{erreur}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variante="secondaire" onClick={onFermer}>Annuler</Button>
          <Button type="submit" variante="valide" disabled={entree.isPending}>
            {entree.isPending ? "Enregistrement…" : "Valider l'entrée"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
