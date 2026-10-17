import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { EnTetePage } from "../../components/layout/EnTetePage";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { Modal } from "../../components/ui/Modal";
import { api, ApiError, type Employe, type EmployeCree } from "../../lib/api";

function lienWhatsApp(tel: string, message: string): string {
  const numero = tel.replace(/[^0-9]/g, ""); // wa.me veut les chiffres sans +
  return `https://wa.me/${numero}?text=${encodeURIComponent(message)}`;
}

function ModalAjout({ onFermer }: { onFermer: () => void }) {
  const queryClient = useQueryClient();
  const [nom, setNom] = useState("");
  const [telephone, setTelephone] = useState("");
  const [role, setRole] = useState("employe");
  const [cree, setCree] = useState<EmployeCree | null>(null);

  const creer = useMutation({
    mutationFn: () => api.creerEmploye({ nom, telephone, role }),
    onSuccess: (data) => {
      setCree(data);
      queryClient.invalidateQueries({ queryKey: ["employes"] });
    },
  });

  const erreur =
    creer.error instanceof ApiError
      ? ((creer.error.corps as { telephone?: string[]; detail?: string })?.telephone?.[0] ??
        (creer.error.corps as { detail?: string })?.detail ??
        "Création impossible.")
      : undefined;

  if (cree) {
    const message =
      `Bonjour ${cree.nom}, voici ton accès SigmaGestion.\n` +
      `Téléphone : ${cree.telephone}\n` +
      `Mot de passe provisoire : ${cree.mot_de_passe_provisoire}\n` +
      `Tu devras le changer à la première connexion.`;
    return (
      <Modal ouvert titre="Employé créé" onFermer={onFermer}>
        <p className="mb-3 text-encre-douce">
          Transmets ce mot de passe provisoire à {cree.nom}. Il ne sera plus affiché ensuite.
        </p>
        <div className="mb-4 rounded-xl bg-papier-creux p-4 text-center">
          <p className="text-sm text-encre-douce">Mot de passe provisoire</p>
          <p className="tabular text-2xl font-semibold text-encre">
            {cree.mot_de_passe_provisoire}
          </p>
        </div>
        <div className="flex justify-end gap-2">
          <Button variante="secondaire" onClick={onFermer}>Fermer</Button>
          <a href={lienWhatsApp(cree.telephone, message)} target="_blank" rel="noreferrer">
            <Button variante="valide">Partager par WhatsApp</Button>
          </a>
        </div>
      </Modal>
    );
  }

  return (
    <Modal ouvert titre="Ajouter un employé" onFermer={onFermer}>
      <div className="flex flex-col gap-3">
        <Input label="Nom complet" value={nom} onChange={(e) => setNom(e.target.value)} placeholder="ex. Awa Ngono" />
        <Input
          label="Téléphone"
          value={telephone}
          onChange={(e) => setTelephone(e.target.value)}
          placeholder="+237 6XX XXX XXX"
          erreur={erreur}
        />
        <div className="flex flex-col gap-1.5">
          <label className="text-sm text-encre-douce">Rôle</label>
          <select
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="h-11 rounded-xl border border-papier-creux bg-papier-surface px-3 text-base text-encre"
          >
            <option value="employe">Employé</option>
            <option value="gerant">Gérant</option>
          </select>
        </div>
      </div>
      <div className="mt-5 flex justify-end gap-2">
        <Button variante="secondaire" onClick={onFermer}>Annuler</Button>
        <Button
          onClick={() => creer.mutate()}
          disabled={creer.isPending || !nom.trim() || !telephone.trim()}
        >
          {creer.isPending ? "Création…" : "Créer"}
        </Button>
      </div>
    </Modal>
  );
}

