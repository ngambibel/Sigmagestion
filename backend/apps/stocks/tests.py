"""Isolation multi-locataire des consommables."""
from rest_framework import status
from rest_framework.test import APITestCase

from apps.comptes.models import Role, Utilisateur
from apps.secretariats.models import Secretariat
from apps.stocks.models import Consommable


class ConsommableIsolationTests(APITestCase):
    def setUp(self):
        self.proprio_a = Utilisateur.objects.create_user(
            telephone="+237600000020", nom="A", password="MotDePasseA1", role=Role.PROPRIETAIRE,
        )
        self.sec_a = Secretariat.objects.create(nom="A", code="AAS01", proprietaire=self.proprio_a)
        self.proprio_a.secretariat = self.sec_a
        self.proprio_a.save(update_fields=["secretariat"])

        self.proprio_b = Utilisateur.objects.create_user(
            telephone="+237600000021", nom="B", password="MotDePasseB1", role=Role.PROPRIETAIRE,
        )
        self.sec_b = Secretariat.objects.create(nom="B", code="BBS01", proprietaire=self.proprio_b)
        self.proprio_b.secretariat = self.sec_b
        self.proprio_b.save(update_fields=["secretariat"])

        self.conso_b = Consommable.objects.create(
            secretariat=self.sec_b, nom="Papier A4 B", unite_mesure="feuille",
            prix_achat=7, qte_stock=500, seuil_alerte=100,
        )

    def test_creation_stock_initial_rattachee(self):
        self.client.force_authenticate(self.proprio_a)
        reponse = self.client.post(
            "/api/v1/consommables/",
            {"nom": "Papier A4", "unite_mesure": "feuille", "prix_achat": 7,
             "qte_stock": 200, "seuil_alerte": 100},
        )
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED)
        conso = Consommable.objects.get(id=reponse.data["id"])
        self.assertEqual(conso.secretariat_id, self.sec_a.id)

    def test_acces_consommable_autre_secretariat_donne_404(self):
        self.client.force_authenticate(self.proprio_a)
        reponse = self.client.get(f"/api/v1/consommables/{self.conso_b.id}/")
        self.assertEqual(reponse.status_code, status.HTTP_404_NOT_FOUND)

    def test_endpoint_alertes(self):
        self.client.force_authenticate(self.proprio_b)
        # conso_b : 500 > seuil 100 → pas d'alerte
        reponse = self.client.get("/api/v1/consommables/alertes/")
        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertEqual(len(reponse.data), 0)
        self.conso_b.qte_stock = 50
        self.conso_b.save()
        reponse = self.client.get("/api/v1/consommables/alertes/")
        self.assertEqual(len(reponse.data), 1)

    def test_indicateur_sous_seuil(self):
        self.client.force_authenticate(self.proprio_b)
        # 500 > 100 → pas sous seuil
        reponse = self.client.get(f"/api/v1/consommables/{self.conso_b.id}/")
        self.assertFalse(reponse.data["sous_seuil"])
        self.conso_b.qte_stock = 50
        self.conso_b.save()
        reponse = self.client.get(f"/api/v1/consommables/{self.conso_b.id}/")
        self.assertTrue(reponse.data["sous_seuil"])


