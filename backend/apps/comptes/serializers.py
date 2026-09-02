"""Serializers de l'authentification et du profil."""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Utilisateur


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


class MoiSerializer(serializers.ModelSerializer):
    """Profil de l'utilisateur courant."""

    class Meta:
        model = Utilisateur
        fields = [
            "id", "telephone", "nom", "email", "role",
            "doit_changer_mdp", "is_active", "date_joined",
        ]
        read_only_fields = ["id", "telephone", "role", "doit_changer_mdp", "date_joined"]
