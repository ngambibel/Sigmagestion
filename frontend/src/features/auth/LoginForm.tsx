import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { api, ApiError } from "../../lib/api";
import { useAuthStore } from "../../stores/auth";

export function LoginForm({ onBascule }: { onBascule: () => void }) {
  const [telephone, setTelephone] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const definirSession = useAuthStore((s) => s.definirSession);
  const definirUtilisateur = useAuthStore((s) => s.definirUtilisateur);

  const connexion = useMutation({
    mutationFn: async () => {
      const r = await api.connexion(telephone, motDePasse);
      definirSession(r.access, r.refresh);
      // On récupère le profil complet juste après.
      const utilisateur = await api.moi();
      definirUtilisateur(utilisateur);
    },
  });

  const soumettre = (e: FormEvent) => {
    e.preventDefault();
    connexion.mutate();
  };

  const messageErreur =
    connexion.error instanceof ApiError && connexion.error.statut === 401
      ? "Téléphone ou mot de passe incorrect."
      : connexion.error
        ? "Connexion impossible. Vérifiez que le backend est démarré."
        : undefined;

  return (
    <div className="mx-auto flex min-h-screen max-w-sm flex-col justify-center px-5">
      <h1 className="mb-1 text-3xl">SigmaGestion</h1>
      <p className="mb-8 text-encre-douce">Connectez-vous pour continuer.</p>

      <form onSubmit={soumettre} className="flex flex-col gap-4">
        <Input
          label="Téléphone"
          placeholder="+237 6XX XXX XXX"
          inputMode="tel"
          autoComplete="username"
          value={telephone}
          onChange={(e) => setTelephone(e.target.value)}
          required
        />
        <Input
          label="Mot de passe"
          type="password"
          placeholder="••••••••"
          autoComplete="current-password"
          value={motDePasse}
          onChange={(e) => setMotDePasse(e.target.value)}
          erreur={messageErreur}
          required
        />
        <Button
          type="submit"
          taille="grand"
          disabled={connexion.isPending}
          className="mt-2"
        >
          {connexion.isPending ? "Connexion…" : "Se connecter"}
        </Button>
      </form>

      <p className="mt-6 text-center text-encre-douce">
        Pas encore de compte ?{" "}
        <button onClick={onBascule} className="font-medium text-cyan underline">
          Créer un compte
        </button>
      </p>
    </div>
  );
}
