"""Testes da issue #36: lista de espera (UC19)."""
from datetime import date, timedelta
from io import StringIO

from django.core.exceptions import ValidationError
from django.core.management import call_command
from rest_framework.test import APIClient

from estrutura.models import Servico
from pessoas.cadastros import cadastrar_responsavel
from pkzlab.testes_comuns import atleta, hora

from .models import Agendamento, Aula, Aviso, Disponibilidade, ListaEspera
from .tests import Base


class ComFila(Base):
    def setUp(self):
        super().setUp()
        Disponibilidade.objects.create(profissional=self.nutricionista, dia_da_semana=hora(2, 9).weekday(),
                                       hora_inicio=hora(2, 8).time(), hora_fim=hora(2, 12).time())
        self.consulta_seg = self.agendar(hora(2, 9))  # João ocupa segunda 9h
        self.maria = atleta("maria", "Maria")
        self.ana = atleta("ana", "Ana")

    def entrar(self, quem, inicio=None, **kw):
        dados = dict(atleta=quem, servico=self.consulta, profissional=self.nutricionista, inicio=inicio or hora(2, 9))
        dados.update(kw)
        espera = ListaEspera(**dados)
        espera.clean()
        espera.save()
        return espera

    def recarregar(self, *esperas):
        for espera in esperas:
            espera.refresh_from_db()


class EntrarNaFila(ComFila):
    def test_entra_e_ganha_a_posicao(self):
        maria, ana = self.entrar(self.maria), self.entrar(self.ana)
        self.assertEqual((maria.posicao, ana.posicao), (1, 2))

    def test_horario_livre_nao_tem_fila(self):
        with self.assertRaises(ValidationError) as erro:
            self.entrar(self.maria, hora(2, 11))
        self.assertIn("inicio", erro.exception.message_dict)

    def test_nao_entra_duas_vezes(self):
        self.entrar(self.maria)
        with self.assertRaises(ValidationError):
            self.entrar(self.maria)

    def test_quem_ja_tem_o_horario_nao_entra(self):
        with self.assertRaises(ValidationError):
            self.entrar(self.joao)


class OfertaDaVaga(ComFila):
    def test_cancelamento_oferece_ao_primeiro_da_fila(self):
        maria, ana = self.entrar(self.maria), self.entrar(self.ana)
        self.consulta_seg.cancelar("viagem")
        self.recarregar(maria, ana)
        self.assertEqual(maria.status, ListaEspera.Status.OFERECIDA)
        self.assertEqual(maria.vaga, self.consulta_seg)
        self.assertIsNotNone(maria.prazo)
        self.assertTrue(Aviso.objects.filter(usuario=self.maria.usuario, texto__contains="Confirme até").exists())
        self.assertEqual(ana.status, ListaEspera.Status.AGUARDANDO)
        self.assertEqual(ana.posicao, 1)

    def test_vaga_oferecida_fica_guardada(self):
        self.entrar(self.maria)
        self.consulta_seg.cancelar("viagem")
        outro = Agendamento(atleta=self.ana, servico=self.consulta, profissional=self.nutricionista,
                            espaco=self.consultorio, inicio=hora(2, 9))
        with self.assertRaises(ValidationError) as erro:
            outro.clean()
        self.assertIn("lista de espera", str(erro.exception))

    def test_confirmar_vira_agendamento(self):
        maria = self.entrar(self.maria)
        self.consulta_seg.cancelar("viagem")
        maria.refresh_from_db()
        novo = maria.confirmar()
        self.assertEqual((novo.atleta, novo.inicio, novo.status), (self.maria, hora(2, 9), Agendamento.Status.AGENDADO))
        maria.refresh_from_db()
        self.assertEqual(maria.status, ListaEspera.Status.CONFIRMADA)
        self.assertEqual(maria.agendamento, novo)

    def test_recusar_passa_para_o_proximo(self):
        maria, ana = self.entrar(self.maria), self.entrar(self.ana)
        self.consulta_seg.cancelar("viagem")
        maria.refresh_from_db()
        maria.recusar()
        self.recarregar(maria, ana)
        self.assertEqual(maria.status, ListaEspera.Status.RECUSADA)
        self.assertEqual(ana.status, ListaEspera.Status.OFERECIDA)

    def test_sair_com_vaga_oferecida_passa_para_o_proximo(self):
        maria, ana = self.entrar(self.maria), self.entrar(self.ana)
        self.consulta_seg.cancelar("viagem")
        maria.refresh_from_db()
        maria.sair()
        self.recarregar(maria, ana)
        self.assertEqual(maria.status, ListaEspera.Status.SAIU)
        self.assertEqual(ana.status, ListaEspera.Status.OFERECIDA)

    def test_pula_quem_ja_marcou_outra_coisa_no_horario(self):
        maria, ana = self.entrar(self.maria), self.entrar(self.ana)
        treino = Servico.objects.create(nome="Treino", especialidade=self.personal, duracao_minutos=50)
        Agendamento.objects.create(atleta=self.maria, servico=treino, profissional=self.treinador,
                                   espaco=self.academia, inicio=hora(2, 9))
        self.consulta_seg.cancelar("viagem")
        self.recarregar(maria, ana)
        self.assertEqual(maria.status, ListaEspera.Status.AGUARDANDO)
        self.assertEqual(ana.status, ListaEspera.Status.OFERECIDA)

    def test_em_cima_da_hora_ninguem_recebe_a_vaga(self):
        maria = self.entrar(self.maria)
        Agendamento.objects.filter(pk=self.consulta_seg.pk).update(status=Agendamento.Status.CANCELADO)
        self.assertIsNone(ListaEspera.oferecer_vaga(self.consulta_seg, agora=hora(2, 8, 40)))
        maria.refresh_from_db()
        self.assertEqual(maria.status, ListaEspera.Status.AGUARDANDO)

    def test_prazo_vencido_passa_para_o_proximo(self):
        maria, ana = self.entrar(self.maria), self.entrar(self.ana)
        self.consulta_seg.cancelar("viagem")
        maria.refresh_from_db()
        self.assertEqual(ListaEspera.vencer_ofertas(agora=maria.prazo), 1)
        self.recarregar(maria, ana)
        self.assertEqual(maria.status, ListaEspera.Status.VENCIDA)
        self.assertEqual(ana.status, ListaEspera.Status.OFERECIDA)
        with self.assertRaises(ValidationError):
            maria.confirmar()

    def test_nao_confirma_depois_do_prazo(self):
        maria = self.entrar(self.maria)
        self.consulta_seg.cancelar("viagem")
        maria.refresh_from_db()
        with self.assertRaises(ValidationError):
            maria.confirmar(agora=maria.prazo + timedelta(minutes=1))

    def test_menor_de_idade_avisa_o_responsavel(self):
        mae = cadastrar_responsavel(email="mae@x.com", nome="Rita", senha="senha12345", aceitou_termos=True)
        pedro = atleta("pedro", "Pedro", nascimento=date(2015, 5, 1), responsavel=mae)
        self.entrar(pedro)
        self.consulta_seg.cancelar("viagem")
        self.assertTrue(Aviso.objects.filter(usuario=pedro.usuario, texto__contains="Confirme até").exists())
        self.assertTrue(Aviso.objects.filter(usuario=mae.usuario, texto__contains="Confirme até").exists())


