from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets

from .models import Profissional
from .serializers import ProfissionalSerializer


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
