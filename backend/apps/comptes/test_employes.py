"""Tests de la gestion des employés (M8) et du changement de mot de passe imposé."""
from rest_framework import status
from rest_framework.test import APITestCase

from apps.caisse.models import SessionCaisse, StatutSession
from apps.comptes.models import Role, Utilisateur
from apps.secretariats.models import Secretariat


class GestionEmployesTests(APITestCase):
    def setUp(self):
        self.proprio = Utilisateur.objects.create_user(
            telephone="+237600000300", nom="Patron", password="MotDePasseP1", role=Role.PROPRIETAIRE,
        )
        self.sec = Secretariat.objects.create(nom="S", code="EMP01", proprietaire=self.proprio)
        self.proprio.secretariat = self.sec
        self.proprio.save(update_fields=["secretariat"])

    def _creer_employe(self, nom="Awa", tel="+237655111222", role="employe"):
        self.client.force_authenticate(self.proprio)
        return self.client.post(
            "/api/v1/employes/", {"nom": nom, "telephone": tel, "role": role}, format="json",
        )

    def test_creation_renvoie_mot_de_passe_provisoire(self):
        r = self._creer_employe()
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertIn("mot_de_passe_provisoire", r.data)
        self.assertTrue(r.data["doit_changer_mdp"])
        employe = Utilisateur.objects.get(telephone="+237655111222")
        self.assertEqual(employe.secretariat_id, self.sec.id)
        self.assertEqual(employe.role, Role.EMPLOYE)

    def test_connexion_puis_changement_impose(self):
        r = self._creer_employe()
        mdp = r.data["mot_de_passe_provisoire"]
        # Connexion avec le provisoire → doit_changer_mdp = true
        self.client.force_authenticate(user=None)
        con = self.client.post(
            "/api/v1/auth/connexion/",
            {"telephone": "+237655111222", "password": mdp}, format="json",
        )
        self.assertEqual(con.status_code, status.HTTP_200_OK)
        self.assertTrue(con.data["doit_changer_mdp"])
        # Changement du mot de passe
        employe = Utilisateur.objects.get(telephone="+237655111222")
        self.client.force_authenticate(employe)
        ch = self.client.post(
            "/api/v1/moi/changer-mot-de-passe/",
            {"nouveau_mot_de_passe": "NouveauMdp2026"}, format="json",
        )
        self.assertEqual(ch.status_code, status.HTTP_200_OK)
        employe.refresh_from_db()
        self.assertFalse(employe.doit_changer_mdp)
        self.assertTrue(employe.check_password("NouveauMdp2026"))

    def test_mot_de_passe_trop_faible_refuse(self):
        r = self._creer_employe()
        employe = Utilisateur.objects.get(telephone="+237655111222")
        self.client.force_authenticate(employe)
        ch = self.client.post(
            "/api/v1/moi/changer-mot-de-passe/",
            {"nouveau_mot_de_passe": "123"}, format="json",
        )
        self.assertEqual(ch.status_code, status.HTTP_400_BAD_REQUEST)

    def test_desactivation_clot_la_session_et_bloque_connexion(self):
        r = self._creer_employe()
        mdp = r.data["mot_de_passe_provisoire"]
        employe = Utilisateur.objects.get(telephone="+237655111222")
        session = SessionCaisse.objects.create(
            secretariat=self.sec, employe=employe, fond_initial=1000,
        )
        self.client.force_authenticate(self.proprio)
        rd = self.client.post(f"/api/v1/employes/{employe.id}/desactiver/")
        self.assertEqual(rd.status_code, status.HTTP_200_OK)
        self.assertFalse(rd.data["is_active"])
        session.refresh_from_db()
        self.assertEqual(session.statut, StatutSession.CLOTUREE)
        # Connexion désormais refusée
        self.client.force_authenticate(user=None)
        con = self.client.post(
            "/api/v1/auth/connexion/",
            {"telephone": "+237655111222", "password": mdp}, format="json",
        )
        self.assertEqual(con.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_fiche_activite(self):
        r = self._creer_employe()
        employe = Utilisateur.objects.get(telephone="+237655111222")
        self.client.force_authenticate(self.proprio)
        a = self.client.get(f"/api/v1/employes/{employe.id}/activite/")
        self.assertEqual(a.status_code, status.HTTP_200_OK)
        self.assertEqual(a.data["ca_genere"], 0)
        self.assertIn("nb_sessions", a.data)

    def test_isolation_entre_secretariats(self):
        autre = Utilisateur.objects.create_user(
            telephone="+237600000301", nom="Autre", password="MotDePasseX1", role=Role.PROPRIETAIRE,
        )
        sec_b = Secretariat.objects.create(nom="B", code="EMP02", proprietaire=autre)
        Utilisateur.objects.create_user(
            telephone="+237655999888", nom="EmpB", password="x", role=Role.EMPLOYE, secretariat=sec_b,
        )
        self.client.force_authenticate(self.proprio)
        liste = self.client.get("/api/v1/employes/").data
        telephones = {e["telephone"] for e in liste}
        self.assertNotIn("+237655999888", telephones)

    def test_employe_ne_peut_pas_lister(self):
        employe = Utilisateur.objects.create_user(
            telephone="+237655111333", nom="E", password="x", role=Role.EMPLOYE, secretariat=self.sec,
        )
        self.client.force_authenticate(employe)
        r = self.client.get("/api/v1/employes/")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
