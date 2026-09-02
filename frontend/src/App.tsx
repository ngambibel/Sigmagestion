import { useState } from "react";
import { useAuthStore } from "./stores/auth";
import { LoginForm } from "./features/auth/LoginForm";
import { RegisterForm } from "./features/auth/RegisterForm";
import { Accueil } from "./features/auth/Accueil";

export default function App() {
  const estConnecte = useAuthStore((s) => s.estConnecte());
  const [vue, setVue] = useState<"connexion" | "inscription">("connexion");

  if (estConnecte) return <Accueil />;

  return vue === "connexion" ? (
    <LoginForm onBascule={() => setVue("inscription")} />
  ) : (
    <RegisterForm onBascule={() => setVue("connexion")} />
  );
}
