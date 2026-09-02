import { lazy } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { RequireAuth, RequireOnboarding, RequireRole } from "./app/guards";
import { AppShell } from "./components/layout/AppShell";
import LoginPage from "./pages/auth/LoginPage";
import RegisterPage from "./pages/auth/RegisterPage";
import InstallationPage from "./pages/InstallationPage";

// Pages chargées paresseusement (découpage de code).
const CaissePage = lazy(() => import("./pages/caisse/CaissePage"));
const StockPage = lazy(() => import("./pages/stock/StockPage"));
const BilanPage = lazy(() => import("./pages/bilan/BilanPage"));
const CataloguePage = lazy(() => import("./pages/catalogue/CataloguePage"));
const ParametresPage = lazy(() => import("./pages/parametres/ParametresPage"));

export default function App() {
  return (
    <Routes>
      <Route path="/connexion" element={<LoginPage />} />
      <Route path="/inscription" element={<RegisterPage />} />

      <Route element={<RequireAuth />}>
        <Route path="/installation" element={<InstallationPage />} />

        <Route element={<RequireOnboarding />}>
          <Route element={<AppShell />}>
            <Route index element={<CaissePage />} />
            <Route path="stock" element={<StockPage />} />
            <Route
              path="bilan"
              element={
                <RequireRole roles={["proprietaire", "gerant", "super_admin"]}>
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

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
