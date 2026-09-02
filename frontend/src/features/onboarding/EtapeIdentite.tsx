import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { api, ApiError, type Secretariat } from "../../lib/api";

interface Props {
  secretariat: Secretariat | null;
  onSuivant: (secretariat: Secretariat) => void;
}

export function EtapeIdentite({ secretariat, onSuivant }: Props) {
  const [nom, setNom] = useState(secretariat?.nom ?? "");
  const [quartier, setQuartier] = useState(secretariat?.quartier ?? "");
  const [ville, setVille] = useState(secretariat?.ville ?? "");
  const [telephone, setTelephone] = useState(secretariat?.telephone ?? "");

  const enregistrer = useMutation({
    mutationFn: async () => {
      const donnees = { nom, quartier, ville, telephone };
      return secretariat
        ? api.modifierSecretariat(secretariat.id, donnees)
        : api.creerSecretariat(donnees);
    },
    onSuccess: onSuivant,
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
    <form onSubmit={soumettre} className="flex flex-col gap-4">
      <div>
        <h2 className="text-xl">Votre secrétariat</h2>
        <p className="text-encre-douce">Ces informations apparaîtront sur vos reçus.</p>
      </div>
      <Input label="Nom du secrétariat" placeholder="Éclair Bureautique" value={nom} onChange={(e) => setNom(e.target.value)} required />
      <div className="grid gap-4 sm:grid-cols-2">
        <Input label="Quartier" placeholder="Bastos" value={quartier} onChange={(e) => setQuartier(e.target.value)} />
        <Input label="Ville" placeholder="Yaoundé" value={ville} onChange={(e) => setVille(e.target.value)} />
      </div>
      <Input label="Téléphone affiché" placeholder="+237 6XX XXX XXX" inputMode="tel" value={telephone} onChange={(e) => setTelephone(e.target.value)} />
      {erreur && <p className="text-sm text-magenta">{erreur}</p>}
      <div className="flex justify-end">
        <Button type="submit" taille="grand" disabled={enregistrer.isPending}>
          {enregistrer.isPending ? "Enregistrement…" : "Continuer"}
        </Button>
      </div>
    </form>
  );
}
