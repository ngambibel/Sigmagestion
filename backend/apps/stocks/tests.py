"""Isolation multi-locataire des consommables."""
from rest_framework import status
from rest_framework.test import APITestCase

from apps.comptes.models import Role, Utilisateur
from apps.secretariats.models import Secretariat
from apps.stocks.models import Consommable


class ConsommableIsolationTests(APITestCase):
    def setUp(self):
        self.proprio_a = Utilisateur.objects.create_user(
            telephone="+237600000020", nom="A", password="MotDePasseA1", role=Role.PROPRIETAIRE,
        )
        self.sec_a = Secretariat.objects.create(nom="A", code="AAS01", proprietaire=self.proprio_a)
        self.proprio_a.secretariat = self.sec_a
        self.proprio_a.save(update_fields=["secretariat"])

        self.proprio_b = Utilisateur.objects.create_user(
            telephone="+237600000021", nom="B", password="MotDePasseB1", role=Role.PROPRIETAIRE,
        )
        self.sec_b = Secretariat.objects.create(nom="B", code="BBS01", proprietaire=self.proprio_b)
        self.proprio_b.secretariat = self.sec_b
        self.proprio_b.save(update_fields=["secretariat"])

        self.conso_b = Consommable.objects.create(
            secretariat=self.sec_b, nom="Papier A4 B", unite_mesure="feuille",
            prix_achat=7, qte_stock=500, seuil_alerte=100,
        )

    def test_creation_stock_initial_rattachee(self):
        self.client.force_authenticate(self.proprio_a)
        reponse = self.client.post(
            "/api/v1/consommables/",
            {"nom": "Papier A4", "unite_mesure": "feuille", "prix_achat": 7,
             "qte_stock": 200, "seuil_alerte": 100},
        )
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED)
        conso = Consommable.objects.get(id=reponse.data["id"])
        self.assertEqual(conso.secretariat_id, self.sec_a.id)

    def test_acces_consommable_autre_secretariat_donne_404(self):
        self.client.force_authenticate(self.proprio_a)
        reponse = self.client.get(f"/api/v1/consommables/{self.conso_b.id}/")
        self.assertEqual(reponse.status_code, status.HTTP_404_NOT_FOUND)

    def test_indicateur_sous_seuil(self):
        self.client.force_authenticate(self.proprio_b)
        # 500 > 100 → pas sous seuil
        reponse = self.client.get(f"/api/v1/consommables/{self.conso_b.id}/")
        self.assertFalse(reponse.data["sous_seuil"])
        self.conso_b.qte_stock = 50
        self.conso_b.save()
        reponse = self.client.get(f"/api/v1/consommables/{self.conso_b.id}/")
        self.assertTrue(reponse.data["sous_seuil"])
