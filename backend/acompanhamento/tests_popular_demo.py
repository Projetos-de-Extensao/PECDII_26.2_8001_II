from io import StringIO

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from agenda.models import Agendamento, Atendimento, Aula
from pessoas.models import Atleta
from pessoas.permissoes import tem_permissao

from .models import AvaliacaoFisica, PlanoTreino


def popular():
    saida = StringIO()
    call_command("popular_demo", stdout=saida)
    return saida.getvalue()


class ComandoPopularDemo(TestCase):
    def test_cria_os_dados_de_exemplo(self):
        saida = popular()
        self.assertIn("senha12345", saida)
        self.assertEqual(Atleta.objects.count(), 4)
        self.assertEqual(Agendamento.objects.filter(status=Agendamento.Status.AGENDADO).count(), 13)  # 11 individuais + 2 na aula
        self.assertEqual(Atendimento.objects.filter(status=Atendimento.Status.FALTA).count(), 1)
        self.assertEqual(Aula.objects.get().agendamentos.filter(status=Agendamento.Status.AGENDADO).count(), 2)
        self.assertEqual(AvaliacaoFisica.objects.filter(atleta__usuario__username="joao@pkzlab.demo").count(), 3)
        plano = PlanoTreino.objects.get(atleta__usuario__username="joao@pkzlab.demo", ativo=True)
        self.assertEqual(plano.versao, 2)
        self.assertEqual(len(mail.outbox), 0)  # os e-mails de exemplo não saem

    def test_rodar_de_novo_nao_duplica(self):
        popular()
        total = User.objects.count()
        self.assertIn("já existem", popular())
        self.assertEqual(User.objects.count(), total)

    def test_os_logins_entram_com_a_senha_de_exemplo(self):
        popular()
        for login in ("carla", "rita", "nina", "joao", "ana", "lucas"):
            self.assertIsNotNone(authenticate(username=f"{login}@pkzlab.demo", password="senha12345"), login)

    def test_cada_papel_recebe_as_permissoes(self):
        popular()
        carla = User.objects.get(username="carla@pkzlab.demo")
        self.assertTrue(carla.is_staff)
        self.assertTrue(tem_permissao(carla, "administrar_sistema"))
        self.assertTrue(tem_permissao(carla, "registrar_dados_tecnicos"))  # também é profissional
        rita = User.objects.get(username="rita@pkzlab.demo")
        self.assertTrue(tem_permissao(rita, "agendar_para_qualquer_atleta"))
        self.assertFalse(tem_permissao(rita, "registrar_dados_tecnicos"))

    def test_a_responsavel_ve_a_agenda_do_dependente(self):
        popular()
        api = APIClient()
        api.force_authenticate(User.objects.get(username="ana@pkzlab.demo"))
        r = api.get("/api/agendamentos/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["count"], 2)  # os dois agendamentos do Lucas
