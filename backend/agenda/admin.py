from django.contrib import admin

from .models import Agendamento


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ("protocolo", "servico", "profissional", "espaco", "inicio", "fim", "status")
    list_filter = ("status", "servico", "profissional", "espaco")
    search_fields = ("protocolo",)
    readonly_fields = ("protocolo", "fim", "substitui")

    def has_delete_permission(self, request, obj=None):
        return False  # agendamento não se apaga: cancela (UC09)
