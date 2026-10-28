from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Agendamento
from .serializers import AgendamentoSerializer, CancelarSerializer, ReagendarSerializer, erro_da_api


@extend_schema(parameters=[OpenApiParameter("status", str, enum=Agendamento.Status.values)])
class AgendamentoViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                         viewsets.GenericViewSet):
    # Sem editar nem apagar: agendamento muda só por cancelar (UC09) ou reagendar (UC08).
    # TODO: quando existir o Atleta, filtrar pelo perfil de quem está logado (UC10).
    queryset = Agendamento.objects.select_related("servico", "profissional__funcionario__usuario", "espaco")
    serializer_class = AgendamentoSerializer

    def get_queryset(self):
        qs = super().get_queryset()
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
