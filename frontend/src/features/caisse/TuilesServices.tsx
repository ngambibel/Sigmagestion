import { useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, type Service } from "../../lib/api";
import { chargerAvecCache } from "../../lib/offline";
import { useTicketStore } from "../../stores/ticket";

// Couleur de repli déterministe quand le service n'a pas d'image.
const COULEURS = ["bg-cyan", "bg-magenta", "bg-jaune", "bg-valide"];
function couleurDe(nom: string) {
  let somme = 0;
  for (const c of nom) somme += c.charCodeAt(0);
  return COULEURS[somme % COULEURS.length];
}

function Vignette({ service }: { service: Service }) {
  if (service.image) {
    return <img src={service.image} alt="" className="h-12 w-12 shrink-0 rounded-lg object-cover" />;
  }
  return (
    <span
      className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-lg text-lg font-semibold text-white ${couleurDe(service.nom)}`}
    >
      {service.nom.charAt(0).toUpperCase()}
    </span>
  );
}

export function TuilesServices() {
  const services = useQuery({
    queryKey: ["services"],
    queryFn: () => chargerAvecCache("services", api.listerServices),
  });
  const ajouter = useTicketStore((s) => s.ajouter);
  const [recherche, setRecherche] = useState("");
  const grille = useRef<HTMLDivElement>(null);

  // Navigation clavier de la grille (flèches), en plus de Tab/Entrée (DA §11.8).
  function surFleches(e: React.KeyboardEvent<HTMLDivElement>) {
    const touches = ["ArrowRight", "ArrowLeft", "ArrowDown", "ArrowUp"];
    if (!touches.includes(e.key) || !grille.current) return;
    const tuiles = Array.from(grille.current.querySelectorAll<HTMLButtonElement>("button[data-tuile]"));
    const i = tuiles.indexOf(document.activeElement as HTMLButtonElement);
    if (i === -1) return;
    e.preventDefault();
    // Nombre de colonnes déduit de la position des tuiles sur la 1re ligne.
    const haut = tuiles[0].offsetTop;
    const colonnes = Math.max(1, tuiles.filter((t) => t.offsetTop === haut).length);
    const pas = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : e.key === "ArrowDown" ? colonnes : -colonnes;
    const cible = tuiles[Math.min(tuiles.length - 1, Math.max(0, i + pas))];
    cible?.focus();
  }

  const resultats = useMemo(() => {
    const actifs = (services.data ?? []).filter((s) => s.actif);
    const q = recherche.trim().toLowerCase();
    if (!q) return actifs;
    return actifs.filter((s) => s.nom.toLowerCase().includes(q));
  }, [services.data, recherche]);

  if (services.isLoading) return <p className="text-encre-pale">Chargement des services…</p>;

  return (
    <div>
      <input
        type="search"
        value={recherche}
        onChange={(e) => setRecherche(e.target.value)}
        placeholder="Rechercher un service…"
        className="mb-3 h-11 w-full rounded-xl border border-papier-creux bg-papier-surface px-4 text-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan"
      />

      {resultats.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-papier-creux bg-papier-surface p-8 text-center text-encre-pale">
          {recherche ? "Aucun service ne correspond." : "Aucun service actif. Ajoutez-en dans le Catalogue."}
        </div>
      ) : (
        <div
          ref={grille}
          role="grid"
          aria-label="Services"
          onKeyDown={surFleches}
          className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-2 xl:grid-cols-3"
        >
          {resultats.map((s) => (
            <button
              key={s.id}
              data-tuile
              aria-label={`${s.nom}, ${s.prix.toLocaleString("fr-FR")} francs`}
              onClick={() => ajouter(s)}
              className="flex items-center gap-2 rounded-xl border border-papier-creux bg-papier-surface p-2 text-left transition-transform active:scale-95 hover:border-cyan"
            >
              <Vignette service={s} />
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm font-medium leading-tight">{s.nom}</span>
                <span className="tabular text-sm text-cyan">{s.prix.toLocaleString("fr-FR")} F</span>
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
