const etapes = ["Identité", "Services", "Stock"];

export function Stepper({ courante }: { courante: number }) {
  return (
    <ol className="mb-8 flex items-center gap-2">
      {etapes.map((nom, i) => {
        const numero = i + 1;
        const active = numero === courante;
        const faite = numero < courante;
        return (
          <li key={nom} className="flex flex-1 items-center gap-2">
            <span
              className={[
                "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-medium",
                faite
                  ? "bg-valide text-white"
                  : active
                    ? "bg-cyan text-white"
                    : "bg-papier-creux text-encre-pale",
              ].join(" ")}
            >
              {faite ? "✓" : numero}
            </span>
            <span className={active ? "text-encre" : "text-encre-pale"}>{nom}</span>
            {numero < etapes.length && <span className="h-px flex-1 bg-papier-creux" />}
          </li>
        );
      })}
    </ol>
  );
}
