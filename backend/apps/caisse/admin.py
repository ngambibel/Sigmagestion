from django.contrib import admin

from .models import SessionCaisse


@admin.register(SessionCaisse)
class SessionCaisseAdmin(admin.ModelAdmin):
    list_display = ("employe", "secretariat", "fond_initial", "statut", "ouverte_le", "cloturee_le")
    list_filter = ("statut",)
    search_fields = ("employe__nom",)
