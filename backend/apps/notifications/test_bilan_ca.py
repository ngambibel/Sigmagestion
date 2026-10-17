"""Tests du bilan de chiffre d'affaires périodique (M6.3, RG-09, RG-10).

Les fonctions `traiter_bilan_ca` / `traiter_bilan_jour` reçoivent l'instant courant
en paramètre : on peut donc tester tous les cas limites (hors plage, jour fermé,
CA nul, passage de minuit) de façon déterministe, sans dépendre de l'horloge réelle.
"""
import re
from datetime import datetime, time, timedelta

from django.test import TestCase
from django.utils import timezone

from apps.caisse.models import SessionCaisse
from apps.catalogue.models import Service
from apps.comptes.models import Role, Utilisateur
from apps.secretariats.models import (
    ParametreNotification,
    PlageHoraire,
    Secretariat,
)
from apps.ventes.models import LignePrestation, Prestation, StatutPrestation

from .models import Notification, TypeNotification
from .tasks import traiter_bilan_ca, traiter_bilan_jour


def aware(an, mois, jour, h, m):
    return timezone.make_aware(datetime(an, mois, jour, h, m))


def sans_espaces(texte: str) -> str:
    r"""Retire toute espace (dont l'espace fine insécable  ) pour comparer les montants."""
    return re.sub(r"\s", "", texte)


class BilanCATests(TestCase):
    def setUp(self):
        self.proprio = Utilisateur.objects.create_user(
            telephone="+237600000090", nom="Awa", password="MotDePasseP1", role=Role.PROPRIETAIRE,
        )
        self.sec = Secretariat.objects.create(
            nom="Sigma Ébolowa", code="EBO01", proprietaire=self.proprio, onboarding_termine=True,
        )
        self.param = ParametreNotification.objects.create(secretariat=self.sec)
        self.service = Service.objects.create(secretariat=self.sec, nom="Photocopie", prix=50)
        self.session = SessionCaisse.objects.create(
            secretariat=self.sec, employe=self.proprio, fond_initial=10000,
        )
        self._n = 0

    def plage(self, jour, *, ouvert=True, debut=time(7, 30), fin=time(19, 0)):
        PlageHoraire.objects.update_or_create(
            secretariat=self.sec, jour=jour,
            defaults={"ouvert": ouvert, "heure_debut": debut, "heure_fin": fin},
        )

    def vente(self, montant, quand, *, service_nom="Photocopie", qte=1, statut=StatutPrestation.VALIDEE):
        self._n += 1
        p = Prestation.objects.create(
            secretariat=self.sec, session=self.session, numero=f"EBO01-T-{self._n:04d}",
            employe=self.proprio, mode_paiement="especes", montant_total=montant, statut=statut,
        )
        LignePrestation.objects.create(
            prestation=p, service=self.service, nom_service=service_nom,
            prix_unitaire=montant // qte if qte else montant, quantite=qte, cout_unitaire=0,
        )
        # auto_now_add fige cree_le : on le repositionne pour le test.
        Prestation.objects.filter(pk=p.pk).update(cree_le=quand)
        return p

    # --- Cas nominal ---
    def test_envoi_pendant_la_plage_avec_ca(self):
        maintenant = aware(2026, 10, 19, 14, 0)  # lundi
        self.plage(maintenant.weekday())
        self.vente(47500, aware(2026, 10, 19, 13, 0))
        self.vente(20700, aware(2026, 10, 19, 9, 0))

        envoye = traiter_bilan_ca(self.sec, self.param, maintenant)

        self.assertTrue(envoye)
        notif = Notification.objects.get(type=TypeNotification.BILAN_CA)
        self.assertIn("Bilan 14h00", notif.titre)
        self.assertIn("Sigma Ébolowa", notif.titre)
        corps = sans_espaces(notif.corps)
        self.assertIn("68200Faujourd'hui", corps)  # 47500 + 20700
        self.assertIn("Photocopie en tête", notif.corps)
        self.param.refresh_from_db()
        self.assertEqual(self.param.dernier_envoi_ca, maintenant)

    # --- RG-09 : hors plage horaire ---
    def test_pas_envoi_avant_ouverture(self):
        maintenant = aware(2026, 10, 19, 6, 0)  # avant 07h30
        self.plage(maintenant.weekday())
        self.vente(5000, aware(2026, 10, 19, 5, 30))
        self.assertFalse(traiter_bilan_ca(self.sec, self.param, maintenant))
        self.assertEqual(Notification.objects.count(), 0)

    def test_pas_envoi_jour_ferme(self):
        maintenant = aware(2026, 10, 18, 11, 0)  # dimanche
        self.plage(maintenant.weekday(), ouvert=False)
        self.vente(5000, aware(2026, 10, 18, 10, 0))
        self.assertFalse(traiter_bilan_ca(self.sec, self.param, maintenant))
        self.assertEqual(Notification.objects.count(), 0)

    # --- RG-10 : jour creux (CA nul) ---
    def test_pas_envoi_si_ca_entierement_nul(self):
        maintenant = aware(2026, 10, 19, 14, 0)
        self.plage(maintenant.weekday())
        self.assertFalse(traiter_bilan_ca(self.sec, self.param, maintenant))
        self.assertEqual(Notification.objects.count(), 0)

    def test_prestation_annulee_ne_compte_pas(self):
        maintenant = aware(2026, 10, 19, 14, 0)
        self.plage(maintenant.weekday())
        self.vente(5000, aware(2026, 10, 19, 13, 0), statut=StatutPrestation.ANNULEE)
        self.assertFalse(traiter_bilan_ca(self.sec, self.param, maintenant))

    # --- Intervalle non écoulé ---
    def test_pas_de_second_envoi_avant_intervalle(self):
        maintenant = aware(2026, 10, 19, 14, 0)
        self.plage(maintenant.weekday())
        self.vente(5000, aware(2026, 10, 19, 13, 0))
        self.assertTrue(traiter_bilan_ca(self.sec, self.param, maintenant))
        # 1h plus tard, intervalle de 2h non écoulé → pas d'envoi
        self.param.refresh_from_db()
        plus_tard = aware(2026, 10, 19, 15, 0)
        self.assertFalse(traiter_bilan_ca(self.sec, self.param, plus_tard))
        self.assertEqual(Notification.objects.count(), 1)

    def test_second_envoi_apres_intervalle(self):
        maintenant = aware(2026, 10, 19, 12, 0)
        self.plage(maintenant.weekday())
        self.vente(5000, aware(2026, 10, 19, 11, 0))
        self.assertTrue(traiter_bilan_ca(self.sec, self.param, maintenant))
        self.param.refresh_from_db()
        self.vente(3000, aware(2026, 10, 19, 13, 30))
        plus_tard = aware(2026, 10, 19, 14, 0)  # 2h après
        self.assertTrue(traiter_bilan_ca(self.sec, self.param, plus_tard))
        self.assertEqual(Notification.objects.count(), 2)
        # L'intervalle du second envoi part du premier envoi (12h00), pas de l'ouverture.
        notif = Notification.objects.filter(type=TypeNotification.BILAN_CA).order_by("-id").first()
        self.assertIn("depuis 12h00", notif.corps)

    # --- Passage de minuit : dernier envoi la veille ---
    def test_nouvelle_journee_repart_de_l_ouverture(self):
        self.plage(0)  # lundi
        self.plage(1)  # mardi
        # Dernier envoi : lundi 18h00.
        self.param.dernier_envoi_ca = aware(2026, 10, 19, 18, 0)
        self.param.save(update_fields=["dernier_envoi_ca"])
        # Mardi 08h00, une vente à 07h45 (après ouverture).
        self.vente(9000, aware(2026, 10, 20, 7, 45))
        maintenant = aware(2026, 10, 20, 8, 0)
        self.assertTrue(traiter_bilan_ca(self.sec, self.param, maintenant))
        notif = Notification.objects.get(type=TypeNotification.BILAN_CA)
        # L'intervalle repart de l'ouverture (07h30), pas de la veille 18h00.
        self.assertIn("depuis 07h30", notif.corps)
        self.assertIn("9000F", sans_espaces(notif.corps))

    def test_desactivation_coupe_l_envoi(self):
        maintenant = aware(2026, 10, 19, 14, 0)
        self.plage(maintenant.weekday())
        self.vente(5000, aware(2026, 10, 19, 13, 0))
        self.param.alerte_ca_on = False
        self.param.save(update_fields=["alerte_ca_on"])
        self.assertFalse(traiter_bilan_ca(self.sec, self.param, maintenant))


