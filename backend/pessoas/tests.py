from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from pkzlab.testes_comuns import atleta as criar_atleta_comum
from pkzlab.testes_comuns import usuario_com_papel
from .cadastros import cadastrar_atleta, cadastrar_responsavel
from .models import Atleta, ConsentimentoLGPD, Responsavel


class CadastroAtletaTests(TestCase):
    def test_cadastrar_atleta_maior_de_idade_e_consentimento_lgpd(self):
        atleta = criar_atleta_comum("joao", "João Silva", nascimento=date(2000, 5, 20))

        self.assertEqual(atleta.nome, "João Silva")
        self.assertEqual(atleta.usuario.username, "joao@x.com")
        self.assertIsNone(atleta.responsavel)
        self.assertTrue(ConsentimentoLGPD.objects.filter(usuario=atleta.usuario, versao_termos="1.0").exists())

    def test_atleta_menor_de_idade_exige_responsavel(self):
        with self.assertRaises(ValidationError) as ctx:
            criar_atleta_comum("menor", "Lucas", nascimento=date(2015, 1, 1), responsavel=None)
        self.assertIn("responsavel", ctx.exception.message_dict)

    def test_atleta_menor_com_responsavel_compartilhado(self):
        mae = cadastrar_responsavel(email="maria@x.com", nome="Maria", sobrenome="Souza", senha="senha12345",
                                    telefone="21999999999", aceitou_termos=True)
        atleta1 = criar_atleta_comum("filho1", "Pedro", nascimento=date(2014, 3, 10), responsavel=mae)
        atleta2 = criar_atleta_comum("filho2", "Ana", nascimento=date(2016, 7, 22), responsavel=mae)

        self.assertEqual(mae.atletas.count(), 2)
        self.assertIn(atleta1, mae.atletas.all())
        self.assertIn(atleta2, mae.atletas.all())

    def test_recusa_cadastro_sem_aceite_lgpd(self):
        with self.assertRaises(ValidationError) as ctx:
            cadastrar_atleta(
                email="semtermo@x.com",
                nome="Carlos",
                senha="senha12345",
                data_nascimento=date(1998, 1, 1),
                aceitou_termos=False,
            )
        self.assertIn("aceitou_termos", ctx.exception.message_dict)


class AtletaAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_post_api_atletas_maior_de_idade(self):
        payload = {
            "nome": "Beatriz",
            "sobrenome": "Costa",
            "email": "bia@x.com",
            "senha": "senha12345",
            "data_nascimento": "2001-08-15",
            "aceitou_termos": True,
        }
        res = self.client.post("/api/atletas/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Atleta.objects.filter(usuario__email="bia@x.com").exists())

    def test_post_api_atletas_menor_sem_responsavel_retorna_400(self):
        payload = {
            "nome": "Enzo",
            "email": "enzo@x.com",
            "senha": "senha12345",
            "data_nascimento": "2015-04-10",
            "aceitou_termos": True,
        }
        res = self.client.post("/api/atletas/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("responsavel", res.data)
class ResponsavelComLogin(TestCase):
    def test_responsavel_tem_login_e_consentimento(self):
        mae = cadastrar_responsavel(email="maria@x.com", nome="Maria", sobrenome="Souza", senha="senha12345",
                                    aceitou_termos=True)
        self.assertEqual(mae.usuario.username, "maria@x.com")
        self.assertTrue(mae.usuario.check_password("senha12345"))
        self.assertEqual(mae.nome, "Maria Souza")
        self.assertTrue(ConsentimentoLGPD.objects.filter(usuario=mae.usuario).exists())

    def test_responsavel_sem_aceite_nao_cadastra(self):
        with self.assertRaises(ValidationError):
            cadastrar_responsavel(email="maria@x.com", nome="Maria", senha="senha12345", aceitou_termos=False)

    def test_regra_do_menor_vale_fora_do_cadastro(self):
        # quem grava direto (painel do admin, shell) também é barrado
        from django.contrib.auth.models import User
        u = User.objects.create_user("lucas@x.com")
        with self.assertRaises(ValidationError):
            Atleta.objects.create(usuario=u, data_nascimento=date(2015, 1, 1))

    def test_menor_sem_responsavel_nao_deixa_login_sobrando(self):
        from django.contrib.auth.models import User
        with self.assertRaises(ValidationError):
            criar_atleta_comum("menor", "Lucas", nascimento=date(2015, 1, 1))
        self.assertFalse(User.objects.filter(username="menor@x.com").exists())


class QuemVeOQueNaApi(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.api = APIClient()
        self.mae = cadastrar_responsavel(email="maria@x.com", nome="Maria", senha="senha12345", aceitou_termos=True)
        self.filho = criar_atleta_comum("pedro", "Pedro", nascimento=date(2014, 3, 10), responsavel=self.mae)
        self.joao = criar_atleta_comum("joao", "João")
        self.recepcao = usuario_com_papel("carla@ct.com", "recepcao")

    def ids(self, usuario):
        self.api.force_authenticate(usuario)
        return {a["id"] for a in self.api.get("/api/atletas/").data["results"]}

    def test_atleta_ve_so_ele(self):
        self.assertEqual(self.ids(self.joao.usuario), {self.joao.pk})

    def test_responsavel_ve_so_os_dependentes(self):
        self.assertEqual(self.ids(self.mae.usuario), {self.filho.pk})

    def test_equipe_ve_todos(self):
        self.assertEqual(self.ids(self.recepcao), {self.joao.pk, self.filho.pk})

    def test_atleta_nao_abre_o_cadastro_de_outro(self):
        self.api.force_authenticate(self.joao.usuario)
        self.assertEqual(self.api.get(f"/api/atletas/{self.filho.pk}/").status_code, 404)


class CadastroDoMenorPelaApi(TestCase):
    def setUp(self):
        self.api = APIClient()
        self.menor = {"nome": "Enzo", "email": "enzo@x.com", "senha": "senha12345",
                      "data_nascimento": "2015-04-10", "aceitou_termos": True}

    def test_responsavel_se_cadastra_pela_api(self):
        r = self.api.post("/api/responsaveis/", {"nome": "Maria", "email": "maria@x.com", "senha": "senha12345",
                                                 "aceitou_termos": True}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertTrue(Responsavel.objects.filter(usuario__username="maria@x.com").exists())

    def test_responsavel_logado_cadastra_o_dependente(self):
        mae = cadastrar_responsavel(email="maria@x.com", nome="Maria", senha="senha12345", aceitou_termos=True)
        self.api.force_authenticate(mae.usuario)
        r = self.api.post("/api/atletas/", self.menor, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(Atleta.objects.get(usuario__username="enzo@x.com").responsavel, mae)

    def test_visitante_nao_escolhe_responsavel_de_ninguem(self):
        mae = cadastrar_responsavel(email="maria@x.com", nome="Maria", senha="senha12345", aceitou_termos=True)
        r = self.api.post("/api/atletas/", {**self.menor, "responsavel": mae.pk}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertFalse(Atleta.objects.exists())        