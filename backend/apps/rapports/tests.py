"""Tests du tableau de bord propriétaire (M7.1)."""
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.caisse.models import SessionCaisse
from apps.catalogue.models import Service
from apps.comptes.models import Role, Utilisateur
from apps.secretariats.models import Secretariat
from apps.ventes.models import LignePrestation, Prestation, StatutPrestation


class TableauDeBordTests(APITestCase):
    def setUp(self):
        self.proprio = Utilisateur.objects.create_user(
            telephone="+237600000200", nom="Awa", password="MotDePasseP1", role=Role.PROPRIETAIRE,
        )
        self.sec = Secretariat.objects.create(nom="S", code="TDB01", proprietaire=self.proprio)
        self.proprio.secretariat = self.sec
        self.proprio.save(update_fields=["secretariat"])
        self.service = Service.objects.create(secretariat=self.sec, nom="Photocopie", prix=50)
        self.session = SessionCaisse.objects.create(
            secretariat=self.sec, employe=self.proprio, fond_initial=0,
        )
        self._n = 0

    def _vente(self, montant, quand=None, qte=1, statut=StatutPrestation.VALIDEE):
        self._n += 1
        p = Prestation.objects.create(
            secretariat=self.sec, session=self.session, numero=f"TDB01-{self._n:04d}",
            employe=self.proprio, mode_paiement="especes", montant_total=montant, statut=statut,
        )
        LignePrestation.objects.create(
            prestation=p, service=self.service, nom_service="Photocopie",
            prix_unitaire=montant // qte if qte else montant, quantite=qte, cout_unitaire=10,
        )
        if quand:
            Prestation.objects.filter(pk=p.pk).update(cree_le=quand)
        return p

    def test_ca_jour_et_structure(self):
        self._vente(1000)
        self._vente(500)
        self._vente(9999, statut=StatutPrestation.ANNULEE)  # exclue
        self.client.force_authenticate(self.proprio)
        reponse = self.client.get("/api/v1/tableau-de-bord/")
        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        d = reponse.data
        self.assertEqual(d["ca_jour"], 1500)
        self.assertEqual(d["nb_prestations_jour"], 2)
        self.assertEqual(len(d["serie_30j"]), 30)
        self.assertEqual(d["serie_30j"][-1]["ca"], 1500)  # aujourd'hui = dernier point
        self.assertEqual(d["top_services"][0]["nom_service"], "Photocopie")
        self.assertIn("par_employe", d)
        self.assertIn("consommables_sous_seuil", d)

    def test_variation_vs_veille(self):
        from datetime import timedelta

        debut_jour = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
        hier = debut_jour - timedelta(days=1) + timedelta(minutes=1)  # hier 00h01, dans la tranche
        self._vente(1000, quand=hier)  # veille
        self._vente(2000)  # aujourd'hui
        self.client.force_authenticate(self.proprio)
        d = self.client.get("/api/v1/tableau-de-bord/").data
        self.assertEqual(d["ca_jour"], 2000)
        self.assertEqual(d["ca_veille"], 1000)
        self.assertEqual(d["variation_pct"], 100)  # +100 %

    def test_employe_interdit(self):
        employe = Utilisateur.objects.create_user(
            telephone="+237600000201", nom="Emp", password="MotDePasseE1",
            role=Role.EMPLOYE, secretariat=self.sec,
        )
        self.client.force_authenticate(employe)
        reponse = self.client.get("/api/v1/tableau-de-bord/")
        self.assertEqual(reponse.status_code, status.HTTP_403_FORBIDDEN)
