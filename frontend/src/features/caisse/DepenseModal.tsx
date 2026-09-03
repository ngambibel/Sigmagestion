import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal } from "../../components/ui/Modal";
import { Input } from "../../components/ui/Input";
import { Select } from "../../components/ui/Select";
import { Button } from "../../components/ui/Button";
import { api, ApiError } from "../../lib/api";

const CATEGORIES = [
  { valeur: "fourniture", libelle: "Fourniture" },
  { valeur: "transport", libelle: "Transport" },
  { valeur: "electricite", libelle: "Électricité / eau" },
  { valeur: "maintenance", libelle: "Maintenance" },
  { valeur: "salaire", libelle: "Salaire / avance" },
  { valeur: "autre", libelle: "Autre" },
];

export function DepenseModal({ onFermer }: { onFermer: () => void }) {
  const [categorie, setCategorie] = useState("fourniture");
  const [montant, setMontant] = useState<number>(0);
  const [description, setDescription] = useState("");
  const [justificatif, setJustificatif] = useState<File | null>(null);
  const queryClient = useQueryClient();

  const enregistrer = useMutation({
    mutationFn: () => {
      const fd = new FormData();
      fd.append("categorie", categorie);
      fd.append("montant", String(Number(montant)));
      fd.append("description", description);
      if (justificatif) fd.append("justificatif", justificatif);
      return api.creerDepense(fd);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["depenses"] });
      await queryClient.invalidateQueries({ queryKey: ["session-active"] });
      onFermer();
    },
  });

  const soumettre = (e: FormEvent) => {
    e.preventDefault();
    enregistrer.mutate();
  };

  const erreur =
    enregistrer.error instanceof ApiError
      ? "Vérifiez le montant."
      : enregistrer.error
        ? "Enregistrement impossible."
        : undefined;

  return (
    <Modal ouvert titre="Nouvelle dépense" onFermer={onFermer}>
      <form onSubmit={soumettre} className="flex flex-col gap-4">
        <Select label="Catégorie" options={CATEGORIES} value={categorie} onChange={(e) => setCategorie(e.target.value)} />
        <Input label="Montant (XAF)" type="number" min={1} value={montant} onChange={(e) => setMontant(Number(e.target.value))} required />
        <Input label="Description" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="ex. Carburant moto" />
        <div className="flex flex-col gap-1.5">
          <label className="text-sm text-encre-douce">Justificatif (facultatif)</label>
          <input type="file" accept="image/*" onChange={(e) => setJustificatif(e.target.files?.[0] ?? null)}
            className="text-sm text-encre-douce file:mr-2 file:rounded-lg file:border-0 file:bg-papier-creux file:px-3 file:py-1.5" />
        </div>
        {erreur && <p className="text-sm text-magenta">{erreur}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variante="secondaire" onClick={onFermer}>Annuler</Button>
          <Button type="submit" variante="danger" disabled={enregistrer.isPending || montant <= 0}>
            {enregistrer.isPending ? "Enregistrement…" : "Enregistrer la dépense"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
