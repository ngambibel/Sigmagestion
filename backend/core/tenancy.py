"""Isolation multi-locataire : chaque requête est cloisonnée à un secrétariat.

Règle RG-14 du cahier des charges : toute requête est filtrée par le secrétariat
de l'utilisateur authentifié, sans exception.
"""
from apps.comptes.models import Role


def secretariat_actif(request):
    """Retourne le secrétariat courant de l'utilisateur authentifié, ou None."""
    utilisateur = getattr(request, "user", None)
    if not (utilisateur and utilisateur.is_authenticated):
        return None
    return utilisateur.secretariat


class TenantQuerySetMixin:
    """À appliquer à tout ViewSet dont le modèle porte un champ `secretariat`.

    - `get_queryset` ne renvoie que les objets du secrétariat actif.
    - `perform_create` rattache automatiquement l'objet au secrétariat actif.

    Un utilisateur sans secrétariat actif ne voit rien (queryset vide), ce qui
    produit un 404 sur tout accès détaillé — l'isolation par défaut est fermée.
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        utilisateur = self.request.user
        if utilisateur.is_authenticated and utilisateur.role == Role.SUPER_ADMIN:
            return queryset
        secretariat = secretariat_actif(self.request)
        if secretariat is None:
            return queryset.none()
        return queryset.filter(secretariat=secretariat)

    def perform_create(self, serializer):
        serializer.save(secretariat=secretariat_actif(self.request))
