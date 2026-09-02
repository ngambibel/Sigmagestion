import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Consommable } from "../../lib/api";
import { EnTetePage, EtatVide } from "../../components/layout/EnTetePage";
import { Button } from "../../components/ui/Button";
import { ConsommableFormModal } from "../../features/stocks/ConsommableFormModal";
import { EntreeStockModal } from "../../features/stocks/EntreeStockModal";
import { AjustementModal } from "../../features/stocks/AjustementModal";
import { useAuthStore } from "../../stores/auth";

function formaterQte(valeur: string) {
  const n = Number(valeur);
  return Number.isInteger(n) ? n.toLocaleString("fr-FR") : n.toString();
}

export default function StockPage() {
  const consommables = useQuery({ queryKey: ["consommables"], queryFn: api.listerConsommables });
  const queryClient = useQueryClient();
  const [edition, setEdition] = useState<{ consommable: Consommable | null } | null>(null);
  const [entree, setEntree] = useState<Consommable | null>(null);
  const [ajustement, setAjustement] = useState<Consommable | null>(null);
  const role = useAuthStore((s) => s.utilisateur?.role);
  const peutReappro = role === "proprietaire" || role === "gerant" || role === "super_admin";
  const estProprietaire = role === "proprietaire" || role === "super_admin";

  const suppression = useMutation({
    mutationFn: (id: number) => api.supprimerConsommable(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["consommables"] }),
  });

  const supprimer = (c: Consommable) => {
    if (window.confirm(`Supprimer « ${c.nom} » ? Cette action est définitive.`)) {
      suppression.mutate(c.id);
    }
  };

  return (
    <div>
      <div className="flex items-start justify-between">
        <EnTetePage titre="Stock" sousTitre="Vos consommables et vos seuils d'alerte." />
        <div className="flex items-center gap-3">
          {peutReappro && (
            <Link to="/mouvements" className="text-sm font-medium text-cyan underline">Journal</Link>
          )}
          <Button onClick={() => setEdition({ consommable: null })}>+ Ajouter</Button>
        </div>
      </div>

      {consommables.isLoading ? (
        <p className="text-encre-pale">Chargement…</p>
      ) : !consommables.data || consommables.data.length === 0 ? (
        <EtatVide message="Aucun consommable enregistré. Ajoutez-en un pour suivre vos stocks." />
      ) : (
        <ul className="divide-y divide-papier-creux rounded-2xl border border-papier-creux bg-papier-surface">
          {consommables.data.map((c) => (
            <li key={c.id} className="flex items-center justify-between gap-3 p-4">
              <div className="min-w-0">
                <p className="flex items-center gap-2 font-medium">
                  <span className="truncate">{c.nom}</span>
                  {c.sous_seuil && (
                    <span className="rounded bg-jaune-clair px-1.5 py-0.5 text-xs text-jaune">
                      stock bas
                    </span>
                  )}
                  {!c.actif && (
                    <span className="rounded bg-papier-creux px-1.5 py-0.5 text-xs text-encre-pale">
                      inactif
                    </span>
                  )}
                </p>
                <p className="text-sm text-encre-pale">
                  seuil {formaterQte(c.seuil_alerte)} · {c.prix_achat.toLocaleString("fr-FR")} XAF/{c.unite_mesure}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-3">
                <span className="tabular text-lg">
                  {formaterQte(c.qte_stock)} <span className="text-sm text-encre-pale">{c.unite_mesure}</span>
                </span>
                {peutReappro && (
                  <button onClick={() => setEntree(c)} className="text-sm font-medium text-valide underline">
                    Entrée
                  </button>
                )}
                {estProprietaire && (
                  <button onClick={() => setAjustement(c)} className="text-sm font-medium text-jaune underline">
                    Ajuster
                  </button>
                )}
                <button onClick={() => setEdition({ consommable: c })} className="text-sm font-medium text-cyan underline">
                  Modifier
                </button>
                <button onClick={() => supprimer(c)} className="text-sm font-medium text-magenta underline" disabled={suppression.isPending}>
                  Supprimer
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {edition && (
        <ConsommableFormModal consommable={edition.consommable} onFermer={() => setEdition(null)} />
      )}
      {entree && (
        <EntreeStockModal consommable={entree} onFermer={() => setEntree(null)} />
      )}
      {ajustement && (
        <AjustementModal consommable={ajustement} onFermer={() => setAjustement(null)} />
      )}
    </div>
  );
}
