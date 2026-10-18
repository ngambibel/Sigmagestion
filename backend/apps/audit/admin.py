from django.contrib import admin

from .models import JournalAudit


@admin.register(JournalAudit)
class JournalAuditAdmin(admin.ModelAdmin):
    list_display = ("action", "modele", "objet_repr", "auteur", "cree_le")
    list_filter = ("action", "modele")
    search_fields = ("objet_repr", "objet_id")
    readonly_fields = [f.name for f in JournalAudit._meta.fields]
