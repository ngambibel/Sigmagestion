import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Button } from "../../components/ui/Button";
import { api, type Secretariat } from "../../lib/api";

interface LigneConso {
  selectionne: boolean;
  qte_stock: number;
  prix_achat: number;
  seuil_alerte: number;
  unite_mesure: string;
  dejaCree: boolean;
}

interface Props {
  secretariat: Secretariat;
  onRetour: () => void;
  onTermine: () => void;
}

export function EtapeStock({ secretariat, onRetour, onTermine }: Props) {
  const modeles = useQuery({ queryKey: ["modeles"], queryFn: api.modelesOnboarding });
  const existants = useQuery({ queryKey: ["consommables"], queryFn: api.listerConsommables });

  const [lignes, setLignes] = useState<Record<string, LigneConso>>({});

  useEffect(() => {
    if (!modeles.data || !existants.data) return;
    const parNom = new Map(existants.data.map((c) => [c.nom, c]));
    const initial: Record<string, LigneConso> = {};
    for (const m of modeles.data.consommables) {
      const ex = parNom.get(m.nom);
      initial[m.nom] = {
        selectionne: Boolean(ex),
        qte_stock: ex ? Number(ex.qte_stock) : 0,
        prix_achat: ex ? ex.prix_achat : m.prix_achat,
        seuil_alerte: ex ? Number(ex.seuil_alerte) : m.seuil_alerte,
        unite_mesure: m.unite_mesure,
        dejaCree: Boolean(ex),
      };
    }
    setLignes(initial);
  }, [modeles.data, existants.data]);

  const maj = (nom: string, champ: Partial<LigneConso>) =>
    setLignes((l) => ({ ...l, [nom]: { ...l[nom], ...champ } }));

  const finaliser = useMutation({
    mutationFn: async () => {
      const aCreer = Object.entries(lignes).filter(([, l]) => l.selectionne && !l.dejaCree);
      for (const [nom, l] of aCreer) {
        await api.creerConsommable({
          nom,
          unite_mesure: l.unite_mesure,
          prix_achat: Number(l.prix_achat),
          qte_stock: Number(l.qte_stock),
          seuil_alerte: Number(l.seuil_alerte),
        });
      }
      await api.modifierSecretariat(secretariat.id, { onboarding_termine: true });
    },
    onSuccess: onTermine,
  });

  if (modeles.isLoading || existants.isLoading) {
    return <p className="text-encre-pale">Chargement des consommables…</p>;
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-xl">Votre stock initial</h2>
        <p className="text-encre-douce">Déclarez ce que vous avez en boutique aujourd'hui.</p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-encre-pale">
              <th className="p-2"></th>
              <th className="p-2">Consommable</th>
              <th className="p-2 text-right">Quantité</th>
              <th className="p-2 text-right">Prix d'achat</th>
              <th className="p-2 text-right">Seuil d'alerte</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(lignes).map(([nom, l]) => (
              <tr key={nom} className="border-t border-papier-creux">
                <td className="p-2">
                  <input
                    type="checkbox"
                    className="h-5 w-5 accent-cyan"
                    checked={l.selectionne}
                    onChange={(e) => maj(nom, { selectionne: e.target.checked })}
                  />
                </td>
                <td className="p-2">
                  {nom}
                  <span className="ml-1 text-encre-pale">({l.unite_mesure})</span>
                </td>
                <td className="p-2 text-right">
                  <input type="number" min={0} disabled={!l.selectionne}
                    className="tabular h-9 w-20 rounded-lg border border-papier-creux bg-papier-surface px-2 text-right"
                    value={l.qte_stock} onChange={(e) => maj(nom, { qte_stock: Number(e.target.value) })} />
                </td>
                <td className="p-2 text-right">
                  <input type="number" min={0} disabled={!l.selectionne}
                    className="tabular h-9 w-24 rounded-lg border border-papier-creux bg-papier-surface px-2 text-right"
                    value={l.prix_achat} onChange={(e) => maj(nom, { prix_achat: Number(e.target.value) })} />
                </td>
                <td className="p-2 text-right">
                  <input type="number" min={0} disabled={!l.selectionne}
                    className="tabular h-9 w-20 rounded-lg border border-papier-creux bg-papier-surface px-2 text-right"
                    value={l.seuil_alerte} onChange={(e) => maj(nom, { seuil_alerte: Number(e.target.value) })} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex justify-between">
        <Button variante="secondaire" onClick={onRetour}>Retour</Button>
        <Button variante="valide" taille="grand" onClick={() => finaliser.mutate()} disabled={finaliser.isPending}>
          {finaliser.isPending ? "Finalisation…" : "Terminer l'installation"}
        </Button>
      </div>
    </div>
  );
}
