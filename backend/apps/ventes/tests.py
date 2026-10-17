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

    def test_credit_avec_client_incremente_encours(self):
        from apps.clients.models import Client
        cl = Client.objects.create(secretariat=self.sec, nom="Awa Ngono")
        r = self.client.post(
            "/api/v1/prestations/",
            {"lignes": [{"service": self.photocopie.id, "quantite": 10}],
             "mode_paiement": "credit", "client": cl.id},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data["prestation"]["nom_client"], "Awa Ngono")
        self.assertIsNone(r.data["prestation"]["monnaie_rendue"])
        cl.refresh_from_db()
        self.assertEqual(cl.encours, 250)  # 10 × 25

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

    def test_annulation_contre_passe_le_stock(self):
        # Vente : papier 1000 → 975
        r = self._vendre([{"service": self.photocopie.id, "quantite": 25}], montant_recu=1000)
        pid = r.data["prestation"]["id"]
        self.papier.refresh_from_db()
        self.assertEqual(float(self.papier.qte_stock), 975.0)
        # Annulation
        ra = self.client.post(f"/api/v1/prestations/{pid}/annuler/", {"motif": "erreur de saisie"}, format="json")
        self.assertEqual(ra.status_code, status.HTTP_200_OK)
        self.assertEqual(ra.data["statut"], "annulee")
        self.papier.refresh_from_db()
        self.assertEqual(float(self.papier.qte_stock), 1000.0)  # stock revenu
        self.assertTrue(MouvementStock.objects.filter(type="annulation", prestation_id=pid).exists())

    def test_annulation_sans_motif_refuse(self):
        r = self._vendre([{"service": self.photocopie.id, "quantite": 5}], montant_recu=1000)
        pid = r.data["prestation"]["id"]
        ra = self.client.post(f"/api/v1/prestations/{pid}/annuler/", {"motif": "  "}, format="json")
        self.assertEqual(ra.status_code, status.HTTP_400_BAD_REQUEST)

    def test_double_annulation_refuse(self):
        r = self._vendre([{"service": self.photocopie.id, "quantite": 5}], montant_recu=1000)
        pid = r.data["prestation"]["id"]
        self.client.post(f"/api/v1/prestations/{pid}/annuler/", {"motif": "x"}, format="json")
        ra = self.client.post(f"/api/v1/prestations/{pid}/annuler/", {"motif": "y"}, format="json")
        self.assertEqual(ra.status_code, status.HTTP_400_BAD_REQUEST)

    def test_employe_ne_peut_pas_annuler(self):
        r = self._vendre([{"service": self.photocopie.id, "quantite": 5}], montant_recu=1000)
        pid = r.data["prestation"]["id"]
        employe = Utilisateur.objects.create_user(
            telephone="+237600000071", nom="E", password="MotDePasseE1",
            role=Role.EMPLOYE, secretariat=self.sec,
        )
        self.client.force_authenticate(employe)
        ra = self.client.post(f"/api/v1/prestations/{pid}/annuler/", {"motif": "x"}, format="json")
        self.assertEqual(ra.status_code, status.HTTP_403_FORBIDDEN)

    def test_numeros_sequentiels(self):
        self._vendre([{"service": self.saisie.id, "quantite": 1}], montant_recu=200)
        self._vendre([{"service": self.saisie.id, "quantite": 1}], montant_recu=200)
        from apps.ventes.models import Prestation
        numeros = list(Prestation.objects.order_by("cree_le").values_list("numero", flat=True))
        self.assertTrue(numeros[0].endswith("-0001"))
        self.assertTrue(numeros[1].endswith("-0002"))

    # --- Prix modifiable à la vente (rabais gros volume) ---
    def test_prix_unitaire_modifie_change_le_ca(self):
        r = self._vendre(
            [{"service": self.photocopie.id, "quantite": 100, "prix_unitaire": 20}],
            montant_recu=2000,
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        ligne = r.data["prestation"]["lignes"][0]
        self.assertEqual(ligne["prix_unitaire"], 20)       # prix appliqué
        self.assertEqual(ligne["prix_catalogue"], 25)      # prix de référence conservé
        self.assertEqual(r.data["prestation"]["montant_total"], 2000)  # 100 × 20
        # Le stock, lui, suit la quantité (100 feuilles).
        self.papier.refresh_from_db()
        self.assertEqual(float(self.papier.qte_stock), 900.0)

    # --- Recto-verso : 2× moins de feuilles (le toner suivrait la page) ---
    def test_recto_verso_divise_les_feuilles(self):
        NomenclatureService.objects.filter(
            service=self.photocopie, consommable=self.papier,
        ).update(divise_en_recto_verso=True)
        # 11 pages recto-verso → ceil(11/2) = 6 feuilles.
        r = self._vendre(
            [{"service": self.photocopie.id, "quantite": 11, "recto_verso": True}],
            montant_recu=1000,
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertTrue(r.data["prestation"]["lignes"][0]["recto_verso"])
        # Le CA reste au nombre de pages : 11 × 25 = 275.
        self.assertEqual(r.data["prestation"]["montant_total"], 275)
        self.papier.refresh_from_db()
        self.assertEqual(float(self.papier.qte_stock), 994.0)  # 1000 - 6

    def test_recto_verso_sans_flag_nomenclature_ne_divise_pas(self):
        # Le flag n'est pas posé sur la nomenclature → recto-verso sans effet sur les feuilles.
        r = self._vendre(
            [{"service": self.photocopie.id, "quantite": 10, "recto_verso": True}],
            montant_recu=1000,
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.papier.refresh_from_db()
        self.assertEqual(float(self.papier.qte_stock), 990.0)  # 1000 - 10 (pas divisé)
