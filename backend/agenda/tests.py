from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase

from estrutura.models import Espaco, Especialidade, Servico,Equipamento
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


class ApiDeAgendamento(Base):
    def setUp(self):
        super().setUp()
        from rest_framework.test import APIClient
        self.api = APIClient()
        self.api.force_authenticate(self.nutricionista.funcionario.usuario)

    def test_sem_login_nao_ve_nada(self):
        from rest_framework.test import APIClient
        self.assertEqual(APIClient().get("/api/agendamentos/").status_code, 403)

    def test_cria_pela_api(self):
        r = self.api.post("/api/agendamentos/", {"servico": self.consulta.pk, "profissional": self.nutricionista.pk,
                                                 "espaco": self.consultorio.pk, "inicio": hora(2, 9).isoformat()})
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["status"], "AGENDADO")
        self.assertEqual(len(r.data["protocolo"]), 10)

    def test_regra_do_model_vira_erro_400(self):
        r = self.api.post("/api/agendamentos/", {"servico": self.consulta.pk, "profissional": self.treinador.pk,
                                                 "espaco": self.consultorio.pk, "inicio": hora(2, 9).isoformat()})
        self.assertEqual(r.status_code, 400)
        self.assertIn("profissional", r.data)

    def test_cancelar_e_reagendar(self):
        a, b = self.agendar(), self.agendar(hora(2, 11))
        self.assertEqual(self.api.post(f"/api/agendamentos/{a.pk}/cancelar/", {"justificativa": ""}).status_code, 400)
        r = self.api.post(f"/api/agendamentos/{a.pk}/cancelar/", {"justificativa": "Atleta doente"})
        self.assertEqual(r.data["status"], "CANCELADO")
        self.assertEqual(self.api.post(f"/api/agendamentos/{a.pk}/cancelar/", {"justificativa": "De novo"}).status_code, 400)
        r = self.api.post(f"/api/agendamentos/{b.pk}/reagendar/", {"inicio": hora(3, 9).isoformat()})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["substitui"], b.pk)

    def test_nao_apaga(self):
        a = self.agendar()
        self.assertEqual(self.api.delete(f"/api/agendamentos/{a.pk}/").status_code, 405)

    def test_filtra_por_status(self):
        self.agendar().cancelar("Atleta doente")
        self.agendar(hora(2, 11))
        r = self.api.get("/api/agendamentos/?status=AGENDADO")
        self.assertEqual(r.data["count"], 1)
class ReservaDeEquipamentos(Base):
    def setUp(self):
        super().setUp()
        from estrutura.models import Equipamento
        self.bioimpedancia = Equipamento.objects.create(nome="Bioimpedância", quantidade=1)
        self.esteiras = Equipamento.objects.create(nome="Esteira", quantidade=2)
        self.consultorio2 = Espaco.objects.create(nome="Consultório 2")
        self.consultorio2.especialidades.add(self.nutri)
        self.bia = profissional("bia", "Bia", "M003", self.nutri)

    def test_reserva_o_equipamento(self):
        a = self.agendar()
        a.reservar_equipamentos([self.bioimpedancia])
        self.assertEqual(list(a.equipamentos.all()), [self.bioimpedancia])

    def test_unidade_unica_ja_reservada_no_mesmo_horario(self):
        self.agendar().reservar_equipamentos([self.bioimpedancia])
        outro = self.agendar(profissional=self.bia, espaco=self.consultorio2)  # mesmo horário, outra sala
        with self.assertRaises(ValidationError) as erro:
            outro.reservar_equipamentos([self.bioimpedancia])
        self.assertIn("equipamentos", erro.exception.message_dict)

    def test_duas_unidades_cabem_duas_reservas(self):
        self.agendar().reservar_equipamentos([self.esteiras])
        self.agendar(profissional=self.bia, espaco=self.consultorio2).reservar_equipamentos([self.esteiras])

    def test_outro_horario_pode(self):
        self.agendar().reservar_equipamentos([self.bioimpedancia])
        self.agendar(hora(2, 10)).reservar_equipamentos([self.bioimpedancia])

    def test_cancelado_libera_o_equipamento(self):
        a = self.agendar()
        a.reservar_equipamentos([self.bioimpedancia])
        a.cancelar("Atleta doente")
        self.agendar(profissional=self.bia, espaco=self.consultorio2).reservar_equipamentos([self.bioimpedancia])

    def test_fora_de_uso_nao_reserva(self):
        self.bioimpedancia.ativo = False
        self.bioimpedancia.save()
        with self.assertRaises(ValidationError):
            self.agendar().reservar_equipamentos([self.bioimpedancia])

    def test_reagendar_leva_os_equipamentos(self):
        a = self.agendar()
        a.reservar_equipamentos([self.bioimpedancia])
        novo = a.reagendar(hora(3, 9))
        self.assertEqual(list(novo.equipamentos.all()), [self.bioimpedancia])

    def test_pela_api(self):
        from rest_framework.test import APIClient
        api = APIClient()
        api.force_authenticate(self.nutricionista.funcionario.usuario)
        dados = {"servico": self.consulta.pk, "profissional": self.nutricionista.pk, "espaco": self.consultorio.pk,
                 "inicio": hora(2, 9).isoformat(), "equipamentos": [self.bioimpedancia.pk]}
        r = api.post("/api/agendamentos/", dados, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["equipamentos"], [self.bioimpedancia.pk])
        dados.update(profissional=self.bia.pk, espaco=self.consultorio2.pk)
        r = api.post("/api/agendamentos/", dados, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("equipamentos", r.data)
        self.assertEqual(Agendamento.objects.count(), 1)  # o segundo não ficou gravado pela metade    
