import { forwardRef } from "react";
import type { ButtonHTMLAttributes } from "react";

type Variante = "primaire" | "secondaire" | "danger" | "valide";
type Taille = "moyen" | "grand";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variante?: Variante;
  taille?: Taille;
}

const styles: Record<Variante, string> = {
  primaire: "bg-cyan text-white hover:bg-cyan/90 focus-visible:ring-cyan",
  secondaire:
    "bg-papier-surface text-encre border border-papier-creux hover:bg-papier-creux focus-visible:ring-encre-pale",
  danger: "bg-magenta text-white hover:bg-magenta/90 focus-visible:ring-magenta",
  valide: "bg-valide text-white hover:bg-valide/90 focus-visible:ring-valide",
};

const tailles: Record<Taille, string> = {
  moyen: "h-11 px-4 text-base",
  grand: "h-14 px-6 text-lg",
};

/**
 * Bouton conforme à la direction artistique SigmaGestion.
 * Cible tactile ≥ 44 px (moyen) / 56 px (grand).
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variante = "primaire", taille = "moyen", className = "", ...props }, ref) => (
    <button
      ref={ref}
      className={[
        "inline-flex items-center justify-center gap-2 rounded-xl font-medium",
        "transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
        "disabled:opacity-50 disabled:pointer-events-none",
        styles[variante],
        tailles[taille],
        className,
      ].join(" ")}
      {...props}
    />
  ),
);
Button.displayName = "Button";
