import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-papier p-6 text-center">
      <p className="font-display text-5xl text-cyan">404</p>
      <h1 className="text-xl text-encre">Page introuvable</h1>
      <p className="max-w-sm text-encre-douce">
        Cette page n'existe pas ou a été déplacée. Revenez à la caisse pour continuer votre travail.
      </p>
      <Link
        to="/"
        className="mt-2 inline-flex h-11 items-center rounded-xl bg-cyan px-5 font-medium text-white"
      >
        Retour à la caisse
      </Link>
    </div>
  );
}
