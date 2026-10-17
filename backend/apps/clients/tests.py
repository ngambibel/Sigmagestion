"""Tests des clients et créances (M9, RG-13)."""
from rest_framework import status
from rest_framework.test import APITestCase

from apps.caisse.models import SessionCaisse
from apps.catalogue.models import Service
from apps.clients.models import Client
from apps.comptes.models import Role, Utilisateur
from apps.secretariats.models import Secretariat
from apps.ventes.services import annuler_prestation, enregistrer_prestation


class CreancesTests(APITestCase):
    def setUp(self):
        self.proprio = Utilisateur.objects.create_user(
            telephone="+237600000400", nom="Patron", password="MotDePasseP1", role=Role.PROPRIETAIRE,
        )
        self.sec = Secretariat.objects.create(nom="S", code="CLI01", proprietaire=self.proprio)
        self.proprio.secretariat = self.sec
        self.proprio.save(update_fields=["secretariat"])
        self.service = Service.objects.create(secretariat=self.sec, nom="Saisie", prix=100)
        self.session = SessionCaisse.objects.create(
            secretariat=self.sec, employe=self.proprio, fond_initial=0,
        )

    def _vente_credit(self, client, qte=5):
        return enregistrer_prestation(
            session=self.session,
            lignes_saisie=[{"service": self.service.id, "quantite": qte}],
            mode_paiement="credit", client=client, auteur=self.proprio,
        )

    def test_vente_credit_incremente_encours(self):
        cl = Client.objects.create(secretariat=self.sec, nom="Awa")
        self._vente_credit(cl, qte=5)  # 5 × 100 = 500
        cl.refresh_from_db()
        self.assertEqual(cl.encours, 500)

    def test_reglement_partiel_diminue_encours(self):
        cl = Client.objects.create(secretariat=self.sec, nom="Awa")
        self._vente_credit(cl, qte=5)  # encours 500
        self.client.force_authenticate(self.proprio)
        r = self.client.post(f"/api/v1/clients/{cl.id}/reglement/", {"montant": 200}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["client"]["encours"], 300)
        cl.refresh_from_db()
        self.assertEqual(cl.encours, 300)

    def test_reglement_superieur_a_encours_refuse(self):
        cl = Client.objects.create(secretariat=self.sec, nom="Awa")
        self._vente_credit(cl, qte=2)  # encours 200
        self.client.force_authenticate(self.proprio)
        r = self.client.post(f"/api/v1/clients/{cl.id}/reglement/", {"montant": 999}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_plafond_credit_bloque_la_vente(self):
        from apps.ventes.services import VenteError
        cl = Client.objects.create(secretariat=self.sec, nom="Awa", plafond_credit=300)
        with self.assertRaises(VenteError):
            self._vente_credit(cl, qte=5)  # 500 > plafond 300
        cl.refresh_from_db()
        self.assertEqual(cl.encours, 0)  # rien n'a bougé (atomique)

    def test_annulation_retire_la_creance(self):
        cl = Client.objects.create(secretariat=self.sec, nom="Awa")
        prestation, _ = self._vente_credit(cl, qte=5)  # encours 500
        annuler_prestation(prestation=prestation, motif="erreur", auteur=self.proprio)
        cl.refresh_from_db()
        self.assertEqual(cl.encours, 0)

    def test_isolation_clients(self):
        autre = Utilisateur.objects.create_user(
            telephone="+237600000401", nom="X", password="MotDePasseX1", role=Role.PROPRIETAIRE,
        )
        sec_b = Secretariat.objects.create(nom="B", code="CLI02", proprietaire=autre)
        Client.objects.create(secretariat=sec_b, nom="ClientB")
        Client.objects.create(secretariat=self.sec, nom="ClientA")
        self.client.force_authenticate(self.proprio)
        noms = {c["nom"] for c in self.client.get("/api/v1/clients/").data}
        self.assertEqual(noms, {"ClientA"})

    def test_historique_liste_ventes_et_reglements(self):
        cl = Client.objects.create(secretariat=self.sec, nom="Awa")
        self._vente_credit(cl, qte=5)
        self.client.force_authenticate(self.proprio)
        self.client.post(f"/api/v1/clients/{cl.id}/reglement/", {"montant": 100}, format="json")
        h = self.client.get(f"/api/v1/clients/{cl.id}/historique/").data
        self.assertEqual(len(h["prestations"]), 1)
        self.assertEqual(len(h["reglements"]), 1)
