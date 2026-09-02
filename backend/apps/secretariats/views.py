"""Vues des secrétariats."""
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.comptes.models import Role
from core.permissions import EstProprietaire

from .models import Secretariat
from .serializers import SecretariatSerializer


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
