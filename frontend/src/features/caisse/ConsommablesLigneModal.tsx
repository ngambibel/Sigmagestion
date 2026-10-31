import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Modal } from "../../components/ui/Modal";
import { Button } from "../../components/ui/Button";
import { api } from "../../lib/api";
import { useTicketStore, type ConsommableChoisi } from "../../stores/ticket";

/**
 * Choix libre des consommables utilisés pour une ligne de vente.
 * Les consommables sélectionnés remplacent la recette du service : à l'encaissement,
 * ce sont eux qui sont déduits du stock et qui donnent le coût matière.
 */
export function ConsommablesLigneModal({
  serviceId,
  nomService,
  onFermer,
}: {
  serviceId: number;
  nomService: string;
  onFermer: () => void;
}) {
  const ligne = useTicketStore((s) => s.lignes.find((l) => l.serviceId === serviceId));
  const definirConsommables = useTicketStore((s) => s.definirConsommables);
  const stock = useQuery({ queryKey: ["consommables"], queryFn: api.listerConsommables });

  const quantiteLigne = ligne?.quantite ?? 1;
  const [choisis, setChoisis] = useState<ConsommableChoisi[]>(ligne?.consommables ?? []);

  const disponibles = (stock.data ?? []).filter(
    (c) => !choisis.some((x) => x.consommableId === c.id),
  );

  const ajouter = (id: number) => {
    const c = stock.data?.find((x) => x.id === id);
    if (!c) return;
    setChoisis((cs) => [
      ...cs,
      { consommableId: c.id, nom: c.nom, quantite: 1, prixAchat: Number(c.prix_achat) },
    ]);
  };
  const majQuantite = (id: number, q: number) =>
    setChoisis((cs) => cs.map((x) => (x.consommableId === id ? { ...x, quantite: Math.max(0, q) } : x)));
  const retirer = (id: number) =>
    setChoisis((cs) => cs.filter((x) => x.consommableId !== id));

  const coutParUnite = choisis.reduce((s, c) => s + c.quantite * c.prixAchat, 0);
  const coutTotal = coutParUnite * quantiteLigne;

  const enregistrer = () => {
    definirConsommables(serviceId, choisis.filter((c) => c.quantite > 0));
    onFermer();
  };

  return (
    <Modal ouvert titre={`Consommables — ${nomService}`} onFermer={onFermer}>
      <p className="mb-4 text-sm text-encre-douce">
        Quantités <strong>par unité vendue</strong> (pré-remplies depuis la recette du service).
        Elles seront multipliées par la quantité du ticket{quantiteLigne > 1 ? ` (× ${quantiteLigne})` : ""},
        déduites du stock, et déterminent le coût matière.
      </p>

      {stock.isLoading ? (
        <p className="text-encre-pale">Chargement…</p>
      ) : (
        <div className="flex flex-col gap-3">
          {choisis.length === 0 && (
            <p className="text-sm text-encre-pale">Aucun consommable sélectionné pour l'instant.</p>
          )}
          {choisis.map((c) => (
            <div key={c.consommableId} className="flex items-center gap-2">
              <span className="min-w-0 flex-1 truncate">{c.nom}</span>
              <input
                type="number"
                min={0}
                step="0.0001"
                value={c.quantite}
                onChange={(e) => majQuantite(c.consommableId, Number(e.target.value))}
                aria-label={`Quantité de ${c.nom}`}
                className="tabular h-9 w-20 rounded-lg border border-papier-creux bg-papier-surface px-2 text-right"
              />
              <span className="tabular w-20 text-right text-sm text-encre-douce">
                {(c.quantite * c.prixAchat).toLocaleString("fr-FR")} F
              </span>
              <button onClick={() => retirer(c.consommableId)} className="px-1 text-magenta" aria-label="Retirer">
                ✕
              </button>
            </div>
          ))}

          {disponibles.length > 0 && (
            <select
              value=""
              onChange={(e) => e.target.value && ajouter(Number(e.target.value))}
              className="h-10 rounded-lg border border-papier-creux bg-papier-surface px-2 text-encre-douce"
            >
              <option value="">+ Ajouter un consommable du stock…</option>
              {disponibles.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nom} — {Number(c.prix_achat).toLocaleString("fr-FR")} F/{c.unite_mesure} (stock {Number(c.qte_stock)})
                </option>
              ))}
            </select>
          )}

          <div className="mt-1 flex items-center justify-between rounded-xl bg-papier-creux p-3">
            <span className="text-encre-douce">
              Coût matière de cette ligne
              {quantiteLigne > 1 && (
                <span className="text-encre-pale"> ({coutParUnite.toLocaleString("fr-FR")} F × {quantiteLigne})</span>
              )}
            </span>
            <span className="tabular text-lg font-semibold text-magenta">
              {coutTotal.toLocaleString("fr-FR")} F
            </span>
          </div>
        </div>
      )}

      <div className="mt-5 flex justify-end gap-2">
        <Button variante="secondaire" onClick={onFermer}>Annuler</Button>
        <Button onClick={enregistrer}>Valider les consommables</Button>
      </div>
    </Modal>
  );
}
