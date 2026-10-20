import { test, expect, type Page } from "@playwright/test";

/**
 * Parcours critiques §15.2 au niveau navigateur.
 * Requiert le compte de démonstration Agale (propriétaire) :
 *   +237698900898 / Sigma2026!  (défini via E2E_TEL / E2E_MDP si besoin)
 * et les serveurs backend + frontend lancés.
 */
const TEL = process.env.E2E_TEL ?? "+237698900898";
const MDP = process.env.E2E_MDP ?? "Sigma2026!";

async function connexion(page: Page) {
  await page.goto("/connexion");
  await page.getByLabel("Téléphone").fill(TEL);
  await page.getByLabel("Mot de passe").fill(MDP);
  await page.getByRole("button", { name: "Se connecter" }).click();
  await expect(page.getByRole("heading", { name: "Caisse" })).toBeVisible();
}

async function assurerSession(page: Page) {
  const ouvrir = page.getByRole("button", { name: /Ouvrir la session/ });
  if (await ouvrir.isVisible().catch(() => false)) {
    await page.getByLabel("Fond de caisse (XAF)").fill("10000");
    await ouvrir.click();
  }
  await expect(page.getByText("Caisse ouverte")).toBeVisible();
}

test("Parcours §15.2-2 : vente d'une photocopie, encaissement espèces", async ({ page }) => {
  await connexion(page);
  await assurerSession(page);

  // Ajoute une photocopie au ticket (la tuile porte un aria-label « nom, prix »).
  await page.getByRole("button", { name: /Photocopie/i }).first().click();

  // Le ticket affiche un bouton « Encaisser … F ».
  const boutonTicket = page.getByRole("button", { name: /^Encaisser/ });
  await expect(boutonTicket).toBeEnabled();
  await boutonTicket.click();

  // Dans la fenêtre d'encaissement, le mode Espèces est actif : on valide.
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", { name: /^Encaisser/ }).click();

  // Toast de confirmation.
  await expect(page.getByText(/Encaissé — ticket/)).toBeVisible();
});

test("Parcours §15.2-7 : vente hors ligne puis synchronisation", async ({ page, context }) => {
  await connexion(page);
  await assurerSession(page);

  await context.setOffline(true);
  await expect(page.getByText(/Hors ligne/)).toBeVisible();

  await page.getByRole("button", { name: /Photocopie/i }).first().click();
  await page.getByRole("button", { name: /^Encaisser/ }).click();
  await page.getByRole("dialog").getByRole("button", { name: /^Encaisser/ }).click();

  // Vente mise en file : toast de confirmation + bandeau de synchronisation en attente.
  await expect(page.getByText(/enregistrée hors ligne/)).toBeVisible();
  await expect(page.getByText(/seront envoyées au retour du réseau/)).toBeVisible();

  // Retour du réseau → la file se vide (le bandeau disparaît).
  await context.setOffline(false);
  await expect(page.getByText(/seront envoyées au retour du réseau/)).toBeHidden({ timeout: 15000 });
});
