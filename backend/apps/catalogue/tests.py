"""Isolation multi-locataire des services + accès au catalogue de démarrage."""
from rest_framework import status
from rest_framework.test import APITestCase

from apps.comptes.models import Role, Utilisateur
from apps.catalogue.models import Service
from apps.secretariats.models import Secretariat


class ServiceIsolationTests(APITestCase):
    def setUp(self):
        self.proprio_a = Utilisateur.objects.create_user(
            telephone="+237600000010", nom="A", password="MotDePasseA1", role=Role.PROPRIETAIRE,
        )
        self.sec_a = Secretariat.objects.create(nom="A", code="AAA01", proprietaire=self.proprio_a)
        self.proprio_a.secretariat = self.sec_a
        self.proprio_a.save(update_fields=["secretariat"])

        self.proprio_b = Utilisateur.objects.create_user(
            telephone="+237600000011", nom="B", password="MotDePasseB1", role=Role.PROPRIETAIRE,
        )
        self.sec_b = Secretariat.objects.create(nom="B", code="BBB01", proprietaire=self.proprio_b)
        self.proprio_b.secretariat = self.sec_b
        self.proprio_b.save(update_fields=["secretariat"])

        self.service_b = Service.objects.create(
            secretariat=self.sec_b, nom="Impression B", prix=50,
        )

    def test_creation_service_rattachee_au_secretariat_actif(self):
        self.client.force_authenticate(self.proprio_a)
        reponse = self.client.post(
            "/api/v1/services/", {"nom": "Photocopie", "prix": 25, "unite_facturation": "page"}
        )
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED)
        service = Service.objects.get(id=reponse.data["id"])
        self.assertEqual(service.secretariat_id, self.sec_a.id)

    def test_liste_ne_montre_que_son_secretariat(self):
        self.client.force_authenticate(self.proprio_a)
        Service.objects.create(secretariat=self.sec_a, nom="Scan A", prix=100)
        reponse = self.client.get("/api/v1/services/")
        noms = {s["nom"] for s in reponse.data}
        self.assertIn("Scan A", noms)
        self.assertNotIn("Impression B", noms)

    def test_acces_service_autre_secretariat_donne_404(self):
        self.client.force_authenticate(self.proprio_a)
        reponse = self.client.get(f"/api/v1/services/{self.service_b.id}/")
        self.assertEqual(reponse.status_code, status.HTTP_404_NOT_FOUND)

    def test_modeles_onboarding_disponibles(self):
        self.client.force_authenticate(self.proprio_a)
        reponse = self.client.get("/api/v1/onboarding/modeles/")
        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertTrue(len(reponse.data["services"]) > 0)
        self.assertTrue(len(reponse.data["consommables"]) > 0)

    def test_employe_ne_peut_pas_creer_service(self):
        employe = Utilisateur.objects.create_user(
            telephone="+237600000012", nom="Emp", password="MotDePasseE1",
            role=Role.EMPLOYE, secretariat=self.sec_a,
        )
        self.client.force_authenticate(employe)
        reponse = self.client.post("/api/v1/services/", {"nom": "X", "prix": 10})
        self.assertEqual(reponse.status_code, status.HTTP_403_FORBIDDEN)
