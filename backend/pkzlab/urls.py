from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from agenda.views import AgendamentoViewSet
from estrutura.views import EspacoViewSet, EspecialidadeViewSet, ServicoViewSet
from pessoas.views import ProfissionalViewSet

router = DefaultRouter()
router.register("especialidades", EspecialidadeViewSet)
router.register("espacos", EspacoViewSet)
router.register("servicos", ServicoViewSet)
router.register("profissionais", ProfissionalViewSet)
router.register("agendamentos", AgendamentoViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/', include('rest_framework.urls')),  # entrar/sair na API pelo navegador
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
