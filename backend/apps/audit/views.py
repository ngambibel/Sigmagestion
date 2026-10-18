"""Vue du journal d'audit (propriétaire)."""
from rest_framework import mixins, viewsets

from core.permissions import EstProprietaire
from core.tenancy import secretariat_actif

from .models import JournalAudit
from .serializers import JournalAuditSerializer


class JournalAuditViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """GET /audit/ — journal des opérations sensibles du secrétariat (propriétaire).

    Filtrable par `?action=` et `?modele=`.
    """

    serializer_class = JournalAuditSerializer
    permission_classes = [EstProprietaire]

    def get_queryset(self):
        secretariat = secretariat_actif(self.request)
        qs = JournalAudit.objects.select_related("auteur")
        qs = qs.all() if secretariat is None else qs.filter(secretariat=secretariat)
        action = self.request.query_params.get("action")
        modele = self.request.query_params.get("modele")
        if action:
            qs = qs.filter(action=action)
        if modele:
            qs = qs.filter(modele=modele)
        return qs
