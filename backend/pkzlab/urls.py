from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from pessoas.autenticacao import CadastroView, RedefinirSenhaView, SolicitarRecuperacaoView, TokenPorEmailView
from rest_framework_simplejwt.views import TokenRefreshView
from agenda.views import (AgendamentoViewSet, AtendimentoViewSet, AulaViewSet, AvisoViewSet, BloqueioViewSet,
                          DisponibilidadeViewSet, HorariosLivresViewSet, InscricaoViewSet)
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
router.register("aulas", AulaViewSet)
router.register("inscricoes", InscricaoViewSet)
router.register("atendimentos", AtendimentoViewSet)
router.register("avisos", AvisoViewSet)
router.register("disponibilidades", DisponibilidadeViewSet)
router.register("bloqueios", BloqueioViewSet)
router.register("horarios-livres", HorariosLivresViewSet, basename="horarios-livres")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenPorEmailView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/cadastro/', CadastroView.as_view(), name='cadastro'),
    path('api/senha/recuperar/', SolicitarRecuperacaoView.as_view(), name='senha_recuperar'),
    path('api/senha/redefinir/', RedefinirSenhaView.as_view(), name='senha_redefinir'),
    path('api/', include(router.urls)),
    path('api/auth/', include('rest_framework.urls')),  # entrar/sair na API pelo navegador
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
