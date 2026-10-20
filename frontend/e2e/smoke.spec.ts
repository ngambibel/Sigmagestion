import { test, expect } from "@playwright/test";

test.describe("Smoke (sans authentification)", () => {
  test("la page de connexion s'affiche", async ({ page }) => {
    await page.goto("/connexion");
    await expect(page.getByRole("heading", { name: "SigmaGestion" })).toBeVisible();
    await expect(page.getByLabel("Téléphone")).toBeVisible();
    await expect(page.getByLabel("Mot de passe")).toBeVisible();
    await expect(page.getByRole("button", { name: "Se connecter" })).toBeVisible();
  });

  test("une route inconnue affiche la page 404", async ({ page }) => {
    await page.goto("/cette-page-nexiste-pas");
    await expect(page.getByText("Page introuvable")).toBeVisible();
    await expect(page.getByRole("link", { name: /Retour à la caisse/ })).toBeVisible();
  });
});
