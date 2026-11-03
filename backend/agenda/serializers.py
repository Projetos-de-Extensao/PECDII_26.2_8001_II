from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from .models import Agendamento,Aviso
from .perfis import pode_agendar_para

def erro_da_api(erro):
    # as regras ficam nos models; aqui só traduz o erro do Django para o formato da API (400)
    return serializers.ValidationError(erro.message_dict if hasattr(erro, "error_dict") else erro.messages)


class AgendamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agendamento
        fields = ["id", "protocolo","atleta", "servico", "profissional", "espaco", "inicio", "fim", "status",
                  "justificativa", "substitui", "criado_em", "equipamentos"]
        read_only_fields = ["status", "justificativa", "substitui"]

    def validate(self, attrs):
        # UC06: atleta marca para si, responsável para o dependente, equipe para qualquer um
        atleta = attrs.get("atleta")
        if atleta and not pode_agendar_para(self.context["request"].user, atleta):
            raise serializers.ValidationError({"atleta": "Você só pode agendar para você mesmo ou para os seus dependentes."})

        dados = {campo: valor for campo, valor in attrs.items() if campo != "equipamentos"}  # lista não entra no construtor
        try:
            Agendamento(**dados).clean()
        except DjangoValidationError as e:
            raise erro_da_api(e)
        return attrs
    @transaction.atomic
    def create(self, validated_data):
        # cria o agendamento e reserva os equipamentos; se a reserva falhar, nada fica gravado
        equipamentos = validated_data.pop("equipamentos", [])
        agendamento = Agendamento.objects.create(**validated_data)
        try:
            agendamento.reservar_equipamentos(equipamentos)
        except DjangoValidationError as e:
            raise erro_da_api(e)
        return agendamento


class CancelarSerializer(serializers.Serializer):
    justificativa = serializers.CharField()


class ReagendarSerializer(serializers.Serializer):
    inicio = serializers.DateTimeField()


class AvisoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aviso
        fields = ["id", "texto", "link", "lido", "criado_em"]
        read_only_fields = fields  # pela API, aviso só se lê; quem cria é o sistema