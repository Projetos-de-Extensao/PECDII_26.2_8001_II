from datetime import timedelta

from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from agenda.models import Agendamento
from estrutura.models import Espaco, Especialidade, Servico
from pessoas.admin import UserAdmin
from pessoas.models import Profissional
from pkzlab.testes_comuns import atleta, hora, profissional, usuario_com_papel


class GruposPorPapel(TestCase):
    def setUp(self):
        self.profissional = usuario_com_papel("profissional", "profissional")
        self.recepcao = usuario_com_papel("recepcao", "recepcao")
        self.administrador = usuario_com_papel("administrador", "administrador")

    def test_cada_papel_recebe_apenas_suas_permissoes(self):
        self.assertTrue(self.profissional.has_perm("pessoas.registrar_dados_tecnicos"))
        self.assertFalse(self.profissional.has_perm("pessoas.gerenciar_agenda"))
        self.assertTrue(self.recepcao.has_perm("pessoas.gerenciar_agenda"))
        self.assertFalse(self.recepcao.has_perm("pessoas.gerenciar_estrutura"))
        self.assertTrue(self.administrador.has_perm("pessoas.administrar_sistema"))
        self.assertTrue(self.administrador.has_perm("pessoas.gerenciar_estrutura"))

    def test_perfis_inativos_perdem_o_grupo_e_a_conta_inativa_nao_recebe_grupo(self):
        perfil = self.profissional.funcionario.profissional
        perfil.ativo = False
        perfil.save()
        profissional_atualizado = User.objects.get(pk=self.profissional.pk)
        self.assertFalse(profissional_atualizado.has_perm("pessoas.registrar_dados_tecnicos"))
        self.assertFalse(profissional_atualizado.groups.filter(name="Profissional").exists())
        perfil.ativo = True
        perfil.save()
        self.assertTrue(User.objects.get(pk=self.profissional.pk).has_perm("pessoas.registrar_dados_tecnicos"))

        self.recepcao.is_active = False
        self.recepcao.save()
        recepcao_atualizada = User.objects.get(pk=self.recepcao.pk)
        self.assertFalse(recepcao_atualizada.groups.filter(name="Recepção").exists())
        self.recepcao.is_active = True
        self.recepcao.save()
        self.assertTrue(User.objects.get(pk=self.recepcao.pk).groups.filter(name="Recepção").exists())

    def test_is_staff_sem_grupo_nao_autoriza_a_api(self):
        usuario = User.objects.create_user("sem-papel", is_staff=True)
        api = APIClient()
        api.force_authenticate(usuario)
        resposta = api.post("/api/equipamentos/", {"nome": "Esteira", "quantidade": 1})
        self.assertEqual(resposta.status_code, 403)


class AvisoAoInativarUsuario(TestCase):
    def setUp(self):
        especialidade = Especialidade.objects.get(nome="Nutricionista")
        self.espaco = Espaco.objects.create(nome="Consultório")
        self.espaco.especialidades.add(especialidade)
        self.servico = Servico.objects.create(nome="Consulta", especialidade=especialidade)
        self.profissional = profissional("nina", "Nina", "M001", especialidade)
        self.administrador = usuario_com_papel("chefe", "administrador")
        self.alvo = atleta("joao", "João")
        self.agendamento = Agendamento.objects.create(
            atleta=self.alvo,
            servico=self.servico,
            profissional=self.profissional,
            espaco=self.espaco,
            inicio=hora(2, 9),
        )

    def request(self):
        request = RequestFactory().post("/admin/auth/user/")
        request.user = self.administrador
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def test_ao_inativar_com_agendamento_futuro_exibe_aviso_sem_cancelar(self):
        usuario = User.objects.get(pk=self.alvo.usuario.pk)
        usuario.is_active = False
        request = self.request()

        UserAdmin(User, admin.site).save_model(request, usuario, form=None, change=True)

        avisos = list(request._messages)
        self.assertEqual(len(avisos), 1)
        self.assertEqual(avisos[0].level, messages.WARNING)
        self.assertIn(self.agendamento.protocolo, str(avisos[0]))
        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.status, Agendamento.Status.AGENDADO)
        self.assertFalse(User.objects.get(pk=usuario.pk).is_active)

    def test_sem_agendamento_futuro_nao_exibe_aviso(self):
        Agendamento.objects.filter(pk=self.agendamento.pk).update(inicio=timezone.now() - timedelta(minutes=1))
        usuario = User.objects.get(pk=self.alvo.usuario.pk)
        usuario.is_active = False
        request = self.request()

        UserAdmin(User, admin.site).save_model(request, usuario, form=None, change=True)

        self.assertEqual(list(request._messages), [])

    def test_avisa_tambem_quando_usuario_inativado_e_profissional(self):
        usuario_profissional = self.profissional.funcionario.usuario
        consulta = Agendamento.objects.create(
            atleta=atleta("maria", "Maria"),
            servico=self.servico,
            profissional=self.profissional,
            espaco=self.espaco,
            inicio=hora(2, 11),
        )
        usuario_profissional.is_active = False
        request = self.request()

        UserAdmin(User, admin.site).save_model(request, usuario_profissional, form=None, change=True)

        self.assertIn(consulta.protocolo, str(list(request._messages)[0]))