class EntreeStockCumpTests(APITestCase):
    def setUp(self):
        self.proprio = Utilisateur.objects.create_user(
            telephone="+237600000040", nom="P", password="MotDePasseP1", role=Role.PROPRIETAIRE,
        )
        self.sec = Secretariat.objects.create(nom="S", code="SEN01", proprietaire=self.proprio)
        self.proprio.secretariat = self.sec
        self.proprio.save(update_fields=["secretariat"])
        self.conso = Consommable.objects.create(
            secretariat=self.sec, nom="Papier A4", unite_mesure="feuille",
            prix_achat=0, qte_stock=0, seuil_alerte=100,
        )

    def _entree(self, quantite, prix_total):
        return self.client.post(
            f"/api/v1/consommables/{self.conso.id}/entree-stock/",
            {"quantite": quantite, "prix_total_lot": prix_total},
            format="json",
        )

    def test_cump_pondere_sur_deux_entrees(self):
        self.client.force_authenticate(self.proprio)
        # Entrée 1 : 100 @ total 1000 → unitaire 10
        r1 = self._entree("100", 1000)
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r1.data["consommable"]["prix_achat"], 10)
        self.assertEqual(float(r1.data["consommable"]["qte_stock"]), 100.0)
        # Entrée 2 : 100 @ total 2000 → unitaire 20 ; CUMP = (100*10 + 100*20)/200 = 15
        r2 = self._entree("100", 2000)
        self.assertEqual(r2.data["consommable"]["prix_achat"], 15)
        self.assertEqual(float(r2.data["consommable"]["qte_stock"]), 200.0)
        # Le mouvement enregistre le stock avant/après
        self.assertEqual(float(r2.data["mouvement"]["stock_avant"]), 100.0)
        self.assertEqual(float(r2.data["mouvement"]["stock_apres"]), 200.0)

    def test_gerant_peut_faire_une_entree(self):
        gerant = Utilisateur.objects.create_user(
            telephone="+237600000041", nom="G", password="MotDePasseG1",
            role=Role.GERANT, secretariat=self.sec,
        )
        self.client.force_authenticate(gerant)
        self.assertEqual(self._entree("50", 500).status_code, status.HTTP_201_CREATED)

    def test_employe_ne_peut_pas_faire_une_entree(self):
        employe = Utilisateur.objects.create_user(
            telephone="+237600000042", nom="E", password="MotDePasseE1",
            role=Role.EMPLOYE, secretariat=self.sec,
        )
        self.client.force_authenticate(employe)
        self.assertEqual(self._entree("50", 500).status_code, status.HTTP_403_FORBIDDEN)

    def test_isolation_entree_autre_secretariat(self):
        autre = Utilisateur.objects.create_user(
            telephone="+237600000043", nom="Autre", password="MotDePasseX1", role=Role.PROPRIETAIRE,
        )
        sec_autre = Secretariat.objects.create(nom="Autre", code="AUT02", proprietaire=autre)
        autre.secretariat = sec_autre
        autre.save(update_fields=["secretariat"])
        self.client.force_authenticate(autre)
        # conso appartient à self.sec → 404 pour l'autre propriétaire
        self.assertEqual(self._entree("50", 500).status_code, status.HTTP_404_NOT_FOUND)


class AjustementEtJournalTests(APITestCase):
    def setUp(self):
        self.proprio = Utilisateur.objects.create_user(
            telephone="+237600000050", nom="P", password="MotDePasseP1", role=Role.PROPRIETAIRE,
        )
        self.sec = Secretariat.objects.create(nom="S", code="SAJ01", proprietaire=self.proprio)
        self.proprio.secretariat = self.sec
        self.proprio.save(update_fields=["secretariat"])
        self.client.force_authenticate(self.proprio)
        # Création via l'API → génère un mouvement "Stock initial"
        self.conso = self.client.post(
            "/api/v1/consommables/",
            {"nom": "Papier A4", "unite_mesure": "feuille", "prix_achat": 7,
             "qte_stock": 500, "seuil_alerte": 100},
            format="json",
        ).data

    def test_ajustement_negatif_avec_motif(self):
        reponse = self.client.post(
            f"/api/v1/consommables/{self.conso['id']}/ajustement/",
            {"quantite_delta": "-10", "motif": "10 feuilles abîmées"},
            format="json",
        )
        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(reponse.data["consommable"]["qte_stock"]), 490.0)

    def test_ajustement_sans_motif_refuse(self):
        reponse = self.client.post(
            f"/api/v1/consommables/{self.conso['id']}/ajustement/",
            {"quantite_delta": "-10", "motif": "   "},
            format="json",
        )
        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ajustement_stock_negatif_refuse(self):
        reponse = self.client.post(
            f"/api/v1/consommables/{self.conso['id']}/ajustement/",
            {"quantite_delta": "-999", "motif": "erreur"},
            format="json",
        )
        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)

    def test_journal_liste_mouvements(self):
        # Stock initial (1) + un ajustement (1) = 2 mouvements
        self.client.post(
            f"/api/v1/consommables/{self.conso['id']}/ajustement/",
            {"quantite_delta": "-10", "motif": "casse"}, format="json",
        )
        reponse = self.client.get("/api/v1/mouvements-stock/")
        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        resultats = reponse.data["results"] if isinstance(reponse.data, dict) else reponse.data
        self.assertEqual(len(resultats), 2)

    def test_journal_interdit_a_employe(self):
        employe = Utilisateur.objects.create_user(
            telephone="+237600000051", nom="E", password="MotDePasseE1",
            role=Role.EMPLOYE, secretariat=self.sec,
        )
        self.client.force_authenticate(employe)
        reponse = self.client.get("/api/v1/mouvements-stock/")
        self.assertEqual(reponse.status_code, status.HTTP_403_FORBIDDEN)

    def test_recalculer_stocks(self):
        from io import StringIO

        from django.core.management import call_command

        from apps.stocks.models import Consommable

        # On casse volontairement la valeur dénormalisée
        c = Consommable.objects.get(id=self.conso["id"])
        c.qte_stock = 999
        c.save(update_fields=["qte_stock"])
        call_command("recalculer_stocks", stdout=StringIO())
        c.refresh_from_db()
        # Le seul mouvement est le stock initial de 500
        self.assertEqual(float(c.qte_stock), 500.0)
