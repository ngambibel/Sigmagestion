import { Navigate, useNavigate } from "react-router-dom";
import { useAuthStore } from "../../stores/auth";
import { RegisterForm } from "../../features/auth/RegisterForm";

export default function RegisterPage() {
  const estConnecte = useAuthStore((s) => s.estConnecte());
  const navigate = useNavigate();
  if (estConnecte) return <Navigate to="/" replace />;
  return <RegisterForm onBascule={() => navigate("/connexion")} />;
}
