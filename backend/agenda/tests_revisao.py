"""Segunda revisão: o que apareceu rodando o sistema de ponta a ponta depois do PR #64."""
from datetime import timedelta

from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from estrutura.models import Espaco
from pkzlab.testes_comuns import atleta, hora, profissional

from .models import Agendamento, Aviso, Bloqueio, ListaEspera
from .tests_grade_de_aulas import ComGrade


class ListaDeEsperaCoerente(ComGrade):
    # a fila não pode dizer "horário livre, agende direto" quando o agendamento direto é recusado

    def mensagens(self, espera):
        with self.assertRaises(ValidationError) as erro:
            espera.clean()
        return erro.exception.message_dict

    def test_horario_da_aula_do_profissional_nao_e_livre(self):
        self.aula(10)  # a Nina dá pilates às 10h, mesmo sem aluno
        erros = self.mensagens(ListaEspera(atleta=self.joao, servico=self.consulta, profissional=self.nutricionista,
                                           inicio=hora(2, 10)))
        self.assertIn("profissional", erros)
        self.assertNotIn("Esse horário está livre: dá para agendar direto.", erros.get("inicio", []))

    def test_servico_em_grupo_sem_aula(self):
        erros = self.mensagens(ListaEspera(atleta=self.joao, servico=self.pilates, profissional=self.nutricionista,
                                           inicio=hora(2, 10)))
        self.assertIn("aula", erros)
        self.assertNotIn("inicio", erros)

    def test_aula_desativada_nao_tem_fila(self):
        aula = self.aula(10)
        self.aluno(aula, atleta("maria", "Maria"))
        self.aluno(aula, atleta("ana", "Ana"))  # lotada (2 vagas)
        aula.ativo = False
        aula.save()
        erros = self.mensagens(ListaEspera(atleta=self.joao, aula=aula))
        self.assertIn("Esta aula foi desativada.", erros["aula"])

    def test_aula_lotada_e_ativa_continua_aceitando_fila(self):
        aula = self.aula(10)
        self.aluno(aula, atleta("maria", "Maria"))
        self.aluno(aula, atleta("ana", "Ana"))
        ListaEspera(atleta=self.joao, aula=aula).clean()  # não levanta erro


