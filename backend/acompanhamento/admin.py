from django.contrib import admin

from .models import AvaliacaoFisica, Exercicio, ItemDoPlano, PlanoTreino


@admin.register(AvaliacaoFisica)
class AvaliacaoFisicaAdmin(admin.ModelAdmin):
    list_display = ("atleta", "data", "profissional", "velocidade", "forca", "resistencia", "agilidade")
    list_filter = ("profissional", "data")
    search_fields = ("atleta__usuario__first_name", "atleta__usuario__last_name")


@admin.register(Exercicio)
class ExercicioAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome",)


class ItemDoPlanoInline(admin.TabularInline):
    model = ItemDoPlano
    extra = 0


@admin.register(PlanoTreino)
class PlanoTreinoAdmin(admin.ModelAdmin):
    # planos novos entram pela API (PlanoTreino.prescrever), que cuida das versões; aqui é consulta
    list_display = ("atleta", "objetivo", "versao", "ativo", "profissional", "inicio", "fim")
    list_filter = ("ativo", "profissional")
    search_fields = ("atleta__usuario__first_name", "atleta__usuario__last_name", "objetivo")
    readonly_fields = ("versao", "substitui", "ativo")
    inlines = [ItemDoPlanoInline]

    def has_add_permission(self, request):
        return False
