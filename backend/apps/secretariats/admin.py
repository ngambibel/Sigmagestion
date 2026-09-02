from django.contrib import admin

from .models import Secretariat


@admin.register(Secretariat)
class SecretariatAdmin(admin.ModelAdmin):
    list_display = ("nom", "code", "ville", "proprietaire", "devise", "cree_le")
    search_fields = ("nom", "code", "ville", "quartier")
    list_filter = ("devise", "ville")
    readonly_fields = ("code", "cree_le", "modifie_le")
