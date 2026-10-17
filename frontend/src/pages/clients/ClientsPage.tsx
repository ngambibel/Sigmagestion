import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { EnTetePage } from "../../components/layout/EnTetePage";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { Modal } from "../../components/ui/Modal";
import { api, ApiError, type Client } from "../../lib/api";
import { useAuthStore } from "../../stores/auth";

const fcfa = (n: number) => `${n.toLocaleString("fr-FR")} F`;
const TYPES = [
  { valeur: "particulier", libelle: "Particulier" },
  { valeur: "entreprise", libelle: "Entreprise" },
  { valeur: "administration", libelle: "Administration" },
];

function estGerantOuPlus(role: string | undefined) {
  return role === "proprietaire" || role === "gerant" || role === "super_admin";
}

function ModalCreation({ onFermer }: { onFermer: () => void }) {
  const queryClient = useQueryClient();
  const [nom, setNom] = useState("");
  const [telephone, setTelephone] = useState("");
  const [type, setType] = useState("particulier");
  const [plafond, setPlafond] = useState(0);

  const creer = useMutation({
    mutationFn: () => api.creerClient({ nom, telephone, type, plafond_credit: plafond }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["clients"] });
      onFermer();
    },
  });

  return (
    <Modal ouvert titre="Nouveau client" onFermer={onFermer}>
      <div className="flex flex-col gap-3">
        <Input label="Nom" value={nom} onChange={(e) => setNom(e.target.value)} placeholder="ex. Awa Ngono / Mairie de…" />
        <Input label="Téléphone (facultatif)" value={telephone} onChange={(e) => setTelephone(e.target.value)} placeholder="+237 6XX XXX XXX" />
        <div className="flex flex-col gap-1.5">
          <label className="text-sm text-encre-douce">Type</label>
          <select value={type} onChange={(e) => setType(e.target.value)}
            className="h-11 rounded-xl border border-papier-creux bg-papier-surface px-3 text-base text-encre">
            {TYPES.map((t) => <option key={t.valeur} value={t.valeur}>{t.libelle}</option>)}
          </select>
        </div>
        <Input label="Plafond de crédit (0 = illimité)" type="number" min={0} value={plafond}
          onChange={(e) => setPlafond(Number(e.target.value))} />
      </div>
      <div className="mt-5 flex justify-end gap-2">
        <Button variante="secondaire" onClick={onFermer}>Annuler</Button>
        <Button onClick={() => creer.mutate()} disabled={creer.isPending || !nom.trim()}>
          {creer.isPending ? "Création…" : "Créer"}
        </Button>
      </div>
    </Modal>
  );
}

