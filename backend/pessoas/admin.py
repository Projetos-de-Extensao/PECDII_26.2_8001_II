from django.contrib import admin

from .models import Administrador, Atleta, ConsentimentoLGPD, Funcionario, Profissional, Recepcao, Responsavel


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


@admin.register(Responsavel)
class ResponsavelAdmin(admin.ModelAdmin):
    list_display = ("nome", "cpf", "telefone", "email")
    search_fields = ("nome", "cpf", "email")


@admin.register(Atleta)
class AtletaAdmin(admin.ModelAdmin):
    list_display = ("nome", "email", "data_nascimento", "responsavel")
    search_fields = ("usuario__first_name", "usuario__last_name", "usuario__email")
    list_filter = ("data_nascimento",)


@admin.register(ConsentimentoLGPD)
class ConsentimentoLGPDAdmin(admin.ModelAdmin):
    list_display = ("usuario", "versao_termos", "data")
    list_filter = ("versao_termos",)
    search_fields = ("usuario__username", "usuario__email")