"""Clients et créances (M9). L'encours est dénormalisé, mis à jour par les ventes
à crédit (incrément) et les règlements (décrément), toujours dans une transaction."""
from django.db import models


class TypeClient(models.TextChoices):
    PARTICULIER = "particulier", "Particulier"
    ENTREPRISE = "entreprise", "Entreprise"
    ADMINISTRATION = "administration", "Administration"


class Client(models.Model):
    secretariat = models.ForeignKey(
        "secretariats.Secretariat", on_delete=models.CASCADE, related_name="clients",
    )
    nom = models.CharField("nom", max_length=150)
    telephone = models.CharField("téléphone", max_length=20, blank=True, default="")
    type = models.CharField(
        "type", max_length=15, choices=TypeClient.choices, default=TypeClient.PARTICULIER,
    )
    plafond_credit = models.PositiveIntegerField(
        "plafond de crédit (XAF)", default=0,
        help_text="0 = pas de plafond. Sinon, l'encours ne peut pas le dépasser.",
    )
    encours = models.PositiveIntegerField(
        "encours de crédit (XAF)", default=0,
        help_text="Montant dû. Mis à jour par les ventes à crédit et les règlements.",
    )
    actif = models.BooleanField("actif", default=True)
    cree_le = models.DateTimeField("créé le", auto_now_add=True)

    class Meta:
        verbose_name = "client"
        verbose_name_plural = "clients"
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} (encours {self.encours} XAF)"


class Reglement(models.Model):
    """Un règlement (total ou partiel) d'une créance client."""

    secretariat = models.ForeignKey(
        "secretariats.Secretariat", on_delete=models.CASCADE, related_name="reglements",
    )
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="reglements")
    montant = models.PositiveIntegerField("montant (XAF)")
    commentaire = models.CharField("commentaire", max_length=255, blank=True, default="")
    auteur = models.ForeignKey(
        "comptes.Utilisateur", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reglements",
    )
    cree_le = models.DateTimeField("créé le", auto_now_add=True)

    class Meta:
        verbose_name = "règlement"
        verbose_name_plural = "règlements"
        ordering = ["-cree_le"]

    def __str__(self):
        return f"{self.montant} XAF — {self.client.nom}"
