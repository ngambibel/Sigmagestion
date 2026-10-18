"""Serializer du journal d'audit."""
from rest_framework import serializers

from .models import JournalAudit


class JournalAuditSerializer(serializers.ModelSerializer):
    action_libelle = serializers.CharField(source="get_action_display", read_only=True)
    auteur_nom = serializers.CharField(source="auteur.nom", read_only=True, default="—")

    class Meta:
        model = JournalAudit
        fields = [
            "id", "action", "action_libelle", "modele", "objet_id", "objet_repr",
            "valeurs_avant", "valeurs_apres", "auteur_nom", "ip", "cree_le",
        ]
        read_only_fields = fields
