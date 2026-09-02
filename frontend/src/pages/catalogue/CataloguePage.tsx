import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { EnTetePage, EtatVide } from "../../components/layout/EnTetePage";

export default function CataloguePage() {
  const services = useQuery({ queryKey: ["services"], queryFn: api.listerServices });

  return (
    <div>
      <EnTetePage titre="Catalogue" sousTitre="Vos services et leurs tarifs." />
      {services.isLoading ? (
        <p className="text-encre-pale">Chargement…</p>
      ) : !services.data || services.data.length === 0 ? (
        <EtatVide message="Aucun service enregistré pour le moment." />
      ) : (
        <ul className="divide-y divide-papier-creux rounded-2xl border border-papier-creux bg-papier-surface">
          {services.data.map((s) => (
            <li key={s.id} className="flex items-center justify-between p-4">
              <div>
                <p className="font-medium">{s.nom}</p>
                <p className="text-sm text-encre-pale">
                  {s.categorie || "—"} · /{s.unite_facturation}
                  {s.consomme_stock ? " · consomme du stock" : ""}
                </p>
              </div>
              <span className="tabular text-lg">{s.prix.toLocaleString("fr-FR")} XAF</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
