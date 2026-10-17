"""Serializers des secrétariats."""
from rest_framework import serializers

from .models import ParametreNotification, PlageHoraire, Secretariat


class SecretariatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Secretariat
        fields = [
            "id", "nom", "code", "ville", "quartier",
            "telephone", "devise", "onboarding_termine", "proprietaire", "cree_le",
        ]
        read_only_fields = ["id", "code", "proprietaire", "cree_le"]

    def create(self, donnees):
        # Le code est généré automatiquement à partir du nom.
        donnees["code"] = Secretariat.generer_code_unique(donnees["nom"])
        return super().create(donnees)


class PlageHoraireSerializer(serializers.ModelSerializer):
    jour_libelle = serializers.CharField(source="get_jour_display", read_only=True)

    class Meta:
        model = PlageHoraire
        fields = ["jour", "jour_libelle", "ouvert", "heure_debut", "heure_fin"]

    def validate(self, donnees):
        debut = donnees.get("heure_debut")
        fin = donnees.get("heure_fin")
        if donnees.get("ouvert") and debut is not None and fin is not None and debut >= fin:
            raise serializers.ValidationError(
                "L'heure de fermeture doit être après l'heure d'ouverture."
            )
        return donnees


class ParametreNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParametreNotification
        fields = [
            "intervalle_ca_min", "alerte_ca_on", "alerte_stock_on",
            "bilan_jour_on", "seuil_ecart_caisse",
            "dernier_envoi_ca", "dernier_bilan_jour",
        ]
        read_only_fields = ["dernier_envoi_ca", "dernier_bilan_jour"]

    def validate_intervalle_ca_min(self, valeur):
        if valeur not in ParametreNotification.INTERVALLES:
            raise serializers.ValidationError(
                f"Intervalle autorisé : {ParametreNotification.INTERVALLES} minutes."
            )
        return valeur
