import { forwardRef, useId } from "react";
import type { InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  erreur?: string;
}

/**
 * Champ de saisie avec libellé. Corps 16 px minimum (évite le zoom iOS).
 */
export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, erreur, className = "", id, ...props }, ref) => {
    const autoId = useId();
    const champId = id ?? autoId;
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label htmlFor={champId} className="text-sm text-encre-douce">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={champId}
          className={[
            "h-11 rounded-xl border bg-papier-surface px-3 text-base text-encre",
            "placeholder:text-encre-pale focus-visible:outline-none focus-visible:ring-2",
            erreur
              ? "border-magenta focus-visible:ring-magenta"
              : "border-papier-creux focus-visible:ring-cyan",
            className,
          ].join(" ")}
          aria-invalid={erreur ? true : undefined}
          {...props}
        />
        {erreur && <span className="text-sm text-magenta">{erreur}</span>}
      </div>
    );
  },
);
Input.displayName = "Input";
