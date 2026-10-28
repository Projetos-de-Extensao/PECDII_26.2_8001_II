from django.contrib import admin

from .models import Administrador, Funcionario, Profissional, Recepcao


class ProfissionalInline(admin.StackedInline):
    model = Profissional
    filter_horizontal = ("especialidades",)
    extra = 0


class RecepcaoInline(admin.TabularInline):
    model = Recepcao
    extra = 0


class AdministradorInline(admin.TabularInline):
    model = Administrador
    extra = 0


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    # os papéis aparecem dentro do funcionário: acrescentar um papel não muda a matrícula (UC04 A3)
    list_display = ("nome", "matricula", "data_admissao", "ativo")
    search_fields = ("usuario__first_name", "usuario__last_name", "usuario__email", "matricula")
    inlines = [ProfissionalInline, RecepcaoInline, AdministradorInline]


@admin.register(Profissional)
class ProfissionalAdmin(admin.ModelAdmin):
    list_display = ("nome", "especialidades_atendidas", "ativo")
    list_filter = ("especialidades", "ativo")
    filter_horizontal = ("especialidades",)

    @admin.display(description="Especialidades")
    def especialidades_atendidas(self, obj):
        return ", ".join(e.nome for e in obj.especialidades.all()) or "-"
