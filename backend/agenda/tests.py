from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase

from estrutura.models import Espaco, Especialidade, Servico,Equipamento
from pkzlab.testes_comuns import hora, profissional,atleta

from .models import Agendamento,Aviso,Disponibilidade


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
        self.joao = atleta("joao", "João")


    def agendar(self, inicio=None, **kw):
        dados = dict(atleta=self.joao, servico=self.consulta, profissional=self.nutricionista, espaco=self.consultorio,
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
        Disponibilidade.objects.create(profissional=self.nutricionista, dia_da_semana=hora(2, 9).weekday(),
                                       hora_inicio=hora(2, 8).time(), hora_fim=hora(2, 12).time())
        novo = original.reagendar(hora(2, 10))
        original.refresh_from_db()
        self.assertEqual(original.status, Agendamento.Status.SUBSTITUIDO)
        self.assertEqual(novo.status, Agendamento.Status.AGENDADO)
        self.assertEqual(novo.substitui, original)
        self.assertEqual(original.substituido_por, novo)
        self.assertEqual(novo.fim - novo.inicio, timedelta(minutes=50))

    def test_reagendar_em_conflito_preserva_o_agendamento_original(self):
        Disponibilidade.objects.create(profissional=self.nutricionista, dia_da_semana=hora(2, 9).weekday(),
                                       hora_inicio=hora(2, 8).time(), hora_fim=hora(2, 12).time())
        original = self.agendar()
        outro_atleta = atleta("maria-reagendamento", "Maria")
        self.agendar(hora(2, 11), atleta=outro_atleta)
        with self.assertRaises(ValidationError):
            original.reagendar(hora(2, 11))
        original.refresh_from_db()
        self.assertEqual(original.status, Agendamento.Status.AGENDADO)
        self.assertEqual(Agendamento.objects.count(), 2)


class ApiDeAgendamento(Base):
    def setUp(self):
        super().setUp()
        from rest_framework.test import APIClient
        self.api = APIClient()
        self.api.force_authenticate(self.nutricionista.funcionario.usuario)
        for profissional in (self.nutricionista, self.treinador):
            Disponibilidade.objects.create(profissional=profissional, dia_da_semana=hora(2, 9).weekday(),
                                           hora_inicio=hora(2, 8).time(), hora_fim=hora(2, 12).time())

    def test_sem_login_nao_ve_nada(self):
        from rest_framework.test import APIClient
        self.assertEqual(APIClient().get("/api/agendamentos/").status_code, 401)

    def test_cria_pela_api(self):
        r = self.api.post("/api/agendamentos/", {"atleta": self.joao.pk, "servico": self.consulta.pk,
                                                 "profissional": self.nutricionista.pk,
                                                 "espaco": self.consultorio.pk, "inicio": hora(2, 9).isoformat()})
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["status"], "AGENDADO")
        self.assertEqual(len(r.data["protocolo"]), 10)

    def test_regra_do_model_vira_erro_400(self):
        r = self.api.post("/api/agendamentos/", {"atleta": self.joao.pk, "servico": self.consulta.pk,
                                                 "profissional": self.treinador.pk,
                                                 "espaco": self.consultorio.pk, "inicio": hora(2, 9).isoformat()}) 
        self.assertEqual(r.status_code, 400)
        self.assertIn("profissional", r.data)

    def test_cancelar_e_reagendar(self):
        a, b = self.agendar(), self.agendar(hora(2, 11))
        self.assertEqual(self.api.post(f"/api/agendamentos/{a.pk}/cancelar/", {"justificativa": ""}).status_code, 400)
        r = self.api.post(f"/api/agendamentos/{a.pk}/cancelar/", {"justificativa": "Atleta doente"})
        self.assertEqual(r.data["status"], "CANCELADO")
        self.assertEqual(self.api.post(f"/api/agendamentos/{a.pk}/cancelar/", {"justificativa": "De novo"}).status_code, 400)
        r = self.api.post(f"/api/agendamentos/{b.pk}/reagendar/", {"inicio": hora(2, 10).isoformat()})
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
        for profissional_atual in (self.nutricionista, self.bia):
            Disponibilidade.objects.create(profissional=profissional_atual, dia_da_semana=hora(2, 9).weekday(),
                                           hora_inicio=hora(2, 8).time(), hora_fim=hora(2, 12).time())

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
        novo = a.reagendar(hora(2, 10))
        self.assertEqual(list(novo.equipamentos.all()), [self.bioimpedancia])

    def test_pela_api(self):
        from rest_framework.test import APIClient
        api = APIClient()
        api.force_authenticate(self.nutricionista.funcionario.usuario)
        dados = {"atleta": self.joao.pk, "servico": self.consulta.pk, "profissional": self.nutricionista.pk, "espaco": self.consultorio.pk,
                 "inicio": hora(2, 9).isoformat(), "equipamentos": [self.bioimpedancia.pk]}
        r = api.post("/api/agendamentos/", dados, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["equipamentos"], [self.bioimpedancia.pk])
        outro_atleta = atleta("maria-equipamento", "Maria")
        dados.update(atleta=outro_atleta.pk, profissional=self.bia.pk, espaco=self.consultorio2.pk)
        r = api.post("/api/agendamentos/", dados, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("equipamentos", r.data)
        self.assertEqual(Agendamento.objects.count(), 1) 
class Avisos(Base):
    def setUp(self):
        super().setUp()
        from rest_framework.test import APIClient
        self.api = APIClient()
        self.nina = self.nutricionista.funcionario.usuario
        self.teo = self.treinador.funcionario.usuario

    def test_cancelar_avisa_o_profissional(self):
        a = self.agendar()
        a.cancelar("Atleta doente")
        aviso = Aviso.objects.get(usuario=self.nina)
        self.assertIn(a.protocolo, aviso.texto)
        self.assertIn("Atleta doente", aviso.texto)
        self.assertFalse(aviso.lido)

    def test_cada_um_ve_so_os_seus(self):
        Aviso.avisar(self.nina, "Para a Nina")
        Aviso.avisar(self.teo, "Para o Teo")
        self.api.force_authenticate(self.nina)
        textos = [a["texto"] for a in self.api.get("/api/avisos/").data["results"]]
        self.assertEqual(textos, ["Para a Nina"])

    def test_marca_como_lido_e_filtra(self):
        aviso = Aviso.avisar(self.nina, "Teste")
        self.api.force_authenticate(self.nina)
        self.assertEqual(self.api.get("/api/avisos/?lido=false").data["count"], 1)
        r = self.api.post(f"/api/avisos/{aviso.pk}/lido/")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data["lido"])
        self.assertEqual(self.api.get("/api/avisos/?lido=false").data["count"], 0)

    def test_nao_mexe_no_aviso_de_outro(self):
        aviso = Aviso.avisar(self.teo, "Para o Teo")
        self.api.force_authenticate(self.nina)
        self.assertEqual(self.api.post(f"/api/avisos/{aviso.pk}/lido/").status_code, 404)
        aviso.refresh_from_db()
        self.assertFalse(aviso.lido)

    def test_api_nao_cria_nem_apaga_aviso(self):
        aviso = Aviso.avisar(self.nina, "Teste")
        self.api.force_authenticate(self.nina)
        self.assertEqual(self.api.post("/api/avisos/", {"texto": "falso"}).status_code, 405)
        self.assertEqual(self.api.delete(f"/api/avisos/{aviso.pk}/").status_code, 405)

    def test_sem_login_nada(self):
        self.assertEqual(self.api.get("/api/avisos/").status_code, 401) 
