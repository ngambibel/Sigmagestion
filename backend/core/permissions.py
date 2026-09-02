"""Classes de permission explicites par rôle (aucune vue ne repose sur le défaut)."""
from rest_framework.permissions import BasePermission

from apps.comptes.models import Role


def _role(request):
    utilisateur = getattr(request, "user", None)
    if not (utilisateur and utilisateur.is_authenticated):
        return None
    return utilisateur.role


class EstProprietaire(BasePermission):
    """Propriétaire (ou super-administrateur)."""

    message = "Réservé au propriétaire du secrétariat."

    def has_permission(self, request, view):
        return _role(request) in (Role.PROPRIETAIRE, Role.SUPER_ADMIN)


class EstGerantOuPlus(BasePermission):
    """Gérant, propriétaire ou super-administrateur."""

    message = "Réservé au gérant ou au propriétaire."

    def has_permission(self, request, view):
        return _role(request) in (Role.GERANT, Role.PROPRIETAIRE, Role.SUPER_ADMIN)


class EstMembreDuSecretariat(BasePermission):
    """L'utilisateur appartient au secrétariat de l'objet visé."""

    message = "Cette ressource n'appartient pas à votre secrétariat."

    def has_object_permission(self, request, view, obj):
        utilisateur = request.user
        if not utilisateur.is_authenticated:
            return False
        if utilisateur.role == Role.SUPER_ADMIN:
            return True
        # Secrétariat lui-même, ou objet portant un champ `secretariat`.
        from apps.secretariats.models import Secretariat

        secretariat_cible = obj if isinstance(obj, Secretariat) else getattr(obj, "secretariat", None)
        if secretariat_cible is None:
            return False
        return (
            secretariat_cible.proprietaire_id == utilisateur.id
            or secretariat_cible.id == utilisateur.secretariat_id
        )
