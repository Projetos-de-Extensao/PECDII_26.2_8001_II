from django.core.exceptions import ValidationError
from django.test import TestCase

from estrutura.models import Especialidade
from pkzlab.testes_comuns import funcionario, profissional

from .models import Profissional, Recepcao


class CadastroDaEquipe(TestCase):
    def test_email_vira_login(self):
        f = funcionario("ana", "Ana", "M001")
        self.assertEqual(f.usuario.username, "ana@ct.com")
        self.assertTrue(f.usuario.check_password("senha12345"))

    def test_email_repetido_e_recusado(self):
        funcionario("ana", "Ana", "M001")
        with self.assertRaises(ValidationError):
            funcionario("ana", "Outra Ana", "M002")

    def test_papeis_se_acumulam_com_a_mesma_matricula(self):
        fisio = Especialidade.objects.get(nome="Fisioterapeuta")
        p = profissional("bia", "Bia", "M010", fisio)
        Recepcao.objects.create(funcionario=p.funcionario)
        self.assertEqual(p.funcionario.recepcao.funcionario.matricula, "M010")
        self.assertTrue(p.atende(fisio))


class ProfissionaisAtivos(TestCase):
    def setUp(self):
        self.personal = Especialidade.objects.get(nome="Personal Trainer")
        self.p = profissional("caio", "Caio", "M020", self.personal)

    def test_conta_inativada_sai_da_lista(self):
        u = self.p.funcionario.usuario
        u.is_active = False
        u.save()
        self.assertNotIn(self.p, Profissional.ativos())

    def test_papel_desativado_sai_da_lista(self):
        self.p.ativo = False
        self.p.save()
        self.assertNotIn(self.p, Profissional.ativos())


class ApiDeProfissionais(TestCase):
    def test_lista_so_ativos_da_especialidade(self):
        from rest_framework.test import APIClient
        nutri = Especialidade.objects.get(nome="Nutricionista")
        personal = Especialidade.objects.get(nome="Personal Trainer")
        nina = profissional("nina", "Nina", "M001", nutri)
        profissional("teo", "Teo", "M002", personal)
        inativo = profissional("ivo", "Ivo", "M003", nutri)
        inativo.ativo = False
        inativo.save()
        api = APIClient()
        api.force_authenticate(nina.funcionario.usuario)
        r = api.get(f"/api/profissionais/?especialidade={nutri.pk}")
        self.assertEqual([p["nome"] for p in r.data["results"]], ["Nina"])
