import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Modal } from "../../components/ui/Modal";
import { Button } from "../../components/ui/Button";
import { api, type Service } from "../../lib/api";

interface Ligne {
  consommable: number | "";
  qte_par_unite: number;
}

export function NomenclatureModal({ service, onFermer }: { service: Service; onFermer: () => void }) {
  const consommables = useQuery({ queryKey: ["consommables"], queryFn: api.listerConsommables });
  const nomenclature = useQuery({
    queryKey: ["nomenclature", service.id],
    queryFn: () => api.getNomenclature(service.id),
  });
  const queryClient = useQueryClient();

  const [lignes, setLignes] = useState<Ligne[]>([]);

  useEffect(() => {
    if (!nomenclature.data) return;
    setLignes(
      nomenclature.data.length
        ? nomenclature.data.map((l) => ({
            consommable: l.consommable,
            qte_par_unite: Number(l.qte_par_unite),
          }))
        : [{ consommable: "", qte_par_unite: 1 }],
    );
  }, [nomenclature.data]);

  const maj = (i: number, champ: Partial<Ligne>) =>
    setLignes((ls) => ls.map((l, idx) => (idx === i ? { ...l, ...champ } : l)));
  const ajouter = () => setLignes((ls) => [...ls, { consommable: "", qte_par_unite: 1 }]);
  const retirer = (i: number) => setLignes((ls) => ls.filter((_, idx) => idx !== i));

  const enregistrer = useMutation({
    mutationFn: async () => {
      const valides = lignes
        .filter((l) => l.consommable !== "")
        .map((l) => ({ consommable: Number(l.consommable), qte_par_unite: Number(l.qte_par_unite) }));
      await api.putNomenclature(service.id, valides);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["services"] });
      await queryClient.invalidateQueries({ queryKey: ["nomenclature", service.id] });
      onFermer();
    },
  });

  const chargement = consommables.isLoading || nomenclature.isLoading;

  return (
    <Modal ouvert titre={`Recette — ${service.nom}`} onFermer={onFermer}>
      <p className="mb-4 text-sm text-encre-douce">
        Indiquez les consommables prélevés à chaque unité vendue (ex. 1 feuille, 0,004 cartouche).
      </p>

      {chargement ? (
        <p className="text-encre-pale">Chargement…</p>
      ) : consommables.data && consommables.data.length === 0 ? (
        <p className="rounded-lg bg-jaune-clair p-3 text-sm text-jaune">
          Ajoutez d'abord des consommables (page Stock) pour définir une recette.
        </p>
      ) : (
        <div className="flex flex-col gap-3">
          {lignes.map((l, i) => (
            <div key={i} className="flex items-center gap-2">
              <select
                className="h-10 flex-1 rounded-lg border border-papier-creux bg-papier-surface px-2"
                value={l.consommable}
                onChange={(e) => maj(i, { consommable: e.target.value === "" ? "" : Number(e.target.value) })}
              >
                <option value="">— Choisir —</option>
                {consommables.data?.map((c) => (
                  <option key={c.id} value={c.id}>{c.nom} ({c.unite_mesure})</option>
                ))}
              </select>
              <input
                type="number" min={0} step="0.0001"
                className="tabular h-10 w-24 rounded-lg border border-papier-creux bg-papier-surface px-2 text-right"
                value={l.qte_par_unite}
                onChange={(e) => maj(i, { qte_par_unite: Number(e.target.value) })}
              />
              <button onClick={() => retirer(i)} className="px-1 text-magenta" aria-label="Retirer">✕</button>
            </div>
          ))}
          <button onClick={ajouter} className="self-start text-sm font-medium text-cyan underline">
            + Ajouter un consommable
          </button>
        </div>
      )}

      <div className="mt-5 flex justify-end gap-2">
        <Button variante="secondaire" onClick={onFermer}>Annuler</Button>
        <Button onClick={() => enregistrer.mutate()} disabled={enregistrer.isPending || chargement}>
          {enregistrer.isPending ? "Enregistrement…" : "Enregistrer la recette"}
        </Button>
      </div>
    </Modal>
  );
}
