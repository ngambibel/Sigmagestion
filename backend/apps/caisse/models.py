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


class CategorieDepense(models.TextChoices):
    FOURNITURE = "fourniture", "Fourniture"
    TRANSPORT = "transport", "Transport"
    ELECTRICITE = "electricite", "Électricité / eau"
    MAINTENANCE = "maintenance", "Maintenance"
    SALAIRE = "salaire", "Salaire / avance"
    AUTRE = "autre", "Autre"


class Depense(models.Model):
    """Sortie de caisse rattachée à une session."""

    secretariat = models.ForeignKey(
        "secretariats.Secretariat", on_delete=models.CASCADE, related_name="depenses",
    )
    session = models.ForeignKey(
        SessionCaisse, on_delete=models.PROTECT, related_name="depenses",
    )
    categorie = models.CharField(
        "catégorie", max_length=15, choices=CategorieDepense.choices,
        default=CategorieDepense.AUTRE,
    )
    montant = models.PositiveIntegerField("montant (XAF)")
    description = models.CharField("description", max_length=255, blank=True, default="")
    justificatif = models.ImageField(
        "justificatif", upload_to="depenses/", null=True, blank=True,
    )
    auteur = models.ForeignKey(
        "comptes.Utilisateur", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="depenses",
    )
    cree_le = models.DateTimeField("créé le", auto_now_add=True)

    class Meta:
        verbose_name = "dépense"
        verbose_name_plural = "dépenses"
        ordering = ["-cree_le"]

    def __str__(self):
        return f"{self.get_categorie_display()} — {self.montant} XAF"
