from datetime import datetime, timedelta

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q

from pkzlab.permissoes import SoAdminAltera

from .models import Agendamento, Atendimento, Aviso, Bloqueio, Disponibilidade
from .permissoes import ProfissionalMantemAPropria
from .serializers import (AgendamentoSerializer, AtendimentoSerializer, AvisoSerializer, BloqueioSerializer,
                          CancelarSerializer, DisponibilidadeSerializer, HorariosLivresQuerySerializer,
                          ReagendarSerializer, RegistrarAtendimentoSerializer, erro_da_api)
from .perfis import pode_registrar_atendimento, profissional_de, ve_a_agenda_toda


@extend_schema(parameters=[OpenApiParameter("status", str, enum=Agendamento.Status.values)])
class AgendamentoViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                         viewsets.GenericViewSet):
    # Sem editar nem apagar: agendamento muda só por cancelar (UC09) ou reagendar (UC08).
    
    queryset = Agendamento.objects.select_related("atleta__usuario", "servico", "profissional__funcionario__usuario",
                                                  "espaco")
    serializer_class = AgendamentoSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        usuario = self.request.user
        if not ve_a_agenda_toda(usuario):
            # UC10: cada um vê só a parte da agenda que é dele
            pode_ver = Q(pk__in=[])                                   # começa vazio e vai somando
            if profissional_de(usuario):
                pode_ver |= Q(profissional=profissional_de(usuario))  # profissional: os atendimentos dele
            if getattr(usuario, "atleta", None):
                pode_ver |= Q(atleta=usuario.atleta)                  # atleta: os dele
            if getattr(usuario, "responsavel", None):
                pode_ver |= Q(atleta__responsavel=usuario.responsavel)  # responsável: os dos dependentes
            qs = qs.filter(pode_ver)
        if s := self.request.query_params.get("status"):
            qs = qs.filter(status=s)
        return qs

    @extend_schema(request=CancelarSerializer, responses=AgendamentoSerializer, summary="Cancela o agendamento (UC09)")
    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        dados = CancelarSerializer(data=request.data)
        dados.is_valid(raise_exception=True)
        agendamento = self.get_object()
        try:
            agendamento.cancelar(dados.validated_data["justificativa"])
        except DjangoValidationError as e:
            raise erro_da_api(e)
        return Response(AgendamentoSerializer(agendamento).data)

    @extend_schema(request=ReagendarSerializer, responses={201: AgendamentoSerializer},
                   summary="Reagenda: o original vira Substituído e um novo é criado (UC08)")
    @action(detail=True, methods=["post"])
    def reagendar(self, request, pk=None):
        dados = ReagendarSerializer(data=request.data)
        dados.is_valid(raise_exception=True)
        try:
            novo = self.get_object().reagendar(dados.validated_data["inicio"])
        except DjangoValidationError as e:
            raise erro_da_api(e)
        return Response(AgendamentoSerializer(novo).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=RegistrarAtendimentoSerializer, responses={201: AtendimentoSerializer},
                   summary="Registra presença, falta ou cancelamento do atendimento (UC11)")
    @action(detail=True, methods=["post"], url_path="atendimento")
    def registrar_atendimento(self, request, pk=None):
        agendamento = self.get_object()
        if not pode_registrar_atendimento(request.user, agendamento):
            raise PermissionDenied("Só o profissional do agendamento ou a administração registra o atendimento.")
        dados = RegistrarAtendimentoSerializer(data=request.data)
        dados.is_valid(raise_exception=True)
        try:
            atendimento = Atendimento.registrar(agendamento, autor=request.user, **dados.validated_data)
        except DjangoValidationError as e:
            raise erro_da_api(e)
        return Response(AtendimentoSerializer(atendimento).data, status=status.HTTP_201_CREATED)


@extend_schema(parameters=[OpenApiParameter("status", str, enum=Atendimento.Status.values),
                           OpenApiParameter("atleta", int, description="Só os atendimentos deste atleta.")])
class AtendimentoViewSet(viewsets.ReadOnlyModelViewSet):
    # UC11 e UC14: histórico de atendimentos. Cada um vê o mesmo recorte que vê da agenda (UC10).
    queryset = Atendimento.objects.select_related("agendamento", "registrado_por")
    serializer_class = AtendimentoSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        usuario = self.request.user
        if not ve_a_agenda_toda(usuario):
            pode_ver = Q(pk__in=[])
            if profissional_de(usuario):
                pode_ver |= Q(agendamento__profissional=profissional_de(usuario))
            if getattr(usuario, "atleta", None):
                pode_ver |= Q(agendamento__atleta=usuario.atleta)
            if getattr(usuario, "responsavel", None):
                pode_ver |= Q(agendamento__atleta__responsavel=usuario.responsavel)
            qs = qs.filter(pode_ver)
        if s := self.request.query_params.get("status"):
            qs = qs.filter(status=s)
        atleta = self.request.query_params.get("atleta")
        if atleta and atleta.isdigit():
            qs = qs.filter(agendamento__atleta=atleta)
        return qs


