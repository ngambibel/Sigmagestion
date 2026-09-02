import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Button } from "../../components/ui/Button";
import { api } from "../../lib/api";

interface LigneService {
  selectionne: boolean;
  prix: number;
  categorie: string;
  unite_facturation: string;
  consomme_stock: boolean;
  dejaCree: boolean;
}

interface Props {
  onSuivant: () => void;
  onRetour: () => void;
}

export function EtapeServices({ onSuivant, onRetour }: Props) {
  const modeles = useQuery({ queryKey: ["modeles"], queryFn: api.modelesOnboarding });
  const existants = useQuery({ queryKey: ["services"], queryFn: api.listerServices });

  const [lignes, setLignes] = useState<Record<string, LigneService>>({});

  useEffect(() => {
    if (!modeles.data || !existants.data) return;
    const nomsExistants = new Map(existants.data.map((s) => [s.nom, s]));
    const initial: Record<string, LigneService> = {};
    for (const m of modeles.data.services) {
      const existant = nomsExistants.get(m.nom);
      initial[m.nom] = {
        selectionne: Boolean(existant),
        prix: existant ? existant.prix : m.prix,
        categorie: m.categorie,
        unite_facturation: m.unite_facturation,
        consomme_stock: m.consomme_stock,
        dejaCree: Boolean(existant),
      };
    }
    setLignes(initial);
  }, [modeles.data, existants.data]);

  const majLigne = (nom: string, champ: Partial<LigneService>) =>
    setLignes((l) => ({ ...l, [nom]: { ...l[nom], ...champ } }));

  const enregistrer = useMutation({
    mutationFn: async () => {
      const aCreer = Object.entries(lignes).filter(
        ([, l]) => l.selectionne && !l.dejaCree,
      );
      for (const [nom, l] of aCreer) {
        await api.creerService({
          nom,
          prix: Number(l.prix),
          categorie: l.categorie,
          unite_facturation: l.unite_facturation,
          consomme_stock: l.consomme_stock,
        });
      }
    },
    onSuccess: onSuivant,
  });

  if (modeles.isLoading || existants.isLoading) {
    return <p className="text-encre-pale">Chargement du catalogue…</p>;
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-xl">Vos services</h2>
        <p className="text-encre-douce">Cochez ceux que vous proposez, ajustez les prix.</p>
      </div>

      <ul className="flex flex-col divide-y divide-papier-creux rounded-xl border border-papier-creux">
        {Object.entries(lignes).map(([nom, l]) => (
          <li key={nom} className="flex items-center gap-3 p-3">
            <input
              type="checkbox"
              className="h-5 w-5 accent-cyan"
              checked={l.selectionne}
              onChange={(e) => majLigne(nom, { selectionne: e.target.checked })}
              id={`svc-${nom}`}
            />
            <label htmlFor={`svc-${nom}`} className="flex-1">
              {nom}
              <span className="ml-2 text-sm text-encre-pale">/ {l.unite_facturation}</span>
            </label>
            <div className="flex items-center gap-1">
              <input
                type="number"
                min={0}
                className="tabular h-9 w-24 rounded-lg border border-papier-creux bg-papier-surface px-2 text-right"
                value={l.prix}
                onChange={(e) => majLigne(nom, { prix: Number(e.target.value) })}
                disabled={!l.selectionne}
              />
              <span className="text-sm text-encre-pale">XAF</span>
            </div>
          </li>
        ))}
      </ul>

      <div className="flex justify-between">
        <Button variante="secondaire" onClick={onRetour}>Retour</Button>
        <Button taille="grand" onClick={() => enregistrer.mutate()} disabled={enregistrer.isPending}>
          {enregistrer.isPending ? "Enregistrement…" : "Continuer"}
        </Button>
      </div>
    </div>
  );
}
