"""Charge l'app Celery avec Django pour l'enregistrement des tâches partagées."""
from .celery import app as celery_app

__all__ = ("celery_app",)
