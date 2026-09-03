import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal } from "../../components/ui/Modal";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { api, ApiError, type SessionCaisse } from "../../lib/api";

export function ClotureModal({ session, onFermer }: { session: SessionCaisse; onFermer: () => void }) {
  const theorique = session.montant_theorique_estime ?? session.fond_initial;
  const [montantCompte, setMontantCompte] = useState<number>(theorique);
  const [commentaire, setCommentaire] = useState("");
  const queryClient = useQueryClient();

  const ecart = montantCompte - theorique;
  const commentaireRequis = ecart !== 0 && commentaire.trim() === "";

  const cloturer = useMutation({
    mutationFn: () =>
      api.cloturerSession(session.id, {
        montant_compte: Number(montantCompte),
        commentaire: commentaire.trim(),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["session-active"] });
      onFermer();
    },
  });

  const soumettre = (e: FormEvent) => {
    e.preventDefault();
    cloturer.mutate();
  };

  const erreur =
    cloturer.error instanceof ApiError
      ? (cloturer.error.corps as { detail?: string })?.detail ?? "Clôture refusée."
      : cloturer.error
        ? "Clôture impossible."
        : undefined;

  return (
    <Modal ouvert titre="Clôturer la caisse" onFermer={onFermer}>
      <form onSubmit={soumettre} className="flex flex-col gap-4">
        <div className="flex items-center justify-between rounded-xl bg-papier-creux p-3">
          <span className="text-encre-douce">Espèces attendues (théorique)</span>
          <span className="tabular font-medium">{theorique.toLocaleString("fr-FR")} F</span>
        </div>
        <Input
          label="Montant compté en caisse (XAF)"
          type="number"
          min={0}
          value={montantCompte}
          onChange={(e) => setMontantCompte(Number(e.target.value))}
          required
        />
        <div
          className={`flex items-center justify-between rounded-xl p-3 ${
            ecart === 0 ? "bg-valide-clair text-valide" : "bg-jaune-clair text-jaune"
          }`}
        >
          <span>Écart</span>
          <span className="tabular font-medium">
            {ecart > 0 ? "+" : ""}{ecart.toLocaleString("fr-FR")} F
          </span>
        </div>
        {ecart !== 0 && (
          <Input
            label="Commentaire (obligatoire si écart)"
            value={commentaire}
            onChange={(e) => setCommentaire(e.target.value)}
            placeholder="ex. Manque constaté"
            erreur={commentaireRequis ? "Un commentaire est requis." : undefined}
          />
        )}
        {erreur && <p className="text-sm text-magenta">{erreur}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variante="secondaire" onClick={onFermer}>Annuler</Button>
          <Button type="submit" disabled={cloturer.isPending || commentaireRequis}>
            {cloturer.isPending ? "Clôture…" : "Clôturer la session"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
