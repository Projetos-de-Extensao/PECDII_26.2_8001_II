from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .cadastros import VERSAO_TERMOS_ATUAL, cadastrar_atleta
from .models import Atleta, Profissional, Responsavel


class ProfissionalSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(read_only=True)

    class Meta:
        model = Profissional
        fields = ["id", "nome", "especialidades"]


class ResponsavelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Responsavel
        fields = ["id", "nome", "cpf", "telefone", "email"]


class AtletaSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(write_only=True)
    sobrenome = serializers.CharField(write_only=True, required=False, allow_blank=True, default="")
    nome_completo = serializers.CharField(source="nome", read_only=True)
    email = serializers.EmailField()
    senha = serializers.CharField(write_only=True)
    aceitou_termos = serializers.BooleanField(write_only=True)
    versao_termos = serializers.CharField(write_only=True, required=False, default=VERSAO_TERMOS_ATUAL)
    responsavel = serializers.PrimaryKeyRelatedField(
        queryset=Responsavel.objects.all(),
        required=False,
        allow_null=True,
    )
    responsavel_dados = ResponsavelSerializer(write_only=True, required=False)

    class Meta:
        model = Atleta
        fields = [
            "id",
            "nome",
            "sobrenome",
            "nome_completo",
            "email",
            "senha",
            "data_nascimento",
            "aceitou_termos",
            "versao_termos",
            "responsavel",
            "responsavel_dados",
        ]

    def create(self, validated_data):
        responsavel_obj = validated_data.pop("responsavel", None)
        responsavel_dados = validated_data.pop("responsavel_dados", None)
        responsavel = responsavel_obj or responsavel_dados

        try:
            return cadastrar_atleta(responsavel=responsavel, **validated_data)
        except DjangoValidationError as erro:
            raise serializers.ValidationError(erro.message_dict if hasattr(erro, "message_dict") else erro.messages)