@extend_schema(parameters=[OpenApiParameter("lido", bool, description="false: só os que ainda não foram lidos.")])
class AvisoViewSet(viewsets.ReadOnlyModelViewSet):
    # UC20: cada pessoa vê só os próprios avisos e marca como lido
    queryset = Aviso.objects.all()
    serializer_class = AvisoSerializer

    def get_queryset(self):
        qs = super().get_queryset().filter(usuario=self.request.user)
        lido = self.request.query_params.get("lido")
        if lido in ("true", "false"):
            qs = qs.filter(lido=(lido == "true"))
        return qs

    @extend_schema(request=None, responses=AvisoSerializer, summary="Marca o aviso como lido")
    @action(detail=True, methods=["post"])
    def lido(self, request, pk=None):
        aviso = self.get_object()
        aviso.marcar_como_lido()
        return Response(AvisoSerializer(aviso).data)


@extend_schema(parameters=[OpenApiParameter("profissional", int, description="Só os turnos deste profissional.")])
class DisponibilidadeViewSet(viewsets.ModelViewSet):
    # UC05: todo mundo consulta; o profissional mantém a própria (a equipe administrativa, a de qualquer um)
    queryset = Disponibilidade.objects.select_related("profissional__funcionario__usuario")
    serializer_class = DisponibilidadeSerializer
    permission_classes = [IsAuthenticated, ProfissionalMantemAPropria]

    def get_queryset(self):
        qs = super().get_queryset()
        profissional = self.request.query_params.get("profissional")
        if profissional and profissional.isdigit():
            qs = qs.filter(profissional=profissional)
        return qs


class BloqueioViewSet(viewsets.ModelViewSet):
    # UC05 e UC17: só a equipe administrativa cria bloqueios; os demais consultam.
    # Se o bloqueio pegar agendamento já marcado, a API recusa com a lista deles até receber confirmar=true.
    queryset = Bloqueio.objects.select_related("profissional__funcionario__usuario", "espaco", "equipamento")
    serializer_class = BloqueioSerializer
    permission_classes = [IsAuthenticated, SoAdminAltera]


class HorariosLivresViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @extend_schema(parameters=[
        OpenApiParameter("servico", int, required=True, description="ID do serviço."),
        OpenApiParameter("dia", str, required=True, description="Data no formato AAAA-MM-DD."),
    ])
    def list(self, request):
        consulta = HorariosLivresQuerySerializer(data=request.query_params)
        consulta.is_valid(raise_exception=True)
        servico = consulta.validated_data["servico"]
        dia = consulta.validated_data["dia"]
        disponibilidades = Disponibilidade.objects.filter(
            profissional__especialidades=servico.especialidade,
            profissional__ativo=True,
            profissional__funcionario__usuario__is_active=True,
            dia_da_semana=dia.weekday(),
        ).select_related("profissional")
        espacos = list(servico.espacos_possiveis())
        fuso = timezone.get_current_timezone()
        opcoes = []

        for disponibilidade in disponibilidades:
            inicio = datetime.combine(dia, disponibilidade.hora_inicio)
            limite = datetime.combine(dia, disponibilidade.hora_fim)
            while inicio + servico.duracao <= limite:
                inicio_agendamento = timezone.make_aware(inicio, fuso)
                fim_agendamento = inicio_agendamento + servico.duracao
                for espaco in espacos:
                    candidato = Agendamento(servico=servico, profissional=disponibilidade.profissional,
                                            espaco=espaco, inicio=inicio_agendamento)
                    try:
                        candidato.clean()
                    except DjangoValidationError:
                        continue
                    opcoes.append({
                        "inicio": inicio_agendamento.isoformat(),
                        "fim": fim_agendamento.isoformat(),
                        "profissional": disponibilidade.profissional_id,
                        "espaco": espaco.pk,
                    })
                    break  # UC06: a sala é escolhida automaticamente, basta a primeira livre
                inicio += timedelta(minutes=30)

        opcoes.sort(key=lambda opcao: (opcao["inicio"], opcao["profissional"], opcao["espaco"]))
        return Response({"results": opcoes})