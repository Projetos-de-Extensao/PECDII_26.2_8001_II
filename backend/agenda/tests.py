from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase

from estrutura.models import Espaco, Especialidade, Servico
from pkzlab.testes_comuns import hora, profissional

from .models import Agendamento


class Base(TestCase):
    def setUp(self):
        self.nutri = Especialidade.objects.get(nome="Nutricionista")
        self.personal = Especialidade.objects.get(nome="Personal Trainer")
        self.consultorio = Espaco.objects.create(nome="Consultório 1")
        self.consultorio.especialidades.add(self.nutri)
        self.academia = Espaco.objects.create(nome="Academia")
        self.academia.especialidades.add(self.personal)
        self.consulta = Servico.objects.create(nome="Consulta", especialidade=self.nutri, duracao_minutos=50)
        self.nutricionista = profissional("nina", "Nina", "M001", self.nutri)
        self.treinador = profissional("teo", "Teo", "M002", self.personal)

    def agendar(self, inicio=None, **kw):
        dados = dict(servico=self.consulta, profissional=self.nutricionista, espaco=self.consultorio,
                     inicio=inicio or hora(2, 9))
        dados.update(kw)
        return Agendamento.objects.create(**dados)


class CriarAgendamento(Base):
    def test_comeca_agendado_com_protocolo(self):
        a = self.agendar()
        self.assertEqual(a.status, Agendamento.Status.AGENDADO)
        self.assertEqual(len(a.protocolo), 10)
        self.assertNotEqual(a.protocolo, self.agendar(hora(2, 10)).protocolo)

    def test_fim_vem_da_duracao_do_servico(self):
        self.assertEqual(self.agendar().fim, hora(2, 9, 50))

    def test_profissional_precisa_atender_a_especialidade(self):
        with self.assertRaises(ValidationError) as erro:
            Agendamento(servico=self.consulta, profissional=self.treinador, espaco=self.consultorio,
                        inicio=hora(2, 9)).full_clean()
        self.assertIn("profissional", erro.exception.message_dict)

    def test_sala_precisa_ser_do_servico(self):
        with self.assertRaises(ValidationError) as erro:
            Agendamento(servico=self.consulta, profissional=self.nutricionista, espaco=self.academia,
                        inicio=hora(2, 9)).full_clean()
        self.assertIn("espaco", erro.exception.message_dict)


class CancelarEReagendar(Base):
    def test_cancelar_exige_justificativa(self):
        a = self.agendar()
        with self.assertRaises(ValidationError):
            a.cancelar("  ")
        a.cancelar("Atleta doente")
        a.refresh_from_db()
        self.assertEqual(a.status, Agendamento.Status.CANCELADO)
        self.assertEqual(a.justificativa, "Atleta doente")

    def test_nao_cancela_duas_vezes(self):
        a = self.agendar()
        a.cancelar("Atleta doente")
        with self.assertRaises(ValidationError):
            a.cancelar("De novo")

    def test_reagendar_guarda_o_original(self):
        original = self.agendar()
        novo = original.reagendar(hora(3, 9))
        original.refresh_from_db()
        self.assertEqual(original.status, Agendamento.Status.SUBSTITUIDO)
        self.assertEqual(novo.status, Agendamento.Status.AGENDADO)
        self.assertEqual(novo.substitui, original)
        self.assertEqual(original.substituido_por, novo)
        self.assertEqual(novo.fim - novo.inicio, timedelta(minutes=50))
