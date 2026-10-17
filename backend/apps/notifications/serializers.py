"""Serializers des notifications push."""
from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    type_libelle = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id", "type", "type_libelle", "titre", "corps",
            "url", "lu", "archivee", "cree_le",
        ]
        read_only_fields = fields


class AbonnementInputSerializer(serializers.Serializer):
    """Abonnement PushSubscription tel qu'envoyé par le navigateur."""

    endpoint = serializers.URLField()
    keys = serializers.DictField(child=serializers.CharField())
    navigateur = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_keys(self, valeur):
        if "p256dh" not in valeur or "auth" not in valeur:
            raise serializers.ValidationError("Clés p256dh et auth requises.")
        return valeur
