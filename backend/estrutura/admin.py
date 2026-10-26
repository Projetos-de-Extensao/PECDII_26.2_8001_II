from django.contrib import admin

from .models import Configuracao, Espaco, Especialidade, Servico


@admin.register(Especialidade)
class EspecialidadeAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo")


@admin.register(Espaco)
class EspacoAdmin(admin.ModelAdmin):
    # O admin cadastra as salas e diz quais especialidades usam cada uma.
    list_display = ("nome", "especialidades_atendidas", "capacidade", "ativo")
    list_filter = ("especialidades", "ativo")
    filter_horizontal = ("especialidades",)

    @admin.display(description="Atende")
    def especialidades_atendidas(self, obj):
        return ", ".join(e.nome for e in obj.especialidades.all()) or "-"


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ("nome", "especialidade", "duracao_minutos", "vagas", "ativo")
    list_filter = ("especialidade", "ativo")
    filter_horizontal = ("espacos",)


@admin.register(Configuracao)
class ConfiguracaoAdmin(admin.ModelAdmin):
    # uma linha só: dá para editar, não dá para criar outra nem apagar
    list_display = ("__str__", "prazo_confirmacao_horas", "confirmar_ate_minutos_antes")

    def has_add_permission(self, request):
        return not Configuracao.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
