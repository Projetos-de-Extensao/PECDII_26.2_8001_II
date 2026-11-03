from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from agenda.views import AgendamentoViewSet,AvisoViewSet
from estrutura.views import EspacoViewSet, EspecialidadeViewSet, ServicoViewSet,EquipamentoViewSet
from pessoas.views import AtletaViewSet, ProfissionalViewSet, ResponsavelViewSet

router = DefaultRouter()
router.register("especialidades", EspecialidadeViewSet)
router.register("espacos", EspacoViewSet)
router.register("servicos", ServicoViewSet)
router.register("equipamentos", EquipamentoViewSet)
router.register("profissionais", ProfissionalViewSet)
router.register("atletas", AtletaViewSet)
router.register("responsaveis", ResponsavelViewSet)
router.register("agendamentos", AgendamentoViewSet)
router.register("avisos", AvisoViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/', include('rest_framework.urls')),  # entrar/sair na API pelo navegador
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]