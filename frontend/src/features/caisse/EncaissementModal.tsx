import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Modal } from "../../components/ui/Modal";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { api, ApiError, type Prestation, type ResultatEncaissement } from "../../lib/api";
import { useTicketStore, totalTicket } from "../../stores/ticket";
import { enfilerVente } from "../../lib/offline";

const MODES = [
  { valeur: "especes", libelle: "Espèces" },
  { valeur: "momo", libelle: "MTN MoMo" },
  { valeur: "orange_money", libelle: "Orange Money" },
  { valeur: "credit", libelle: "Crédit" },
];

export function EncaissementModal({
  onFermer,
  onSucces,
}: {
  onFermer: () => void;
  onSucces: (resultat: ResultatEncaissement) => void;
}) {
  const lignes = useTicketStore((s) => s.lignes);
  const remise = useTicketStore((s) => s.remise);
  const vider = useTicketStore((s) => s.vider);
  const total = totalTicket(lignes, remise);
  const queryClient = useQueryClient();

  const [mode, setMode] = useState("especes");
  const [montantRecu, setMontantRecu] = useState<number>(total);
  const [clientId, setClientId] = useState<number | null>(null);
  const [nouveauNom, setNouveauNom] = useState("");

  const clients = useQuery({
    queryKey: ["clients"],
    queryFn: api.listerClients,
    enabled: mode === "credit",
  });

  const creerClient = useMutation({
    mutationFn: () => api.creerClient({ nom: nouveauNom.trim() }),
    onSuccess: (c) => {
      setClientId(c.id);
      setNouveauNom("");
      queryClient.invalidateQueries({ queryKey: ["clients"] });
    },
  });

  const monnaie = mode === "especes" ? Math.max(0, montantRecu - total) : 0;
  const insuffisant = mode === "especes" && montantRecu < total;
  const clientManquant = mode === "credit" && !clientId;

  function resultatHorsLigne(): ResultatEncaissement {
    const prestation = {
      id: 0, numero: "Hors ligne", statut: "validee", mode_paiement: mode,
      client: mode === "credit" ? clientId : null, nom_client: "", remise,
      montant_total: total, montant_recu: mode === "especes" ? Number(montantRecu) : null,
      monnaie_rendue: mode === "especes" ? monnaie : null, employe_nom: "", lignes: [],
      client_uuid: null, annulee_le: null, motif_annulation: "", cree_le: new Date().toISOString(),
    } as unknown as Prestation;
    return { prestation, alertes_stock: [], hors_ligne: true };
  }

  const encaisser = useMutation({
    // « always » : la mutation s'exécute même hors ligne (TanStack met sinon les
    // mutations en pause) — on gère nous-mêmes la mise en file locale.
    networkMode: "always",
    mutationFn: async (): Promise<ResultatEncaissement> => {
      const base = {
        lignes: lignes.map((l) => ({
          service: l.serviceId,
          quantite: l.quantite,
          prix_unitaire: l.prix,
          recto_verso: l.rectoVerso,
        })),
        mode_paiement: mode,
        remise,
        montant_recu: mode === "especes" ? Number(montantRecu) : null,
        client: mode === "credit" ? clientId : null,
      };
      const resume = { total, nb_lignes: lignes.length, mode };

      // Hors ligne : on met en file (zéro perte de saisie), synchro plus tard.
      // On lit navigator.onLine directement (autoritatif au clic, sans attendre l'état React).
      if (!navigator.onLine) {
        await enfilerVente(base, resume);
        return resultatHorsLigne();
      }
      try {
        return await api.enregistrerPrestation({ ...base, client_uuid: crypto.randomUUID() });
      } catch (e) {
        // Erreur serveur (stock, validation…) → on la remonte. Panne réseau → on met en file.
        if (e instanceof ApiError) throw e;
        await enfilerVente(base, resume);
        return resultatHorsLigne();
      }
    },
    onSuccess: async (resultat) => {
      vider();
      await queryClient.invalidateQueries({ queryKey: ["consommables"] });
      // Met à jour le montant en caisse affiché (ventes espèces).
      await queryClient.invalidateQueries({ queryKey: ["session-active"] });
      onSucces(resultat);
      onFermer();
    },
  });

  const erreur =
    encaisser.error instanceof ApiError
      ? (encaisser.error.corps as { detail?: string })?.detail ?? "Encaissement refusé."
      : encaisser.error
        ? "Encaissement impossible."
        : undefined;

  return (
    <Modal ouvert titre="Encaissement" onFermer={onFermer}>
      <div className="mb-4 flex items-end justify-between">
        <span className="text-encre-douce">Total à payer</span>
        <span className="tabular text-3xl">{total.toLocaleString("fr-FR")} F</span>
      </div>

      <div className="mb-4">
        <p className="mb-2 text-sm text-encre-douce">Mode de paiement</p>
        <div className="grid grid-cols-2 gap-2">
          {MODES.map((m) => (
            <button
              key={m.valeur}
              onClick={() => setMode(m.valeur)}
              className={[
                "h-11 rounded-xl border text-sm font-medium",
                mode === m.valeur
                  ? "border-cyan bg-cyan-clair text-cyan"
                  : "border-papier-creux text-encre-douce",
              ].join(" ")}
            >
              {m.libelle}
            </button>
          ))}
        </div>
      </div>

      {mode === "especes" && (
        <div className="mb-4">
          <Input
            label="Montant reçu (XAF)"
            type="number"
            min={0}
            value={montantRecu}
            onChange={(e) => setMontantRecu(Number(e.target.value))}
          />
          <div className="mt-2 flex items-center justify-between rounded-xl bg-valide-clair p-3">
            <span className="text-encre-douce">Monnaie à rendre</span>
            <span className="tabular text-xl text-valide">{monnaie.toLocaleString("fr-FR")} F</span>
          </div>
        </div>
      )}

      {mode === "credit" && (
        <div className="mb-4">
          <label className="mb-1.5 block text-sm text-encre-douce">Client (à crédit)</label>
          <select
            value={clientId ?? ""}
            onChange={(e) => setClientId(e.target.value ? Number(e.target.value) : null)}
            className="h-11 w-full rounded-xl border border-papier-creux bg-papier-surface px-3 text-base text-encre"
          >
            <option value="">— Choisir un client —</option>
            {clients.data?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nom}{c.encours > 0 ? ` (doit ${c.encours.toLocaleString("fr-FR")} F)` : ""}
              </option>
            ))}
          </select>
          <div className="mt-2 flex items-end gap-2">
            <Input
              label="…ou nouveau client"
              value={nouveauNom}
              onChange={(e) => setNouveauNom(e.target.value)}
              placeholder="Nom du nouveau client"
              className="flex-1"
            />
            <Button
              variante="secondaire"
              onClick={() => creerClient.mutate()}
              disabled={creerClient.isPending || nouveauNom.trim() === ""}
            >
              Créer
            </Button>
          </div>
          {clientManquant && (
            <p className="mt-1 text-sm text-magenta">Un client est requis pour une vente à crédit.</p>
          )}
        </div>
      )}

      {erreur && <p className="mb-3 text-sm text-magenta">{erreur}</p>}

      <div className="flex justify-end gap-2">
        <Button variante="secondaire" onClick={onFermer}>Annuler</Button>
        <Button
          variante="valide"
          taille="grand"
          onClick={() => encaisser.mutate()}
          disabled={encaisser.isPending || insuffisant || clientManquant || lignes.length === 0}
        >
          {encaisser.isPending ? "Encaissement…" : `Encaisser ${total.toLocaleString("fr-FR")} F`}
        </Button>
      </div>
    </Modal>
  );
}
