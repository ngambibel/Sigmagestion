import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { api, ApiError } from "../../lib/api";
import { useAuthStore } from "../../stores/auth";

export default function ChangerMotDePassePage() {
  const navigate = useNavigate();
  const utilisateur = useAuthStore((s) => s.utilisateur);
  const definirUtilisateur = useAuthStore((s) => s.definirUtilisateur);
  const [mdp, setMdp] = useState("");
  const [confirme, setConfirme] = useState("");

  const changer = useMutation({
    mutationFn: () => api.changerMotDePasse(mdp),
    onSuccess: () => {
      if (utilisateur) definirUtilisateur({ ...utilisateur, doit_changer_mdp: false });
      navigate("/", { replace: true });
    },
  });

  const erreur =
    changer.error instanceof ApiError
      ? ((changer.error.corps as { nouveau_mot_de_passe?: string[] })?.nouveau_mot_de_passe?.[0] ??
        "Changement impossible.")
      : undefined;
  const incohérent = confirme.length > 0 && mdp !== confirme;

  return (
    <div className="flex min-h-screen items-center justify-center bg-papier p-4">
      <div className="w-full max-w-sm rounded-2xl bg-papier-surface p-6 shadow-sm">
        <h1 className="mb-1 text-2xl">Nouveau mot de passe</h1>
        <p className="mb-5 text-encre-douce">
          Pour sécuriser votre compte, choisissez votre propre mot de passe.
        </p>
        <div className="flex flex-col gap-3">
          <Input
            label="Nouveau mot de passe"
            type="password"
            value={mdp}
            onChange={(e) => setMdp(e.target.value)}
            erreur={erreur}
          />
          <Input
            label="Confirmer"
            type="password"
            value={confirme}
            onChange={(e) => setConfirme(e.target.value)}
            erreur={incohérent ? "Les mots de passe ne correspondent pas." : undefined}
          />
          <Button
            className="mt-2 w-full"
            taille="grand"
            onClick={() => changer.mutate()}
            disabled={changer.isPending || mdp.length < 8 || mdp !== confirme}
          >
            {changer.isPending ? "Enregistrement…" : "Valider"}
          </Button>
        </div>
      </div>
    </div>
  );
}
