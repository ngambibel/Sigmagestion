"""Tests de l'encaissement (RG-04 : atomicité + décrément stock)."""
from rest_framework import status
from rest_framework.test import APITestCase

from apps.caisse.models import SessionCaisse
from apps.catalogue.models import NomenclatureService, Service
from apps.comptes.models import Role, Utilisateur
from apps.secretariats.models import Secretariat
from apps.stocks.models import Consommable, MouvementStock


class EncaissementTests(APITestCase):
    def setUp(self):
        self.proprio = Utilisateur.objects.create_user(
            telephone="+237600000070", nom="P", password="MotDePasseP1", role=Role.PROPRIETAIRE,
        )
        self.sec = Secretariat.objects.create(nom="S", code="SVE01", proprietaire=self.proprio)
        self.proprio.secretariat = self.sec
        self.proprio.save(update_fields=["secretariat"])
        self.client.force_authenticate(self.proprio)

        # Consommables
        self.papier = Consommable.objects.create(
            secretariat=self.sec, nom="Papier A4", unite_mesure="feuille",
            prix_achat=7, qte_stock=1000, seuil_alerte=100,
        )
        self.spirale = Consommable.objects.create(
            secretariat=self.sec, nom="Spirale", unite_mesure="spirale",
            prix_achat=150, qte_stock=50, seuil_alerte=10,
        )
        # Services
        self.photocopie = Service.objects.create(
            secretariat=self.sec, nom="Photocopie", prix=25, consomme_stock=True,
        )
        NomenclatureService.objects.create(
            service=self.photocopie, consommable=self.papier, qte_par_unite=1,
        )
        self.reliure = Service.objects.create(
            secretariat=self.sec, nom="Reliure", prix=500, consomme_stock=True,
        )
        NomenclatureService.objects.create(
            service=self.reliure, consommable=self.spirale, qte_par_unite=1,
        )
        NomenclatureService.objects.create(
            service=self.reliure, consommable=self.papier, qte_par_unite=2,
        )
        self.saisie = Service.objects.create(
            secretariat=self.sec, nom="Saisie", prix=200, consomme_stock=False,
        )
        # Session ouverte
        self.session = SessionCaisse.objects.create(
            secretariat=self.sec, employe=self.proprio, fond_initial=10000,
        )

    def _vendre(self, lignes, mode="especes", montant_recu=None, remise=0):
        corps = {"lignes": lignes, "mode_paiement": mode, "remise": remise}
        if montant_recu is not None:
            corps["montant_recu"] = montant_recu
        return self.client.post("/api/v1/prestations/", corps, format="json")

    def test_vente_especes_decremente_stock_et_rend_monnaie(self):
        r = self._vendre([{"service": self.photocopie.id, "quantite": 25}], montant_recu=1000)
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        p = r.data["prestation"]
        self.assertEqual(p["montant_total"], 625)  # 25 × 25
        self.assertEqual(p["monnaie_rendue"], 375)  # 1000 - 625
        self.assertTrue(p["numero"].startswith("SVE01-"))
        self.papier.refresh_from_db()
        self.assertEqual(float(self.papier.qte_stock), 975.0)  # 1000 - 25

    def test_reliure_decremente_plusieurs_consommables(self):
        self._vendre([{"service": self.reliure.id, "quantite": 3}], montant_recu=1500)
        self.spirale.refresh_from_db()
        self.papier.refresh_from_db()
        self.assertEqual(float(self.spirale.qte_stock), 47.0)   # 50 - 3
        self.assertEqual(float(self.papier.qte_stock), 994.0)   # 1000 - 3×2

    def test_service_sans_stock_ne_bouge_pas_le_stock(self):
        self._vendre([{"service": self.saisie.id, "quantite": 2}], montant_recu=500)
        self.papier.refresh_from_db()
        self.assertEqual(float(self.papier.qte_stock), 1000.0)
        self.assertFalse(MouvementStock.objects.filter(type="sortie_vente").exists())

    def test_stock_insuffisant_bloque_et_nannule_rien(self):
        self.papier.qte_stock = 10
        self.papier.save()
        r = self._vendre([{"service": self.photocopie.id, "quantite": 25}], montant_recu=1000)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        # Atomicité : rien n'a bougé
        self.papier.refresh_from_db()
        self.assertEqual(float(self.papier.qte_stock), 10.0)
        from apps.ventes.models import Prestation
        self.assertEqual(Prestation.objects.count(), 0)

    def test_especes_montant_insuffisant_refuse(self):
        r = self._vendre([{"service": self.photocopie.id, "quantite": 25}], montant_recu=100)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_credit_exige_nom_client(self):
        r = self.client.post(
            "/api/v1/prestations/",
            {"lignes": [{"service": self.photocopie.id, "quantite": 10}], "mode_paiement": "credit"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_credit_avec_nom_client(self):
        r = self.client.post(
            "/api/v1/prestations/",
            {"lignes": [{"service": self.photocopie.id, "quantite": 10}],
             "mode_paiement": "credit", "nom_client": "Awa Ngono"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data["prestation"]["nom_client"], "Awa Ngono")
        self.assertIsNone(r.data["prestation"]["monnaie_rendue"])

    def test_alerte_stock_apres_vente(self):
        self.spirale.qte_stock = 11
        self.spirale.save()
        r = self._vendre([{"service": self.reliure.id, "quantite": 3}], montant_recu=1500)
        # 11 - 3 = 8 <= seuil 10 → alerte
        noms = {a["nom"] for a in r.data["alertes_stock"]}
        self.assertIn("Spirale", noms)

    def test_vente_sans_session_refusee(self):
        self.session.statut = "cloturee"
        self.session.save()
        r = self._vendre([{"service": self.photocopie.id, "quantite": 1}], montant_recu=100)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_numeros_sequentiels(self):
        self._vendre([{"service": self.saisie.id, "quantite": 1}], montant_recu=200)
        self._vendre([{"service": self.saisie.id, "quantite": 1}], montant_recu=200)
        from apps.ventes.models import Prestation
        numeros = list(Prestation.objects.order_by("cree_le").values_list("numero", flat=True))
        self.assertTrue(numeros[0].endswith("-0001"))
        self.assertTrue(numeros[1].endswith("-0002"))
