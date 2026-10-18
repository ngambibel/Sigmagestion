"""Journal d'audit (RG-16) : trace des opérations sensibles avec avant/après."""
from django.db import models


class ActionAudit(models.TextChoices):
    PRIX_MODIFIE = "prix_modifie", "Modification de prix"
    STOCK_AJUSTE = "stock_ajuste", "Ajustement de stock"
    PRESTATION_ANNULEE = "prestation_annulee", "Annulation de prestation"
    COMPTE_DESACTIVE = "compte_desactive", "Désactivation de compte"
    COMPTE_REACTIVE = "compte_reactive", "Réactivation de compte"


class JournalAudit(models.Model):
    secretariat = models.ForeignKey(
        "secretariats.Secretariat", on_delete=models.CASCADE, related_name="journal_audit",
        null=True, blank=True,
    )
    auteur = models.ForeignKey(
        "comptes.Utilisateur", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="actions_audit",
    )
    action = models.CharField("action", max_length=30, choices=ActionAudit.choices)
    modele = models.CharField("modèle", max_length=50)
    objet_id = models.CharField("identifiant objet", max_length=50, blank=True, default="")
    objet_repr = models.CharField("objet", max_length=200, blank=True, default="")
    valeurs_avant = models.JSONField("valeurs avant", null=True, blank=True)
    valeurs_apres = models.JSONField("valeurs après", null=True, blank=True)
    ip = models.GenericIPAddressField("adresse IP", null=True, blank=True)
    cree_le = models.DateTimeField("horodatage", auto_now_add=True)

    class Meta:
        verbose_name = "entrée d'audit"
        verbose_name_plural = "journal d'audit"
        ordering = ["-cree_le"]
        indexes = [models.Index(fields=["secretariat", "cree_le"])]

    def __str__(self):
        return f"{self.get_action_display()} — {self.objet_repr} ({self.cree_le:%Y-%m-%d %H:%M})"
