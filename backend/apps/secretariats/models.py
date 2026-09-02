"""Modèle Secretariat — racine du multi-locataire."""
import re

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
