"""Tests du centre de notifications et des réglages fins (M6.5, M6.6)."""
from rest_framework import status
from rest_framework.test import APITestCase

from apps.comptes.models import Role, Utilisateur
from apps.secretariats.models import ParametreNotification, Secretariat

from .models import Notification, TypeNotification
from .tasks import notifier_utilisateur


class CentreNotificationsTests(APITestCase):
    def setUp(self):
        self.proprio = Utilisateur.objects.create_user(
            telephone="+237600000100", nom="Awa", password="MotDePasseP1", role=Role.PROPRIETAIRE,
        )
        self.sec = Secretariat.objects.create(
            nom="S", code="SCE01", proprietaire=self.proprio,
        )
        self.proprio.secretariat = self.sec
        self.proprio.save(update_fields=["secretariat"])
        # Un autre utilisateur, pour vérifier le cloisonnement.
        self.autre = Utilisateur.objects.create_user(
            telephone="+237600000101", nom="Bob", password="MotDePasseB1", role=Role.PROPRIETAIRE,
        )
        for i in range(3):
            Notification.objects.create(
                secretariat=self.sec, utilisateur=self.proprio,
                type=TypeNotification.AUTRE, titre=f"N{i}", corps="…",
            )
        Notification.objects.create(
            secretariat=self.sec, utilisateur=self.autre,
            type=TypeNotification.AUTRE, titre="pour Bob", corps="…",
        )

    def test_liste_cloisonnee_et_compteur(self):
        self.client.force_authenticate(self.proprio)
        reponse = self.client.get("/api/v1/notifications/")
        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertEqual(reponse.data["non_lues"], 3)
        titres = {n["titre"] for n in reponse.data["resultats"]}
        self.assertNotIn("pour Bob", titres)

    def test_tout_lire(self):
        self.client.force_authenticate(self.proprio)
        reponse = self.client.post("/api/v1/notifications/tout-lire/")
        self.assertEqual(reponse.data["marquees"], 3)
        self.assertEqual(
            Notification.objects.filter(utilisateur=self.proprio, lu=False).count(), 0,
        )
        self.assertEqual(self.client.get("/api/v1/notifications/compteur/").data["non_lues"], 0)

    def test_archiver_retire_du_centre(self):
        self.client.force_authenticate(self.proprio)
        notif = Notification.objects.filter(utilisateur=self.proprio).first()
        self.client.post(f"/api/v1/notifications/{notif.id}/archiver/")
        reponse = self.client.get("/api/v1/notifications/")
        ids = {n["id"] for n in reponse.data["resultats"]}
        self.assertNotIn(notif.id, ids)
        # Mais consultable via ?archivees=seules
        archivees = self.client.get("/api/v1/notifications/?archivees=seules")
        self.assertIn(notif.id, {n["id"] for n in archivees.data["resultats"]})

    def test_un_utilisateur_ne_lit_pas_les_notifs_d_un_autre(self):
        self.client.force_authenticate(self.proprio)
        notif_bob = Notification.objects.get(utilisateur=self.autre)
        reponse = self.client.post(f"/api/v1/notifications/{notif_bob.id}/lire/")
        self.assertEqual(reponse.status_code, status.HTTP_404_NOT_FOUND)


class ReglagesFinsTests(APITestCase):
    def setUp(self):
        self.proprio = Utilisateur.objects.create_user(
            telephone="+237600000102", nom="Awa", password="MotDePasseP1", role=Role.PROPRIETAIRE,
        )
        self.sec = Secretariat.objects.create(nom="S", code="SCE02", proprietaire=self.proprio)
        self.param = ParametreNotification.objects.create(secretariat=self.sec)

    def test_type_desactive_bloque_tout(self):
        self.param.alerte_stock_on = False
        self.param.save(update_fields=["alerte_stock_on"])
        notifier_utilisateur(
            self.proprio, self.sec, type=TypeNotification.STOCK_FAIBLE,
            titre="Stock", corps="…",
        )
        self.assertEqual(Notification.objects.count(), 0)

    def test_ne_pas_deranger_persiste_sans_push(self):
        self.param.ne_pas_deranger = True
        self.param.save(update_fields=["ne_pas_deranger"])
        notifier_utilisateur(
            self.proprio, self.sec, type=TypeNotification.BILAN_CA, titre="Bilan", corps="…",
        )
        # Persistée dans le centre…
        self.assertEqual(Notification.objects.count(), 1)

    def test_forcer_court_circuite_les_reglages(self):
        self.param.ne_pas_deranger = True
        self.param.alerte_stock_on = False
        self.param.save()
        notifier_utilisateur(
            self.proprio, self.sec, type=TypeNotification.STOCK_FAIBLE,
            titre="Test", corps="…", forcer=True,
        )
        self.assertEqual(Notification.objects.count(), 1)

    def test_patch_parametres_fins(self):
        self.proprio.secretariat = self.sec
        self.proprio.save(update_fields=["secretariat"])
        self.client.force_authenticate(self.proprio)
        reponse = self.client.patch(
            f"/api/v1/secretariats/{self.sec.id}/parametres-notification/",
            {"ne_pas_deranger": True, "alerte_session_on": True}, format="json",
        )
        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.param.refresh_from_db()
        self.assertTrue(self.param.ne_pas_deranger)
        self.assertTrue(self.param.alerte_session_on)
