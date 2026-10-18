"""Tests du journal d'audit (RG-16)."""
from rest_framework import status
from rest_framework.test import APITestCase

from apps.caisse.models import SessionCaisse
from apps.catalogue.models import Service
from apps.comptes.models import Role, Utilisateur
from apps.secretariats.models import Secretariat


class AuditTests(APITestCase):
    def setUp(self):
        self.proprio = Utilisateur.objects.create_user(
            telephone="+237600000500", nom="Patron", password="MotDePasseP1", role=Role.PROPRIETAIRE,
        )
        self.sec = Secretariat.objects.create(nom="S", code="AUD01", proprietaire=self.proprio)
        self.proprio.secretariat = self.sec
        self.proprio.save(update_fields=["secretariat"])
        self.service = Service.objects.create(secretariat=self.sec, nom="Photocopie", prix=25)

    def test_changement_prix_journalise_avant_apres(self):
        self.client.force_authenticate(self.proprio)
        self.client.patch(f"/api/v1/services/{self.service.id}/", {"prix": 30}, format="json")
        r = self.client.get("/api/v1/audit/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        entrees = [e for e in r.data if e["action"] == "prix_modifie"]
        self.assertEqual(len(entrees), 1)
        self.assertEqual(entrees[0]["valeurs_avant"]["prix"], 25)
        self.assertEqual(entrees[0]["valeurs_apres"]["prix"], 30)
        self.assertEqual(entrees[0]["auteur_nom"], "Patron")

    def test_prix_inchange_pas_de_trace(self):
        self.client.force_authenticate(self.proprio)
        self.client.patch(f"/api/v1/services/{self.service.id}/", {"prix": 25}, format="json")
        r = self.client.get("/api/v1/audit/")
        self.assertEqual(len([e for e in r.data if e["action"] == "prix_modifie"]), 0)

    def test_ajustement_stock_journalise(self):
        from apps.stocks.models import Consommable
        conso = Consommable.objects.create(
            secretariat=self.sec, nom="Papier", unite_mesure="feuille",
            prix_achat=7, qte_stock=100, seuil_alerte=10,
        )
        self.client.force_authenticate(self.proprio)
        self.client.post(
            f"/api/v1/consommables/{conso.id}/ajustement/",
            {"quantite_delta": -5, "motif": "casse"}, format="json",
        )
        r = self.client.get("/api/v1/audit/?action=stock_ajuste")
        self.assertEqual(len(r.data), 1)
        self.assertIn("casse", r.data[0]["valeurs_apres"]["motif"])

    def test_audit_reserve_au_proprietaire(self):
        gerant = Utilisateur.objects.create_user(
            telephone="+237600000501", nom="G", password="MotDePasseG1",
            role=Role.GERANT, secretariat=self.sec,
        )
        self.client.force_authenticate(gerant)
        self.assertEqual(
            self.client.get("/api/v1/audit/").status_code, status.HTTP_403_FORBIDDEN,
        )

    def test_isolation_journal(self):
        autre = Utilisateur.objects.create_user(
            telephone="+237600000502", nom="X", password="MotDePasseX1", role=Role.PROPRIETAIRE,
        )
        sec_b = Secretariat.objects.create(nom="B", code="AUD02", proprietaire=autre)
        svc_b = Service.objects.create(secretariat=sec_b, nom="X", prix=10)
        autre.secretariat = sec_b
        autre.save(update_fields=["secretariat"])
        # Autre proprio change un prix dans son secrétariat
        self.client.force_authenticate(autre)
        self.client.patch(f"/api/v1/services/{svc_b.id}/", {"prix": 99}, format="json")
        # Le premier proprio ne voit rien de B
        self.client.force_authenticate(self.proprio)
        r = self.client.get("/api/v1/audit/")
        self.assertEqual(len(r.data), 0)
