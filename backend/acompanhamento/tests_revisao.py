"""Segunda revisão: avaliação física e plano de treino com valores impossíveis."""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from estrutura.models import Especialidade
from pkzlab.testes_comuns import atleta, profissional

from .models import Exercicio


class ValoresDaAvaliacaoEDoPlano(TestCase):
    def setUp(self):
        self.prof = profissional("paulo", "Paulo", "M001", Especialidade.objects.get(nome="Preparador Físico"))
        self.joao = atleta("joao", "João")
        self.api = APIClient()
        self.api.force_authenticate(self.prof.funcionario.usuario)

    def avaliar(self, **dados):
        return self.api.post("/api/avaliacoes/", {"atleta": self.joao.pk, **dados}, format="json")

    def test_resultado_negativo(self):
        r = self.avaliar(velocidade="-5.00")
        self.assertEqual(r.status_code, 400)
        self.assertIn("velocidade", r.data)

    def test_avaliacao_no_futuro(self):
        amanha = (timezone.localdate() + timedelta(days=1)).isoformat()
        r = self.avaliar(forca="80.00", data=amanha)
        self.assertEqual(r.status_code, 400)
        self.assertIn("data", r.data)

    def test_avaliacao_de_hoje_e_zero_valem(self):
        self.assertEqual(self.avaliar(forca="0.00").status_code, 201)

    def test_plano_com_zero_series_ou_repeticoes(self):
        agachamento = Exercicio.objects.create(nome="Agachamento")
        for item in ({"series": 0, "repeticoes": 10}, {"series": 3, "repeticoes": 0}):
            r = self.api.post("/api/planos/", {"atleta": self.joao.pk, "objetivo": "Força", "frequencia_semanal": 3,
                                               "itens": [{"exercicio": agachamento.pk, **item}]}, format="json")
            self.assertEqual(r.status_code, 400, item)
