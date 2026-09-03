"""Application Celery de SigmaGestion."""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("sigmagestion")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Tâche de diagnostic — vérifie que le worker traite bien les messages."""
    print(f"[celery] debug_task OK — requête {self.request!r}")
    return "ok"
