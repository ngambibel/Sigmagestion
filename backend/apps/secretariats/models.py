"""Modèle Secretariat — racine du multi-locataire."""
import re
from datetime import time

from django.conf import settings
from django.db import models


def generer_code(nom: str) -> str:
    """Produit un code court en majuscules à partir du nom (ex. « Éclair Bureau » → « ECBU »).

    Utilisé comme préfixe de reçus. L'unicité est garantie par l'appelant.
    """
    mots = re.findall(r"[A-Za-zÀ-ÿ]+", nom)
    if not mots:
        return "SEC"
    if len(mots) == 1:
        base = mots[0][:4]
    else:
        base = "".join(mot[:2] for mot in mots[:2])
    return base.upper()


class Secretariat(models.Model):
    """Un point de vente. Toutes les données métier lui sont rattachées."""

    nom = models.CharField("nom", max_length=150)
    code = models.CharField(
        "code", max_length=12, unique=True,
        help_text="Préfixe court des reçus, ex. EBO01.",
    )
    ville = models.CharField("ville", max_length=100, blank=True, default="")
    quartier = models.CharField("quartier", max_length=100, blank=True, default="")
    telephone = models.CharField(
        "téléphone affiché", max_length=20, blank=True, default="",
        help_text="Numéro imprimé sur les reçus.",
    )
    devise = models.CharField("devise", max_length=3, default="XAF")
    onboarding_termine = models.BooleanField(
        "installation terminée", default=False,
        help_text="Faux tant que l'assistant en 3 écrans n'est pas achevé.",
    )
    autoriser_stock_negatif = models.BooleanField(
        "autoriser la vente en stock négatif", default=False,
        help_text="Si faux, une vente est bloquée quand un consommable manque.",
    )
    proprietaire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="secretariats_possedes",
        verbose_name="propriétaire",
    )
    cree_le = models.DateTimeField("créé le", auto_now_add=True)
    modifie_le = models.DateTimeField("modifié le", auto_now=True)

    class Meta:
        verbose_name = "secrétariat"
        verbose_name_plural = "secrétariats"
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} [{self.code}]"

    @classmethod
    def generer_code_unique(cls, nom: str) -> str:
        """Génère un code unique, en suffixant un numéro si nécessaire."""
        base = generer_code(nom)
        code = f"{base}01"
        compteur = 1
        while cls.objects.filter(code=code).exists():
            compteur += 1
            code = f"{base}{compteur:02d}"
        return code


class JourSemaine(models.IntegerChoices):
    """Jours alignés sur `datetime.weekday()` : 0 = lundi … 6 = dimanche."""

    LUNDI = 0, "Lundi"
    MARDI = 1, "Mardi"
    MERCREDI = 2, "Mercredi"
    JEUDI = 3, "Jeudi"
    VENDREDI = 4, "Vendredi"
    SAMEDI = 5, "Samedi"
    DIMANCHE = 6, "Dimanche"


class PlageHoraire(models.Model):
    """Heures d'ouverture d'un secrétariat pour un jour de la semaine.

    Une ligne par jour (7 au total). `ouvert = False` signifie « fermé ce jour ».
    Sert à décider si une notification de CA peut partir (RG-09).
    """

    secretariat = models.ForeignKey(
        Secretariat, on_delete=models.CASCADE, related_name="plages_horaires",
    )
    jour = models.PositiveSmallIntegerField("jour", choices=JourSemaine.choices)
    ouvert = models.BooleanField("ouvert", default=True)
    heure_debut = models.TimeField("heure d'ouverture", default=time(7, 30))
    heure_fin = models.TimeField("heure de fermeture", default=time(19, 0))

    class Meta:
        verbose_name = "plage horaire"
        verbose_name_plural = "plages horaires"
        ordering = ["secretariat", "jour"]
        constraints = [
            models.UniqueConstraint(
                fields=["secretariat", "jour"], name="une_plage_par_jour_et_secretariat",
            ),
        ]

    def __str__(self):
        etat = f"{self.heure_debut:%H:%M}–{self.heure_fin:%H:%M}" if self.ouvert else "fermé"
        return f"{self.get_jour_display()} : {etat}"

    def contient(self, heure) -> bool:
        """Vrai si `heure` (datetime.time) tombe dans la plage ouverte du jour."""
        return self.ouvert and self.heure_debut <= heure < self.heure_fin


class ParametreNotification(models.Model):
    """Réglages de notification propres à un secrétariat (un seul par secrétariat)."""

    INTERVALLES = [60, 120, 180, 240]

    secretariat = models.OneToOneField(
        Secretariat, on_delete=models.CASCADE, related_name="parametre_notification",
    )
    intervalle_ca_min = models.PositiveSmallIntegerField(
        "intervalle du bilan de CA (minutes)", default=120,
        help_text="Fréquence d'envoi du CA pendant les horaires : 60, 120, 180 ou 240 min.",
    )
    alerte_ca_on = models.BooleanField("bilan de CA périodique activé", default=True)
    alerte_stock_on = models.BooleanField("alerte de stock faible activée", default=True)
    bilan_jour_on = models.BooleanField("bilan de fin de journée activé", default=True)
    seuil_ecart_caisse = models.PositiveIntegerField(
        "seuil d'alerte sur écart de caisse (XAF)", default=0,
        help_text="0 = pas d'alerte sur l'écart de caisse.",
    )
    dernier_envoi_ca = models.DateTimeField("dernier bilan de CA envoyé", null=True, blank=True)
    dernier_bilan_jour = models.DateField("dernier bilan de journée envoyé", null=True, blank=True)

    class Meta:
        verbose_name = "paramètre de notification"
        verbose_name_plural = "paramètres de notification"

    def __str__(self):
        return f"Notifications — {self.secretariat.nom}"


def plages_par_defaut(secretariat) -> list["PlageHoraire"]:
    """Crée les 7 plages horaires d'un secrétariat si elles n'existent pas encore.

    Par défaut : lundi–vendredi 07 h 30 → 19 h 00, samedi 08 h 00 → 15 h 00,
    dimanche fermé. Idempotent — ne recrée jamais une plage existante.
    """
    existantes = {p.jour: p for p in secretariat.plages_horaires.all()}
    for jour in JourSemaine.values:
        if jour in existantes:
            continue
        if jour == JourSemaine.DIMANCHE:
            defauts = {"ouvert": False, "heure_debut": time(8, 0), "heure_fin": time(15, 0)}
        elif jour == JourSemaine.SAMEDI:
            defauts = {"ouvert": True, "heure_debut": time(8, 0), "heure_fin": time(15, 0)}
        else:
            defauts = {"ouvert": True, "heure_debut": time(7, 30), "heure_fin": time(19, 0)}
        existantes[jour] = PlageHoraire.objects.create(
            secretariat=secretariat, jour=jour, **defauts,
        )
    return [existantes[j] for j in JourSemaine.values]
