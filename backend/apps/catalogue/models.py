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
    image = models.ImageField(
        "image", upload_to="services/", null=True, blank=True,
        help_text="Photo/pictogramme du service, pour une reconnaissance rapide au comptoir.",
    )
    ordre = models.PositiveIntegerField("ordre d'affichage", default=0)

    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "service"
        verbose_name_plural = "services"
        ordering = ["ordre", "nom"]

    def __str__(self):
        return f"{self.nom} — {self.prix} XAF"

    @property
    def activable(self) -> bool:
        """RG-06 : un service consommateur doit avoir une nomenclature pour être activable."""
        if not self.consomme_stock:
            return True
        return self.lignes_nomenclature.exists()


class NomenclatureService(models.Model):
    """Recette d'un service : quel consommable, en quelle quantité par unité vendue.

    Exemple : « Impression N&B » → 1 feuille A4 + 0,004 cartouche toner noir.
    La quantité accepte 4 décimales pour modéliser le rendement des toners.
    """

    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="lignes_nomenclature",
    )
    consommable = models.ForeignKey(
        "stocks.Consommable", on_delete=models.PROTECT, related_name="nomenclatures",
    )
    qte_par_unite = models.DecimalField(
        "quantité par unité vendue", max_digits=10, decimal_places=4,
    )

    class Meta:
        verbose_name = "ligne de nomenclature"
        verbose_name_plural = "nomenclature"
        unique_together = ("service", "consommable")

    def __str__(self):
        return f"{self.service.nom} : {self.qte_par_unite} × {self.consommable.nom}"
