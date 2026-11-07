"""Testes da issue #32: Disponibilidade e Bloqueio (UC05, UC17)."""
from datetime import datetime, time

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from estrutura.models import Equipamento, Espaco
from pkzlab.testes_comuns import atleta, hora, profissional

from .models import Agendamento, Bloqueio, Disponibilidade
from .tests import Base


class DisponibilidadeDoProfissional(Base):
    def turno(self, inicio, fim, dia=0, profissional=None):
        return Disponibilidade(profissional=profissional or self.nutricionista, dia_da_semana=dia,
                               hora_inicio=inicio, hora_fim=fim)

    def test_fim_precisa_ser_depois_do_inicio(self):
        with self.assertRaises(ValidationError) as erro:
            self.turno(time(10), time(9)).full_clean()
        self.assertIn("hora_fim", erro.exception.message_dict)

    def test_turnos_do_mesmo_dia_nao_se_sobrepoem(self):
        self.turno(time(8), time(12)).save()
        with self.assertRaises(ValidationError):
            self.turno(time(11), time(14)).full_clean()
        self.turno(time(12), time(14)).full_clean()  # encostar não é sobrepor

    def test_outro_dia_ou_outro_profissional_pode(self):
        self.turno(time(8), time(12)).save()
        self.turno(time(8), time(12), dia=1).full_clean()
        self.turno(time(8), time(12), profissional=self.treinador).full_clean()

    def test_editar_o_proprio_turno_nao_conta_como_sobreposicao(self):
        d = self.turno(time(8), time(12))
        d.save()
        d.hora_fim = time(13)
        d.full_clean()


class BloqueioNoModel(Base):
    def bloqueio(self, inicio, fim, **alvo):
        return Bloqueio(inicio=inicio, fim=fim, motivo="Teste", **alvo)

    def test_exige_um_so_alvo(self):
        with self.assertRaises(ValidationError):
            self.bloqueio(hora(2, 9), hora(2, 10)).full_clean()
        with self.assertRaises(ValidationError):
            self.bloqueio(hora(2, 9), hora(2, 10), profissional=self.nutricionista,
                          espaco=self.consultorio).full_clean()
        self.bloqueio(hora(2, 9), hora(2, 10), profissional=self.nutricionista).full_clean()

    def test_fim_precisa_ser_depois_do_inicio(self):
        with self.assertRaises(ValidationError):
            self.bloqueio(hora(2, 10), hora(2, 9), profissional=self.nutricionista).full_clean()

    def test_afetados_do_profissional(self):
        dentro = self.agendar(hora(2, 9))
        self.agendar(hora(2, 11))                       # depois do bloqueio
        self.agendar(hora(2, 9, 30)).cancelar("Teste")  # cancelado não conta
        b = self.bloqueio(hora(2, 9, 30), hora(2, 10), profissional=self.nutricionista)
        self.assertEqual(list(b.agendamentos_afetados()), [dentro])

    def test_encostar_no_bloqueio_nao_afeta(self):
        self.agendar(hora(2, 9))  # 9:00 às 9:50
        b = self.bloqueio(hora(2, 9, 50), hora(2, 10), profissional=self.nutricionista)
        self.assertFalse(b.agendamentos_afetados().exists())

    def test_afetados_da_sala(self):
        a = self.agendar(hora(2, 9))
        self.assertEqual(list(self.bloqueio(hora(2, 9), hora(2, 10), espaco=self.consultorio)
                              .agendamentos_afetados()), [a])
        self.assertFalse(self.bloqueio(hora(2, 9), hora(2, 10), espaco=self.academia)
                         .agendamentos_afetados().exists())

    def test_afetados_do_equipamento(self):
        esteira = Equipamento.objects.create(nome="Esteira", quantidade=1)
        a = self.agendar(hora(2, 9))
        a.reservar_equipamentos([esteira])
        self.agendar(hora(2, 9, 10), profissional=self.nutricionista)  # sem equipamento
        b = self.bloqueio(hora(2, 9), hora(2, 10), equipamento=esteira)
        self.assertEqual(list(b.agendamentos_afetados()), [a])


