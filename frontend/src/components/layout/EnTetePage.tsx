import type { ReactNode } from "react";

export function EnTetePage({
  titre,
  sousTitre,
  children,
}: {
  titre: string;
  sousTitre?: string;
  children?: ReactNode;
}) {
  return (
    <div className="mb-6">
      <h1 className="text-2xl">{titre}</h1>
      {sousTitre && <p className="text-encre-douce">{sousTitre}</p>}
      {children}
    </div>
  );
}

export function EtatVide({ message }: { message: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-papier-creux bg-papier-surface p-10 text-center text-encre-pale">
      {message}
    </div>
  );
}
