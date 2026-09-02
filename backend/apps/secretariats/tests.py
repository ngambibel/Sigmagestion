"""Tests d'isolation multi-locataire (le point de sécurité critique)."""
from rest_framework import status
from rest_framework.test import APITestCase

from apps.comptes.models import Role, Utilisateur
from apps.secretariats.models import Secretariat


class IsolationSecretariatTests(APITestCase):
    """Un secrétariat ne doit jamais voir les données d'un autre."""

    def setUp(self):
        # Propriétaire A + son secrétariat
        self.proprio_a = Utilisateur.objects.create_user(
            telephone="+237600000001", nom="Proprio A",
            password="MotDePasseA1", role=Role.PROPRIETAIRE,
        )
        self.sec_a = Secretariat.objects.create(
            nom="Secrétariat A", code="SECA01", proprietaire=self.proprio_a,
        )
        self.proprio_a.secretariat = self.sec_a
        self.proprio_a.save(update_fields=["secretariat"])

        # Propriétaire B + son secrétariat
        self.proprio_b = Utilisateur.objects.create_user(
            telephone="+237600000002", nom="Proprio B",
            password="MotDePasseB1", role=Role.PROPRIETAIRE,
        )
        self.sec_b = Secretariat.objects.create(
            nom="Secrétariat B", code="SECB01", proprietaire=self.proprio_b,
        )
        self.proprio_b.secretariat = self.sec_b
        self.proprio_b.save(update_fields=["secretariat"])

    def _connecter(self, utilisateur):
        self.client.force_authenticate(user=utilisateur)

    def test_liste_ne_montre_que_ses_secretariats(self):
        self._connecter(self.proprio_a)
        reponse = self.client.get("/api/v1/secretariats/")
        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        ids = {s["id"] for s in reponse.data}
        self.assertEqual(ids, {self.sec_a.id})
        self.assertNotIn(self.sec_b.id, ids)

    def test_acces_detail_autre_secretariat_donne_404(self):
        """A ne peut PAS lire le secrétariat de B → 404 (pas 403 : on ne révèle pas l'existence)."""
        self._connecter(self.proprio_a)
        reponse = self.client.get(f"/api/v1/secretariats/{self.sec_b.id}/")
        self.assertEqual(reponse.status_code, status.HTTP_404_NOT_FOUND)

    def test_modification_autre_secretariat_donne_404(self):
        self._connecter(self.proprio_a)
        reponse = self.client.patch(
            f"/api/v1/secretariats/{self.sec_b.id}/", {"ville": "Piratée"}
        )
        self.assertEqual(reponse.status_code, status.HTTP_404_NOT_FOUND)
        self.sec_b.refresh_from_db()
        self.assertNotEqual(self.sec_b.ville, "Piratée")

    def test_creation_rattache_au_proprietaire_et_genere_code(self):
        self._connecter(self.proprio_a)
        reponse = self.client.post(
            "/api/v1/secretariats/",
            {"nom": "Deuxième Boutique", "ville": "Douala"},
        )
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED)
        self.assertEqual(reponse.data["proprietaire"], self.proprio_a.id)
        self.assertTrue(reponse.data["code"])  # code généré automatiquement

    def test_employe_sans_secretariat_ne_voit_rien(self):
        employe = Utilisateur.objects.create_user(
            telephone="+237600000003", nom="Employé Orphelin",
            password="MotDePasseE1", role=Role.EMPLOYE,
        )
        self._connecter(employe)
        reponse = self.client.get("/api/v1/secretariats/")
        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertEqual(list(reponse.data), [])

    def test_employe_ne_peut_pas_creer_de_secretariat(self):
        employe = Utilisateur.objects.create_user(
            telephone="+237600000004", nom="Employé", password="MotDePasseE2",
            role=Role.EMPLOYE, secretariat=self.sec_a,
        )
        self._connecter(employe)
        reponse = self.client.post(
            "/api/v1/secretariats/", {"nom": "Tentative", "ville": "X"}
        )
        self.assertEqual(reponse.status_code, status.HTTP_403_FORBIDDEN)

    def test_acces_anonyme_refuse(self):
        reponse = self.client.get("/api/v1/secretariats/")
        self.assertEqual(reponse.status_code, status.HTTP_401_UNAUTHORIZED)
