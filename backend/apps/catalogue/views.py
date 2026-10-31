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
    queryset = Service.objects.prefetch_related("lignes_nomenclature__consommable").all()

    def get_permissions(self):
        actions_ecriture = ("create", "update", "partial_update", "destroy")
        if self.action in actions_ecriture or (
            self.action == "nomenclature" and self.request.method == "PUT"
        ):
            return [EstProprietaire()]
        return [IsAuthenticated()]

    def perform_update(self, serializer):
        prix_avant = serializer.instance.prix
        service = serializer.save()
        if service.prix != prix_avant:
            from apps.audit.models import ActionAudit
            from apps.audit.services import tracer

            tracer(
                action=ActionAudit.PRIX_MODIFIE, instance=service, auteur=self.request.user,
                avant={"prix": prix_avant}, apres={"prix": service.prix}, request=self.request,
                objet_repr=service.nom,
            )

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
                        divise_en_recto_verso=ligne.get("divise_en_recto_verso", False),
                    )
                    for ligne in serializer.validated_data
                ]
            )
            # Une recette implique que le service consomme du stock : on aligne le
            # drapeau pour que la vente déduise le stock et calcule le coût, et que
            # les badges/activation restent cohérents.
            a_recette = bool(serializer.validated_data)
            if service.consomme_stock != a_recette:
                service.consomme_stock = a_recette
                service.save(update_fields=["consomme_stock"])

        lignes = service.lignes_nomenclature.select_related("consommable")
        return Response(NomenclatureLigneSerializer(lignes, many=True).data)
