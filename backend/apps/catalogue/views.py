"""Vues du catalogue."""
from django.db import transaction
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import EstProprietaire
from core.tenancy import TenantQuerySetMixin

from .models import NomenclatureService, Service
from .serializers import (
    NomenclatureEcritureLigneSerializer,
    NomenclatureLigneSerializer,
    ServiceSerializer,
)


class ServiceViewSet(TenantQuerySetMixin, viewsets.ModelViewSet):
    """CRUD des services, cloisonné au secrétariat actif."""

    serializer_class = ServiceSerializer
    queryset = Service.objects.all()

    def get_permissions(self):
        actions_ecriture = ("create", "update", "partial_update", "destroy")
        if self.action in actions_ecriture or (
            self.action == "nomenclature" and self.request.method == "PUT"
        ):
            return [EstProprietaire()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["get", "put"])
    def nomenclature(self, request, pk=None):
        """GET/PUT /services/{id}/nomenclature/ — recette du service."""
        service = self.get_object()

        if request.method == "GET":
            lignes = service.lignes_nomenclature.select_related("consommable")
            return Response(NomenclatureLigneSerializer(lignes, many=True).data)

        # PUT : on remplace intégralement la nomenclature.
        serializer = NomenclatureEcritureLigneSerializer(
            data=request.data, many=True, context={"secretariat": service.secretariat}
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            service.lignes_nomenclature.all().delete()
            NomenclatureService.objects.bulk_create(
                [
                    NomenclatureService(
                        service=service,
                        consommable_id=ligne["consommable"],
                        qte_par_unite=ligne["qte_par_unite"],
                    )
                    for ligne in serializer.validated_data
                ]
            )

        lignes = service.lignes_nomenclature.select_related("consommable")
        return Response(NomenclatureLigneSerializer(lignes, many=True).data)
