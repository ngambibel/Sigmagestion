"""Serializers des ventes."""
from decimal import Decimal

from rest_framework import serializers

from .models import LignePrestation, ModePaiement, Prestation


class LignePrestationSerializer(serializers.ModelSerializer):
    montant = serializers.IntegerField(read_only=True)

    class Meta:
        model = LignePrestation
        fields = [
            "id", "service", "nom_service", "prix_unitaire", "prix_catalogue",
            "quantite", "cout_unitaire", "recto_verso", "montant",
        ]


class PrestationSerializer(serializers.ModelSerializer):
    lignes = LignePrestationSerializer(many=True, read_only=True)
    employe_nom = serializers.CharField(source="employe.nom", read_only=True)

    class Meta:
        model = Prestation
        fields = [
            "id", "numero", "statut", "mode_paiement", "client", "nom_client", "remise",
            "montant_total", "montant_recu", "monnaie_rendue", "employe_nom", "lignes",
            "client_uuid", "annulee_le", "motif_annulation", "cree_le",
        ]


class ConsommableChoisiSerializer(serializers.Serializer):
    """Consommable choisi librement au moment de la vente (écrase la recette)."""

    consommable = serializers.IntegerField()
    quantite = serializers.DecimalField(max_digits=10, decimal_places=4, min_value=Decimal("0"))


class LigneSaisieSerializer(serializers.Serializer):
    service = serializers.IntegerField()
    quantite = serializers.IntegerField(min_value=1)
    # Prix appliqué (rabais gros volume) ; absent = prix du catalogue.
    prix_unitaire = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    recto_verso = serializers.BooleanField(required=False, default=False)
    # Consommables choisis à la vente : s'ils sont fournis, ils remplacent la
    # recette du service pour le calcul du coût et la déduction du stock.
    consommables = ConsommableChoisiSerializer(many=True, required=False)


class PrestationCreationSerializer(serializers.Serializer):
    lignes = LigneSaisieSerializer(many=True)
    mode_paiement = serializers.ChoiceField(choices=ModePaiement.choices)
    remise = serializers.IntegerField(min_value=0, default=0)
    montant_recu = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    nom_client = serializers.CharField(required=False, allow_blank=True, default="")
    client = serializers.IntegerField(required=False, allow_null=True)
    client_uuid = serializers.UUIDField(required=False, allow_null=True)

    def validate_lignes(self, valeur):
        if not valeur:
            raise serializers.ValidationError("Le ticket est vide.")
        return valeur
