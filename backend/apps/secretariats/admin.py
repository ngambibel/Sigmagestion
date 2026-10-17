from django.contrib import admin

from .models import ParametreNotification, PlageHoraire, Secretariat


class PlageHoraireInline(admin.TabularInline):
    model = PlageHoraire
    extra = 0


@admin.register(Secretariat)
class SecretariatAdmin(admin.ModelAdmin):
    list_display = ("nom", "code", "ville", "proprietaire", "devise", "cree_le")
    search_fields = ("nom", "code", "ville", "quartier")
    list_filter = ("devise", "ville")
    readonly_fields = ("code", "cree_le", "modifie_le")
    inlines = [PlageHoraireInline]


@admin.register(ParametreNotification)
class ParametreNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "secretariat", "intervalle_ca_min", "alerte_ca_on",
        "bilan_jour_on", "dernier_envoi_ca",
    )
    list_filter = ("alerte_ca_on", "alerte_stock_on", "bilan_jour_on")