class BilanJourTests(TestCase):
    def setUp(self):
        self.proprio = Utilisateur.objects.create_user(
            telephone="+237600000091", nom="Awa", password="MotDePasseP1", role=Role.PROPRIETAIRE,
        )
        self.sec = Secretariat.objects.create(
            nom="Sigma Ébolowa", code="EBO02", proprietaire=self.proprio, onboarding_termine=True,
        )
        self.param = ParametreNotification.objects.create(secretariat=self.sec)
        self.service = Service.objects.create(secretariat=self.sec, nom="Photocopie", prix=50)
        self.session = SessionCaisse.objects.create(
            secretariat=self.sec, employe=self.proprio, fond_initial=10000,
        )

    def _plage(self, jour, **kw):
        PlageHoraire.objects.update_or_create(
            secretariat=self.sec, jour=jour,
            defaults={"ouvert": True, "heure_debut": time(7, 30), "heure_fin": time(19, 0), **kw},
        )

    def _vente(self, montant, quand):
        p = Prestation.objects.create(
            secretariat=self.sec, session=self.session, numero=f"EBO02-{montant}-{quand:%H%M}",
            employe=self.proprio, mode_paiement="especes", montant_total=montant,
        )
        Prestation.objects.filter(pk=p.pk).update(cree_le=quand)

    def test_envoi_a_la_fermeture_une_seule_fois(self):
        jour = aware(2026, 10, 19, 19, 5).weekday()
        self._plage(jour)
        self._vente(40000, aware(2026, 10, 19, 15, 0))
        maintenant = aware(2026, 10, 19, 19, 5)  # après 19h00
        self.assertTrue(traiter_bilan_jour(self.sec, self.param, maintenant))
        notif = Notification.objects.get()
        self.assertIn("Clôture", notif.titre)
        self.assertIn("40000F", sans_espaces(notif.corps))
        # Deuxième passage le même jour → pas de doublon.
        self.assertFalse(traiter_bilan_jour(self.sec, self.param, aware(2026, 10, 19, 19, 20)))
        self.assertEqual(Notification.objects.count(), 1)

    def test_pas_envoi_avant_fermeture(self):
        jour = aware(2026, 10, 19, 16, 0).weekday()
        self._plage(jour)
        self._vente(40000, aware(2026, 10, 19, 15, 0))
        self.assertFalse(traiter_bilan_jour(self.sec, self.param, aware(2026, 10, 19, 16, 0)))

    def test_pas_envoi_jour_creux(self):
        jour = aware(2026, 10, 19, 19, 5).weekday()
        self._plage(jour)
        self.assertFalse(traiter_bilan_jour(self.sec, self.param, aware(2026, 10, 19, 19, 5)))
        self.assertEqual(Notification.objects.count(), 0)
