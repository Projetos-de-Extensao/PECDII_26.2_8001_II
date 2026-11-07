from datetime import timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APIClient

from pessoas.models import Recepcao
from pkzlab.testes_comuns import atleta, funcionario, hora, usuario_com_papel

from .models import Agendamento, Atendimento
from .tests import Base


class RegrasDoAtendimento(Base):
    def setUp(self):
        super().setUp()
        self.agendamento = self.agendar()  # segunda às 9h
        self.depois = hora(2, 9, 30)
        self.autor = self.nutricionista.funcionario.usuario

    def registrar(self, status, justificativa="", agora=None):
        return Atendimento.registrar(self.agendamento, status, self.autor, justificativa, agora or self.depois)

    def test_presenca_nao_precisa_de_justificativa(self):
        a = self.registrar(Atendimento.Status.PRESENCA)
        self.assertEqual(a.registrado_por, self.autor)
        self.assertIsNotNone(a.registrado_em)

    def test_falta_exige_justificativa(self):
        with self.assertRaises(ValidationError) as erro:
            self.registrar(Atendimento.Status.FALTA, "  ")
        self.assertIn("justificativa", erro.exception.message_dict)
        self.registrar(Atendimento.Status.FALTA, "Não avisou")

    def test_so_depois_que_o_horario_comeca(self):
        with self.assertRaises(ValidationError) as erro:
            self.registrar(Atendimento.Status.PRESENCA, agora=hora(2, 8, 59))
        self.assertIn("agendamento", erro.exception.message_dict)

    def test_um_registro_por_agendamento(self):
        self.registrar(Atendimento.Status.PRESENCA)
        with self.assertRaises(ValidationError):
            self.registrar(Atendimento.Status.FALTA, "Engano")

    def test_agendamento_cancelado_nao_recebe_registro(self):
        self.agendamento.cancelar("Atleta doente")
        with self.assertRaises(ValidationError):
            self.registrar(Atendimento.Status.PRESENCA)

    def test_cancelamento_libera_o_horario(self):
        self.registrar(Atendimento.Status.CANCELAMENTO, "Sala sem luz")
        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.status, Agendamento.Status.CANCELADO)
        self.assertEqual(self.agendamento.justificativa, "Sala sem luz")


class ApiDeAtendimento(Base):
    def setUp(self):
        super().setUp()
        self.agendamento = self.agendar(timezone.now() - timedelta(minutes=30))  # já começou
        self.url = f"/api/agendamentos/{self.agendamento.pk}/atendimento/"
        self.api = APIClient()

    def como(self, usuario):
        self.api.force_authenticate(usuario)
        return self.api

    def test_profissional_do_agendamento_registra(self):
        r = self.como(self.nutricionista.funcionario.usuario).post(self.url, {"status": "PRESENCA"})
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["status"], "PRESENCA")
        self.assertEqual(r.data["registrado_por"], self.nutricionista.funcionario.usuario.pk)

    def test_falta_sem_justificativa_da_400(self):
        r = self.como(self.nutricionista.funcionario.usuario).post(self.url, {"status": "FALTA"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("justificativa", r.data)

    def test_recepcao_e_atleta_nao_registram(self):
        recepcao = Recepcao.objects.create(funcionario=funcionario("rita", "Rita", "M050"))
        self.assertEqual(self.como(recepcao.funcionario.usuario).post(self.url, {"status": "PRESENCA"}).status_code, 403)
        # o atleta vê o próprio agendamento, mas não registra o atendimento
        self.assertEqual(self.como(self.joao.usuario).post(self.url, {"status": "PRESENCA"}).status_code, 403)

    def test_admin_registra(self):
        chefe = usuario_com_papel("chefe", "administrador")
        self.assertEqual(self.como(chefe).post(self.url, {"status": "PRESENCA"}).status_code, 201)

    def test_cada_um_ve_so_o_seu_historico(self):
        Atendimento.registrar(self.agendamento, Atendimento.Status.PRESENCA, self.nutricionista.funcionario.usuario)
        maria = atleta("maria", "Maria")
        self.assertEqual(self.como(self.joao.usuario).get("/api/atendimentos/").data["count"], 1)
        self.assertEqual(self.como(maria.usuario).get("/api/atendimentos/").data["count"], 0)
        self.assertEqual(self.como(self.treinador.funcionario.usuario).get("/api/atendimentos/").data["count"], 0)