class ServicoInativo(ComGrade):
    # UC18: serviço inativo não recebe agendamento novo nem aula nova; o que já estava marcado continua

    def test_nao_aceita_agendamento_novo(self):
        self.consulta.ativo = False
        self.consulta.save()
        with self.assertRaises(ValidationError) as erro:
            Agendamento(atleta=self.joao, servico=self.consulta, profissional=self.nutricionista,
                        espaco=self.consultorio, inicio=hora(2, 9)).clean()
        self.assertIn("servico", erro.exception.message_dict)

    def test_nao_cria_aula(self):
        self.pilates.ativo = False
        self.pilates.save()
        r = self.criar_aula(hora(2, 10))
        self.assertEqual(r.status_code, 400)
        self.assertIn("servico", r.data)

    def test_inativar_alerta_e_so_inativa_confirmando(self):
        marcado = self.agendar(hora(2, 9))
        r = self.api.patch(f"/api/servicos/{self.consulta.pk}/", {"ativo": False}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn(marcado.protocolo, str(r.data["confirmar"]))
        self.consulta.refresh_from_db()
        self.assertTrue(self.consulta.ativo)
        r = self.api.patch(f"/api/servicos/{self.consulta.pk}/", {"ativo": False, "confirmar": True}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        marcado.refresh_from_db()
        self.assertEqual(marcado.status, Agendamento.Status.AGENDADO)  # UC18 A1: mantém o que estava marcado

    def test_inativar_alerta_quando_tem_aula_na_grade(self):
        self.aula(10)
        r = self.api.patch(f"/api/servicos/{self.pilates.pk}/", {"ativo": False}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("1 aula(s) na grade", str(r.data["confirmar"]))
        self.assertNotIn("0 agendamento", str(r.data["confirmar"]))

    def test_inativar_sem_agenda_futura_nao_pergunta(self):
        r = self.api.patch(f"/api/servicos/{self.consulta.pk}/", {"ativo": False}, format="json")
        self.assertEqual(r.status_code, 200, r.data)


class ReagendarAlunoDeAula(ComGrade):
    def test_mensagem_clara_e_o_original_fica(self):
        aula = self.aula(10)
        joao = self.aluno(aula, self.joao)
        api = APIClient()
        api.force_authenticate(self.joao.usuario)
        r = api.post(f"/api/agendamentos/{joao.pk}/reagendar/", {"inicio": hora(3, 10).isoformat()}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("cancele", str(r.data))
        joao.refresh_from_db()
        self.assertEqual(joao.status, Agendamento.Status.AGENDADO)


class AulaSuspensa(ComGrade):
    # UC21 A2: com o professor ou a sala bloqueados, naquele dia a aula aparece como suspensa

    def ver(self, aula):
        return self.api.get(f"/api/aulas/{aula.pk}/").data["suspensa"]

    def test_bloqueio_do_professor_suspende(self):
        aula = self.aula(10)
        self.assertFalse(self.ver(aula))
        Bloqueio.objects.create(profissional=self.nutricionista, inicio=hora(2, 8), fim=hora(2, 12), motivo="Médico")
        self.assertTrue(self.ver(aula))

    def test_bloqueio_da_sala_suspende(self):
        aula = self.aula(10)
        Bloqueio.objects.create(espaco=self.consultorio, inicio=hora(2, 10, 30), fim=hora(2, 11), motivo="Vazamento")
        self.assertTrue(self.ver(aula))

    def test_bloqueio_em_outro_horario_nao_suspende(self):
        aula = self.aula(10)
        Bloqueio.objects.create(profissional=self.nutricionista, inicio=hora(2, 11), fim=hora(2, 12), motivo="Reunião")
        self.assertFalse(self.ver(aula))

    def test_alunos_sao_avisados_e_nao_recebem_lembrete_de_venha(self):
        aula = self.aula(10)
        joao = self.aluno(aula, self.joao)
        Bloqueio.objects.create(profissional=self.nutricionista, inicio=hora(2, 8), fim=hora(2, 12), motivo="Médico")
        self.assertTrue(Aviso.objects.filter(usuario=self.joao.usuario, texto__contains="suspensa").exists())
        joao.refresh_from_db()
        self.assertIsNotNone(joao.lembrete_enviado_em)
        self.assertNotIn(joao, Agendamento.precisam_de_lembrete(agora=hora(2, 10) - timedelta(hours=3)))

    def test_na_hora_do_lembrete_aula_suspensa_vira_aviso_de_suspensao(self):
        aula = self.aula(10)
        joao = self.aluno(aula, self.joao)
        Bloqueio.objects.create(profissional=self.nutricionista, inicio=hora(2, 8), fim=hora(2, 12), motivo="Médico")
        Aviso.objects.all().delete()
        Agendamento.objects.filter(pk=joao.pk).update(lembrete_enviado_em=None)
        Agendamento.enviar_lembretes(agora=hora(2, 10) - timedelta(hours=3))
        textos = list(Aviso.objects.filter(usuario=self.joao.usuario).values_list("texto", flat=True))
        self.assertTrue(textos and all("suspensa" in t for t in textos), textos)

    def test_aula_desativada_nao_recebe_lembrete(self):
        aula = self.aula(10)
        joao = self.aluno(aula, self.joao)
        individual = self.agendar(hora(2, 9))
        aula.ativo = False
        aula.save()
        pendentes = list(Agendamento.precisam_de_lembrete(agora=hora(2, 9) - timedelta(hours=3)))
        self.assertNotIn(joao, pendentes)
        self.assertIn(individual, pendentes)  # o individual continua recebendo


class FiltrosDaAgenda(ComGrade):
    # UC10 passo 2: período e, para a administração, profissional e sala

    def setUp(self):
        super().setUp()
        self.segunda = self.agendar(hora(2, 9))
        self.terca = self.agendar(hora(3, 9))
        sala2 = Espaco.objects.create(nome="Consultório 2")
        sala2.especialidades.add(self.nutri)
        self.outra = profissional("lu", "Lu", "M010", self.nutri)
        self.na_sala2 = self.agendar(hora(2, 11), profissional=self.outra, espaco=sala2, atleta=atleta("bia", "Bia"))
        self.sala2 = sala2

    def ids(self, filtro):
        r = self.api.get(f"/api/agendamentos/?{filtro}")
        self.assertEqual(r.status_code, 200, r.data)
        return {a["id"] for a in r.data["results"]}

    def test_periodo(self):
        dia = hora(2, 9).date().isoformat()
        self.assertEqual(self.ids(f"de={dia}&ate={dia}"), {self.segunda.pk, self.na_sala2.pk})
        self.assertEqual(self.ids(f"de={hora(3, 9).date().isoformat()}"), {self.terca.pk})

    def test_profissional_e_sala(self):
        self.assertEqual(self.ids(f"profissional={self.outra.pk}"), {self.na_sala2.pk})
        self.assertEqual(self.ids(f"espaco={self.sala2.pk}"), {self.na_sala2.pk})

    def test_filtro_invalido_da_400(self):
        self.assertEqual(self.api.get("/api/agendamentos/?de=ontem").status_code, 400)
        r = self.api.get(f"/api/agendamentos/?de={hora(3, 9).date()}&ate={hora(2, 9).date()}")
        self.assertEqual(r.status_code, 400)

    def test_atleta_filtra_so_dentro_do_que_e_dele(self):
        api = APIClient()
        api.force_authenticate(self.joao.usuario)
        r = api.get(f"/api/agendamentos/?profissional={self.outra.pk}")
        self.assertEqual(r.data["count"], 0)
