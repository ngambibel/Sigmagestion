import { useState } from "react";
import type { Secretariat } from "../../lib/api";
import { Stepper } from "./Stepper";
import { EtapeIdentite } from "./EtapeIdentite";
import { EtapeServices } from "./EtapeServices";
import { EtapeStock } from "./EtapeStock";

interface Props {
  /** Secrétariat déjà créé (reprise) ou null (première fois). */
  secretariatInitial: Secretariat | null;
  onTermine: () => void;
}

export function OnboardingWizard({ secretariatInitial, onTermine }: Props) {
  const [etape, setEtape] = useState(1);
  const [secretariat, setSecretariat] = useState<Secretariat | null>(secretariatInitial);

  return (
    <div className="mx-auto max-w-2xl px-5 py-10">
      <header className="mb-6">
        <p className="text-encre-pale">Installation</p>
        <h1 className="text-3xl">Configurons votre secrétariat</h1>
      </header>

      <Stepper courante={etape} />

      <div className="rounded-2xl bg-papier-surface p-6 shadow-sm">
        {etape === 1 && (
          <EtapeIdentite
            secretariat={secretariat}
            onSuivant={(s) => {
              setSecretariat(s);
              setEtape(2);
            }}
          />
        )}
        {etape === 2 && (
          <EtapeServices onRetour={() => setEtape(1)} onSuivant={() => setEtape(3)} />
        )}
        {etape === 3 && secretariat && (
          <EtapeStock
            secretariat={secretariat}
            onRetour={() => setEtape(2)}
            onTermine={onTermine}
          />
        )}
      </div>

      <p className="mt-4 text-center text-sm text-encre-pale">
        Vous pouvez quitter et reprendre plus tard : vos choix sont enregistrés à chaque étape.
      </p>
    </div>
  );
}
