from django.contrib import admin, messages

from .models import Agendamento, Atendimento, Aula, Aviso, Bloqueio, Disponibilidade, Inscricao


@admin.register(Aula)
class AulaAdmin(admin.ModelAdmin):
    list_display = ("servico", "profissional", "espaco", "dia", "hora_inicio", "hora_fim", "ativo")
    list_filter = ("ativo", "servico", "profissional", "espaco")
    search_fields = ("servico__nome", "profissional__funcionario__usuario__username")


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ("protocolo", "servico", "profissional", "espaco", "aula", "inicio", "fim", "status")
    list_filter = ("status", "servico", "profissional", "espaco")
    search_fields = ("protocolo",)
    readonly_fields = ("protocolo", "fim", "substitui", "lembrete_enviado_em")

    def has_delete_permission(self, request, obj=None):
        return False  # agendamento não se apaga: cancela (UC09)


@admin.register(Inscricao)
class InscricaoAdmin(admin.ModelAdmin):
    list_display = ("aula", "atleta", "status", "criado_em")
    list_filter = ("status", "aula__servico")
    search_fields = ("atleta__usuario__username", "aula__servico__nome")
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


@admin.register(Disponibilidade)
class DisponibilidadeAdmin(admin.ModelAdmin):
    list_display = ("profissional", "dia_da_semana", "hora_inicio", "hora_fim")
    list_filter = ("dia_da_semana", "profissional")


@admin.register(Bloqueio)
class BloqueioAdmin(admin.ModelAdmin):
    list_display = ("alvo", "inicio", "fim", "motivo")
    list_filter = ("profissional", "espaco", "equipamento")
    search_fields = ("motivo",)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # UC05 A1 / UC17 A1: o bloqueio é gravado, mas o admin é avisado do que ele atinge
        protocolos = list(obj.agendamentos_afetados().values_list("protocolo", flat=True))
        if protocolos:
            self.message_user(request, "Atenção: este bloqueio atinge agendamentos já marcados: "
                                       + ", ".join(protocolos) + ". Reagende ou cancele cada um.",
                              messages.WARNING)


@admin.register(Atendimento)
class AtendimentoAdmin(admin.ModelAdmin):
    # registro de presença ou falta (UC11): só leitura no painel, quem grava é a API
    list_display = ("agendamento", "status", "registrado_por", "registrado_em")
    list_filter = ("status",)
    search_fields = ("agendamento__protocolo",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
