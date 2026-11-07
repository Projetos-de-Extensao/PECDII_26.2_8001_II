from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from estrutura.models import Especialidade
from pessoas.cadastros import cadastrar_responsavel
from pessoas.models import Recepcao
from pkzlab.testes_comuns import atleta, funcionario, profissional

from .models import AvaliacaoFisica, Exercicio, PlanoTreino


class Base(TestCase):
    def setUp(self):
        preparador = Especialidade.objects.get(nome="Preparador Físico")
        self.prof = profissional("pedro", "Pedro", "M001", preparador)
        self.joao = atleta("joao", "João")
        self.agachamento = Exercicio.objects.create(nome="Agachamento")
        self.prancha = Exercicio.objects.create(nome="Prancha")

    def avaliar(self, dia, **testes):
        return AvaliacaoFisica.objects.create(atleta=self.joao, profissional=self.prof, data=dia, **testes)

    def prescrever(self, objetivo="Força", **kw):
        dados = dict(atleta=self.joao, profissional=self.prof, objetivo=objetivo, frequencia_semanal=3,
                     itens=[{"exercicio": self.agachamento, "series": 4, "repeticoes": 10, "carga": "20 kg"}])
        dados.update(kw)
        return PlanoTreino.prescrever(**dados)


class AvaliacaoFisicaRegras(Base):
    def test_precisa_de_pelo_menos_um_teste(self):
        with self.assertRaises(ValidationError):
            AvaliacaoFisica(atleta=self.joao, profissional=self.prof).clean()

    def test_primeira_avaliacao_nao_tem_comparacao(self):
        self.assertIsNone(self.avaliar(date(2026, 3, 1), velocidade=Decimal("5.20")).comparacao())

    def test_compara_com_a_avaliacao_anterior(self):
        self.avaliar(date(2026, 3, 1), velocidade=Decimal("5.20"), forca=Decimal("80"))
        self.avaliar(date(2026, 4, 1), velocidade=Decimal("5.00"), forca=Decimal("90"))
        nova = self.avaliar(date(2026, 5, 1), velocidade=Decimal("4.90"), agilidade=Decimal("10"))
        self.assertEqual(nova.comparacao(), {"velocidade": Decimal("-0.10"), "forca": None,
                                             "resistencia": None, "agilidade": None})

    def test_nao_compara_com_outro_atleta(self):
        maria = atleta("maria", "Maria")
        AvaliacaoFisica.objects.create(atleta=maria, profissional=self.prof, data=date(2026, 3, 1),
                                       velocidade=Decimal("6"))
        self.assertIsNone(self.avaliar(date(2026, 4, 1), velocidade=Decimal("5")).comparacao())


class PlanoTreinoVersoes(Base):
    def test_precisa_de_exercicio(self):
        with self.assertRaises(ValidationError):
            self.prescrever(itens=[])

    def test_atualizar_guarda_a_versao_anterior(self):
        v1 = self.prescrever()
        v2 = self.prescrever("Resistência",
                             itens=[{"exercicio": self.prancha, "series": 3, "repeticoes": 1, "carga": "60 s"}])
        v1.refresh_from_db()
        self.assertFalse(v1.ativo)
        self.assertTrue(v2.ativo)
        self.assertEqual(v2.versao, 2)
        self.assertEqual(v2.substitui, v1)
        self.assertEqual(list(v1.exercicios.all()), [self.agachamento])  # o histórico fica como era

    def test_fim_do_ciclo_depois_do_inicio(self):
        with self.assertRaises(ValidationError):
            self.prescrever(inicio=date(2026, 5, 1), fim=date(2026, 4, 1))
        self.assertFalse(PlanoTreino.objects.exists())


class ApiDeAcompanhamento(Base):
    def setUp(self):
        super().setUp()
        self.api = APIClient()

    def como(self, usuario):
        self.api.force_authenticate(usuario)
        return self.api

    def test_profissional_avalia_em_seu_nome(self):
        r = self.como(self.prof.funcionario.usuario).post(
            "/api/avaliacoes/", {"atleta": self.joao.pk, "data": "2026-03-01", "velocidade": "5.20"})
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["profissional"], self.prof.pk)
        self.assertIsNone(r.data["comparacao"])

    def test_avaliacao_vazia_da_400(self):
        r = self.como(self.prof.funcionario.usuario).post("/api/avaliacoes/", {"atleta": self.joao.pk})
        self.assertEqual(r.status_code, 400)

    def test_atleta_e_recepcao_nao_registram(self):
        dados = {"atleta": self.joao.pk, "velocidade": "5"}
        self.assertEqual(self.como(self.joao.usuario).post("/api/avaliacoes/", dados).status_code, 403)
        rita = Recepcao.objects.create(funcionario=funcionario("rita", "Rita", "M050")).funcionario.usuario
        self.assertEqual(self.como(rita).post("/api/avaliacoes/", dados).status_code, 403)

    def test_cada_um_ve_so_o_seu(self):
        self.avaliar(date(2026, 3, 1), velocidade=Decimal("5"))
        maria = atleta("maria", "Maria")
        self.assertEqual(self.como(self.joao.usuario).get("/api/avaliacoes/").data["count"], 1)
        self.assertEqual(self.como(maria.usuario).get("/api/avaliacoes/").data["count"], 0)
        self.assertEqual(self.como(self.prof.funcionario.usuario).get("/api/avaliacoes/").data["count"], 1)

    def test_responsavel_ve_o_do_dependente(self):
        mae = cadastrar_responsavel(email="mae@x.com", nome="Ana", senha="senha12345", aceitou_termos=True)
        filho = atleta("lucas", "Lucas", nascimento=date(2015, 1, 1), responsavel=mae)
        PlanoTreino.prescrever(atleta=filho, profissional=self.prof, objetivo="Coordenação", frequencia_semanal=2,
                               itens=[{"exercicio": self.prancha, "series": 2, "repeticoes": 1}])
        self.prescrever()
        r = self.como(mae.usuario).get("/api/planos/")
        self.assertEqual([p["atleta"] for p in r.data["results"]], [filho.pk])

    def test_prescreve_plano_pela_api_e_versiona(self):
        api = self.como(self.prof.funcionario.usuario)
        dados = {"atleta": self.joao.pk, "objetivo": "Força", "frequencia_semanal": 3,
                 "itens": [{"exercicio": self.agachamento.pk, "series": 4, "repeticoes": 10, "carga": "20 kg"}]}
        self.assertEqual(api.post("/api/planos/", dados, format="json").status_code, 201)
        r = api.post("/api/planos/", {**dados, "objetivo": "Hipertrofia"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["versao"], 2)
        self.assertEqual(r.data["itens"][0]["nome"], "Agachamento")
        self.assertEqual(api.get(f"/api/planos/?atleta={self.joao.pk}&ativo=true").data["count"], 1)

    def test_plano_sem_exercicio_da_400(self):
        r = self.como(self.prof.funcionario.usuario).post(
            "/api/planos/", {"atleta": self.joao.pk, "objetivo": "Força", "frequencia_semanal": 3, "itens": []},
            format="json")
        self.assertEqual(r.status_code, 400)

    def test_admin_precisa_dizer_o_profissional(self):
        chefe = User.objects.create_user("chefe", is_staff=True)
        r = self.como(chefe).post("/api/avaliacoes/", {"atleta": self.joao.pk, "velocidade": "5"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("profissional", r.data)
