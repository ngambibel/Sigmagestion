import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "./lib/queryClient";
import App from "./App.tsx";
import { ErrorBoundary } from "./components/ErrorBoundary";
import "./index.css";
import { registerSW } from "virtual:pwa-register";
import { appliquerTheme, useThemeStore } from "./stores/theme";

// Enregistre le service worker (précache + push) ; met à jour automatiquement.
registerSW({ immediate: true });

// Applique le thème choisi (persisté) au démarrage, et suit l'OS en mode « système ».
appliquerTheme(useThemeStore.getState().theme);
window
  .matchMedia("(prefers-color-scheme: dark)")
  .addEventListener("change", () => {
    if (useThemeStore.getState().theme === "systeme") appliquerTheme("systeme");
  });

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  </StrictMode>,
);
