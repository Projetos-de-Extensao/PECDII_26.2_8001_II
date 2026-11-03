from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from pkzlab.permissoes import SoAdminAltera

from .models import Espaco, Especialidade, Servico,Equipamento
from .serializers import EspacoSerializer, EspecialidadeSerializer, ServicoSerializer, EquipamentoSerializer


class EspecialidadeViewSet(viewsets.ModelViewSet):
    queryset = Especialidade.objects.all()
    serializer_class = EspecialidadeSerializer
    permission_classes = [IsAuthenticated, SoAdminAltera]


class EspacoViewSet(viewsets.ModelViewSet):
    queryset = Espaco.objects.prefetch_related("especialidades")
    serializer_class = EspacoSerializer
    permission_classes = [IsAuthenticated, SoAdminAltera]


class ServicoViewSet(viewsets.ModelViewSet):
    # UC18: o admin cadastra as modalidades; os demais só consultam
    queryset = Servico.objects.select_related("especialidade").prefetch_related("espacos")
    serializer_class = ServicoSerializer
    permission_classes = [IsAuthenticated, SoAdminAltera]
class EquipamentoViewSet(viewsets.ModelViewSet):
    
    queryset = Equipamento.objects.all()
    serializer_class = EquipamentoSerializer
    permission_classes = [IsAuthenticated, SoAdminAltera]