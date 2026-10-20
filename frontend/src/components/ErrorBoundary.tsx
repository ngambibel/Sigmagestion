import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}
interface State {
  erreur: Error | null;
}

/** Capture les erreurs de rendu pour éviter l'écran blanc : message clair + recharger. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { erreur: null };

  static getDerivedStateFromError(erreur: Error): State {
    return { erreur };
  }

  componentDidCatch(erreur: Error, info: ErrorInfo) {
    // En production, on brancherait Sentry ici.
    console.error("Erreur applicative :", erreur, info.componentStack);
  }

  render() {
    if (this.state.erreur) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-papier p-6 text-center">
          <p className="text-4xl" aria-hidden>
            ⚠️
          </p>
          <h1 className="text-xl text-encre">Une erreur est survenue</h1>
          <p className="max-w-sm text-encre-douce">
            L'application a rencontré un problème inattendu. Vos ventes déjà enregistrées sont
            conservées. Rechargez pour continuer.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-2 inline-flex h-11 items-center rounded-xl bg-cyan px-5 font-medium text-white"
          >
            Recharger l'application
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
