"""Modèle Utilisateur personnalisé — téléphone comme identifiant principal."""
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class Role(models.TextChoices):
    SUPER_ADMIN = "super_admin", "Super-administrateur"
    PROPRIETAIRE = "proprietaire", "Propriétaire"
    GERANT = "gerant", "Gérant"
    EMPLOYE = "employe", "Employé"


class UtilisateurManager(BaseUserManager):
    """Gestionnaire d'utilisateurs identifiés par leur téléphone."""

    use_in_migrations = True

    def _creer(self, telephone, password, **extra):
        if not telephone:
            raise ValueError("Le numéro de téléphone est obligatoire.")
        utilisateur = self.model(telephone=telephone, **extra)
        utilisateur.set_password(password)
        utilisateur.save(using=self._db)
        return utilisateur

    def create_user(self, telephone, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._creer(telephone, password, **extra)

    def create_superuser(self, telephone, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", Role.SUPER_ADMIN)
        if extra.get("is_staff") is not True:
            raise ValueError("Un super-utilisateur doit avoir is_staff=True.")
        if extra.get("is_superuser") is not True:
            raise ValueError("Un super-utilisateur doit avoir is_superuser=True.")
        return self._creer(telephone, password, **extra)


class Utilisateur(AbstractUser):
    """Utilisateur de SigmaGestion.

    Le téléphone remplace le nom d'utilisateur comme identifiant de connexion.
    """

    # On neutralise les champs hérités que l'on ne veut pas.
    username = None
    first_name = None
    last_name = None

    telephone = models.CharField(
        "téléphone", max_length=20, unique=True,
        help_text="Format camerounais, ex. +237 6XX XXX XXX",
    )
    nom = models.CharField("nom complet", max_length=150)
    role = models.CharField(
        "rôle", max_length=20, choices=Role.choices, default=Role.EMPLOYE,
    )
    doit_changer_mdp = models.BooleanField(
        "doit changer de mot de passe", default=False,
        help_text="Vrai après création par le propriétaire (mot de passe provisoire).",
    )
    code_pin_hash = models.CharField(
        "empreinte du code PIN", max_length=128, blank=True, default="",
    )
    secretariat = models.ForeignKey(
        "secretariats.Secretariat",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="membres",
        verbose_name="secrétariat actif",
        help_text="Secrétariat de rattachement (employés/gérants) ou secrétariat courant.",
    )

    USERNAME_FIELD = "telephone"
    REQUIRED_FIELDS = ["nom"]

    objects = UtilisateurManager()

    class Meta:
        verbose_name = "utilisateur"
        verbose_name_plural = "utilisateurs"

    def __str__(self):
        return f"{self.nom} ({self.telephone})"

    # --- Code PIN de déverrouillage rapide ---
    def definir_code_pin(self, code_pin):
        """Hache et enregistre un code PIN à 4 chiffres."""
        self.code_pin_hash = make_password(code_pin)

    def verifier_code_pin(self, code_pin):
        """Vérifie un code PIN fourni contre l'empreinte enregistrée."""
        if not self.code_pin_hash:
            return False
        return check_password(code_pin, self.code_pin_hash)
