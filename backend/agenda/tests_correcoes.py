"""Correções da revisão do back-end: turmas, lista de espera da aula, horário passado e avisos."""
from datetime import time, timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APIClient

from pessoas.cadastros import cadastrar_responsavel
from pkzlab.testes_comuns import atleta, hora, usuario_com_papel

from .models import Agendamento, Aula, Aviso, ListaEspera
from .tests import Base
from .tests_lista_espera import ComTurma


class EntrarNaTurma(ComTurma):
    # turma de 2 vagas (pilates) na segunda às 10h. Entrar na aula = agendamento com aula (UC06 A2).
    # self.inscrever(quem) vem do ComTurma e cria o agendamento da aula passando pelo clean().

    def test_voltar_depois_de_cancelar_precisa_de_vaga(self):
        joao = self.inscrever(self.joao)
        self.inscrever(self.ana)
        joao.cancelar("Não vou poder ir.")
        self.inscrever(self.maria)  # a Maria pega a vaga que o João largou
        with self.assertRaises(ValidationError) as erro:
            self.inscrever(self.joao)
        self.assertIn("aula", erro.exception.message_dict)

    def test_voltar_depois_de_cancelar_com_vaga_livre_funciona(self):
        joao = self.inscrever(self.joao)
        joao.cancelar("Errei o dia.")
        self.inscrever(self.joao)  # não existe trava de "já inscrito" para quem cancelou
        self.assertEqual(self.aula.agendamentos.filter(atleta=self.joao, status=Agendamento.Status.AGENDADO).count(), 1)

    def test_mesmo_atleta_nao_ocupa_duas_vagas(self):
        self.inscrever(self.joao)
        with self.assertRaises(ValidationError) as erro:
            self.inscrever(self.joao)
        self.assertIn("atleta", erro.exception.message_dict)
        self.assertEqual(self.aula.vagas_restantes, 1)

    def test_cancelar_oferece_a_vaga_para_a_fila(self):
        joao = self.inscrever(self.joao)
        self.inscrever(self.ana)
        maria = self.entrar(self.maria, aula=self.aula)
        joao.cancelar("Não vou poder ir.")
        maria.refresh_from_db()
        self.assertEqual(maria.status, ListaEspera.Status.OFERECIDA)
        self.assertTrue(self.aula.lotada)  # a vaga fica guardada para a Maria
        novo = maria.confirmar()
        self.assertEqual((novo.aula, novo.inicio, novo.espaco), (self.aula, self.aula.inicio, self.consultorio))

    def test_recusar_passa_a_vaga_para_o_proximo(self):
        joao = self.inscrever(self.joao)
        self.inscrever(self.ana)
        maria = self.entrar(self.maria, aula=self.aula)
        pedro = self.entrar(atleta("pedro", "Pedro"), aula=self.aula)
        joao.cancelar("Não vou poder ir.")
        maria.refresh_from_db()
        maria.recusar()
        pedro.refresh_from_db()
        self.assertEqual(pedro.status, ListaEspera.Status.OFERECIDA)

    def test_responsavel_coloca_o_dependente_na_aula(self):
        mae = cadastrar_responsavel(email="mae@x.com", nome="Mãe", senha="senha12345", aceitou_termos=True)
        filho = atleta("filho", "Filho", nascimento=hora(2, 9).date() - timedelta(days=365 * 12), responsavel=mae)
        api = APIClient()
        api.force_authenticate(mae.usuario)
        r = api.post("/api/agendamentos/", {"aula": self.aula.pk, "atleta": filho.pk})
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(api.get("/api/agendamentos/").data["count"], 1)
        # e não vê o de quem não é dependente dela
        self.inscrever(self.joao)
        self.assertEqual(api.get("/api/agendamentos/").data["count"], 1)

    def test_nao_coloca_atleta_de_outra_pessoa_na_aula(self):
        mae = cadastrar_responsavel(email="mae@x.com", nome="Mãe", senha="senha12345", aceitou_termos=True)
        api = APIClient()
        api.force_authenticate(mae.usuario)
        r = api.post("/api/agendamentos/", {"aula": self.aula.pk, "atleta": self.joao.pk})
        self.assertIn(r.status_code, (400, 403))
        self.assertFalse(self.aula.agendamentos.exists())

    def test_rota_de_inscricoes_nao_existe_mais(self):
        api = APIClient()
        api.force_authenticate(usuario_com_papel("adm", "administrador"))
        self.assertEqual(api.get("/api/inscricoes/").status_code, 404)


