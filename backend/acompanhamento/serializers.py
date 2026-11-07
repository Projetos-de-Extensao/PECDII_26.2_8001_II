from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from agenda.perfis import profissional_de
from agenda.serializers import erro_da_api

from .models import TESTES, AvaliacaoFisica, Exercicio, ItemDoPlano, PlanoTreino


def _profissional_da_requisicao(serializer, attrs):
    # o profissional logado registra em nome dele; a administração escolhe de quem é
    usuario = serializer.context["request"].user
    if usuario.is_staff:
        if not attrs.get("profissional"):
            raise serializers.ValidationError({"profissional": "Informe o profissional."})
        return attrs["profissional"]
    proprio = profissional_de(usuario)
    if attrs.get("profissional", proprio) != proprio:
        raise serializers.ValidationError({"profissional": "Você só registra em seu próprio nome."})
    return proprio


class AvaliacaoFisicaSerializer(serializers.ModelSerializer):
    comparacao = serializers.SerializerMethodField(help_text="Diferença de cada teste para a avaliação anterior.")

    class Meta:
        model = AvaliacaoFisica
        fields = ["id", "atleta", "profissional", "data", *TESTES, "observacoes", "comparacao", "criado_em"]
        extra_kwargs = {"profissional": {"required": False}}

    @extend_schema_field(serializers.DictField(child=serializers.DecimalField(max_digits=7, decimal_places=2,
                                                                              allow_null=True), allow_null=True))
    def get_comparacao(self, obj):
        return obj.comparacao()

    def validate(self, attrs):
        attrs["profissional"] = _profissional_da_requisicao(self, attrs)
        try:
            AvaliacaoFisica(**attrs).clean()
        except DjangoValidationError as e:
            raise erro_da_api(e)
        return attrs


class ExercicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercicio
        fields = ["id", "nome", "descricao", "ativo"]


class ItemDoPlanoSerializer(serializers.ModelSerializer):
    exercicio = serializers.PrimaryKeyRelatedField(queryset=Exercicio.objects.filter(ativo=True))
    nome = serializers.CharField(source="exercicio.nome", read_only=True)

    class Meta:
        model = ItemDoPlano
        fields = ["exercicio", "nome", "ordem", "series", "repeticoes", "carga"]
        read_only_fields = ["ordem"]


class PlanoTreinoSerializer(serializers.ModelSerializer):
    itens = ItemDoPlanoSerializer(many=True)

    class Meta:
        model = PlanoTreino
        fields = ["id", "atleta", "profissional", "objetivo", "frequencia_semanal", "inicio", "fim", "observacoes",
                  "itens", "versao", "ativo", "substitui", "criado_em"]
        extra_kwargs = {"profissional": {"required": False}}

    def validate(self, attrs):
        attrs["profissional"] = _profissional_da_requisicao(self, attrs)
        return attrs

    def create(self, validated_data):
        # UC13: se o atleta já tem plano ativo, este vira a nova versão e o antigo vai para o histórico (A1)
        try:
            return PlanoTreino.prescrever(**validated_data)
        except DjangoValidationError as e:
            raise erro_da_api(e)


class PeriodoSerializer(serializers.Serializer):
    de = serializers.DateField(required=False)
    ate = serializers.DateField(required=False)

    def validate(self, attrs):
        if attrs.get("de") and attrs.get("ate") and attrs["ate"] < attrs["de"]:
            raise serializers.ValidationError({"ate": "O fim do período precisa ser depois do início."})
        return attrs


class FiltroRelatorioSerializer(PeriodoSerializer):
    # UC15: o período é obrigatório no relatório
    de = serializers.DateField()
    ate = serializers.DateField()
    atleta = serializers.ListField(child=serializers.IntegerField(), required=False)
    profissional = serializers.IntegerField(required=False)
