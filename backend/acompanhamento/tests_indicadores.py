from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone

from agenda.models import Agendamento, Atendimento
from estrutura.models import Espaco, Servico
from pessoas.cadastros import cadastrar_responsavel
from pessoas.models import Recepcao
from pkzlab.testes_comuns import atleta, funcionario, profissional, usuario_com_papel

from .indicadores import evolucao, relatorio_de_desempenho
from .models import AvaliacaoFisica
from .tests import Base

HOJE = timezone.localdate()


class ComDados(Base):
    def setUp(self):
        super().setUp()
        especialidade = self.prof.especialidades.first()
        self.sala = Espaco.objects.create(nome="Pista")
        self.sala.especialidades.add(especialidade)
        self.treino = Servico.objects.create(nome="Treino", especialidade=especialidade)
        self.outro_prof = profissional("olga", "Olga", "M002", especialidade)

    def avaliar(self, dia, prof=None, quem=None, **testes):
        return AvaliacaoFisica.objects.create(atleta=quem or self.joao, profissional=prof or self.prof,
                                              data=dia, **testes)

    def atendimento(self, dias_atras, status, prof=None, quem=None):
        inicio = timezone.now() - timedelta(days=dias_atras)
        agendamento = Agendamento.objects.create(atleta=quem or self.joao, servico=self.treino,
                                                 profissional=prof or self.prof, espaco=self.sala, inicio=inicio)
        return Atendimento.registrar(agendamento, status, (prof or self.prof).funcionario.usuario,
                                     "" if status == Atendimento.Status.PRESENCA else "Motivo")


class Evolucao(ComDados):
    def test_sem_historico_avisa(self):
        self.avaliar(HOJE, velocidade=Decimal("5"))
        dados = evolucao(self.joao)
        self.assertFalse(dados["historico_suficiente"])
        self.assertTrue(dados["mensagem"])
        self.assertIsNone(dados["variacao"]["velocidade"])

    def test_variacao_do_primeiro_ao_ultimo(self):
        self.avaliar(HOJE - timedelta(days=60), velocidade=Decimal("5.40"), forca=Decimal("80"))
        self.avaliar(HOJE - timedelta(days=30), velocidade=Decimal("5.10"))
        self.avaliar(HOJE, velocidade=Decimal("4.90"), forca=Decimal("95"))
        dados = evolucao(self.joao)
        self.assertTrue(dados["historico_suficiente"])
        self.assertEqual(dados["variacao"]["velocidade"], Decimal("-0.50"))
        self.assertEqual(dados["variacao"]["forca"], Decimal("15"))
        self.assertEqual([a["data"] for a in dados["avaliacoes"]],
                         [HOJE - timedelta(days=60), HOJE - timedelta(days=30), HOJE])

    def test_frequencia_ignora_cancelamento_na_taxa(self):
        for dias, status in ((3, "PRESENCA"), (2, "PRESENCA"), (1, "FALTA"), (1, "CANCELAMENTO")):
            self.atendimento(dias, status)
        freq = evolucao(self.joao)["frequencia"]
        self.assertEqual((freq["presencas"], freq["faltas"], freq["cancelamentos"]), (2, 1, 1))
        self.assertEqual(freq["taxa_presenca"], 0.67)

    def test_periodo_filtra(self):
        self.avaliar(HOJE - timedelta(days=60), velocidade=Decimal("5.40"))
        self.avaliar(HOJE, velocidade=Decimal("4.90"))
        self.assertEqual(len(evolucao(self.joao, de=HOJE - timedelta(days=10))["avaliacoes"]), 1)

    def test_planos_ao_longo_do_tempo(self):
        self.prescrever()
        self.prescrever("Hipertrofia")
        self.assertEqual([(p["versao"], p["ativo"]) for p in evolucao(self.joao)["planos"]], [(1, False), (2, True)])


