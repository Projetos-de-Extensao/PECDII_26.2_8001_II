from django.contrib import admin

from .models import Agendamento,Aviso


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ("protocolo", "servico", "profissional", "espaco", "inicio", "fim", "status")
    list_filter = ("status", "servico", "profissional", "espaco")
    search_fields = ("protocolo",)
    readonly_fields = ("protocolo", "fim", "substitui")

    def has_delete_permission(self, request, obj=None):
        return False  # agendamento não se apaga: cancela (UC09)
@admin.register(Aviso)
class AvisoAdmin(admin.ModelAdmin):
    # histórico do que foi avisado a cada pessoa: só leitura
    list_display = ("usuario", "texto", "lido", "criado_em")
    list_filter = ("lido",)
    search_fields = ("usuario__username", "texto")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
