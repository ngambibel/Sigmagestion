"""Serializers de la caisse."""
from rest_framework import serializers

from .models import Depense, SessionCaisse


class SessionCaisseSerializer(serializers.ModelSerializer):
    employe_nom = serializers.CharField(source="employe.nom", read_only=True)

    class Meta:
        model = SessionCaisse
        fields = [
            "id", "employe", "employe_nom", "fond_initial", "statut",
            "montant_theorique", "montant_compte", "ecart", "commentaire",
            "ouverte_le", "cloturee_le",
        ]
        read_only_fields = [
            "id", "employe", "employe_nom", "statut", "montant_theorique",
            "montant_compte", "ecart", "commentaire", "ouverte_le", "cloturee_le",
        ]


class DepenseSerializer(serializers.ModelSerializer):
    categorie_libelle = serializers.CharField(source="get_categorie_display", read_only=True)
    auteur_nom = serializers.CharField(source="auteur.nom", read_only=True, default="")

    class Meta:
        model = Depense
        fields = [
            "id", "categorie", "categorie_libelle", "montant", "description",
            "justificatif", "auteur_nom", "cree_le",
        ]
        read_only_fields = ["id", "categorie_libelle", "auteur_nom", "cree_le"]


class ClotureSerializer(serializers.Serializer):
    montant_compte = serializers.IntegerField(min_value=0)
    commentaire = serializers.CharField(required=False, allow_blank=True, default="")