function ModalFiche({ client, onFermer }: { client: Client; onFermer: () => void }) {
  const queryClient = useQueryClient();
  const role = useAuthStore((s) => s.utilisateur?.role);
  const { data, isLoading } = useQuery({
    queryKey: ["historique-client", client.id],
    queryFn: () => api.historiqueClient(client.id),
  });
  const [montant, setMontant] = useState(0);

  const regler = useMutation({
    mutationFn: () => api.reglementClient(client.id, montant),
    onSuccess: () => {
      setMontant(0);
      queryClient.invalidateQueries({ queryKey: ["historique-client", client.id] });
      queryClient.invalidateQueries({ queryKey: ["clients"] });
    },
  });
  const erreurReglement =
    regler.error instanceof ApiError
      ? ((regler.error.corps as { detail?: string })?.detail ?? "Règlement refusé.")
      : undefined;

  const encours = data?.client.encours ?? client.encours;
  const relance =
    `Bonjour ${client.nom}, petit rappel amical : votre encours est de ${fcfa(encours)}. ` +
    `Merci de régulariser quand vous le pouvez.`;
  const lienWa = client.telephone
    ? `https://wa.me/${client.telephone.replace(/[^0-9]/g, "")}?text=${encodeURIComponent(relance)}`
    : null;

  return (
    <Modal ouvert titre={client.nom} onFermer={onFermer}>
      <div className="mb-4 flex items-end justify-between rounded-xl bg-papier-creux p-4">
        <span className="text-encre-douce">Encours dû</span>
        <span className={["tabular text-2xl font-semibold", encours > 0 ? "text-magenta" : "text-valide"].join(" ")}>
          {fcfa(encours)}
        </span>
      </div>

      {/* Règlement (gérant/propriétaire) */}
      {estGerantOuPlus(role) && encours > 0 && (
        <div className="mb-4">
          <p className="mb-2 text-sm text-encre-douce">Enregistrer un règlement</p>
          <div className="flex items-end gap-2">
            <Input label="Montant reçu" type="number" min={0} max={encours} value={montant}
              onChange={(e) => setMontant(Number(e.target.value))} className="flex-1" />
            <Button variante="valide" onClick={() => regler.mutate()}
              disabled={regler.isPending || montant <= 0 || montant > encours}>
              Encaisser
            </Button>
          </div>
          {erreurReglement && <p className="mt-1 text-sm text-magenta">{erreurReglement}</p>}
        </div>
      )}

      {lienWa && (
        <a href={lienWa} target="_blank" rel="noreferrer" className="mb-4 inline-block">
          <Button variante="secondaire">Relancer par WhatsApp</Button>
        </a>
      )}

      {/* Historique */}
      <h3 className="mb-2 text-sm font-medium text-encre">Historique</h3>
      {isLoading || !data ? (
        <p className="text-encre-pale">Chargement…</p>
      ) : (
        <div className="max-h-56 overflow-y-auto text-sm">
          {data.prestations.length === 0 && data.reglements.length === 0 ? (
            <p className="text-encre-pale">Aucun mouvement.</p>
          ) : (
            <ul className="divide-y divide-papier-creux">
              {data.prestations.map((p) => (
                <li key={`p${p.id}`} className="flex justify-between py-1.5">
                  <span className="text-encre-douce">
                    Vente {p.numero}{p.statut === "annulee" && " (annulée)"}
                  </span>
                  <span className="tabular text-encre">+{fcfa(p.montant_total)}</span>
                </li>
              ))}
              {data.reglements.map((r) => (
                <li key={`r${r.id}`} className="flex justify-between py-1.5">
                  <span className="text-encre-douce">Règlement</span>
                  <span className="tabular text-valide">−{fcfa(r.montant)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </Modal>
  );
}

export default function ClientsPage() {
  const { data: clients, isLoading } = useQuery({ queryKey: ["clients"], queryFn: api.listerClients });
  const [creation, setCreation] = useState(false);
  const [fiche, setFiche] = useState<Client | null>(null);

  const totalEncours = (clients ?? []).reduce((s, c) => s + c.encours, 0);

  return (
    <div>
      <EnTetePage titre="Clients" sousTitre="Créances et ventes à crédit.">
        <div className="mt-3 flex items-center gap-4">
          <Button onClick={() => setCreation(true)}>+ Nouveau client</Button>
          <span className="text-sm text-encre-douce">
            Encours total : <span className="tabular font-medium text-encre">{fcfa(totalEncours)}</span>
          </span>
        </div>
      </EnTetePage>

      <div className="overflow-x-auto rounded-2xl bg-papier-surface p-4 shadow-sm">
        {isLoading ? (
          <p className="text-encre-pale">Chargement…</p>
        ) : !clients || clients.length === 0 ? (
          <p className="text-encre-pale">Aucun client. Créez-en un pour gérer les ventes à crédit.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-encre-pale">
                <th className="py-2 font-normal">Nom</th>
                <th className="py-2 font-normal">Type</th>
                <th className="py-2 font-normal">Téléphone</th>
                <th className="py-2 text-right font-normal">Encours</th>
                <th className="py-2 text-right font-normal"></th>
              </tr>
            </thead>
            <tbody>
              {clients.map((c) => (
                <tr key={c.id} className="border-t border-papier-creux">
                  <td className="py-2 text-encre">{c.nom}</td>
                  <td className="py-2 text-encre-douce">{c.type_libelle}</td>
                  <td className="tabular py-2 text-encre-douce">{c.telephone || "—"}</td>
                  <td className={["tabular py-2 text-right", c.encours > 0 ? "text-magenta" : "text-encre-douce"].join(" ")}>
                    {fcfa(c.encours)}
                  </td>
                  <td className="py-2 text-right">
                    <button onClick={() => setFiche(c)} className="text-sm text-cyan hover:underline">
                      Ouvrir
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {creation && <ModalCreation onFermer={() => setCreation(false)} />}
      {fiche && <ModalFiche client={fiche} onFermer={() => setFiche(null)} />}
    </div>
  );
}
