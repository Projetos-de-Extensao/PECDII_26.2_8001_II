from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from pkzlab.testes_comuns import atleta as criar_atleta_comum
from .cadastros import cadastrar_atleta
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
        mae = Responsavel.objects.create(nome="Maria Souza", telefone="21999999999")
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