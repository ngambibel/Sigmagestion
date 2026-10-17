import { useState } from "react";
import { useTicketStore, sousTotal, totalTicket } from "../../stores/ticket";
import { Button } from "../../components/ui/Button";
import { EncaissementModal } from "./EncaissementModal";
import type { ResultatEncaissement } from "../../lib/api";

export function TicketEnCours({ onSucces }: { onSucces: (r: ResultatEncaissement) => void }) {
  const [encaissementOuvert, setEncaissementOuvert] = useState(false);
  const lignes = useTicketStore((s) => s.lignes);
  const remise = useTicketStore((s) => s.remise);
  const changerQuantite = useTicketStore((s) => s.changerQuantite);
  const changerPrix = useTicketStore((s) => s.changerPrix);
  const basculerRectoVerso = useTicketStore((s) => s.basculerRectoVerso);
  const retirer = useTicketStore((s) => s.retirer);
  const definirRemise = useTicketStore((s) => s.definirRemise);
  const vider = useTicketStore((s) => s.vider);

  const st = sousTotal(lignes);
  const total = totalTicket(lignes, remise);

  return (
    <div className="flex h-full flex-col rounded-2xl bg-papier-surface p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg">Ticket en cours</h2>
        {lignes.length > 0 && (
          <button onClick={vider} className="text-sm text-encre-pale underline">Vider</button>
        )}
      </div>

      {lignes.length === 0 ? (
        <p className="flex-1 text-encre-pale">Appuyez sur un service pour l'ajouter.</p>
      ) : (
        <ul className="flex-1 divide-y divide-papier-creux overflow-y-auto">
          {lignes.map((l) => (
            <li key={l.serviceId} className="py-2">
              <div className="flex items-center gap-2">
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium">{l.nom}</p>
                  <div className="mt-0.5 flex items-center gap-1 text-sm text-encre-pale">
                    <input
                      type="number" min={0} value={l.prix}
                      onChange={(e) => changerPrix(l.serviceId, Number(e.target.value))}
                      aria-label={`Prix unitaire de ${l.nom}`}
                      className={[
                        "tabular h-7 w-16 rounded-md border bg-papier-surface px-1 text-right",
                        l.prix !== l.prixCatalogue ? "border-cyan text-cyan" : "border-papier-creux",
                      ].join(" ")}
                    />
                    <span>F ×</span>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <button onClick={() => changerQuantite(l.serviceId, l.quantite - 1)}
                    className="h-8 w-8 rounded-lg bg-papier-creux text-lg" aria-label="Moins">−</button>
                  <input type="number" min={0} value={l.quantite}
                    onChange={(e) => changerQuantite(l.serviceId, Number(e.target.value))}
                    className="tabular h-8 w-12 rounded-lg border border-papier-creux bg-papier-surface text-center" />
                  <button onClick={() => changerQuantite(l.serviceId, l.quantite + 1)}
                    className="h-8 w-8 rounded-lg bg-papier-creux text-lg" aria-label="Plus">+</button>
                </div>
                <span className="tabular w-20 text-right font-medium">
                  {(l.prix * l.quantite).toLocaleString("fr-FR")} F
                </span>
                <button onClick={() => retirer(l.serviceId)} className="px-1 text-magenta" aria-label="Retirer">✕</button>
              </div>
              {l.rectoVersoPossible && (
                <label className="mt-1 flex w-fit items-center gap-1.5 text-sm text-encre-douce">
                  <input
                    type="checkbox"
                    checked={l.rectoVerso}
                    onChange={() => basculerRectoVerso(l.serviceId)}
                    className="h-4 w-4 accent-cyan"
                  />
                  Recto-verso (2× moins de feuilles)
                </label>
              )}
            </li>
          ))}
        </ul>
      )}

      <div className="mt-3 border-t border-papier-creux pt-3">
        <div className="mb-2 flex items-center justify-between text-sm text-encre-douce">
          <span>Sous-total</span>
          <span className="tabular">{st.toLocaleString("fr-FR")} F</span>
        </div>
        <div className="mb-3 flex items-center justify-between text-sm text-encre-douce">
          <label htmlFor="remise">Remise (F)</label>
          <input id="remise" type="number" min={0} value={remise}
            onChange={(e) => definirRemise(Number(e.target.value))}
            className="tabular h-8 w-24 rounded-lg border border-papier-creux bg-papier-surface px-2 text-right" />
        </div>
        <div className="mb-3 flex items-end justify-between">
          <span className="text-encre-douce">Total</span>
          <span className="tabular text-4xl">{total.toLocaleString("fr-FR")} F</span>
        </div>
        <Button
          variante="valide"
          taille="grand"
          className="w-full"
          disabled={lignes.length === 0}
          onClick={() => setEncaissementOuvert(true)}
        >
          Encaisser {total.toLocaleString("fr-FR")} F
        </Button>
      </div>

      {encaissementOuvert && (
        <EncaissementModal onFermer={() => setEncaissementOuvert(false)} onSucces={onSucces} />
      )}
    </div>
  );
}
