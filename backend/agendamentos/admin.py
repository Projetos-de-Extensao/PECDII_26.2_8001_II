from django.contrib import admin

from .models import Agendamento, Profissional


@admin.register(Profissional)
class ProfissionalAdmin(admin.ModelAdmin):
    list_display = ("nome", "especialidade", "email")
    search_fields = ("nome", "email")


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ("profissional", "data_hora", "status")
    list_filter = ("status",)
