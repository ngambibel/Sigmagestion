import { Modal } from "../../components/ui/Modal";
import { Button } from "../../components/ui/Button";
import type { Prestation, Secretariat } from "../../lib/api";

function texteWhatsApp(prestation: Prestation, secretariat: Secretariat | null): string {
  const lignes = prestation.lignes
    .map((l) => `- ${l.quantite} x ${l.nom_service} = ${l.montant.toLocaleString("fr-FR")} F`)
    .join("\n");
  const entete = secretariat ? `*${secretariat.nom}*\n` : "";
  return (
    `${entete}Reçu ${prestation.numero}\n${lignes}\n` +
    `Total : ${prestation.montant_total.toLocaleString("fr-FR")} F\n` +
    (prestation.monnaie_rendue != null
      ? `Rendu : ${prestation.monnaie_rendue.toLocaleString("fr-FR")} F\n`
      : "") +
    `Merci !`
  );
}

export function RecuModal({
  prestation,
  secretariat,
  onFermer,
}: {
  prestation: Prestation;
  secretariat: Secretariat | null;
  onFermer: () => void;
}) {
  const lienWhatsApp = `https://api.whatsapp.com/send?text=${encodeURIComponent(
    texteWhatsApp(prestation, secretariat),
  )}`;
  const date = new Date(prestation.cree_le).toLocaleString("fr-FR", {
    dateStyle: "short",
    timeStyle: "short",
  });

  return (
    <Modal ouvert titre={`Reçu ${prestation.numero}`} onFermer={onFermer}>
      {/* Zone imprimable — largeur ticket. */}
      <div
        id="recu-imprimable"
        className="mx-auto max-w-[280px] rounded-lg border border-papier-creux bg-white p-4 font-sans text-encre"
      >
        <div className="mb-2 text-center">
          <p className="font-display text-lg font-semibold">{secretariat?.nom ?? "Secrétariat"}</p>
          {secretariat?.quartier || secretariat?.ville ? (
            <p className="text-xs text-encre-douce">
              {[secretariat?.quartier, secretariat?.ville].filter(Boolean).join(", ")}
            </p>
          ) : null}
          {secretariat?.telephone && <p className="text-xs text-encre-douce">{secretariat.telephone}</p>}
        </div>

        <div className="border-y border-dashed border-encre-pale py-1 text-xs text-encre-douce">
          <div className="flex justify-between"><span>Reçu</span><span>{prestation.numero}</span></div>
          <div className="flex justify-between"><span>Date</span><span>{date}</span></div>
        </div>

        <table className="my-2 w-full text-xs">
          <tbody>
            {prestation.lignes.map((l) => (
              <tr key={l.id}>
                <td className="py-0.5">{l.quantite} × {l.nom_service}</td>
                <td className="tabular py-0.5 text-right">{l.montant.toLocaleString("fr-FR")}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="border-t border-dashed border-encre-pale pt-1">
          {prestation.remise > 0 && (
            <div className="flex justify-between text-xs">
              <span>Remise</span><span className="tabular">-{prestation.remise.toLocaleString("fr-FR")}</span>
            </div>
          )}
          <div className="flex justify-between font-semibold">
            <span>TOTAL</span>
            <span className="tabular">{prestation.montant_total.toLocaleString("fr-FR")} F</span>
          </div>
          {prestation.monnaie_rendue != null && (
            <div className="flex justify-between text-xs">
              <span>Rendu</span><span className="tabular">{prestation.monnaie_rendue.toLocaleString("fr-FR")} F</span>
            </div>
          )}
        </div>

        <p className="mt-3 text-center text-xs text-encre-douce">Merci de votre visite !</p>
      </div>

      <div className="mt-4 flex flex-wrap justify-end gap-2 print:hidden">
        <Button variante="secondaire" onClick={onFermer}>Fermer</Button>
        <a href={lienWhatsApp} target="_blank" rel="noreferrer">
          <Button variante="valide">Partager WhatsApp</Button>
        </a>
        <Button onClick={() => window.print()}>Imprimer</Button>
      </div>
    </Modal>
  );
}
