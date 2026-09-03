"""Abonnements aux notifications push (Web Push / VAPID)."""
from django.db import models


class AbonnementPush(models.Model):
    """Un appareil abonné aux notifications d'un utilisateur.

    Un utilisateur peut avoir plusieurs appareils (plusieurs abonnements).
    """

    secretariat = models.ForeignKey(
        "secretariats.Secretariat", on_delete=models.CASCADE,
        related_name="abonnements_push", null=True, blank=True,
    )
    utilisateur = models.ForeignKey(
        "comptes.Utilisateur", on_delete=models.CASCADE, related_name="abonnements_push",
    )
    endpoint = models.URLField("endpoint", max_length=500, unique=True)
    cle_p256dh = models.CharField("clé p256dh", max_length=255)
    cle_auth = models.CharField("clé auth", max_length=255)
    navigateur = models.CharField("navigateur", max_length=200, blank=True, default="")
    cree_le = models.DateTimeField("créé le", auto_now_add=True)

    class Meta:
        verbose_name = "abonnement push"
        verbose_name_plural = "abonnements push"
        ordering = ["-cree_le"]

    def __str__(self):
        return f"{self.utilisateur.nom} — {self.endpoint[:40]}…"

    def info_abonnement(self) -> dict:
        """Format attendu par pywebpush (subscription_info)."""
        return {
            "endpoint": self.endpoint,
            "keys": {"p256dh": self.cle_p256dh, "auth": self.cle_auth},
        }


class TypeNotification(models.TextChoices):
    STOCK_FAIBLE = "stock_faible", "Stock faible"
    BILAN_CA = "bilan_ca", "Bilan de chiffre d'affaires"
    ECART_CAISSE = "ecart_caisse", "Écart de caisse"
    AUTRE = "autre", "Autre"


class Notification(models.Model):
    """Notification persistée (centre de notifications dans l'app)."""

    secretariat = models.ForeignKey(
        "secretariats.Secretariat", on_delete=models.CASCADE, related_name="notifications",
    )
    utilisateur = models.ForeignKey(
        "comptes.Utilisateur", on_delete=models.CASCADE, related_name="notifications",
    )
    type = models.CharField(
        max_length=20, choices=TypeNotification.choices, default=TypeNotification.AUTRE,
    )
    titre = models.CharField(max_length=150)
    corps = models.CharField(max_length=500)
    url = models.CharField(max_length=200, blank=True, default="/")
    lu = models.BooleanField("lue", default=False)
    cree_le = models.DateTimeField("créé le", auto_now_add=True)

    class Meta:
        verbose_name = "notification"
        verbose_name_plural = "notifications"
        ordering = ["-cree_le"]

    def __str__(self):
        return f"{self.titre} → {self.utilisateur.nom}"
