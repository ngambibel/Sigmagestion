import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Service } from "../../lib/api";
import { EnTetePage, EtatVide } from "../../components/layout/EnTetePage";
import { Button } from "../../components/ui/Button";
import { ServiceFormModal } from "../../features/catalogue/ServiceFormModal";

export default function CataloguePage() {
  const services = useQuery({ queryKey: ["services"], queryFn: api.listerServices });
  const queryClient = useQueryClient();

  // null fermé ; {service|null} ouvert (null = création)
  const [edition, setEdition] = useState<{ service: Service | null } | null>(null);

  const suppression = useMutation({
    mutationFn: (id: number) => api.supprimerService(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["services"] }),
  });

  const supprimer = (s: Service) => {
    if (window.confirm(`Supprimer « ${s.nom} » ? Cette action est définitive.`)) {
      suppression.mutate(s.id);
    }
  };

  return (
    <div>
      <div className="flex items-start justify-between">
        <EnTetePage titre="Catalogue" sousTitre="Vos services et leurs tarifs." />
        <Button onClick={() => setEdition({ service: null })}>+ Ajouter</Button>
      </div>

      {services.isLoading ? (
        <p className="text-encre-pale">Chargement…</p>
      ) : !services.data || services.data.length === 0 ? (
        <EtatVide message="Aucun service enregistré. Ajoutez-en un pour commencer." />
      ) : (
        <ul className="divide-y divide-papier-creux rounded-2xl border border-papier-creux bg-papier-surface">
          {services.data.map((s) => (
            <li key={s.id} className="flex items-center justify-between gap-3 p-4">
              <div className="min-w-0">
                <p className="flex items-center gap-2 font-medium">
                  <span className="truncate">{s.nom}</span>
                  {!s.actif && (
                    <span className="rounded bg-papier-creux px-1.5 py-0.5 text-xs text-encre-pale">
                      inactif
                    </span>
                  )}
                </p>
                <p className="text-sm text-encre-pale">
                  {s.categorie || "—"} · /{s.unite_facturation}
                  {s.consomme_stock ? " · consomme du stock" : ""}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-3">
                <span className="tabular text-lg">{s.prix.toLocaleString("fr-FR")} XAF</span>
                <button
                  onClick={() => setEdition({ service: s })}
                  className="text-sm font-medium text-cyan underline"
                >
                  Modifier
                </button>
                <button
                  onClick={() => supprimer(s)}
                  className="text-sm font-medium text-magenta underline"
                  disabled={suppression.isPending}
                >
                  Supprimer
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {edition && (
        <ServiceFormModal service={edition.service} onFermer={() => setEdition(null)} />
      )}
    </div>
  );
}
