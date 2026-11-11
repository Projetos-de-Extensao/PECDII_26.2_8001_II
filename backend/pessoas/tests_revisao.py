"""Segunda revisão: data de nascimento no futuro."""
from django.test import TestCase
from rest_framework.test import APIClient

from .cadastros import cadastrar_responsavel


class NascimentoNoFuturo(TestCase):
    def setUp(self):
        self.api = APIClient()

    def test_cadastro_pela_tela_de_criar_conta(self):
        r = self.api.post("/api/cadastro/", {"tipo": "atleta", "nome": "Bia", "email": "bia@x.com",
                                             "senha": "Xy!8kq2LmZ", "data_nascimento": "2999-01-01",
                                             "aceitou_termos": True}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("data_nascimento", r.data)  # e não "menor de idade exige responsável"

    def test_responsavel_cadastrando_dependente(self):
        mae = cadastrar_responsavel(email="mae@x.com", nome="Mãe", senha="senha12345", aceitou_termos=True)
        self.api.force_authenticate(mae.usuario)
        r = self.api.post("/api/atletas/", {"nome": "Bebê", "email": "bebe@x.com", "senha": "Xy!8kq2LmZ",
                                            "data_nascimento": "2999-01-01", "aceitou_termos": True}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("data_nascimento", r.data)