class Relatorio(ComDados):
    def test_sem_dados_no_periodo(self):
        dados = relatorio_de_desempenho(date(2020, 1, 1), date(2020, 1, 31))
        self.assertEqual(dados["atletas"], [])
        self.assertTrue(dados["mensagem"])

    def test_consolida_por_atleta(self):
        maria = atleta("maria", "Maria")
        self.avaliar(HOJE - timedelta(days=5), velocidade=Decimal("5"))
        self.avaliar(HOJE, velocidade=Decimal("4.8"))
        self.atendimento(1, "PRESENCA")
        self.atendimento(2, "FALTA", quem=maria)
        dados = relatorio_de_desempenho(HOJE - timedelta(days=30), HOJE)
        self.assertEqual([linha["nome"] for linha in dados["atletas"]], ["João", "Maria"])
        joao = dados["atletas"][0]
        self.assertEqual((joao["avaliacoes"], joao["variacao"]["velocidade"]), (2, Decimal("-0.2")))
        self.assertEqual(dados["totais"]["faltas"], 1)

    def test_profissional_so_ve_o_seu(self):
        self.avaliar(HOJE, velocidade=Decimal("5"))
        self.avaliar(HOJE, prof=self.outro_prof, quem=atleta("maria", "Maria"), velocidade=Decimal("6"))
        dados = relatorio_de_desempenho(HOJE - timedelta(days=1), HOJE, profissional=self.prof)
        self.assertEqual([linha["nome"] for linha in dados["atletas"]], ["João"])


class ApiDeIndicadores(ComDados):
    def setUp(self):
        super().setUp()
        self.avaliar(HOJE, velocidade=Decimal("5"))
        self.url = f"/api/atletas/{self.joao.pk}/evolucao/"
        self.relatorio = f"/api/relatorios/desempenho/?de={HOJE - timedelta(days=30)}&ate={HOJE}"

    def get(self, usuario, url):
        self.client.force_login(usuario)
        return self.client.get(url)

    def test_quem_ve_a_evolucao(self):
        mae = cadastrar_responsavel(email="mae@x.com", nome="Ana", senha="senha12345", aceitou_termos=True)
        filho = atleta("lucas", "Lucas", nascimento=date(2015, 1, 1), responsavel=mae)
        self.assertEqual(self.get(self.joao.usuario, self.url).status_code, 200)
        self.assertEqual(self.get(self.prof.funcionario.usuario, self.url).status_code, 200)
        self.assertEqual(self.get(mae.usuario, f"/api/atletas/{filho.pk}/evolucao/").status_code, 200)
        self.assertEqual(self.get(mae.usuario, self.url).status_code, 404)              # não é dependente dela
        self.assertEqual(self.get(atleta("maria", "Maria").usuario, self.url).status_code, 404)

    def test_recepcao_nao_ve_a_evolucao(self):
        rita = Recepcao.objects.create(funcionario=funcionario("rita", "Rita", "M050")).funcionario.usuario
        self.assertEqual(self.get(rita, self.url).status_code, 404)  # RNF03: dado técnico é da equipe técnica
        self.assertEqual(self.get(usuario_com_papel("chefe", "administrador"), self.url).status_code, 200)

    def test_periodo_invertido_da_400(self):
        r = self.get(self.joao.usuario, f"{self.url}?de={HOJE}&ate={HOJE - timedelta(days=1)}")
        self.assertEqual(r.status_code, 400)

    def test_relatorio_so_para_profissional_e_admin(self):
        rita = Recepcao.objects.create(funcionario=funcionario("rita", "Rita", "M050")).funcionario.usuario
        self.assertEqual(self.get(self.joao.usuario, self.relatorio).status_code, 403)
        self.assertEqual(self.get(rita, self.relatorio).status_code, 403)
        self.assertEqual(self.get(self.prof.funcionario.usuario, self.relatorio).status_code, 200)
        chefe = usuario_com_papel("chefe", "administrador")
        self.assertEqual(self.get(chefe, self.relatorio).json()["totais"]["avaliacoes"], 1)

    def test_relatorio_exige_periodo(self):
        r = self.get(self.prof.funcionario.usuario, "/api/relatorios/desempenho/")
        self.assertEqual(r.status_code, 400)
        self.assertIn("de", r.json())

    def test_profissional_nao_ve_relatorio_de_outro(self):
        r = self.get(self.outro_prof.funcionario.usuario, f"{self.relatorio}&profissional={self.prof.pk}")
        self.assertEqual(r.json()["atletas"], [])  # o filtro é ignorado: ele só vê o que é dele
