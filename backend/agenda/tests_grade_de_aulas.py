"""Grade de aulas (UC21) e o que depende dela: conferências da aula, aula ocupando professor e sala,
mudança de horário levando os alunos e apagar registro em uso."""
from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APIClient

from estrutura.models import Espaco, Servico
from pkzlab.testes_comuns import atleta, hora, profissional, usuario_com_papel

from .models import Agendamento, Aula, Aviso, Bloqueio, Disponibilidade
from .tests import Base


class ComGrade(Base):
    # professora Nina atende segunda das 8h às 12h; pilates é em grupo (2 vagas) no consultório
    def setUp(self):
        super().setUp()
        Disponibilidade.objects.create(profissional=self.nutricionista, dia_da_semana=hora(2, 9).weekday(),
                                       hora_inicio=hora(2, 8).time(), hora_fim=hora(2, 12).time())
        self.pilates = Servico.objects.create(nome="Pilates", especialidade=self.nutri, duracao_minutos=50, vagas=2)
        self.pilates.espacos.add(self.consultorio)
        self.api = APIClient()
        self.api.force_authenticate(usuario_com_papel("adm", "administrador"))

    def criar_aula(self, inicio, **kw):
        dados = {"servico": self.pilates.pk, "profissional": self.nutricionista.pk, "espaco": self.consultorio.pk,
                 "dia": inicio.date().isoformat(), "hora_inicio": inicio.strftime("%H:%M")}
        dados.update(kw)
        return self.api.post("/api/aulas/", dados, format="json")

    def aula(self, h=10):
        return Aula.objects.create(servico=self.pilates, profissional=self.nutricionista, espaco=self.consultorio,
                                   dia=hora(2, h).date(), hora_inicio=hora(2, h).time())

    def aluno(self, aula, quem):
        agendamento = Agendamento(atleta=quem, servico=aula.servico, profissional=aula.profissional,
                                  espaco=aula.espaco, aula=aula, inicio=aula.inicio)
        agendamento.clean()
        agendamento.save()
        return agendamento


class CadastrarAula(ComGrade):
    def test_aula_dentro_do_turno_e_aceita(self):
        r = self.criar_aula(hora(2, 10))
        self.assertEqual(r.status_code, 201, r.data)

    def test_fora_da_disponibilidade_do_professor(self):
        r = self.criar_aula(hora(2, 18))
        self.assertEqual(r.status_code, 400)
        self.assertIn("profissional", r.data)

    def test_professor_bloqueado(self):
        Bloqueio.objects.create(profissional=self.nutricionista, inicio=hora(2, 8), fim=hora(2, 12), motivo="Folga")
        r = self.criar_aula(hora(2, 10))
        self.assertEqual(r.status_code, 400)
        self.assertIn("profissional", r.data)

    def test_sala_bloqueada(self):
        Bloqueio.objects.create(espaco=self.consultorio, inicio=hora(2, 8), fim=hora(2, 12), motivo="Reforma")
        r = self.criar_aula(hora(2, 10))
        self.assertEqual(r.status_code, 400)
        self.assertIn("espaco", r.data)

    def test_no_passado(self):
        r = self.criar_aula(timezone.localtime() - timedelta(days=3))
        self.assertEqual(r.status_code, 400)
        self.assertIn("hora_inicio", r.data)

    def test_servico_individual_nao_vira_aula(self):
        r = self.criar_aula(hora(2, 10), servico=self.consulta.pk)
        self.assertEqual(r.status_code, 400)
        self.assertIn("servico", r.data)

    def test_professor_nao_da_duas_aulas_ao_mesmo_tempo(self):
        self.assertEqual(self.criar_aula(hora(2, 10)).status_code, 201)
        outra_sala = Espaco.objects.create(nome="Sala 2", capacidade=1)
        outra_sala.especialidades.add(self.nutri)
        self.pilates.espacos.add(outra_sala)
        r = self.criar_aula(hora(2, 10, 30), espaco=outra_sala.pk)
        self.assertEqual(r.status_code, 400)
        self.assertIn("profissional", r.data)

    def test_sala_respeita_a_capacidade(self):
        lia = profissional("lia", "Lia", "M009", self.nutri)
        Disponibilidade.objects.create(profissional=lia, dia_da_semana=hora(2, 9).weekday(),
                                       hora_inicio=hora(2, 8).time(), hora_fim=hora(2, 12).time())
        self.assertEqual(self.criar_aula(hora(2, 10)).status_code, 201)
        r = self.criar_aula(hora(2, 10), profissional=lia.pk)  # consultório tem capacidade 1
        self.assertEqual(r.status_code, 400)
        self.assertIn("espaco", r.data)
        self.consultorio.capacidade = 2
        self.consultorio.save()
        self.assertEqual(self.criar_aula(hora(2, 10), profissional=lia.pk).status_code, 201)

    def test_professor_com_consulta_marcada(self):
        self.agendar(hora(2, 10))
        r = self.criar_aula(hora(2, 10))
        self.assertEqual(r.status_code, 400)
        self.assertIn("profissional", r.data)

    def test_desativar_nao_confere_a_agenda_de_novo(self):
        aula = self.aula()
        Bloqueio.objects.create(profissional=self.nutricionista, inicio=hora(2, 8), fim=hora(2, 12), motivo="Folga")
        r = self.api.patch(f"/api/aulas/{aula.pk}/", {"ativo": False}, format="json")
        self.assertEqual(r.status_code, 200, r.data)


