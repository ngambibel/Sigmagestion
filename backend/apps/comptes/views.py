"""Vues d'authentification et de profil."""
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import ConnexionSerializer, MoiSerializer


class ConnexionView(TokenObtainPairView):
    """POST /auth/connexion/ — téléphone + mot de passe → paire de tokens."""

    serializer_class = ConnexionSerializer


class DeconnexionView(APIView):
    """POST /auth/deconnexion/ — invalide le refresh token (liste noire)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response(
                {"detail": "Le champ 'refresh' est requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(refresh).blacklist()
        except TokenError:
            return Response(
                {"detail": "Token invalide ou déjà expiré."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MoiView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /moi/ — profil de l'utilisateur courant."""

    serializer_class = MoiSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
