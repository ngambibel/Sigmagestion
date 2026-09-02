"""Réglages de développement."""
from .base import *  # noqa: F401,F403

DEBUG = True

# En dev, on autorise toutes les origines (localhost, 127.0.0.1, IP LAN de Vite).
# L'authentification passe par un jeton dans l'en-tête, pas par un cookie,
# donc ouvrir le CORS ici ne présente pas de risque. La prod garde la liste stricte.
CORS_ALLOW_ALL_ORIGINS = True

# Confort dev : navigateur DRF activé
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]