class AulaOcupaAAgenda(ComGrade):
    def test_consulta_individual_por_cima_de_aula_vazia(self):
        self.aula(10)
        with self.assertRaises(ValidationError) as erro:
            Agendamento(atleta=self.joao, servico=self.consulta, profissional=self.nutricionista,
                        espaco=self.consultorio, inicio=hora(2, 10)).clean()
        self.assertIn("profissional", erro.exception.message_dict)

    def test_horarios_livres_pula_a_aula(self):
        self.aula(10)
        api = APIClient()
        api.force_authenticate(self.joao.usuario)
        r = api.get("/api/horarios-livres/", {"servico": self.consulta.pk, "dia": hora(2, 9).date().isoformat()})
        self.assertEqual(r.status_code, 200)
        inicios = [timezone.localtime(datetime.fromisoformat(o["inicio"])).time() for o in r.data["results"]]
        self.assertIn(hora(2, 9).time(), inicios)
        self.assertNotIn(hora(2, 10).time(), inicios)

    def test_servico_em_grupo_so_entra_pela_aula(self):
        api = APIClient()
        api.force_authenticate(self.joao.usuario)
        r = api.post("/api/agendamentos/", {"atleta": self.joao.pk, "servico": self.pilates.pk,
                                            "profissional": self.nutricionista.pk, "espaco": self.consultorio.pk,
                                            "inicio": hora(2, 10).isoformat()}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("aula", r.data)


class MudarHorarioDaAula(ComGrade):
    def test_os_alunos_vao_junto_e_sao_avisados(self):
        aula = self.aula(10)
        joao = self.aluno(aula, self.joao)
        r = self.api.patch(f"/api/aulas/{aula.pk}/", {"hora_inicio": "11:00"}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        joao.refresh_from_db()
        self.assertEqual((joao.inicio, joao.fim), (hora(2, 11), hora(2, 11, 50)))
        self.assertIsNone(joao.lembrete_enviado_em)
        self.assertTrue(Aviso.objects.filter(usuario=self.joao.usuario, texto__contains="mudou").exists())

    def test_recusa_se_um_aluno_tem_outro_compromisso_no_horario_novo(self):
        aula = self.aula(10)
        joao = self.aluno(aula, self.joao)
        lia = profissional("lia", "Lia", "M009", self.nutri)
        sala2 = Espaco.objects.create(nome="Sala 2")
        sala2.especialidades.add(self.nutri)
        Agendamento.objects.create(atleta=self.joao, servico=self.consulta, profissional=lia, espaco=sala2,
                                   inicio=hora(2, 11))
        r = self.api.patch(f"/api/aulas/{aula.pk}/", {"hora_inicio": "11:00"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("hora_inicio", r.data)
        joao.refresh_from_db()
        self.assertEqual(joao.inicio, hora(2, 10))

    def test_nao_troca_o_servico_de_aula_com_alunos(self):
        aula = self.aula(10)
        self.aluno(aula, self.joao)
        yoga = Servico.objects.create(nome="Yoga", especialidade=self.nutri, duracao_minutos=50, vagas=5)
        r = self.api.patch(f"/api/aulas/{aula.pk}/", {"servico": yoga.pk}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("servico", r.data)


class ApagarRegistroEmUso(ComGrade):
    def test_sala_em_uso(self):
        self.agendar(hora(2, 9))
        r = self.api.delete(f"/api/espacos/{self.consultorio.pk}/")
        self.assertEqual(r.status_code, 400)
        self.assertIn("Não dá para apagar", r.data["detail"])
        self.assertTrue(Espaco.objects.filter(pk=self.consultorio.pk).exists())

    def test_servico_em_uso(self):
        self.agendar(hora(2, 9))
        r = self.api.delete(f"/api/servicos/{self.consulta.pk}/")
        self.assertEqual(r.status_code, 400)
        self.assertIn("Desative", r.data["detail"])

    def test_aula_com_aluno(self):
        aula = self.aula(10)
        self.aluno(aula, atleta("maria", "Maria"))
        r = self.api.delete(f"/api/aulas/{aula.pk}/")
        self.assertEqual(r.status_code, 400)
        self.assertTrue(Aula.objects.filter(pk=aula.pk).exists())

    def test_aula_vazia_pode_apagar(self):
        aula = self.aula(10)
        self.assertEqual(self.api.delete(f"/api/aulas/{aula.pk}/").status_code, 204)
