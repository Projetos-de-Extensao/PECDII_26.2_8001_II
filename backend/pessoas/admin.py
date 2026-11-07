from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone

from .models import Administrador, Atleta, ConsentimentoLGPD, Funcionario, Profissional, Recepcao, Responsavel


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    def save_model(self, request, obj, form, change):
        estava_ativo = User.objects.filter(pk=obj.pk, is_active=True).exists() if change else False
        super().save_model(request, obj, form, change)
        if estava_ativo and not obj.is_active:
            from agenda.models import Agendamento

            futuros = Agendamento.objects.filter(
                status=Agendamento.Status.AGENDADO,
                inicio__gt=timezone.now(),
            ).filter(
                Q(atleta__usuario=obj) | Q(profissional__funcionario__usuario=obj)
            ).distinct()
            protocolos = list(futuros.values_list("protocolo", flat=True)[:5])
            if protocolos:
                total = futuros.count()
                lista = ", ".join(protocolos)
                if total > len(protocolos):
                    lista += f" e mais {total - len(protocolos)}"
                self.message_user(
                    request,
                    f"Atenção: a conta foi inativada, mas há {total} agendamento(s) futuro(s) "
                    f"que precisam de revisão: {lista}.",
                    level="WARNING",
                )


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
    search_fields = ("usuario__first_name", "usuario__last_name", "usuario__email", "cpf")


@admin.register(Atleta)
class AtletaAdmin(admin.ModelAdmin):
    list_display = ("nome", "email", "data_nascimento", "responsavel")
    search_fields = ("usuario__first_name", "usuario__last_name", "usuario__email")
    list_filter = ("data_nascimento",)


@admin.register(ConsentimentoLGPD)
class ConsentimentoLGPDAdmin(admin.ModelAdmin):
    # Só leitura: o consentimento é a prova do aceite (LGPD), não se cria, edita nem apaga pelo painel
    list_display = ("usuario", "versao_termos", "data")
    list_filter = ("versao_termos",)
    search_fields = ("usuario__username", "usuario__email")
    readonly_fields = ("usuario", "versao_termos", "data")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False