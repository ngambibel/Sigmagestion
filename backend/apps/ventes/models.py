"""Prestations (ventes) et leurs lignes. Prix et coûts figés à la vente."""
from django.db import models


class StatutPrestation(models.TextChoices):
    VALIDEE = "validee", "Validée"
    ANNULEE = "annulee", "Annulée"


class ModePaiement(models.TextChoices):
    ESPECES = "especes", "Espèces"
    MOMO = "momo", "MTN MoMo"
    ORANGE = "orange_money", "Orange Money"
    CREDIT = "credit", "Crédit"


class Prestation(models.Model):
    """Une vente. Le numéro est séquentiel par secrétariat et par jour."""

    secretariat = models.ForeignKey(
        "secretariats.Secretariat", on_delete=models.CASCADE, related_name="prestations",
    )
    session = models.ForeignKey(
        "caisse.SessionCaisse", on_delete=models.PROTECT, related_name="prestations",
    )
    numero = models.CharField("numéro", max_length=30, unique=True)
    employe = models.ForeignKey(
        "comptes.Utilisateur", on_delete=models.PROTECT, related_name="prestations",
    )
    statut = models.CharField(
        max_length=10, choices=StatutPrestation.choices, default=StatutPrestation.VALIDEE,
    )
    mode_paiement = models.CharField(max_length=15, choices=ModePaiement.choices)

    client = models.ForeignKey(
        "clients.Client", on_delete=models.PROTECT, null=True, blank=True,
        related_name="prestations",
        help_text="Client rattaché pour une vente à crédit (RG-13).",
    )
    nom_client = models.CharField(
        "nom du client", max_length=150, blank=True, default="",
        help_text="Copie du nom du client pour une vente à crédit (qui doit l'argent).",
    )
    remise = models.PositiveIntegerField("remise (XAF)", default=0)
    montant_total = models.PositiveIntegerField("montant total (XAF)")
    montant_recu = models.PositiveIntegerField("montant reçu (XAF)", null=True, blank=True)
    monnaie_rendue = models.PositiveIntegerField("monnaie rendue (XAF)", null=True, blank=True)

    # Annulation (étape 3.4)
    annulee_le = models.DateTimeField(null=True, blank=True)
    motif_annulation = models.CharField(max_length=255, blank=True, default="")

    cree_le = models.DateTimeField("créé le", auto_now_add=True)

    class Meta:
        verbose_name = "prestation"
        verbose_name_plural = "prestations"
        ordering = ["-cree_le"]

    def __str__(self):
        return f"{self.numero} — {self.montant_total} XAF"


class LignePrestation(models.Model):
    """Une ligne de vente. Nom, prix et coût sont figés au moment de la vente."""

    prestation = models.ForeignKey(
        Prestation, on_delete=models.CASCADE, related_name="lignes",
    )
    service = models.ForeignKey(
        "catalogue.Service", on_delete=models.PROTECT, related_name="lignes_prestation",
    )
    nom_service = models.CharField("nom du service", max_length=120)
    prix_unitaire = models.PositiveIntegerField("prix unitaire appliqué, figé (XAF)")
    prix_catalogue = models.PositiveIntegerField(
        "prix catalogue au moment de la vente (XAF)", default=0,
        help_text="Prix de référence du service ; un prix appliqué inférieur traduit un rabais.",
    )
    quantite = models.PositiveIntegerField("quantité")
    cout_unitaire = models.PositiveIntegerField(
        "coût de revient unitaire figé (XAF)", default=0,
    )
    recto_verso = models.BooleanField(
        "recto-verso", default=False,
        help_text="Si vrai, la consommation de feuilles a été divisée par 2 (arrondi au supérieur).",
    )

    class Meta:
        verbose_name = "ligne de prestation"
        verbose_name_plural = "lignes de prestation"

    def __str__(self):
        return f"{self.quantite} × {self.nom_service}"

    @property
    def montant(self) -> int:
        return self.prix_unitaire * self.quantite
