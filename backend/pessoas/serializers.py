from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .cadastros import VERSAO_TERMOS_ATUAL, cadastrar_atleta,cadastrar_responsavel
from .models import Atleta, Profissional, Responsavel
from .permissoes import tem_permissao


class ProfissionalSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(read_only=True)

    class Meta:
        model = Profissional
        fields = ["id", "nome", "especialidades"]


class ResponsavelSerializer(serializers.ModelSerializer):
    # Cadastro do responsável (UC02): cria o login e registra o aceite da LGPD
    nome = serializers.CharField(write_only=True)
    sobrenome = serializers.CharField(write_only=True, required=False, allow_blank=True, default="")
    nome_completo = serializers.CharField(source="nome", read_only=True)
    email = serializers.EmailField()
    senha = serializers.CharField(write_only=True)
    aceitou_termos = serializers.BooleanField(write_only=True)

    class Meta:
        model = Responsavel
        fields = ["id", "nome", "sobrenome", "nome_completo", "email", "senha", "cpf", "telefone", "aceitou_termos"]

    def create(self, validated_data):
        try:
            return cadastrar_responsavel(**validated_data)
        except DjangoValidationError as erro:
            raise serializers.ValidationError(erro.message_dict if hasattr(erro, "message_dict") else erro.messages)


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
        ]

    def create(self, validated_data):
        # Quem define o responsável depende de quem está cadastrando:
        #   responsável logado  -> o dependente fica ligado a ele mesmo
        #   equipe (recepção)   -> pode escolher o responsável pelo id
        #   visitante           -> não escolhe responsável de ninguém (menor de idade é recusado)
        usuario = self.context["request"].user
        responsavel = validated_data.pop("responsavel", None)
        if hasattr(usuario, "responsavel"):
            responsavel = usuario.responsavel
        elif not tem_permissao(usuario, "gerenciar_cadastros"):
            responsavel = None
        try:
            return cadastrar_atleta(responsavel=responsavel, **validated_data)
        except DjangoValidationError as erro:
            raise serializers.ValidationError(erro.message_dict if hasattr(erro, "message_dict") else erro.messages)