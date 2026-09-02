import { useAuthStore } from "./stores/auth";
import { LoginForm } from "./features/auth/LoginForm";
import { Accueil } from "./features/auth/Accueil";

export default function App() {
  const estConnecte = useAuthStore((s) => s.estConnecte());
  return estConnecte ? <Accueil /> : <LoginForm />;
}