class AtletaNoAgendamento(Base):
    def setUp(self):
        super().setUp()
        from datetime import date
        from rest_framework.test import APIClient
        from pessoas.cadastros import cadastrar_responsavel
        self.api = APIClient()
        self.maria = atleta("maria", "Maria")
        self.mae = cadastrar_responsavel(email="mae@x.com", nome="Mãe", senha="senha12345", aceitou_termos=True)
        self.pedro = atleta("pedro", "Pedro", nascimento=date(2014, 3, 10), responsavel=self.mae)
        self.consultorio2 = Espaco.objects.create(nome="Consultório 2")
        self.consultorio2.especialidades.add(self.nutri)
        self.bia = profissional("bia", "Bia", "M003", self.nutri)
        Disponibilidade.objects.create(profissional=self.nutricionista, dia_da_semana=hora(2, 9).weekday(),
                           hora_inicio=hora(2, 8).time(), hora_fim=hora(2, 12).time())

    def pedido(self, atleta_alvo, **kw):
        dados = {"atleta": atleta_alvo.pk, "servico": self.consulta.pk, "profissional": self.nutricionista.pk,
                 "espaco": self.consultorio.pk, "inicio": hora(2, 9).isoformat()}
        dados.update(kw)
        return self.api.post("/api/agendamentos/", dados, format="json")

    def protocolos(self, usuario):
        self.api.force_authenticate(usuario)
        return {a["protocolo"] for a in self.api.get("/api/agendamentos/").data["results"]}

    def test_atleta_e_obrigatorio(self):
        self.api.force_authenticate(self.nutricionista.funcionario.usuario)
        r = self.api.post("/api/agendamentos/", {"servico": self.consulta.pk, "profissional": self.nutricionista.pk,
                                                 "espaco": self.consultorio.pk, "inicio": hora(2, 9).isoformat()})
        self.assertEqual(r.status_code, 400)
        self.assertIn("atleta", r.data)

    def test_atleta_marca_para_ele_mesmo(self):
        self.api.force_authenticate(self.joao.usuario)
        self.assertEqual(self.pedido(self.joao).status_code, 201)

    def test_atleta_nao_marca_para_outro(self):
        self.api.force_authenticate(self.joao.usuario)
        r = self.pedido(self.maria)
        self.assertEqual(r.status_code, 400)
        self.assertIn("atleta", r.data)
        self.assertFalse(Agendamento.objects.exists())

    def test_responsavel_marca_para_o_dependente_e_nao_para_outro(self):
        self.api.force_authenticate(self.mae.usuario)
        self.assertEqual(self.pedido(self.pedro).status_code, 201)
        self.assertEqual(self.pedido(self.maria, inicio=hora(2, 11).isoformat()).status_code, 400)

    def test_cada_um_ve_so_a_sua_parte_da_agenda(self):
        do_joao = self.agendar()
        da_maria = self.agendar(hora(2, 10), atleta=self.maria, profissional=self.bia, espaco=self.consultorio2)
        do_pedro = self.agendar(hora(2, 11), atleta=self.pedro)
        self.assertEqual(self.protocolos(self.joao.usuario), {do_joao.protocolo})
        self.assertEqual(self.protocolos(self.mae.usuario), {do_pedro.protocolo})
        self.assertEqual(self.protocolos(self.nutricionista.funcionario.usuario), {do_joao.protocolo, do_pedro.protocolo})
        self.assertEqual(self.protocolos(self.bia.funcionario.usuario), {da_maria.protocolo})

    def test_recepcao_ve_a_agenda_toda(self):
        from pessoas.models import Recepcao
        from pkzlab.testes_comuns import funcionario
        carla = funcionario("carla", "Carla", "F002")
        Recepcao.objects.create(funcionario=carla)
        self.agendar()
        self.agendar(hora(2, 10), atleta=self.maria, profissional=self.bia, espaco=self.consultorio2)
        self.assertEqual(len(self.protocolos(carla.usuario)), 2)

    def test_atleta_nao_cancela_o_de_outro(self):
        da_maria = self.agendar(atleta=self.maria)
        self.api.force_authenticate(self.joao.usuario)
        r = self.api.post(f"/api/agendamentos/{da_maria.pk}/cancelar/", {"justificativa": "Teste"})
        self.assertEqual(r.status_code, 404)

    def test_reagendar_mantem_o_atleta(self):
        novo = self.agendar(atleta=self.maria).reagendar(hora(2, 10))
        self.assertEqual(novo.atleta, self.maria)                    # o segundo não ficou gravado pela metade    