class ApiDeDisponibilidade(Base):
    def setUp(self):
        super().setUp()
        self.api = APIClient()
        self.nina = self.nutricionista.funcionario.usuario
        self.admin = User.objects.create_user("chefe", is_staff=True)
        self.turno = {"dia_da_semana": 0, "hora_inicio": "08:00", "hora_fim": "12:00"}

    def test_profissional_cria_a_propria(self):
        self.api.force_authenticate(self.nina)
        r = self.api.post("/api/disponibilidades/", self.turno, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["profissional"], self.nutricionista.pk)

    def test_profissional_nao_cria_para_outro(self):
        self.api.force_authenticate(self.nina)
        r = self.api.post("/api/disponibilidades/", {**self.turno, "profissional": self.treinador.pk},
                          format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("profissional", r.data)
        self.assertFalse(Disponibilidade.objects.exists())

    def test_profissional_nao_mexe_na_de_outro(self):
        do_teo = Disponibilidade.objects.create(profissional=self.treinador, dia_da_semana=0,
                                                hora_inicio=time(8), hora_fim=time(12))
        self.api.force_authenticate(self.nina)
        self.assertEqual(self.api.patch(f"/api/disponibilidades/{do_teo.pk}/", {"hora_fim": "11:00"},
                                        format="json").status_code, 403)
        self.assertEqual(self.api.delete(f"/api/disponibilidades/{do_teo.pk}/").status_code, 403)

    def test_profissional_edita_e_apaga_a_propria(self):
        d = Disponibilidade.objects.create(profissional=self.nutricionista, dia_da_semana=0,
                                           hora_inicio=time(8), hora_fim=time(12))
        self.api.force_authenticate(self.nina)
        r = self.api.patch(f"/api/disponibilidades/{d.pk}/", {"hora_fim": "11:00"}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(self.api.delete(f"/api/disponibilidades/{d.pk}/").status_code, 204)

    def test_atleta_consulta_mas_nao_cadastra(self):
        Disponibilidade.objects.create(profissional=self.nutricionista, dia_da_semana=0,
                                       hora_inicio=time(8), hora_fim=time(12))
        self.api.force_authenticate(self.joao.usuario)
        self.assertEqual(self.api.get("/api/disponibilidades/").data["count"], 1)
        self.assertEqual(self.api.post("/api/disponibilidades/", self.turno, format="json").status_code, 403)

    def test_sem_login_nada(self):
        self.assertEqual(self.api.get("/api/disponibilidades/").status_code, 401)

    def test_sobreposicao_vira_400(self):
        self.api.force_authenticate(self.nina)
        self.api.post("/api/disponibilidades/", self.turno, format="json")
        r = self.api.post("/api/disponibilidades/", {**self.turno, "hora_inicio": "11:00", "hora_fim": "13:00"},
                          format="json")
        self.assertEqual(r.status_code, 400)

    def test_fim_antes_do_inicio_vira_400(self):
        self.api.force_authenticate(self.nina)
        r = self.api.post("/api/disponibilidades/", {**self.turno, "hora_inicio": "12:00", "hora_fim": "08:00"},
                          format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("hora_fim", r.data)

    def test_admin_cria_para_qualquer_um_mas_precisa_dizer_quem(self):
        self.api.force_authenticate(self.admin)
        r = self.api.post("/api/disponibilidades/", {**self.turno, "profissional": self.treinador.pk},
                          format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(self.api.post("/api/disponibilidades/", self.turno, format="json").status_code, 400)

    def test_filtra_por_profissional(self):
        for p in (self.nutricionista, self.treinador):
            Disponibilidade.objects.create(profissional=p, dia_da_semana=0, hora_inicio=time(8),
                                           hora_fim=time(12))
        self.api.force_authenticate(self.nina)
        r = self.api.get(f"/api/disponibilidades/?profissional={self.treinador.pk}")
        self.assertEqual(r.data["count"], 1)


class ApiDeBloqueio(Base):
    def setUp(self):
        super().setUp()
        self.api = APIClient()
        self.admin = User.objects.create_user("chefe", is_staff=True)
        self.pedido = {"profissional": self.nutricionista.pk, "inicio": hora(2, 9, 30).isoformat(),
                       "fim": hora(2, 10).isoformat(), "motivo": "Folga"}

    def test_so_o_admin_cria(self):
        self.api.force_authenticate(self.nutricionista.funcionario.usuario)
        self.assertEqual(self.api.post("/api/bloqueios/", self.pedido, format="json").status_code, 403)
        self.assertFalse(Bloqueio.objects.exists())

    def test_todos_consultam(self):
        Bloqueio.objects.create(profissional=self.nutricionista, inicio=hora(2, 9), fim=hora(2, 10), motivo="Folga")
        self.api.force_authenticate(self.joao.usuario)
        self.assertEqual(self.api.get("/api/bloqueios/").data["count"], 1)

    def test_admin_cria_sem_agendamento_no_caminho(self):
        self.api.force_authenticate(self.admin)
        r = self.api.post("/api/bloqueios/", self.pedido, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["agendamentos_afetados"], [])

    def test_alerta_quando_pega_agendamento_marcado(self):
        a = self.agendar()  # 9:00 às 9:50, dentro do bloqueio
        self.api.force_authenticate(self.admin)
        r = self.api.post("/api/bloqueios/", self.pedido, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("confirmar", r.data)
        self.assertIn(a.protocolo, str(r.data["confirmar"]))
        self.assertFalse(Bloqueio.objects.exists())

    def test_confirmando_grava_e_nao_mexe_no_agendamento(self):
        a = self.agendar()
        self.api.force_authenticate(self.admin)
        r = self.api.post("/api/bloqueios/", {**self.pedido, "confirmar": True}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["agendamentos_afetados"], [a.protocolo])
        a.refresh_from_db()
        self.assertEqual(a.status, Agendamento.Status.AGENDADO)

    def test_bloqueio_de_sala_tambem_alerta(self):
        self.agendar()
        self.api.force_authenticate(self.admin)
        r = self.api.post("/api/bloqueios/", {"espaco": self.consultorio.pk, "inicio": hora(2, 9).isoformat(),
                                              "fim": hora(2, 10).isoformat(), "motivo": "Manutenção"},
                          format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("confirmar", r.data)

    def test_exige_um_so_alvo(self):
        self.api.force_authenticate(self.admin)
        sem_alvo = {"inicio": hora(2, 9).isoformat(), "fim": hora(2, 10).isoformat(), "motivo": "Teste"}
        self.assertEqual(self.api.post("/api/bloqueios/", sem_alvo, format="json").status_code, 400)
        dois = {**sem_alvo, "profissional": self.nutricionista.pk, "espaco": self.consultorio.pk}
        self.assertEqual(self.api.post("/api/bloqueios/", dois, format="json").status_code, 400)
        self.assertFalse(Bloqueio.objects.exists())


class ValidacaoDeConflitosAgendamento(Base):
    def setUp(self):
        super().setUp()
        self.api = APIClient()
        self.api.force_authenticate(self.nutricionista.funcionario.usuario)
        self.consultorio2 = Espaco.objects.create(nome="Consultório 2")
        self.consultorio2.especialidades.add(self.nutri)
        self.bia = profissional("bia", "Bia", "M003", self.nutri)
        self.maria = atleta("maria", "Maria")
        self.dia = hora(2, 9).date()
        for profissional_atual in (self.nutricionista, self.bia):
            Disponibilidade.objects.create(profissional=profissional_atual, dia_da_semana=self.dia.weekday(),
                                           hora_inicio=time(8), hora_fim=time(12))

    def candidato(self, **alteracoes):
        dados = {"atleta": self.joao, "servico": self.consulta, "profissional": self.nutricionista,
                 "espaco": self.consultorio, "inicio": hora(2, 9)}
        dados.update(alteracoes)
        return Agendamento(**dados)

    def test_profissional_em_conflito_identifica_o_recurso(self):
        self.agendar()
        with self.assertRaises(ValidationError) as erro:
            self.candidato(atleta=self.maria, espaco=self.consultorio2).full_clean()
        self.assertIn("profissional", erro.exception.message_dict)

        resposta = self.api.post("/api/agendamentos/", {
            "atleta": self.maria.pk, "servico": self.consulta.pk, "profissional": self.nutricionista.pk,
            "espaco": self.consultorio2.pk, "inicio": hora(2, 9).isoformat(),
        }, format="json")
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("profissional", resposta.data)

    def test_atleta_em_conflito_identifica_o_recurso(self):
        self.agendar()
        with self.assertRaises(ValidationError) as erro:
            self.candidato(profissional=self.bia, espaco=self.consultorio2).full_clean()
        self.assertIn("atleta", erro.exception.message_dict)

    def test_capacidade_da_sala_e_respeitada(self):
        self.consultorio.capacidade = 2
        self.consultorio.save()
        self.agendar()
        Agendamento.objects.create(atleta=self.maria, servico=self.consulta, profissional=self.bia,
                                   espaco=self.consultorio, inicio=hora(2, 9))
        carlos_profissional = profissional("carlos-prof", "Carlos Profissional", "M004", self.nutri)
        Disponibilidade.objects.create(profissional=carlos_profissional, dia_da_semana=self.dia.weekday(),
                                       hora_inicio=time(8), hora_fim=time(12))
        with self.assertRaises(ValidationError) as erro:
            self.candidato(atleta=atleta("carlos", "Carlos"), profissional=carlos_profissional).full_clean()
        self.assertIn("espaco", erro.exception.message_dict)

    def test_indisponibilidade_do_profissional_e_bloqueios_identificam_o_recurso(self):
        with self.assertRaises(ValidationError) as erro:
            self.candidato(inicio=hora(2, 13)).full_clean()
        self.assertIn("profissional", erro.exception.message_dict)

        Bloqueio.objects.create(profissional=self.nutricionista, inicio=hora(2, 9), fim=hora(2, 10),
                                motivo="Folga")
        with self.assertRaises(ValidationError) as erro:
            self.candidato().full_clean()
        self.assertIn("profissional", erro.exception.message_dict)

    def test_bloqueio_de_sala_equipamento_e_respeitado(self):
        Bloqueio.objects.create(espaco=self.consultorio, inicio=hora(2, 9), fim=hora(2, 10), motivo="Manutenção")
        with self.assertRaises(ValidationError) as erro:
            self.candidato().full_clean()
        self.assertIn("espaco", erro.exception.message_dict)

        equipamento = Equipamento.objects.create(nome="Esteira bloqueada", quantidade=1)
        agendamento = self.agendar(hora(2, 11))
        Bloqueio.objects.create(equipamento=equipamento, inicio=hora(2, 11), fim=hora(2, 12), motivo="Manutenção")
        with self.assertRaises(ValidationError) as erro:
            agendamento.reservar_equipamentos([equipamento])
        self.assertIn("equipamentos", erro.exception.message_dict)

    def test_horarios_livres_retorna_intervalos_de_30_minutos(self):
        resposta = self.api.get(f"/api/horarios-livres/?servico={self.consulta.pk}&dia={self.dia.isoformat()}")
        self.assertEqual(resposta.status_code, 200, resposta.data)
        inicios = [datetime.fromisoformat(opcao["inicio"]) for opcao in resposta.data["results"]
               if opcao["profissional"] == self.nutricionista.pk]
        self.assertEqual(len(inicios), 7)
        self.assertEqual([(b - a).total_seconds() // 60 for a, b in zip(inicios, inicios[1:])], [30] * 6)
        self.assertEqual(inicios[0].time().replace(tzinfo=None), time(8))
        self.assertEqual(inicios[-1].time().replace(tzinfo=None), time(11))