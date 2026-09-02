"""Modèle Consommable — les fournitures dont on suit le stock."""
from django.db import models


class Consommable(models.Model):
    """Une fourniture. `qte_stock` est dénormalisé : mis à jour par mouvement.

    (Les mouvements de stock et le CUMP arrivent en phase Stock ; ici on pose
    la fiche et le stock initial déclaré à l'installation.)
    """

    secretariat = models.ForeignKey(
        "secretariats.Secretariat",
        on_delete=models.CASCADE,
        related_name="consommables",
    )
    nom = models.CharField("nom", max_length=120)
    unite_mesure = models.CharField(
        "unité de mesure", max_length=30,
        help_text="feuille, spirale, pochette, cartouche, ramette…",
    )
    prix_achat = models.PositiveIntegerField(
        "prix d'achat unitaire (XAF)", default=0,
    )
    qte_stock = models.DecimalField(
        "quantité en stock", max_digits=12, decimal_places=2, default=0,
    )
    seuil_alerte = models.DecimalField(
        "seuil d'alerte", max_digits=12, decimal_places=2, default=0,
    )
    seuil_critique = models.DecimalField(
        "seuil critique", max_digits=12, decimal_places=2, null=True, blank=True,
    )
    fournisseur = models.CharField("fournisseur", max_length=120, blank=True, default="")
    actif = models.BooleanField("actif", default=True)

    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "consommable"
        verbose_name_plural = "consommables"
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} ({self.qte_stock} {self.unite_mesure})"

    @property
    def sous_seuil(self) -> bool:
        return self.qte_stock <= self.seuil_alerte