class AgendamentoDaAulaPelaApi(ComTurma):
    def test_basta_mandar_a_aula(self):
        api = APIClient()
        api.force_authenticate(self.maria.usuario)
        r = api.post("/api/agendamentos/", {"atleta": self.maria.pk, "aula": self.aula.pk})
        self.assertEqual(r.status_code, 201, r.data)
        agendamento = Agendamento.objects.get(pk=r.data["id"])
        self.assertEqual((agendamento.aula, agendamento.inicio), (self.aula, self.aula.inicio))
        self.assertEqual(self.aula.vagas_restantes, 1)

    def test_sem_aula_os_campos_continuam_obrigatorios(self):
        api = APIClient()
        api.force_authenticate(self.maria.usuario)
        r = api.post("/api/agendamentos/", {"atleta": self.maria.pk, "servico": self.consulta.pk})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(set(r.data), {"profissional", "espaco", "inicio"})

    def test_aula_desativada_nao_recebe_agendamento(self):
        self.aula.ativo = False
        self.aula.save()
        with self.assertRaises(ValidationError) as erro:
            self.inscrever(self.maria)
        self.assertIn("aula", erro.exception.message_dict)


class EditarAula(ComTurma):
    def test_mudar_o_inicio_recalcula_o_fim(self):
        self.assertEqual(self.aula.hora_fim, time(10, 50))
        self.aula.hora_inicio = time(11)
        self.aula.save()
        self.aula.refresh_from_db()
        self.assertEqual(self.aula.hora_fim, time(11, 50))

    def test_editar_pela_api(self):
        admin = usuario_com_papel("chefe", "administrador")
        api = APIClient()
        api.force_authenticate(admin)
        r = api.patch(f"/api/aulas/{self.aula.pk}/", {"hora_inicio": "11:00"})
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["hora_fim"], "11:50:00")

    def test_os_alunos_da_propria_turma_nao_sao_conflito(self):
        self.inscrever(self.ana)
        self.aula.clean()

    def test_aula_que_passa_da_meia_noite_e_recusada(self):
        self.aula.hora_inicio = time(23, 30)
        with self.assertRaises(ValidationError) as erro:
            self.aula.clean()
        self.assertIn("hora_inicio", erro.exception.message_dict)


class HorarioQueJaPassou(Base):
    def novo(self, inicio):
        return Agendamento(atleta=self.joao, servico=self.consulta, profissional=self.nutricionista,
                           espaco=self.consultorio, inicio=inicio)

    def test_nao_agenda_no_passado(self):
        with self.assertRaises(ValidationError) as erro:
            self.novo(timezone.now() - timedelta(hours=1)).clean()
        self.assertIn("inicio", erro.exception.message_dict)

    def test_o_relogio_pode_ser_informado(self):
        inicio = hora(2, 9)
        with self.assertRaises(ValidationError) as erro:
            self.novo(inicio).clean(agora=inicio + timedelta(minutes=1))
        self.assertIn("Esse horário já passou.", erro.exception.message_dict["inicio"])

    def test_nao_reagenda_para_o_passado(self):
        agendamento = self.agendar()
        with self.assertRaises(ValidationError) as erro:
            agendamento.reagendar(timezone.now() - timedelta(days=1))
        self.assertIn("Esse horário já passou.", erro.exception.message_dict["inicio"])
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, Agendamento.Status.AGENDADO)  # nada mudou

    def test_api_recusa_o_passado(self):
        api = APIClient()
        api.force_authenticate(self.joao.usuario)
        r = api.post("/api/agendamentos/", {
            "atleta": self.joao.pk, "servico": self.consulta.pk, "profissional": self.nutricionista.pk,
            "espaco": self.consultorio.pk, "inicio": (timezone.now() - timedelta(days=7)).isoformat()})
        self.assertEqual(r.status_code, 400)
        self.assertIn("inicio", r.data)


class AvisoNoHorarioLocal(Base):
    def test_cancelamento_mostra_o_horario_de_brasilia(self):
        agendamento = Agendamento.objects.get(pk=self.agendar(hora(2, 9)).pk)  # vem do banco em UTC
        agendamento.cancelar("Atleta doente")
        texto = Aviso.objects.get(usuario=self.nutricionista.funcionario.usuario).texto
        self.assertIn("às 09:00", texto)
