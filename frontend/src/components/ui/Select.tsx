import { forwardRef, useId } from "react";
import type { SelectHTMLAttributes } from "react";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: { valeur: string; libelle: string }[];
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, options, id, className = "", ...props }, ref) => {
    const autoId = useId();
    const champId = id ?? autoId;
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label htmlFor={champId} className="text-sm text-encre-douce">
            {label}
          </label>
        )}
        <select
          ref={ref}
          id={champId}
          className={[
            "h-11 rounded-xl border border-papier-creux bg-papier-surface px-3 text-base text-encre",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan",
            className,
          ].join(" ")}
          {...props}
        >
          {options.map((o) => (
            <option key={o.valeur} value={o.valeur}>
              {o.libelle}
            </option>
          ))}
        </select>
      </div>
    );
  },
);
Select.displayName = "Select";
