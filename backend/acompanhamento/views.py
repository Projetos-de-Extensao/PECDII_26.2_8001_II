from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from pkzlab.permissoes import SoAdminAltera

from .models import AvaliacaoFisica, Exercicio, PlanoTreino
from .permissoes import EquipeTecnicaRegistra
from .serializers import AvaliacaoFisicaSerializer, ExercicioSerializer, PlanoTreinoSerializer


def do_proprio_atleta(qs, usuario):
    # a equipe do CT vê todos; o atleta, os dele; o responsável, os dos dependentes (UC12 e UC13, pós-condições)
    if usuario.is_staff or hasattr(usuario, "funcionario"):
        return qs
    pode_ver = Q(pk__in=[])
    if hasattr(usuario, "atleta"):
        pode_ver |= Q(atleta=usuario.atleta)
    if hasattr(usuario, "responsavel"):
        pode_ver |= Q(atleta__responsavel=usuario.responsavel)
    return qs.filter(pode_ver)


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