function ModalActivite({ employe, onFermer }: { employe: Employe; onFermer: () => void }) {
  const { data, isLoading } = useQuery({
    queryKey: ["activite-employe", employe.id],
    queryFn: () => api.activiteEmploye(employe.id),
  });
  const fcfa = (n: number) => `${n.toLocaleString("fr-FR")} F`;
  return (
    <Modal ouvert titre={`Activité — ${employe.nom}`} onFermer={onFermer}>
      {isLoading || !data ? (
        <p className="text-encre-pale">Chargement…</p>
      ) : (
        <dl className="flex flex-col gap-2 text-sm">
          {[
            ["CA généré", fcfa(data.ca_genere)],
            ["Prestations", String(data.nb_prestations)],
            ["Annulations", String(data.nb_annulations)],
            ["Sessions", String(data.nb_sessions)],
            ["Sessions avec écart", String(data.nb_sessions_avec_ecart)],
            ["Écart cumulé", fcfa(data.ecart_cumule)],
          ].map(([k, v]) => (
            <div key={k} className="flex justify-between border-t border-papier-creux py-1.5 first:border-t-0">
              <dt className="text-encre-douce">{k}</dt>
              <dd className="tabular text-encre">{v}</dd>
            </div>
          ))}
        </dl>
      )}
    </Modal>
  );
}

export default function EmployesPage() {
  const queryClient = useQueryClient();
  const { data: employes, isLoading } = useQuery({ queryKey: ["employes"], queryFn: api.listerEmployes });
  const [ajoutOuvert, setAjoutOuvert] = useState(false);
  const [activite, setActivite] = useState<Employe | null>(null);

  const basculer = useMutation({
    mutationFn: (e: Employe) => (e.is_active ? api.desactiverEmploye(e.id) : api.reactiverEmploye(e.id)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["employes"] }),
  });

  return (
    <div>
      <EnTetePage titre="Employés" sousTitre="Créez et gérez vos comptes employés et gérants.">
        <div className="mt-3">
          <Button onClick={() => setAjoutOuvert(true)}>+ Ajouter un employé</Button>
        </div>
      </EnTetePage>

      <div className="overflow-x-auto rounded-2xl bg-papier-surface p-4 shadow-sm">
        {isLoading ? (
          <p className="text-encre-pale">Chargement…</p>
        ) : !employes || employes.length === 0 ? (
          <p className="text-encre-pale">
            Aucun employé pour le moment. Ajoutez-en un pour déléguer la caisse.
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-encre-pale">
                <th className="py-2 font-normal">Nom</th>
                <th className="py-2 font-normal">Téléphone</th>
                <th className="py-2 font-normal">Rôle</th>
                <th className="py-2 font-normal">Statut</th>
                <th className="py-2 text-right font-normal">Actions</th>
              </tr>
            </thead>
            <tbody>
              {employes.map((e) => (
                <tr key={e.id} className="border-t border-papier-creux">
                  <td className="py-2 text-encre">{e.nom}</td>
                  <td className="tabular py-2 text-encre-douce">{e.telephone}</td>
                  <td className="py-2 text-encre-douce">{e.role_libelle}</td>
                  <td className="py-2">
                    {e.is_active ? (
                      <span className="rounded-md bg-valide-clair px-2 py-0.5 text-xs text-valide">Actif</span>
                    ) : (
                      <span className="rounded-md bg-papier-creux px-2 py-0.5 text-xs text-encre-pale">Désactivé</span>
                    )}
                  </td>
                  <td className="py-2">
                    <div className="flex justify-end gap-2">
                      <button onClick={() => setActivite(e)} className="text-sm text-cyan hover:underline">
                        Activité
                      </button>
                      <button
                        onClick={() => basculer.mutate(e)}
                        disabled={basculer.isPending}
                        className={["text-sm hover:underline", e.is_active ? "text-magenta" : "text-valide"].join(" ")}
                      >
                        {e.is_active ? "Désactiver" : "Réactiver"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {ajoutOuvert && <ModalAjout onFermer={() => setAjoutOuvert(false)} />}
      {activite && <ModalActivite employe={activite} onFermer={() => setActivite(null)} />}
    </div>
  );
}
