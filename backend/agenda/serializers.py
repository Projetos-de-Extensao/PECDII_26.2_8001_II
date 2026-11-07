from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from estrutura.models import Servico
from pessoas.permissoes import tem_permissao

from .models import Agendamento, Atendimento, Aula, Aviso, Bloqueio, Disponibilidade, Inscricao, ListaEspera
from .perfis import pode_agendar_para, profissional_de

def erro_da_api(erro):
    # as regras ficam nos models; aqui só traduz o erro do Django para o formato da API (400)
    return serializers.ValidationError(erro.message_dict if hasattr(erro, "error_dict") else erro.messages)


class AgendamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agendamento
        fields = ["id", "protocolo","atleta", "servico", "profissional", "espaco", "inicio", "fim", "status",
                  "justificativa", "substitui", "criado_em", "equipamentos", "lembrete_enviado_em"]
        read_only_fields = ["status", "justificativa", "substitui", "lembrete_enviado_em"]

    def validate(self, attrs):
        # UC06: atleta marca para si, responsável para o dependente, equipe para qualquer um
        atleta = attrs.get("atleta")
        if atleta and not pode_agendar_para(self.context["request"].user, atleta):
            raise serializers.ValidationError({"atleta": "Você só pode agendar para você mesmo ou para os seus dependentes."})

        if attrs.get("aula"):
            aula = attrs["aula"]
            attrs.setdefault("servico", aula.servico)
            attrs.setdefault("profissional", aula.profissional)
            attrs.setdefault("espaco", aula.espaco)
            attrs.setdefault("inicio", aula.inicio)

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


class AulaSerializer(serializers.ModelSerializer):
    vagas_restantes = serializers.IntegerField(read_only=True)
    lotada = serializers.BooleanField(read_only=True)

    class Meta:
        model = Aula
        fields = ["id", "servico", "profissional", "espaco", "dia", "hora_inicio", "hora_fim",
                  "ativo", "vagas_restantes", "lotada", "criado_em"]
        read_only_fields = ["hora_fim", "criado_em", "vagas_restantes", "lotada"]

    def validate(self, attrs):
        usuario = self.context["request"].user
        if not tem_permissao(usuario, "administrar_sistema"):
            raise serializers.ValidationError({"detail": "Só a equipe administrativa pode gerenciar aulas."})
        dados = _dados_com_instancia(self.instance, attrs,
                                     ("servico", "profissional", "espaco", "dia", "hora_inicio", "hora_fim", "ativo"))
        try:
            Aula(pk=self.instance.pk if self.instance else None, **dados).clean()
        except DjangoValidationError as e:
            raise erro_da_api(e)
        return attrs


class InscricaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inscricao
        fields = ["id", "aula", "atleta", "agendamento", "status", "criado_em"]
        read_only_fields = ["criado_em"]

    def validate(self, attrs):
        usuario = self.context["request"].user
        atleta = attrs.get("atleta") or getattr(self.instance, "atleta", None)
        if atleta and not pode_agendar_para(usuario, atleta):
            raise serializers.ValidationError({"atleta": "Você só pode se inscrever para você mesmo ou para os seus dependentes."})
        dados = _dados_com_instancia(self.instance, attrs, ("aula", "atleta", "agendamento", "status"))
        try:
            Inscricao(pk=self.instance.pk if self.instance else None, **dados).clean()
        except DjangoValidationError as e:
            raise erro_da_api(e)
        return attrs


class ListaEsperaSerializer(serializers.ModelSerializer):
    # UC19: para entrar na fila, mande a aula (aula em grupo) ou serviço, profissional e início (individual)
    posicao = serializers.IntegerField(read_only=True, allow_null=True,
                                       help_text="Posição na fila (1 = o próximo). Vazio se não está aguardando.")

    class Meta:
        model = ListaEspera
        fields = ["id", "atleta", "servico", "profissional", "aula", "inicio", "status", "posicao", "vaga", "prazo",
                  "agendamento", "criado_em"]
        read_only_fields = ["status", "vaga", "prazo", "agendamento", "criado_em"]
        extra_kwargs = {"servico": {"required": False}, "profissional": {"required": False},
                        "inicio": {"required": False}}

    def validate(self, attrs):
        if not pode_agendar_para(self.context["request"].user, attrs["atleta"]):
            raise serializers.ValidationError(
                {"atleta": "Você só pode entrar na lista para você mesmo ou para os seus dependentes."})
        if not attrs.get("aula"):
            faltando = {campo: "Informe este campo (ou a aula)." for campo in ("servico", "profissional", "inicio")
                        if not attrs.get(campo)}
            if faltando:
                raise serializers.ValidationError(faltando)
        espera = ListaEspera(**attrs)
        try:
            espera.clean()  # numa aula, o clean copia serviço, profissional e horário dela
        except DjangoValidationError as e:
            raise erro_da_api(e)
        attrs.update(servico=espera.servico, profissional=espera.profissional, inicio=espera.inicio)
        return attrs


class CancelarSerializer(serializers.Serializer):
    justificativa = serializers.CharField()


class ReagendarSerializer(serializers.Serializer):
    inicio = serializers.DateTimeField()


class AtendimentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Atendimento
        fields = ["id", "agendamento", "status", "justificativa", "registrado_por", "registrado_em"]
        read_only_fields = fields  # quem grava é a ação registrar_atendimento do agendamento


class RegistrarAtendimentoSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Atendimento.Status.choices)
    justificativa = serializers.CharField(required=False, allow_blank=True, default="")


class HorariosLivresQuerySerializer(serializers.Serializer):
    servico = serializers.PrimaryKeyRelatedField(queryset=Servico.objects.filter(ativo=True))
    dia = serializers.DateField()


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
        if tem_permissao(usuario, "gerenciar_agenda"):
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