import { useEffect, useState } from "react";
import { Button } from "./components/ui/Button";
import { Input } from "./components/ui/Input";
import { api, type Sante } from "./lib/api";

const encres = [
  { nom: "Cyan — agir", classe: "bg-cyan", texte: "text-white" },
  { nom: "Magenta — corriger", classe: "bg-magenta", texte: "text-white" },
  { nom: "Jaune — surveiller", classe: "bg-jaune", texte: "text-white" },
  { nom: "Vert — encaissé", classe: "bg-valide", texte: "text-white" },
  { nom: "Encre", classe: "bg-encre", texte: "text-white" },
  { nom: "Papier creux", classe: "bg-papier-creux", texte: "text-encre" },
];

function BadgeSante({ sante }: { sante: Sante | "chargement" | "erreur" }) {
  if (sante === "chargement")
    return <span className="text-encre-pale">Vérification du backend…</span>;
  if (sante === "erreur")
    return (
      <span className="rounded-lg bg-magenta-clair px-2 py-1 text-sm text-magenta">
        Backend injoignable
      </span>
    );
  const ok = sante.base === "ok" && sante.redis === "ok";
  return (
    <span
      className={`rounded-lg px-2 py-1 text-sm ${
        ok ? "bg-valide-clair text-valide" : "bg-jaune-clair text-jaune"
      }`}
    >
      Backend : base {sante.base} · redis {sante.redis}
    </span>
  );
}

export default function App() {
  const [sante, setSante] = useState<Sante | "chargement" | "erreur">("chargement");

  useEffect(() => {
    api
      .sante()
      .then(setSante)
      .catch(() => setSante("erreur"));
  }, []);

  return (
    <div className="mx-auto max-w-3xl px-5 py-10">
      <header className="mb-10 flex items-center justify-between">
        <div>
          <h1 className="text-3xl">SigmaGestion</h1>
          <p className="text-encre-douce">Gestion de secrétariat bureautique</p>
        </div>
        <BadgeSante sante={sante} />
      </header>

      <section className="mb-10">
        <h2 className="mb-3 text-xl">Palette — les quatre encres</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {encres.map((e) => (
            <div
              key={e.nom}
              className={`flex h-20 items-end rounded-xl p-3 ${e.classe} ${e.texte}`}
            >
              <span className="text-sm font-medium">{e.nom}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="mb-10">
        <h2 className="mb-3 text-xl">Typographie & montants</h2>
        <div className="rounded-xl bg-papier-surface p-5 shadow-sm">
          <p className="tabular text-4xl">68 200 F</p>
          <p className="text-encre-douce">Aujourd'hui ↑ 12 %</p>
        </div>
      </section>

      <section className="mb-10">
        <h2 className="mb-3 text-xl">Boutons</h2>
        <div className="flex flex-wrap gap-3">
          <Button variante="primaire">Nouvelle prestation</Button>
          <Button variante="valide" taille="grand">
            Encaisser 1 750 F
          </Button>
          <Button variante="danger">Annuler la ligne</Button>
          <Button variante="secondaire">Plus tard</Button>
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-xl">Champs</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Input label="Téléphone" placeholder="+237 6XX XXX XXX" inputMode="tel" />
          <Input
            label="Mot de passe"
            type="password"
            placeholder="••••••••"
            erreur="Exemple d'erreur affichée"
          />
        </div>
      </section>
    </div>
  );
}
