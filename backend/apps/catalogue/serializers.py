"""Serializers du catalogue."""
from rest_framework import serializers

from .models import Service


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            "id", "nom", "categorie", "unite_facturation", "prix",
            "consomme_stock", "actif", "couleur", "icone", "ordre",
        ]
        read_only_fields = ["id"]
