import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Notification } from "../../lib/api";

function depuis(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const min = Math.round(diff / 60000);
  if (min < 1) return "à l'instant";
  if (min < 60) return `il y a ${min} min`;
  const h = Math.round(min / 60);
  if (h < 24) return `il y a ${h} h`;
  const j = Math.round(h / 24);
  return `il y a ${j} j`;
}

export function ClocheNotifications() {
  const [ouvert, setOuvert] = useState(false);
  const conteneur = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Compteur rafraîchi en tâche de fond (une push peut être manquée).
  const compteur = useQuery({
    queryKey: ["notifications-compteur"],
    queryFn: api.compteurNotifications,
    refetchInterval: 60_000,
  });

  const liste = useQuery({
    queryKey: ["notifications-liste"],
    queryFn: () => api.listerNotifications(),
    enabled: ouvert,
  });

  const rafraichir = () => {
    queryClient.invalidateQueries({ queryKey: ["notifications-compteur"] });
    queryClient.invalidateQueries({ queryKey: ["notifications-liste"] });
  };

  const toutLire = useMutation({ mutationFn: api.toutLireNotifications, onSuccess: rafraichir });
  const lire = useMutation({ mutationFn: api.lireNotification, onSuccess: rafraichir });
  const archiver = useMutation({ mutationFn: api.archiverNotification, onSuccess: rafraichir });

  // Fermeture au clic extérieur.
  useEffect(() => {
    if (!ouvert) return;
    function surClic(e: MouseEvent) {
      if (conteneur.current && !conteneur.current.contains(e.target as Node)) setOuvert(false);
    }
    document.addEventListener("mousedown", surClic);
    return () => document.removeEventListener("mousedown", surClic);
  }, [ouvert]);

  const nonLues = compteur.data?.non_lues ?? 0;
  const notifications = liste.data?.resultats ?? [];

  function ouvrir(n: Notification) {
    if (!n.lu) lire.mutate(n.id);
    setOuvert(false);
    if (n.url && n.url !== "/") navigate(n.url);
  }

  return (
    <div ref={conteneur} className="relative">
      <button
        className="relative rounded-lg p-1 text-xl"
        aria-label={`Notifications${nonLues > 0 ? `, ${nonLues} non lues` : ""}`}
        aria-expanded={ouvert}
        onClick={() => setOuvert((v) => !v)}
      >
        🔔
        {nonLues > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-magenta px-1 text-xs font-semibold text-white">
            {nonLues > 9 ? "9+" : nonLues}
          </span>
        )}
      </button>

      {ouvert && (
        <div className="absolute right-0 top-11 z-30 w-80 max-w-[90vw] overflow-hidden rounded-2xl border border-papier-creux bg-papier-surface shadow-lg">
          <div className="flex items-center justify-between border-b border-papier-creux px-4 py-2.5">
            <span className="font-medium">Notifications</span>
            {nonLues > 0 && (
              <button
                className="text-sm text-cyan hover:underline"
                onClick={() => toutLire.mutate()}
                disabled={toutLire.isPending}
              >
                Tout marquer comme lu
              </button>
            )}
          </div>

          <div className="max-h-96 overflow-y-auto">
            {liste.isLoading ? (
              <p className="px-4 py-6 text-center text-encre-pale">Chargement…</p>
            ) : notifications.length === 0 ? (
              <p className="px-4 py-8 text-center text-encre-pale">Aucune notification.</p>
            ) : (
              <ul>
                {notifications.map((n) => (
                  <li
                    key={n.id}
                    className={[
                      "flex items-start gap-2 border-b border-papier-creux px-4 py-3 last:border-b-0",
                      n.lu ? "" : "bg-cyan-clair/40",
                    ].join(" ")}
                  >
                    <button
                      className="min-w-0 flex-1 text-left"
                      onClick={() => ouvrir(n)}
                    >
                      <p className={["truncate", n.lu ? "text-encre-douce" : "font-medium text-encre"].join(" ")}>
                        {n.titre}
                      </p>
                      <p className="mt-0.5 line-clamp-2 whitespace-pre-line text-sm text-encre-douce">
                        {n.corps}
                      </p>
                      <p className="mt-1 text-xs text-encre-pale">{depuis(n.cree_le)}</p>
                    </button>
                    <button
                      className="shrink-0 rounded-md p-1 text-encre-pale hover:bg-papier-creux hover:text-encre"
                      aria-label="Archiver"
                      title="Archiver"
                      onClick={() => archiver.mutate(n.id)}
                    >
                      ✕
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
