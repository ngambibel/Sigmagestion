import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "./stores/auth";
import { api } from "./lib/api";
import { LoginForm } from "./features/auth/LoginForm";
import { RegisterForm } from "./features/auth/RegisterForm";
import { Accueil } from "./features/auth/Accueil";
import { OnboardingWizard } from "./features/onboarding/OnboardingWizard";

function EspaceConnecte() {
  const utilisateur = useAuthStore((s) => s.utilisateur);
  const queryClient = useQueryClient();
  const secretariats = useQuery({
    queryKey: ["secretariats"],
    queryFn: api.listerSecretariats,
  });

  if (secretariats.isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-encre-pale">
        Chargement…
      </div>
    );
  }

  const estProprietaire = utilisateur?.role === "proprietaire";
  const secretariat = secretariats.data?.[0] ?? null;
  const doitConfigurer =
    estProprietaire && (!secretariat || !secretariat.onboarding_termine);

  if (doitConfigurer) {
    return (
      <OnboardingWizard
        secretariatInitial={secretariat}
        onTermine={() => queryClient.invalidateQueries({ queryKey: ["secretariats"] })}
      />
    );
  }

  return <Accueil secretariat={secretariat} />;
}

export default function App() {
  const estConnecte = useAuthStore((s) => s.estConnecte());
  const [vue, setVue] = useState<"connexion" | "inscription">("connexion");

  if (estConnecte) return <EspaceConnecte />;

  return vue === "connexion" ? (
    <LoginForm onBascule={() => setVue("inscription")} />
  ) : (
    <RegisterForm onBascule={() => setVue("connexion")} />
  );
}
