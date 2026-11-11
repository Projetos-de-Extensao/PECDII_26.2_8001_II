"""Segunda revisão: valores que não fazem sentido para serviço e sala."""
from django.test import TestCase
from rest_framework.test import APIClient

from pkzlab.testes_comuns import usuario_com_papel

from .models import Especialidade


class ValoresMinimos(TestCase):
    def setUp(self):
        self.api = APIClient()
        self.api.force_authenticate(usuario_com_papel("adm", "administrador"))
        self.nutri = Especialidade.objects.get(nome="Nutricionista")

    def servico(self, **kw):
        return self.api.post("/api/servicos/", {"nome": "Consulta", "especialidade": self.nutri.pk,
                                                "duracao_minutos": 50, "vagas": 1, **kw}, format="json")

    def test_servico_de_zero_minutos(self):
        # com 0 minutos o início é igual ao fim e nenhum horário "bate" com outro: dava para marcar
        # várias pessoas com o mesmo profissional no mesmo horário
        r = self.servico(duracao_minutos=0)
        self.assertEqual(r.status_code, 400)
        self.assertIn("duracao_minutos", r.data)

    def test_servico_de_zero_vagas(self):
        r = self.servico(vagas=0)
        self.assertEqual(r.status_code, 400)
        self.assertIn("vagas", r.data)

    def test_sala_de_capacidade_zero(self):
        r = self.api.post("/api/espacos/", {"nome": "Sala", "capacidade": 0, "especialidades": [self.nutri.pk]},
                          format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("capacidade", r.data)

    def test_valores_normais_continuam_valendo(self):
        self.assertEqual(self.servico().status_code, 201)
        self.assertEqual(self.servico(nome="Pilates", vagas=8).status_code, 201)
