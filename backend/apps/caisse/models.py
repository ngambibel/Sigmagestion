"""Sessions de caisse : chaque opérateur ouvre et clôture sa caisse."""
from django.db import models


class StatutSession(models.TextChoices):
    OUVERTE = "ouverte", "Ouverte"
    CLOTUREE = "cloturee", "Clôturée"


class SessionCaisse(models.Model):
    """Une session de caisse d'un opérateur, du fond initial à la clôture."""

    secretariat = models.ForeignKey(
        "secretariats.Secretariat", on_delete=models.CASCADE, related_name="sessions_caisse",
    )
    employe = models.ForeignKey(
        "comptes.Utilisateur", on_delete=models.PROTECT, related_name="sessions_caisse",
    )
    fond_initial = models.PositiveIntegerField("fond de caisse initial (XAF)", default=0)
    statut = models.CharField(
        "statut", max_length=10, choices=StatutSession.choices, default=StatutSession.OUVERTE,
    )

    # Renseignés à la clôture (étape 3.5).
    montant_theorique = models.IntegerField("montant théorique (XAF)", null=True, blank=True)
    montant_compte = models.IntegerField("montant compté (XAF)", null=True, blank=True)
    ecart = models.IntegerField("écart (XAF)", null=True, blank=True)
    commentaire = models.CharField("commentaire de clôture", max_length=255, blank=True, default="")

    ouverte_le = models.DateTimeField("ouverte le", auto_now_add=True)
    cloturee_le = models.DateTimeField("clôturée le", null=True, blank=True)

    class Meta:
        verbose_name = "session de caisse"
        verbose_name_plural = "sessions de caisse"
        ordering = ["-ouverte_le"]
        constraints = [
            # RG-11 : au plus une session ouverte par employé.
            models.UniqueConstraint(
                fields=["employe"],
                condition=models.Q(statut="ouverte"),
                name="une_seule_session_ouverte_par_employe",
            ),
        ]

    def __str__(self):
        return f"Session {self.employe.nom} — {self.get_statut_display()}"

    @property
    def est_ouverte(self) -> bool:
        return self.statut == StatutSession.OUVERTE
