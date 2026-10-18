import { Suspense } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { useAuthStore } from "../../stores/auth";
import { api } from "../../lib/api";
import { entreesVisibles } from "./navigation";
import { ClocheNotifications } from "../../features/notifications/ClocheNotifications";
import { useOnline, useVentesEnAttente } from "../../features/offline/useOffline";

function lienClasses({ isActive }: { isActive: boolean }) {
  return [
    "flex items-center gap-3 rounded-xl px-3 py-2 transition-colors",
    isActive ? "bg-cyan-clair text-cyan" : "text-encre-douce hover:bg-papier-creux",
  ].join(" ");
}

export function AppShell() {
  const utilisateur = useAuthStore((s) => s.utilisateur);
  const refreshToken = useAuthStore((s) => s.refreshToken);
  const reinitialiser = useAuthStore((s) => s.reinitialiser);
  const entrees = entreesVisibles(utilisateur?.role);
  const entreesMobile = entrees.filter((e) => e.mobile);
  const enLigne = useOnline();
  const nbEnAttente = useVentesEnAttente();

  const deconnexion = useMutation({
    mutationFn: async () => {
      if (refreshToken) await api.deconnexion(refreshToken).catch(() => undefined);
    },
    onSettled: () => reinitialiser(),
  });

  return (
    <div className="min-h-screen bg-papier">
      {/* En-tête compact sticky */}
      <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-papier-creux bg-papier-surface px-4">
        <span className="font-display text-lg font-semibold">SigmaGestion</span>
        <div className="flex items-center gap-3">
          <ClocheNotifications />
          <button
            onClick={() => deconnexion.mutate()}
            className="text-sm text-encre-douce underline"
          >
            Déconnexion
          </button>
        </div>
      </header>

      {/* Bandeau hors-ligne / synchronisation en attente */}
      {(!enLigne || nbEnAttente > 0) && (
        <div className="flex items-center justify-center gap-2 bg-jaune-clair px-4 py-1.5 text-sm text-jaune">
          <span aria-hidden>{enLigne ? "⏳" : "📴"}</span>
          {!enLigne
            ? nbEnAttente > 0
              ? `Hors ligne. ${nbEnAttente} vente(s) seront envoyées au retour du réseau.`
              : "Hors ligne. Vos ventes seront enregistrées localement."
            : `${nbEnAttente} vente(s) en attente de synchronisation.`}
        </div>
      )}

      <div className="mx-auto flex w-full max-w-6xl">
        {/* Barre latérale desktop */}
        <aside className="hidden w-60 shrink-0 border-r border-papier-creux p-3 md:block">
          <nav className="flex flex-col gap-1">
            {entrees.map((e) => (
              <NavLink key={e.chemin} to={e.chemin} end={e.chemin === "/"} className={lienClasses}>
                <span className="text-lg">{e.icone}</span>
                {e.libelle}
              </NavLink>
            ))}
          </nav>
        </aside>

        {/* Zone de travail */}
        <main className="min-h-[calc(100vh-3.5rem)] flex-1 p-4 pb-24 md:pb-4">
          <Suspense fallback={<p className="text-encre-pale">Chargement…</p>}>
            <Outlet />
          </Suspense>
        </main>
      </div>

      {/* Navigation basse mobile */}
      <nav className="fixed inset-x-0 bottom-0 z-20 flex h-16 items-stretch border-t border-papier-creux bg-papier-surface md:hidden">
        {entreesMobile.map((e) => (
          <NavLink
            key={e.chemin}
            to={e.chemin}
            end={e.chemin === "/"}
            className={({ isActive }) =>
              [
                "flex flex-1 flex-col items-center justify-center gap-0.5 text-xs",
                isActive ? "text-cyan" : "text-encre-pale",
              ].join(" ")
            }
          >
            <span className="text-xl">{e.icone}</span>
            {e.libelle}
          </NavLink>
        ))}
        <NavLink
          to="/parametres"
          className={({ isActive }) =>
            [
              "flex flex-1 flex-col items-center justify-center gap-0.5 text-xs",
              isActive ? "text-cyan" : "text-encre-pale",
            ].join(" ")
          }
        >
          <span className="text-xl">⋯</span>
          Plus
        </NavLink>
      </nav>
    </div>
  );
}
