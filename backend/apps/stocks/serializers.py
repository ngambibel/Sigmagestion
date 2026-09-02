"""Serializers des stocks."""
from decimal import Decimal

from rest_framework import serializers

from .models import Consommable, MouvementStock


class ConsommableSerializer(serializers.ModelSerializer):
    sous_seuil = serializers.BooleanField(read_only=True)

    class Meta:
        model = Consommable
        fields = [
            "id", "nom", "unite_mesure", "prix_achat", "qte_stock",
            "seuil_alerte", "seuil_critique", "fournisseur", "actif", "sous_seuil",
        ]
        read_only_fields = ["id", "sous_seuil"]


class EntreeStockSerializer(serializers.Serializer):
    """Réapprovisionnement : quantité entrante + prix total du lot."""

    quantite = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01"),
    )
    prix_total_lot = serializers.IntegerField(min_value=0)
    fournisseur = serializers.CharField(required=False, allow_blank=True, default="")
    motif = serializers.CharField(required=False, allow_blank=True, default="")


class AjustementSerializer(serializers.Serializer):
    """Correction de stock : delta signé + motif obligatoire."""

    quantite_delta = serializers.DecimalField(max_digits=12, decimal_places=2)
    motif = serializers.CharField(max_length=255)

    def validate_quantite_delta(self, valeur):
        if valeur == 0:
            raise serializers.ValidationError("L'ajustement ne peut pas être nul.")
        return valeur

    def validate_motif(self, valeur):
        if not valeur.strip():
            raise serializers.ValidationError("Le motif est obligatoire.")
        return valeur


class MouvementStockSerializer(serializers.ModelSerializer):
    consommable_nom = serializers.CharField(source="consommable.nom", read_only=True)
    type_libelle = serializers.CharField(source="get_type_display", read_only=True)
    auteur_nom = serializers.CharField(source="auteur.nom", read_only=True, default="")

    class Meta:
        model = MouvementStock
        fields = [
            "id", "consommable", "consommable_nom", "type", "type_libelle",
            "quantite", "stock_avant", "stock_apres", "prix_achat_unitaire",
            "motif", "auteur_nom", "cree_le",
        ]
