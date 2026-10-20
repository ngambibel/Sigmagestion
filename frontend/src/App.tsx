import { lazy } from "react";
import { Route, Routes } from "react-router-dom";
import {
  RequireAuth,
  RequireMotDePasseAJour,
  RequireOnboarding,
  RequireRole,
} from "./app/guards";
import { AppShell } from "./components/layout/AppShell";
import LoginPage from "./pages/auth/LoginPage";
import RegisterPage from "./pages/auth/RegisterPage";
import ChangerMotDePassePage from "./pages/auth/ChangerMotDePassePage";
import InstallationPage from "./pages/InstallationPage";
import NotFoundPage from "./pages/erreur/NotFoundPage";

// Pages chargées paresseusement (découpage de code).
const CaissePage = lazy(() => import("./pages/caisse/CaissePage"));
const StockPage = lazy(() => import("./pages/stock/StockPage"));
const BilanPage = lazy(() => import("./pages/bilan/BilanPage"));
const MouvementsPage = lazy(() => import("./pages/stock/MouvementsPage"));
const VentesPage = lazy(() => import("./pages/ventes/VentesPage"));
const CataloguePage = lazy(() => import("./pages/catalogue/CataloguePage"));
const RapportsPage = lazy(() => import("./pages/rapports/RapportsPage"));
const EmployesPage = lazy(() => import("./pages/employes/EmployesPage"));
const ClientsPage = lazy(() => import("./pages/clients/ClientsPage"));
const AuditPage = lazy(() => import("./pages/audit/AuditPage"));
const ParametresPage = lazy(() => import("./pages/parametres/ParametresPage"));

export default function App() {
  return (
    <Routes>
      <Route path="/connexion" element={<LoginPage />} />
      <Route path="/inscription" element={<RegisterPage />} />

      <Route element={<RequireAuth />}>
        <Route path="/changer-mot-de-passe" element={<ChangerMotDePassePage />} />

        <Route element={<RequireMotDePasseAJour />}>
          <Route path="/installation" element={<InstallationPage />} />

          <Route element={<RequireOnboarding />}>
            <Route element={<AppShell />}>
            <Route index element={<CaissePage />} />
            <Route path="stock" element={<StockPage />} />
            <Route
              path="ventes"
              element={
                <RequireRole roles={["proprietaire", "gerant", "super_admin"]}>
                  <VentesPage />
                </RequireRole>
              }
            />
            <Route
              path="mouvements"
              element={
                <RequireRole roles={["proprietaire", "gerant", "super_admin"]}>
                  <MouvementsPage />
                </RequireRole>
              }
            />
            <Route
              path="bilan"
              element={
                <RequireRole roles={["proprietaire", "gerant", "super_admin", "employe"]}>
                  <BilanPage />
                </RequireRole>
              }
            />
            <Route
              path="catalogue"
              element={
                <RequireRole roles={["proprietaire", "super_admin"]}>
                  <CataloguePage />
                </RequireRole>
              }
            />
            <Route
              path="rapports"
              element={
                <RequireRole roles={["proprietaire", "super_admin"]}>
                  <RapportsPage />
                </RequireRole>
              }
            />
            <Route
              path="employes"
              element={
                <RequireRole roles={["proprietaire", "super_admin"]}>
                  <EmployesPage />
                </RequireRole>
              }
            />
            <Route
              path="clients"
              element={
                <RequireRole roles={["proprietaire", "gerant", "super_admin"]}>
                  <ClientsPage />
                </RequireRole>
              }
            />
            <Route
              path="audit"
              element={
                <RequireRole roles={["proprietaire", "super_admin"]}>
                  <AuditPage />
                </RequireRole>
              }
            />
            <Route
              path="parametres"
              element={
                <RequireRole roles={["proprietaire", "super_admin"]}>
                  <ParametresPage />
                </RequireRole>
              }
            />
            </Route>
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
