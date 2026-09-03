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

    def test_depense_et_cloture_avec_ecart(self):
        from apps.catalogue.models import Service
        from apps.ventes.services import enregistrer_prestation

        # Le propriétaire peut enregistrer une dépense (matrice de permissions).
        self.client.force_authenticate(self.proprio)
        session = self.client.post(
            "/api/v1/sessions-caisse/", {"fond_initial": 10000}, format="json"
        ).data
        session_obj = SessionCaisse.objects.get(id=session["id"])

        # Une vente espèces de 625
        service = Service.objects.create(secretariat=self.sec, nom="Photocopie", prix=25)
        enregistrer_prestation(
            session=session_obj,
            lignes_saisie=[{"service": service.id, "quantite": 25}],
            mode_paiement="especes", montant_recu=1000, auteur=self.proprio,
        )
        # Une dépense de 2000
        rd = self.client.post(
            "/api/v1/depenses/",
            {"categorie": "transport", "montant": 2000, "description": "Carburant"},
            format="json",
        )
        self.assertEqual(rd.status_code, status.HTTP_201_CREATED)

        # Théorique = 10000 + 625 - 2000 = 8625
        # Clôture avec écart sans commentaire → 400 (RG-12)
        r1 = self.client.post(
            f"/api/v1/sessions-caisse/{session['id']}/cloturer/",
            {"montant_compte": 8600}, format="json",
        )
        self.assertEqual(r1.status_code, status.HTTP_400_BAD_REQUEST)

        # Avec commentaire → OK, écart = 8600 - 8625 = -25
        r2 = self.client.post(
            f"/api/v1/sessions-caisse/{session['id']}/cloturer/",
            {"montant_compte": 8600, "commentaire": "Manque 25 F"}, format="json",
        )
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertEqual(r2.data["montant_theorique"], 8625)
        self.assertEqual(r2.data["ecart"], -25)
        self.assertEqual(r2.data["statut"], "cloturee")

    def test_cloture_sans_ecart_sans_commentaire(self):
        self.client.force_authenticate(self.employe)
        session = self.client.post(
            "/api/v1/sessions-caisse/", {"fond_initial": 5000}, format="json"
        ).data
        # Théorique = 5000 (aucune vente ni dépense) ; compté 5000 → écart 0
        r = self.client.post(
            f"/api/v1/sessions-caisse/{session['id']}/cloturer/",
            {"montant_compte": 5000}, format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["ecart"], 0)

    def test_double_cloture_refusee(self):
        self.client.force_authenticate(self.employe)
        session = self.client.post(
            "/api/v1/sessions-caisse/", {"fond_initial": 5000}, format="json"
        ).data
        self.client.post(
            f"/api/v1/sessions-caisse/{session['id']}/cloturer/",
            {"montant_compte": 5000}, format="json",
        )
        r = self.client.post(
            f"/api/v1/sessions-caisse/{session['id']}/cloturer/",
            {"montant_compte": 5000}, format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_employe_ne_peut_pas_creer_depense(self):
        # Un employé ne peut pas enregistrer une dépense (matrice : propriétaire/gérant).
        self.client.force_authenticate(self.employe)
        self.client.post("/api/v1/sessions-caisse/", {"fond_initial": 5000}, format="json")
        r = self.client.post(
            "/api/v1/depenses/", {"categorie": "autre", "montant": 500}, format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

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
