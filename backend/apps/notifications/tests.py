"""Tests des alertes de stock (RG-08)."""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.comptes.models import Role, Utilisateur
from apps.secretariats.models import Secretariat
from apps.stocks.models import Consommable

from .models import Notification, TypeNotification
from .tasks import verifier_seuils_stock


class AlerteStockTests(TestCase):
    def setUp(self):
        self.proprio = Utilisateur.objects.create_user(
            telephone="+237600000080", nom="P", password="MotDePasseP1", role=Role.PROPRIETAIRE,
        )
        self.sec = Secretariat.objects.create(nom="S", code="SNO01", proprietaire=self.proprio)
        self.conso = Consommable.objects.create(
            secretariat=self.sec, nom="Papier A4", unite_mesure="feuille",
            prix_achat=7, qte_stock=50, seuil_alerte=100,  # sous le seuil
        )

    def test_alerte_creee_quand_sous_seuil(self):
        verifier_seuils_stock(self.conso.id)
        self.assertEqual(Notification.objects.filter(type=TypeNotification.STOCK_FAIBLE).count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.utilisateur, self.proprio)
        self.assertIn("Papier A4", notif.corps)
        self.assertIn("50", notif.corps)
        self.conso.refresh_from_db()
        self.assertIsNotNone(self.conso.derniere_alerte_le)

    def test_anti_spam_pas_de_seconde_alerte_en_24h(self):
        verifier_seuils_stock(self.conso.id)
        verifier_seuils_stock(self.conso.id)  # tout de suite après
        self.assertEqual(Notification.objects.count(), 1)

    def test_nouvelle_alerte_apres_24h(self):
        verifier_seuils_stock(self.conso.id)
        self.conso.refresh_from_db()
        self.conso.derniere_alerte_le = timezone.now() - timedelta(hours=25)
        self.conso.save(update_fields=["derniere_alerte_le"])
        verifier_seuils_stock(self.conso.id)
        self.assertEqual(Notification.objects.count(), 2)

    def test_pas_alerte_si_au_dessus_du_seuil(self):
        self.conso.qte_stock = 500
        self.conso.save()
        verifier_seuils_stock(self.conso.id)
        self.assertEqual(Notification.objects.count(), 0)

    def test_rearmement_quand_stock_remonte(self):
        verifier_seuils_stock(self.conso.id)  # alerte + derniere_alerte_le fixée
        self.conso.refresh_from_db()
        self.assertIsNotNone(self.conso.derniere_alerte_le)
        # Réapprovisionnement
        self.conso.qte_stock = 500
        self.conso.save()
        verifier_seuils_stock(self.conso.id)  # au-dessus → réarme
        self.conso.refresh_from_db()
        self.assertIsNone(self.conso.derniere_alerte_le)
