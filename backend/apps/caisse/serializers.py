"""Serializers de la caisse."""
from rest_framework import serializers

from .models import SessionCaisse


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
