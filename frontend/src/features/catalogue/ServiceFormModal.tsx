import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal } from "../../components/ui/Modal";
import { Input } from "../../components/ui/Input";
import { Select } from "../../components/ui/Select";
import { Button } from "../../components/ui/Button";
import { api, ApiError, type Service } from "../../lib/api";

const UNITES = [
  { valeur: "page", libelle: "La page" },
  { valeur: "document", libelle: "Le document" },
  { valeur: "piece", libelle: "La pièce" },
  { valeur: "forfait", libelle: "Le forfait" },
];

interface Props {
  service: Service | null; // null = création
  onFermer: () => void;
}

export function ServiceFormModal({ service, onFermer }: Props) {
  const creation = service === null;
  const [nom, setNom] = useState(service?.nom ?? "");
  const [categorie, setCategorie] = useState(service?.categorie ?? "");
  const [prix, setPrix] = useState<number>(service?.prix ?? 0);
  const [unite, setUnite] = useState(service?.unite_facturation ?? "page");
  const [consommeStock, setConsommeStock] = useState(service?.consomme_stock ?? false);
  const [actif, setActif] = useState(service?.actif ?? true);

  const queryClient = useQueryClient();

  const enregistrer = useMutation({
    mutationFn: async () => {
      const donnees = {
        nom,
        categorie,
        prix: Number(prix),
        unite_facturation: unite,
        consomme_stock: consommeStock,
        actif,
      };
      return creation
        ? api.creerService(donnees)
        : api.modifierService(service.id, donnees);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["services"] });
      onFermer();
    },
  });

  const soumettre = (e: FormEvent) => {
    e.preventDefault();
    enregistrer.mutate();
  };

  const erreur =
    enregistrer.error instanceof ApiError
      ? "Vérifiez les champs (prix entier ≥ 0)."
      : enregistrer.error
        ? "Enregistrement impossible."
        : undefined;

  return (
    <Modal ouvert titre={creation ? "Nouveau service" : "Modifier le service"} onFermer={onFermer}>
      <form onSubmit={soumettre} className="flex flex-col gap-4">
        <Input label="Nom" value={nom} onChange={(e) => setNom(e.target.value)} required />
        <div className="grid grid-cols-2 gap-3">
          <Input
            label="Prix (XAF)"
            type="number"
            min={0}
            value={prix}
            onChange={(e) => setPrix(Number(e.target.value))}
            required
          />
          <Select label="Facturation" options={UNITES} value={unite} onChange={(e) => setUnite(e.target.value)} />
        </div>
        <Input label="Catégorie" value={categorie} onChange={(e) => setCategorie(e.target.value)} />
        <label className="flex items-center gap-2 text-encre-douce">
          <input type="checkbox" className="h-5 w-5 accent-cyan" checked={consommeStock} onChange={(e) => setConsommeStock(e.target.checked)} />
          Consomme du stock
        </label>
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
