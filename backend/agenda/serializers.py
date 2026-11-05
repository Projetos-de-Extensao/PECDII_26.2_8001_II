from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Agendamento, Aviso, Bloqueio, Disponibilidade
from .perfis import pode_agendar_para, profissional_de

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


def _dados_com_instancia(instancia, attrs, campos):
    # numa edição parcial, completa o que não veio com o valor já gravado, para validar o conjunto
    base = {campo: getattr(instancia, campo) for campo in campos} if instancia else {}
    return {**base, **attrs}


class DisponibilidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disponibilidade
        fields = ["id", "profissional", "dia_da_semana", "hora_inicio", "hora_fim"]
        extra_kwargs = {"profissional": {"required": False}}  # o profissional logado é o dono

    def validate(self, attrs):
        # UC05: o profissional mantém só a própria; a equipe administrativa escolhe de quem é
        usuario = self.context["request"].user
        if usuario.is_staff:
            if not self.instance and not attrs.get("profissional"):
                raise serializers.ValidationError({"profissional": "Informe o profissional."})
        else:
            proprio = profissional_de(usuario)
            if attrs.get("profissional", proprio) != proprio:
                raise serializers.ValidationError({"profissional": "Você só mantém a sua própria disponibilidade."})
            attrs["profissional"] = proprio

        dados = _dados_com_instancia(self.instance, attrs,
                                     ("profissional", "dia_da_semana", "hora_inicio", "hora_fim"))
        try:
            Disponibilidade(pk=self.instance.pk if self.instance else None, **dados).clean()
        except DjangoValidationError as e:
            raise erro_da_api(e)
        return attrs


class BloqueioSerializer(serializers.ModelSerializer):
    confirmar = serializers.BooleanField(write_only=True, required=False, default=False,
                                         help_text="Envie true para gravar mesmo atingindo agendamentos já marcados.")
    agendamentos_afetados = serializers.SerializerMethodField()

    class Meta:
        model = Bloqueio
        fields = ["id", "profissional", "espaco", "equipamento", "inicio", "fim", "motivo", "criado_em",
                  "confirmar", "agendamentos_afetados"]
        read_only_fields = ["criado_em"]

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_agendamentos_afetados(self, obj):
        return list(obj.agendamentos_afetados().values_list("protocolo", flat=True))

    def validate(self, attrs):
        confirmar = attrs.pop("confirmar", False)  # não é campo do model
        dados = _dados_com_instancia(self.instance, attrs,
                                     ("profissional", "espaco", "equipamento", "inicio", "fim", "motivo"))
        bloqueio = Bloqueio(pk=self.instance.pk if self.instance else None, **dados)
        try:
            bloqueio.clean()
        except DjangoValidationError as e:
            raise erro_da_api(e)

        # UC05 A1 / UC17 A1: alerta antes de confirmar
        protocolos = list(bloqueio.agendamentos_afetados().values_list("protocolo", flat=True))
        if protocolos and not confirmar:
            raise serializers.ValidationError({"confirmar": (
                f"Este bloqueio atinge {len(protocolos)} agendamento(s): {', '.join(protocolos)}. "
                "Reagende ou cancele, ou envie confirmar=true para gravar mesmo assim.")})
        return attrs