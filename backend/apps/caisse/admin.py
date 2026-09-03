from django.contrib import admin

from .models import Depense, SessionCaisse


@admin.register(Depense)
class DepenseAdmin(admin.ModelAdmin):
    list_display = ("categorie", "montant", "session", "auteur", "cree_le")
    list_filter = ("categorie",)


@admin.register(SessionCaisse)
class SessionCaisseAdmin(admin.ModelAdmin):
    list_display = ("employe", "secretariat", "fond_initial", "statut", "ouverte_le", "cloturee_le")
    list_filter = ("statut",)
    search_fields = ("employe__nom",)
