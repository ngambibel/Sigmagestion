"""Garde-fou performance : les endpoints de liste ne font pas de N+1
(le nombre de requêtes ne doit pas croître avec le nombre de lignes)."""
from django.test.utils import CaptureQueriesContext
from django.db import connection
from rest_framework.test import APITestCase

from apps.caisse.models import SessionCaisse
from apps.catalogue.models import NomenclatureService, Service
from apps.comptes.models import Role, Utilisateur
from apps.secretariats.models import Secretariat
from apps.stocks.models import Consommable


class PerfListesTests(APITestCase):
    def setUp(self):
        self.proprio = Utilisateur.objects.create_user(
            telephone="+237600000600", nom="P", password="MotDePasseP1", role=Role.PROPRIETAIRE,
        )
        self.sec = Secretariat.objects.create(nom="S", code="PERF01", proprietaire=self.proprio)
        self.proprio.secretariat = self.sec
        self.proprio.save(update_fields=["secretariat"])
        self.client.force_authenticate(self.proprio)
        self.papier = Consommable.objects.create(
            secretariat=self.sec, nom="Papier", unite_mesure="feuille",
            prix_achat=7, qte_stock=100000, seuil_alerte=10,
        )
        self.svc = Service.objects.create(
            secretariat=self.sec, nom="Photocopie", prix=25, consomme_stock=True,
        )
        NomenclatureService.objects.create(service=self.svc, consommable=self.papier, qte_par_unite=1)
        self.session = SessionCaisse.objects.create(
            secretariat=self.sec, employe=self.proprio, fond_initial=0,
        )

    def _vendre(self, n):
        for _ in range(n):
            self.client.post(
                "/api/v1/prestations/",
                {"lignes": [{"service": self.svc.id, "quantite": 2}],
                 "mode_paiement": "especes", "montant_recu": 1000},
                format="json",
            )

    def _nb_requetes(self, url):
        with CaptureQueriesContext(connection) as ctx:
            self.client.get(url)
        return len(ctx.captured_queries)

    def test_prestations_pas_de_n_plus_un(self):
        self._vendre(2)
        base = self._nb_requetes("/api/v1/prestations/")
        self._vendre(6)
        apres = self._nb_requetes("/api/v1/prestations/")
        self.assertEqual(base, apres, f"N+1 détecté : {base} → {apres} requêtes")

    def test_mouvements_pas_de_n_plus_un(self):
        self._vendre(2)
        base = self._nb_requetes("/api/v1/mouvements-stock/")
        self._vendre(6)
        apres = self._nb_requetes("/api/v1/mouvements-stock/")
        self.assertEqual(base, apres, f"N+1 détecté : {base} → {apres} requêtes")
