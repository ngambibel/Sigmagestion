"""Tests des sessions de caisse."""
from rest_framework import status
from rest_framework.test import APITestCase

from apps.comptes.models import Role, Utilisateur
from apps.secretariats.models import Secretariat

from .models import SessionCaisse, StatutSession


class SessionCaisseTests(APITestCase):
    def setUp(self):
        self.proprio = Utilisateur.objects.create_user(
            telephone="+237600000060", nom="P", password="MotDePasseP1", role=Role.PROPRIETAIRE,
        )
        self.sec = Secretariat.objects.create(nom="S", code="SCA01", proprietaire=self.proprio)
        self.proprio.secretariat = self.sec
        self.proprio.save(update_fields=["secretariat"])
        self.employe = Utilisateur.objects.create_user(
            telephone="+237600000061", nom="E", password="MotDePasseE1",
            role=Role.EMPLOYE, secretariat=self.sec,
        )

    def test_ouverture_session(self):
        self.client.force_authenticate(self.employe)
        reponse = self.client.post("/api/v1/sessions-caisse/", {"fond_initial": 10000}, format="json")
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED)
        self.assertEqual(reponse.data["fond_initial"], 10000)
        self.assertEqual(reponse.data["statut"], StatutSession.OUVERTE)
        self.assertEqual(reponse.data["employe"], self.employe.id)

    def test_rg11_une_seule_session_ouverte(self):
        self.client.force_authenticate(self.employe)
        self.client.post("/api/v1/sessions-caisse/", {"fond_initial": 10000}, format="json")
        reponse = self.client.post("/api/v1/sessions-caisse/", {"fond_initial": 5000}, format="json")
        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SessionCaisse.objects.filter(employe=self.employe).count(), 1)

    def test_session_active(self):
        self.client.force_authenticate(self.employe)
        # Aucune session → null
        self.assertIsNone(self.client.get("/api/v1/sessions-caisse/active/").data)
        # Après ouverture → renvoie la session
        self.client.post("/api/v1/sessions-caisse/", {"fond_initial": 10000}, format="json")
        active = self.client.get("/api/v1/sessions-caisse/active/").data
        self.assertIsNotNone(active)
        self.assertEqual(active["fond_initial"], 10000)

    def test_employe_ne_voit_que_ses_sessions(self):
        # Session d'un autre employé
        autre = Utilisateur.objects.create_user(
            telephone="+237600000062", nom="E2", password="MotDePasseE2",
            role=Role.EMPLOYE, secretariat=self.sec,
        )
        SessionCaisse.objects.create(secretariat=self.sec, employe=autre, fond_initial=3000)

        self.client.force_authenticate(self.employe)
        self.client.post("/api/v1/sessions-caisse/", {"fond_initial": 10000}, format="json")
        liste = self.client.get("/api/v1/sessions-caisse/").data
        resultats = liste["results"] if isinstance(liste, dict) else liste
        self.assertEqual(len(resultats), 1)
        self.assertEqual(resultats[0]["employe"], self.employe.id)

    def test_isolation_multi_locataire(self):
        autre_proprio = Utilisateur.objects.create_user(
            telephone="+237600000063", nom="X", password="MotDePasseX1", role=Role.PROPRIETAIRE,
        )
        sec_b = Secretariat.objects.create(nom="B", code="SCB01", proprietaire=autre_proprio)
        autre_proprio.secretariat = sec_b
        autre_proprio.save(update_fields=["secretariat"])
        SessionCaisse.objects.create(secretariat=self.sec, employe=self.employe, fond_initial=1000)

        self.client.force_authenticate(autre_proprio)
        liste = self.client.get("/api/v1/sessions-caisse/").data
        resultats = liste["results"] if isinstance(liste, dict) else liste
        self.assertEqual(len(resultats), 0)
