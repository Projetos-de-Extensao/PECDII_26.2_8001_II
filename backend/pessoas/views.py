from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, permissions, viewsets

from .models import Atleta, Profissional,Responsavel
from .serializers import AtletaSerializer, ProfissionalSerializer, ResponsavelSerializer


@extend_schema(parameters=[OpenApiParameter("especialidade", int, description="Só quem atende esta especialidade.")])
class ProfissionalViewSet(viewsets.ReadOnlyModelViewSet):
    # Só consulta: o cadastro da equipe é feito pelo administrador (UC04).
    # Mostra apenas os ativos, que são os que podem receber agendamentos (UC06 A4).
    queryset = Profissional.objects.none()
    serializer_class = ProfissionalSerializer

    def get_queryset(self):
        qs = Profissional.ativos().select_related("funcionario__usuario").prefetch_related("especialidades")
        especialidade = self.request.query_params.get("especialidade")
        if especialidade:
            qs = qs.filter(especialidades=especialidade)
        return qs.order_by("funcionario__usuario__first_name")


def ve_todas_as_pessoas(usuario):
    # a equipe do CT (recepção, profissionais, administração) enxerga todos os cadastros
    return usuario.is_staff or hasattr(usuario, "funcionario")


class AtletaViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Atleta.objects.select_related("usuario", "responsavel__usuario")
    serializer_class = AtletaSerializer

    def get_permissions(self):
        # UC02: qualquer visitante pode se cadastrar como atleta (POST /api/atletas/)
        if self.action == "create":
            return [permissions.AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        # RNF03 e RNF10: dado de atleta (muitas vezes menor de idade) só para quem pode ver
        usuario = self.request.user
        qs = super().get_queryset()
        if ve_todas_as_pessoas(usuario):
            return qs
        if hasattr(usuario, "atleta"):
            return qs.filter(pk=usuario.atleta.pk)
        if hasattr(usuario, "responsavel"):
            return qs.filter(responsavel=usuario.responsavel)
        return qs.none()


class ResponsavelViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Responsavel.objects.select_related("usuario")
    serializer_class = ResponsavelSerializer

    def get_permissions(self):
        # UC02: o responsável cria a própria conta antes de cadastrar o dependente
        if self.action == "create":
            return [permissions.AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        usuario = self.request.user
        qs = super().get_queryset()
        if ve_todas_as_pessoas(usuario):
            return qs
        if hasattr(usuario, "responsavel"):
            return qs.filter(pk=usuario.responsavel.pk)
        return qs.none()