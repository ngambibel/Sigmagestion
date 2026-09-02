"""Réglages de développement."""
from .base import *  # noqa: F401,F403

DEBUG = True

# Confort dev : navigateur DRF activé
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]
