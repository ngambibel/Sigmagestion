"""Serializers de l'authentification et du profil."""
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Role, Utilisateur
from .validators import normaliser_telephone


class ConnexionSerializer(TokenObtainPairSerializer):
    """Connexion par téléphone + mot de passe.

    Ajoute quelques informations utiles dans la réponse du token.
    """

    username_field = Utilisateur.USERNAME_FIELD  # "telephone"

    def validate(self, attrs):
        donnees = super().validate(attrs)
        donnees["doit_changer_mdp"] = self.user.doit_changer_mdp
        donnees["role"] = self.user.role
        donnees["nom"] = self.user.nom
        return donnees


class InscriptionSerializer(serializers.ModelSerializer):
    """Inscription d'un propriétaire (M1.1).

    Crée le compte, le connecte immédiatement (renvoie une paire de tokens).
    """

    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = Utilisateur
        fields = ["nom", "telephone", "email", "password"]
        extra_kwargs = {"email": {"required": False, "allow_blank": True}}

    def validate_telephone(self, valeur):
        try:
            valeur = normaliser_telephone(valeur)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        if Utilisateur.objects.filter(telephone=valeur).exists():
            raise serializers.ValidationError("Ce numéro est déjà utilisé.")
        return valeur

    def validate_password(self, valeur):
        try:
            validate_password(valeur)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return valeur

    def create(self, donnees):
        mot_de_passe = donnees.pop("password")
        utilisateur = Utilisateur(role=Role.PROPRIETAIRE, **donnees)
        utilisateur.set_password(mot_de_passe)
        utilisateur.save()
        return utilisateur

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "nom": instance.nom,
            "role": instance.role,
            "doit_changer_mdp": instance.doit_changer_mdp,
        }


class MoiSerializer(serializers.ModelSerializer):
    """Profil de l'utilisateur courant."""

    class Meta:
        model = Utilisateur
        fields = [
            "id", "telephone", "nom", "email", "role",
            "doit_changer_mdp", "is_active", "date_joined",
        ]
        read_only_fields = ["id", "telephone", "role", "doit_changer_mdp", "date_joined"]
