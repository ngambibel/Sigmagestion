"""Serializers des clients et créances."""
from rest_framework import serializers

from .models import Client, Reglement


class ClientSerializer(serializers.ModelSerializer):
    type_libelle = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = Client
        fields = [
            "id", "nom", "telephone", "type", "type_libelle",
            "plafond_credit", "encours", "actif", "cree_le",
        ]
        read_only_fields = ["id", "encours", "cree_le"]


class ReglementSerializer(serializers.ModelSerializer):
    auteur_nom = serializers.CharField(source="auteur.nom", read_only=True, default="")

    class Meta:
        model = Reglement
        fields = ["id", "montant", "commentaire", "auteur_nom", "cree_le"]
        read_only_fields = fields
