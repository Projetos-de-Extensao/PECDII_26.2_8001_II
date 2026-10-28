from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Agendamento


def erro_da_api(erro):
    # as regras ficam nos models; aqui só traduz o erro do Django para o formato da API (400)
    return serializers.ValidationError(erro.message_dict if hasattr(erro, "error_dict") else erro.messages)


class AgendamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agendamento
        fields = ["id", "protocolo", "servico", "profissional", "espaco", "inicio", "fim", "status",
                  "justificativa", "substitui", "criado_em"]
        read_only_fields = ["status", "justificativa", "substitui"]

    def validate(self, attrs):
        try:
            Agendamento(**attrs).clean()
        except DjangoValidationError as e:
            raise erro_da_api(e)
        return attrs


class CancelarSerializer(serializers.Serializer):
    justificativa = serializers.CharField()


class ReagendarSerializer(serializers.Serializer):
    inicio = serializers.DateTimeField()
