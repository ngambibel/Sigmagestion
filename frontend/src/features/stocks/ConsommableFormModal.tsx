import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal } from "../../components/ui/Modal";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { api, ApiError, type Consommable } from "../../lib/api";

interface Props {
  consommable: Consommable | null; // null = création
  onFermer: () => void;
}

export function ConsommableFormModal({ consommable, onFermer }: Props) {
  const creation = consommable === null;
  const [nom, setNom] = useState(consommable?.nom ?? "");
  const [unite, setUnite] = useState(consommable?.unite_mesure ?? "");
  const [prixAchat, setPrixAchat] = useState<number>(consommable?.prix_achat ?? 0);
  const [qteStock, setQteStock] = useState<number>(Number(consommable?.qte_stock ?? 0));
  const [seuilAlerte, setSeuilAlerte] = useState<number>(Number(consommable?.seuil_alerte ?? 0));
  const [seuilCritique, setSeuilCritique] = useState<string>(
    consommable?.seuil_critique ?? "",
  );
  const [fournisseur, setFournisseur] = useState(consommable?.fournisseur ?? "");
  const [actif, setActif] = useState(consommable?.actif ?? true);

  const queryClient = useQueryClient();

  const enregistrer = useMutation({
    mutationFn: async () => {
      const donnees: Record<string, unknown> = {
        nom,
        unite_mesure: unite,
        prix_achat: Number(prixAchat),
        qte_stock: Number(qteStock),
        seuil_alerte: Number(seuilAlerte),
        seuil_critique: seuilCritique === "" ? null : Number(seuilCritique),
        fournisseur,
        actif,
      };
      return creation
        ? api.creerConsommable(donnees)
        : api.modifierConsommable(consommable.id, donnees);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["consommables"] });
      onFermer();
    },
  });

  const soumettre = (e: FormEvent) => {
    e.preventDefault();
    enregistrer.mutate();
  };

  const erreur =
    enregistrer.error instanceof ApiError
      ? "Vérifiez les champs."
      : enregistrer.error
        ? "Enregistrement impossible."
        : undefined;

  return (
    <Modal ouvert titre={creation ? "Nouveau consommable" : "Modifier le consommable"} onFermer={onFermer}>
      <form onSubmit={soumettre} className="flex flex-col gap-4">
        <Input label="Nom" value={nom} onChange={(e) => setNom(e.target.value)} required />
        <div className="grid grid-cols-2 gap-3">
          <Input label="Unité de mesure" placeholder="feuille, cartouche…" value={unite} onChange={(e) => setUnite(e.target.value)} required />
          <Input label="Prix d'achat (XAF)" type="number" min={0} value={prixAchat} onChange={(e) => setPrixAchat(Number(e.target.value))} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Input label="Quantité en stock" type="number" min={0} value={qteStock} onChange={(e) => setQteStock(Number(e.target.value))} />
          <Input label="Seuil d'alerte" type="number" min={0} value={seuilAlerte} onChange={(e) => setSeuilAlerte(Number(e.target.value))} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Input label="Seuil critique (facultatif)" type="number" min={0} value={seuilCritique} onChange={(e) => setSeuilCritique(e.target.value)} />
          <Input label="Fournisseur (facultatif)" value={fournisseur} onChange={(e) => setFournisseur(e.target.value)} />
        </div>
        <label className="flex items-center gap-2 text-encre-douce">
          <input type="checkbox" className="h-5 w-5 accent-cyan" checked={actif} onChange={(e) => setActif(e.target.checked)} />
          Actif
        </label>
        {erreur && <p className="text-sm text-magenta">{erreur}</p>}
        <div className="mt-2 flex justify-end gap-2">
          <Button type="button" variante="secondaire" onClick={onFermer}>Annuler</Button>
          <Button type="submit" disabled={enregistrer.isPending}>
            {enregistrer.isPending ? "Enregistrement…" : "Enregistrer"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
