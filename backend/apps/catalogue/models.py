"""Modèle Service — le catalogue tarifaire d'un secrétariat."""
from django.db import models


class UniteFacturation(models.TextChoices):
    PAGE = "page", "La page"
    DOCUMENT = "document", "Le document"
    PIECE = "piece", "La pièce"
    FORFAIT = "forfait", "Le forfait"


class Service(models.Model):
    """Une prestation vendable. Le prix est en XAF entier."""

    secretariat = models.ForeignKey(
        "secretariats.Secretariat",
        on_delete=models.CASCADE,
        related_name="services",
    )
    nom = models.CharField("nom", max_length=120)
    categorie = models.CharField("catégorie", max_length=60, blank=True, default="")
    unite_facturation = models.CharField(
        "unité de facturation", max_length=10,
        choices=UniteFacturation.choices, default=UniteFacturation.PAGE,
    )
    prix = models.PositiveIntegerField("prix de vente (XAF)")
    consomme_stock = models.BooleanField("consomme du stock", default=False)
    actif = models.BooleanField("actif", default=True)
    couleur = models.CharField("couleur", max_length=7, blank=True, default="")
    icone = models.CharField("icône", max_length=40, blank=True, default="")
    ordre = models.PositiveIntegerField("ordre d'affichage", default=0)

    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "service"
        verbose_name_plural = "services"
        ordering = ["ordre", "nom"]

    def __str__(self):
        return f"{self.nom} — {self.prix} XAF"
