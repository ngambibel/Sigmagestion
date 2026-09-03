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
    derniere_alerte_le = models.DateTimeField(
        "dernière alerte de seuil", null=True, blank=True,
        help_text="Anti-spam RG-08 : au plus une alerte par 24 h tant que le stock reste bas.",
    )

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


class TypeMouvement(models.TextChoices):
    ENTREE = "entree", "Entrée (réapprovisionnement)"
    SORTIE_VENTE = "sortie_vente", "Sortie (vente)"
    AJUSTEMENT = "ajustement", "Ajustement"
    ANNULATION = "annulation", "Annulation"


class MouvementStock(models.Model):
    """Trace immuable de chaque variation de stock. Source de vérité du `qte_stock`."""

    secretariat = models.ForeignKey(
        "secretariats.Secretariat", on_delete=models.CASCADE, related_name="mouvements_stock",
    )
    consommable = models.ForeignKey(
        Consommable, on_delete=models.PROTECT, related_name="mouvements",
    )
    type = models.CharField("type", max_length=15, choices=TypeMouvement.choices)
    quantite = models.DecimalField(
        "quantité (signée)", max_digits=12, decimal_places=2,
        help_text="Positive pour une entrée, négative pour une sortie.",
    )
    stock_avant = models.DecimalField("stock avant", max_digits=12, decimal_places=2)
    stock_apres = models.DecimalField("stock après", max_digits=12, decimal_places=2)
    prix_achat_unitaire = models.PositiveIntegerField(
        "prix d'achat unitaire du lot (XAF)", null=True, blank=True,
    )
    motif = models.CharField("motif", max_length=255, blank=True, default="")
    prestation = models.ForeignKey(
        "ventes.Prestation", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="mouvements_stock",
    )
    auteur = models.ForeignKey(
        "comptes.Utilisateur", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="mouvements_stock",
    )
    cree_le = models.DateTimeField("créé le", auto_now_add=True)

    class Meta:
        verbose_name = "mouvement de stock"
        verbose_name_plural = "mouvements de stock"
        ordering = ["-cree_le"]

    def __str__(self):
        return f"{self.get_type_display()} {self.quantite} × {self.consommable.nom}"
