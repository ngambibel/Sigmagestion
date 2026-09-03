"""Serializers des ventes."""
from rest_framework import serializers

from .models import LignePrestation, ModePaiement, Prestation


class LignePrestationSerializer(serializers.ModelSerializer):
    montant = serializers.IntegerField(read_only=True)

    class Meta:
        model = LignePrestation
        fields = ["id", "service", "nom_service", "prix_unitaire", "quantite", "cout_unitaire", "montant"]


class PrestationSerializer(serializers.ModelSerializer):
    lignes = LignePrestationSerializer(many=True, read_only=True)
    employe_nom = serializers.CharField(source="employe.nom", read_only=True)

    class Meta:
        model = Prestation
        fields = [
            "id", "numero", "statut", "mode_paiement", "nom_client", "remise",
            "montant_total", "montant_recu", "monnaie_rendue", "employe_nom", "lignes",
            "annulee_le", "motif_annulation", "cree_le",
        ]


class LigneSaisieSerializer(serializers.Serializer):
    service = serializers.IntegerField()
    quantite = serializers.IntegerField(min_value=1)


class PrestationCreationSerializer(serializers.Serializer):
    lignes = LigneSaisieSerializer(many=True)
    mode_paiement = serializers.ChoiceField(choices=ModePaiement.choices)
    remise = serializers.IntegerField(min_value=0, default=0)
    montant_recu = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    nom_client = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_lignes(self, valeur):
        if not valeur:
            raise serializers.ValidationError("Le ticket est vide.")
        return valeur