class ComTurma(ComFila):
    # turma de pilates com 2 vagas na segunda às 10h (base de outros testes, sem testes próprios)
    def setUp(self):
        super().setUp()
        self.pilates = Servico.objects.create(nome="Pilates", especialidade=self.nutri, duracao_minutos=50, vagas=2)
        self.pilates.espacos.add(self.consultorio)
        self.aula = Aula.objects.create(servico=self.pilates, profissional=self.nutricionista,
                                        espaco=self.consultorio, dia=hora(2, 10).date(), hora_inicio=hora(2, 10).time())

    def inscrever(self, quem):
        agendamento = Agendamento(atleta=quem, servico=self.pilates, profissional=self.nutricionista,
                                  espaco=self.consultorio, aula=self.aula, inicio=self.aula.inicio)
        agendamento.clean()
        agendamento.save()
        return agendamento


class FilaDaAula(ComTurma):
    def test_segundo_atleta_entra_na_aula_com_vaga(self):
        self.inscrever(self.joao)
        self.inscrever(self.ana)
        self.assertTrue(self.aula.lotada)

    def test_turma_lotada_oferece_a_vaga_e_guarda_ate_confirmar(self):
        joao_na_aula = self.inscrever(self.joao)
        self.inscrever(self.ana)
        maria = self.entrar(self.maria, aula=self.aula)
        self.assertEqual((maria.servico, maria.inicio), (self.pilates, self.aula.inicio))
        joao_na_aula.cancelar("lesão")
        maria.refresh_from_db()
        self.assertEqual(maria.status, ListaEspera.Status.OFERECIDA)
        self.assertTrue(self.aula.lotada)  # a vaga está guardada para a Maria
        novo = maria.confirmar()
        self.assertEqual(novo.aula, self.aula)

    def test_aula_com_vaga_nao_tem_fila(self):
        with self.assertRaises(ValidationError):
            self.entrar(self.maria, aula=self.aula)


class ApiDaListaDeEspera(ComFila):
    def setUp(self):
        super().setUp()
        self.api = APIClient()
        self.api.force_authenticate(self.maria.usuario)

    def test_entra_pela_api(self):
        resposta = self.api.post("/api/lista-espera/", {
            "atleta": self.maria.pk, "servico": self.consulta.pk, "profissional": self.nutricionista.pk,
            "inicio": hora(2, 9).isoformat()}, format="json")
        self.assertEqual(resposta.status_code, 201, resposta.data)
        self.assertEqual(resposta.data["posicao"], 1)
        self.assertEqual(resposta.data["status"], ListaEspera.Status.AGUARDANDO)

    def test_nao_coloca_outro_atleta_na_fila(self):
        resposta = self.api.post("/api/lista-espera/", {
            "atleta": self.ana.pk, "servico": self.consulta.pk, "profissional": self.nutricionista.pk,
            "inicio": hora(2, 9).isoformat()}, format="json")
        self.assertEqual(resposta.status_code, 400)

    def test_confirma_pela_api(self):
        maria = self.entrar(self.maria)
        self.consulta_seg.cancelar("viagem")
        resposta = self.api.post(f"/api/lista-espera/{maria.pk}/confirmar/")
        self.assertEqual(resposta.status_code, 201, resposta.data)
        self.assertEqual(resposta.data["atleta"], self.maria.pk)

    def test_nao_ve_a_fila_dos_outros(self):
        ana = self.entrar(self.ana)
        self.assertEqual(self.api.post(f"/api/lista-espera/{ana.pk}/sair/").status_code, 404)
        self.assertEqual(self.api.get("/api/lista-espera/").data["count"], 0)


class RotinaVenceAsVagas(ComFila):
    def test_comando_diz_quantas_vencidas(self):
        saida = StringIO()
        call_command("rotinas_da_agenda", stdout=saida)
        self.assertIn("Vagas da lista de espera vencidas: 0", saida.getvalue())
        self.assertIn("Lembretes enviados:", saida.getvalue())
