"""Serializers des secrétariats."""
from rest_framework import serializers

from .models import Secretariat


class SecretariatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Secretariat
        fields = [
            "id", "nom", "code", "ville", "quartier",
            "telephone", "devise", "onboarding_termine", "proprietaire", "cree_le",
        ]
        read_only_fields = ["id", "code", "proprietaire", "cree_le"]

    def create(self, donnees):
        # Le code est généré automatiquement à partir du nom.
        donnees["code"] = Secretariat.generer_code_unique(donnees["nom"])
        return super().create(donnees)
