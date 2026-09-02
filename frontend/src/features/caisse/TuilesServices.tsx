import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { useTicketStore } from "../../stores/ticket";

export function TuilesServices() {
  const services = useQuery({ queryKey: ["services"], queryFn: api.listerServices });
  const ajouter = useTicketStore((s) => s.ajouter);

  if (services.isLoading) return <p className="text-encre-pale">Chargement des services…</p>;

  const actifs = (services.data ?? []).filter((s) => s.actif);
  if (actifs.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-papier-creux bg-papier-surface p-8 text-center text-encre-pale">
        Aucun service actif. Ajoutez-en dans le Catalogue.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
      {actifs.map((s) => (
        <button
          key={s.id}
          onClick={() => ajouter(s)}
          className="flex min-h-[88px] flex-col items-start justify-between rounded-xl border border-papier-creux bg-papier-surface p-3 text-left transition-transform active:scale-95 hover:border-cyan"
        >
          <span className="font-medium leading-tight">{s.nom}</span>
          <span className="tabular text-lg text-cyan">{s.prix.toLocaleString("fr-FR")} F</span>
        </button>
      ))}
    </div>
  );
}
