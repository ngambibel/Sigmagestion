import type { ReactNode } from "react";
import { useEffect } from "react";

interface ModalProps {
  ouvert: boolean;
  titre: string;
  onFermer: () => void;
  children: ReactNode;
}

export function Modal({ ouvert, titre, onFermer, children }: ModalProps) {
  useEffect(() => {
    if (!ouvert) return;
    const surEchap = (e: KeyboardEvent) => e.key === "Escape" && onFermer();
    window.addEventListener("keydown", surEchap);
    return () => window.removeEventListener("keydown", surEchap);
  }, [ouvert, onFermer]);

  if (!ouvert) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-encre/40 p-0 sm:items-center sm:p-4"
      onClick={onFermer}
    >
      <div
        className="w-full max-w-md rounded-t-2xl bg-papier-surface p-5 shadow-lg sm:rounded-2xl"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={titre}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl">{titre}</h2>
          <button onClick={onFermer} className="rounded-lg p-1 text-encre-pale" aria-label="Fermer">
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
