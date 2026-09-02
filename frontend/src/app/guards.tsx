import type { ReactNode } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "../stores/auth";
import { useSecretariats } from "../features/secretariats/useSecretariats";

function Chargement() {
  return (
    <div className="flex min-h-screen items-center justify-center text-encre-pale">
      Chargement…
    </div>
  );
}

/** Exige une session. Sinon, redirige vers la connexion. */
export function RequireAuth() {
  const estConnecte = useAuthStore((s) => s.estConnecte());
  return estConnecte ? <Outlet /> : <Navigate to="/connexion" replace />;
}

/**
 * Exige que le propriétaire ait terminé son installation.
 * Sinon, redirige vers l'assistant.
 */
export function RequireOnboarding() {
  const role = useAuthStore((s) => s.utilisateur?.role);
  const { secretariat, isLoading } = useSecretariats();

  if (isLoading) return <Chargement />;

  const doitConfigurer =
    role === "proprietaire" && (!secretariat || !secretariat.onboarding_termine);
  return doitConfigurer ? <Navigate to="/installation" replace /> : <Outlet />;
}

/** Restreint l'accès à certains rôles. */
export function RequireRole({ roles, children }: { roles: string[]; children: ReactNode }) {
  const role = useAuthStore((s) => s.utilisateur?.role);
  if (!role || !roles.includes(role)) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}
