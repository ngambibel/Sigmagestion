"""Vues des secrétariats."""
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comptes.models import Role
from core.permissions import EstProprietaire

from .models import ParametreNotification, Secretariat, plages_par_defaut
from .serializers import (
    ParametreNotificationSerializer,
    PlageHoraireSerializer,
    SecretariatSerializer,
)


class SecretariatViewSet(viewsets.ModelViewSet):
    """CRUD des secrétariats.

    Isolation : un utilisateur ne voit que les secrétariats qu'il possède
    ou auquel il est rattaché. Un accès à un autre secrétariat donne un 404
    (il est simplement hors du queryset).
    """

    serializer_class = SecretariatSerializer

    def get_permissions(self):
        # Création / modification / suppression réservées au propriétaire.
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [EstProprietaire()]
        return [IsAuthenticated()]

    def get_queryset(self):
        utilisateur = self.request.user
        if utilisateur.role == Role.SUPER_ADMIN:
            return Secretariat.objects.all()
        return Secretariat.objects.filter(
            Q(proprietaire=utilisateur) | Q(id=utilisateur.secretariat_id)
        ).distinct()

    def perform_create(self, serializer):
        secretariat = serializer.save(proprietaire=self.request.user)
        # Premier secrétariat → devient le secrétariat actif du propriétaire.
        utilisateur = self.request.user
        if utilisateur.secretariat_id is None:
            utilisateur.secretariat = secretariat
            utilisateur.save(update_fields=["secretariat"])


def _secretariat_du_proprietaire(request, secretariat_id) -> Secretariat:
    """Renvoie le secrétariat demandé s'il appartient à l'utilisateur, sinon 404.

    Barrière d'isolation : un propriétaire ne configure que ses propres secrétariats.
    """
    base = Secretariat.objects.all()
    if request.user.role != Role.SUPER_ADMIN:
        base = base.filter(proprietaire=request.user)
    return get_object_or_404(base, pk=secretariat_id)


class PlagesHorairesView(APIView):
    """GET/PUT /secretariats/{id}/plages-horaires/ — horaires hebdomadaires (RG-09)."""

    permission_classes = [EstProprietaire]

    def get(self, request, secretariat_id):
        secretariat = _secretariat_du_proprietaire(request, secretariat_id)
        plages = plages_par_defaut(secretariat)  # crée les 7 jours au besoin
        return Response(PlageHoraireSerializer(plages, many=True).data)

    def put(self, request, secretariat_id):
        secretariat = _secretariat_du_proprietaire(request, secretariat_id)
        serializer = PlageHoraireSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        for ligne in serializer.validated_data:
            secretariat.plages_horaires.update_or_create(
                jour=ligne["jour"],
                defaults={
                    "ouvert": ligne.get("ouvert", True),
                    "heure_debut": ligne["heure_debut"],
                    "heure_fin": ligne["heure_fin"],
                },
            )
        plages = plages_par_defaut(secretariat)
        return Response(PlageHoraireSerializer(plages, many=True).data)


class ParametresNotificationView(APIView):
    """GET/PATCH /secretariats/{id}/parametres-notification/ — réglages de notification."""

    permission_classes = [EstProprietaire]

    def get(self, request, secretariat_id):
        secretariat = _secretariat_du_proprietaire(request, secretariat_id)
        parametre, _ = ParametreNotification.objects.get_or_create(secretariat=secretariat)
        return Response(ParametreNotificationSerializer(parametre).data)

    def patch(self, request, secretariat_id):
        secretariat = _secretariat_du_proprietaire(request, secretariat_id)
        parametre, _ = ParametreNotification.objects.get_or_create(secretariat=secretariat)
        serializer = ParametreNotificationSerializer(parametre, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
