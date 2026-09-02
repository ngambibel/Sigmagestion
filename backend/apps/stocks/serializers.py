"""Serializers des stocks."""
from rest_framework import serializers

from .models import Consommable


class ConsommableSerializer(serializers.ModelSerializer):
    sous_seuil = serializers.BooleanField(read_only=True)

    class Meta:
        model = Consommable
        fields = [
            "id", "nom", "unite_mesure", "prix_achat", "qte_stock",
            "seuil_alerte", "seuil_critique", "fournisseur", "actif", "sous_seuil",
        ]
        read_only_fields = ["id", "sous_seuil"]
