from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from agenda.perfis import profissional_de
from pessoas.models import Atleta
from pkzlab.permissoes import SoAdminAltera

from .indicadores import evolucao, relatorio_de_desempenho
from .models import AvaliacaoFisica, Exercicio, PlanoTreino
from .permissoes import EquipeTecnicaRegistra, da_equipe_tecnica
from .serializers import (AvaliacaoFisicaSerializer, ExercicioSerializer, FiltroRelatorioSerializer,
                          PeriodoSerializer, PlanoTreinoSerializer)


def do_visivel(qs, usuario, campo=""):
    # a equipe do CT vê todos; o atleta, os dele; o responsável, os dos dependentes (UC12, UC13 e UC14)
    # campo: o caminho até o Atleta ("atleta" numa avaliação, "" no próprio Atleta)
    if usuario.is_staff or hasattr(usuario, "funcionario"):
        return qs
    prefixo = f"{campo}__" if campo else ""
    pode_ver = Q(pk__in=[])
    if hasattr(usuario, "atleta"):
        pode_ver |= Q(**{f"{prefixo}pk": usuario.atleta.pk})
    if hasattr(usuario, "responsavel"):
        pode_ver |= Q(**{f"{prefixo}responsavel": usuario.responsavel})
    return qs.filter(pode_ver)


def do_proprio_atleta(qs, usuario):
    return do_visivel(qs, usuario, "atleta")


def filtrar_por_atleta(qs, request):
    atleta = request.query_params.get("atleta")
    return qs.filter(atleta=atleta) if atleta and atleta.isdigit() else qs


@extend_schema(parameters=[OpenApiParameter("atleta", int, description="Só as avaliações deste atleta.")])
class AvaliacaoFisicaViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                             viewsets.GenericViewSet):
    # UC12: sem editar nem apagar, a avaliação é histórico do atleta
    queryset = AvaliacaoFisica.objects.select_related("atleta__usuario", "profissional__funcionario__usuario")
    serializer_class = AvaliacaoFisicaSerializer
    permission_classes = [IsAuthenticated, EquipeTecnicaRegistra]

    def get_queryset(self):
        return filtrar_por_atleta(do_proprio_atleta(super().get_queryset(), self.request.user), self.request)


class ExercicioViewSet(viewsets.ModelViewSet):
    # catálogo de exercícios: todos consultam, a equipe técnica cadastra
    queryset = Exercicio.objects.all()
    serializer_class = ExercicioSerializer
    permission_classes = [IsAuthenticated, EquipeTecnicaRegistra]

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAuthenticated(), SoAdminAltera()]  # apagar só a administração (melhor desativar)
        return super().get_permissions()


@extend_schema(parameters=[
    OpenApiParameter("atleta", int, description="Só os planos deste atleta."),
    OpenApiParameter("ativo", bool, description="true: só o plano em vigor; false: só o histórico."),
])
class PlanoTreinoViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                         viewsets.GenericViewSet):
    # UC13: para atualizar, prescreva um novo plano para o atleta; o anterior vira histórico (A1)
    queryset = PlanoTreino.objects.select_related("atleta__usuario").prefetch_related("itens__exercicio")
    serializer_class = PlanoTreinoSerializer
    permission_classes = [IsAuthenticated, EquipeTecnicaRegistra]

    def get_queryset(self):
        qs = filtrar_por_atleta(do_proprio_atleta(super().get_queryset(), self.request.user), self.request)
        ativo = self.request.query_params.get("ativo")
        if ativo in ("true", "false"):
            qs = qs.filter(ativo=(ativo == "true"))
        return qs


def _periodo(serializer_class, request):
    params = {chave: request.query_params.get(chave) for chave in ("de", "ate", "profissional")
              if request.query_params.get(chave)}
    if request.query_params.getlist("atleta"):
        params["atleta"] = request.query_params.getlist("atleta")
    filtro = serializer_class(data=params)
    filtro.is_valid(raise_exception=True)
    return filtro.validated_data


class EvolucaoDoAtletaView(APIView):
    # UC14: o próprio atleta, o responsável dele e a equipe do CT
    permission_classes = [IsAuthenticated]

    @extend_schema(parameters=[OpenApiParameter("de", OpenApiTypes.DATE), OpenApiParameter("ate", OpenApiTypes.DATE)],
                   responses=OpenApiTypes.OBJECT, summary="Evolução do atleta: avaliações, frequência e planos (UC14)")
    def get(self, request, pk):
        atleta = get_object_or_404(do_visivel(Atleta.objects.all(), request.user), pk=pk)
        periodo = _periodo(PeriodoSerializer, request)
        return Response(evolucao(atleta, periodo.get("de"), periodo.get("ate")))


class RelatorioDeDesempenhoView(APIView):
    # UC15: profissional (só o que ele avaliou e atendeu) e administração (tudo, ou filtrando por profissional)
    permission_classes = [IsAuthenticated]

    @extend_schema(parameters=[
        OpenApiParameter("de", OpenApiTypes.DATE, required=True),
        OpenApiParameter("ate", OpenApiTypes.DATE, required=True),
        OpenApiParameter("atleta", int, many=True, description="Um ou mais atletas (repita o parâmetro)."),
        OpenApiParameter("profissional", int, description="Só a administração usa; o profissional vê só o seu."),
    ], responses=OpenApiTypes.OBJECT, summary="Relatório de desempenho por período (UC15)")
    def get(self, request):
        usuario = request.user
        if not da_equipe_tecnica(usuario):
            raise PermissionDenied("Relatórios são só para profissionais e administração.")
        filtro = _periodo(FiltroRelatorioSerializer, request)
        if usuario.is_staff:
            profissional = filtro.get("profissional")
        else:
            profissional = profissional_de(usuario)
        return Response(relatorio_de_desempenho(filtro["de"], filtro["ate"], filtro.get("atleta"), profissional))
