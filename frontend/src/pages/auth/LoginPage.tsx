import { Navigate, useNavigate } from "react-router-dom";
import { useAuthStore } from "../../stores/auth";
import { LoginForm } from "../../features/auth/LoginForm";

export default function LoginPage() {
  const estConnecte = useAuthStore((s) => s.estConnecte());
  const navigate = useNavigate();
  if (estConnecte) return <Navigate to="/" replace />;
  return <LoginForm onBascule={() => navigate("/inscription")} />;
}
