"""Serializers du catalogue."""
from decimal import Decimal

from rest_framework import serializers

from apps.stocks.models import Consommable

from .models import NomenclatureService, Service


class ServiceSerializer(serializers.ModelSerializer):
    activable = serializers.BooleanField(read_only=True)
    recto_verso_possible = serializers.BooleanField(read_only=True)

    class Meta:
        model = Service
        fields = [
            "id", "nom", "categorie", "unite_facturation", "prix",
            "consomme_stock", "actif", "couleur", "icone", "image", "ordre",
            "activable", "recto_verso_possible",
        ]
        read_only_fields = ["id", "activable", "recto_verso_possible"]

    def validate(self, attrs):
        """RG-06 : on ne peut pas *activer* un service consommateur sans nomenclature."""
        if self.instance is None:
            return attrs  # à la création, la nomenclature se définit ensuite
        actif_demande = attrs.get("actif", None)
        consomme = attrs.get("consomme_stock", self.instance.consomme_stock)
        transition_vers_actif = actif_demande is True and not self.instance.actif
        if consomme and transition_vers_actif and not self.instance.lignes_nomenclature.exists():
            raise serializers.ValidationError(
                {"actif": "Définissez d'abord la nomenclature (au moins un consommable)."}
            )
        return attrs


class NomenclatureLigneSerializer(serializers.ModelSerializer):
    """Lecture d'une ligne de nomenclature."""

    consommable_nom = serializers.CharField(source="consommable.nom", read_only=True)
    unite_mesure = serializers.CharField(source="consommable.unite_mesure", read_only=True)

    class Meta:
        model = NomenclatureService
        fields = [
            "id", "consommable", "consommable_nom", "unite_mesure",
            "qte_par_unite", "divise_en_recto_verso",
        ]


class NomenclatureEcritureLigneSerializer(serializers.Serializer):
    """Écriture d'une ligne (dans le PUT de la nomenclature complète)."""

    consommable = serializers.IntegerField()
    qte_par_unite = serializers.DecimalField(
        max_digits=10, decimal_places=4, min_value=Decimal("0"),
    )
    divise_en_recto_verso = serializers.BooleanField(required=False, default=False)

    def validate_consommable(self, valeur):
        secretariat = self.context["secretariat"]
        if not Consommable.objects.filter(id=valeur, secretariat=secretariat).exists():
            raise serializers.ValidationError("Consommable inconnu dans ce secrétariat.")
        return valeur
