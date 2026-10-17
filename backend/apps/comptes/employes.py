"""Gestion des employés par le propriétaire (M8).

Création avec mot de passe provisoire (partage WhatsApp), changement imposé à la
première connexion, désactivation (jamais de suppression) avec clôture auto de la
session ouverte, et fiche de suivi d'activité.
"""
import secrets
import string

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import EstProprietaire
from core.tenancy import secretariat_actif

from .models import Role, Utilisateur
from .validators import normaliser_telephone


def _mot_de_passe_provisoire() -> str:
    """Génère un mot de passe provisoire lisible (8 car., ni 100 % numérique)."""
    lettres = "".join(secrets.choice(string.ascii_uppercase) for _ in range(2))
    chiffres = "".join(secrets.choice(string.digits) for _ in range(6))
    return f"{lettres}{chiffres}"


class EmployeSerializer(serializers.ModelSerializer):
    role_libelle = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = Utilisateur
        fields = [
            "id", "nom", "telephone", "role", "role_libelle",
            "is_active", "doit_changer_mdp", "date_joined",
        ]
        read_only_fields = fields


class EmployeCreationSerializer(serializers.Serializer):
    nom = serializers.CharField(max_length=150)
    telephone = serializers.CharField()
    role = serializers.ChoiceField(choices=[Role.EMPLOYE, Role.GERANT], default=Role.EMPLOYE)

    def validate_telephone(self, valeur):
        try:
            valeur = normaliser_telephone(valeur)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        if Utilisateur.objects.filter(telephone=valeur).exists():
            raise serializers.ValidationError("Ce numéro est déjà utilisé.")
        return valeur


class EmployeViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet,
):
    """CRUD des employés/gérants d'un secrétariat (propriétaire uniquement)."""

    serializer_class = EmployeSerializer
    permission_classes = [EstProprietaire]

    def get_queryset(self):
        secretariat = secretariat_actif(self.request)
        if secretariat is None:
            return Utilisateur.objects.none()
        return Utilisateur.objects.filter(
            secretariat=secretariat, role__in=[Role.EMPLOYE, Role.GERANT],
        ).order_by("-is_active", "nom")

    def create(self, request, *args, **kwargs):
        secretariat = secretariat_actif(request)
        if secretariat is None:
            return Response({"detail": "Aucun secrétariat actif."}, status=400)

        entree = EmployeCreationSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        donnees = entree.validated_data

        mot_de_passe = _mot_de_passe_provisoire()
        employe = Utilisateur(
            nom=donnees["nom"], telephone=donnees["telephone"], role=donnees["role"],
            secretariat=secretariat, doit_changer_mdp=True,
        )
        employe.set_password(mot_de_passe)
        employe.save()

        # Le mot de passe provisoire n'est renvoyé qu'ici, une seule fois.
        sortie = EmployeSerializer(employe).data
        sortie["mot_de_passe_provisoire"] = mot_de_passe
        return Response(sortie, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def desactiver(self, request, pk=None):
        """POST /employes/{id}/desactiver/ — désactive (jamais de suppression) + clôt la session."""
        from apps.caisse.models import SessionCaisse, StatutSession
        from apps.caisse.services import montant_theorique_session

        employe = self.get_object()
        employe.is_active = False
        employe.save(update_fields=["is_active"])

        # Clôture automatique de la session ouverte éventuelle (M8.2).
        session = SessionCaisse.objects.filter(
            employe=employe, statut=StatutSession.OUVERTE,
        ).first()
        if session is not None:
            session.statut = StatutSession.CLOTUREE
            session.cloturee_le = timezone.now()
            session.montant_theorique = montant_theorique_session(session)
            session.commentaire = "Clôture automatique (désactivation du compte)."
            session.save(update_fields=[
                "statut", "cloturee_le", "montant_theorique", "commentaire",
            ])
        return Response(EmployeSerializer(employe).data)

    @action(detail=True, methods=["post"])
    def reactiver(self, request, pk=None):
        """POST /employes/{id}/reactiver/ — réactive un compte désactivé."""
        employe = self.get_object()
        employe.is_active = True
        employe.save(update_fields=["is_active"])
        return Response(EmployeSerializer(employe).data)

    @action(detail=True, methods=["get"])
    def activite(self, request, pk=None):
        """GET /employes/{id}/activite/ — fiche de suivi (sessions, CA, écarts, annulations)."""
        from apps.caisse.models import SessionCaisse
        from apps.ventes.models import Prestation, StatutPrestation

        employe = self.get_object()
        ventes = Prestation.objects.filter(employe=employe, secretariat=employe.secretariat)
        validees = ventes.filter(statut=StatutPrestation.VALIDEE).aggregate(
            ca=Sum("montant_total"), nb=Count("id"),
        )
        sessions = SessionCaisse.objects.filter(
            employe=employe, secretariat=employe.secretariat,
        ).aggregate(
            nb=Count("id"),
            ecart_cumule=Sum("ecart"),
            nb_ecarts=Count("id", filter=~Q(ecart=0) & Q(ecart__isnull=False)),
        )
        return Response({
            "employe": EmployeSerializer(employe).data,
            "ca_genere": validees["ca"] or 0,
            "nb_prestations": validees["nb"] or 0,
            "nb_annulations": ventes.filter(statut=StatutPrestation.ANNULEE).count(),
            "nb_sessions": sessions["nb"] or 0,
            "ecart_cumule": sessions["ecart_cumule"] or 0,
            "nb_sessions_avec_ecart": sessions["nb_ecarts"] or 0,
        })


class ChangerMotDePasseSerializer(serializers.Serializer):
    nouveau_mot_de_passe = serializers.CharField(write_only=True)

    def validate_nouveau_mot_de_passe(self, valeur):
        try:
            validate_password(valeur)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return valeur


class ChangerMotDePasseView(APIView):
    """POST /moi/changer-mot-de-passe/ — change son propre mot de passe (fin du provisoire)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangerMotDePasseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        utilisateur = request.user
        utilisateur.set_password(serializer.validated_data["nouveau_mot_de_passe"])
        utilisateur.doit_changer_mdp = False
        utilisateur.save(update_fields=["password", "doit_changer_mdp"])
        return Response({"detail": "Mot de passe mis à jour."})
