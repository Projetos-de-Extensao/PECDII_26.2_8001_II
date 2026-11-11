"""A migração 0010 transforma as inscrições confirmadas em agendamentos antes de apagar a tabela,
para um banco que já está no ar (servidor) não perder os alunos das aulas."""
from datetime import date, time, timedelta

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

ANTES = [("agenda", "0009_lista_de_espera"), ("pessoas", "0005_grupos_de_papeis"), ("estrutura", "0003_equipamento")]
DEPOIS = [("agenda", "0010_remove_inscricao")]


class MigracaoDaInscricao(TransactionTestCase):
    def migrar(self, alvo):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(alvo)
        return executor.loader.project_state(alvo).apps

    def tearDown(self):
        # devolve o banco de teste ao estado atual, para os outros testes
        self.migrar(MigrationExecutor(connection).loader.graph.leaf_nodes())

    def test_inscricao_confirmada_vira_agendamento(self):
        apps = self.migrar(ANTES)
        User = apps.get_model("auth", "User")
        Especialidade = apps.get_model("estrutura", "Especialidade")
        Espaco = apps.get_model("estrutura", "Espaco")
        Servico = apps.get_model("estrutura", "Servico")
        Funcionario = apps.get_model("pessoas", "Funcionario")
        Profissional = apps.get_model("pessoas", "Profissional")
        Atleta = apps.get_model("pessoas", "Atleta")
        Aula = apps.get_model("agenda", "Aula")
        Inscricao = apps.get_model("agenda", "Inscricao")

        nutri = Especialidade.objects.get_or_create(nome="Nutricionista")[0]
        sala = Espaco.objects.create(nome="Studio")
        pilates = Servico.objects.create(nome="Pilates", especialidade=nutri, duracao_minutos=50, vagas=8)
        prof = Profissional.objects.create(funcionario=Funcionario.objects.create(
            usuario=User.objects.create(username="lia"), matricula="M1", data_admissao=date(2025, 1, 1)))
        aula = Aula.objects.create(servico=pilates, profissional=prof, espaco=sala, dia=date(2030, 3, 4),
                                   hora_inicio=time(15), hora_fim=time(15, 50))
        atletas = [Atleta.objects.create(usuario=User.objects.create(username=n), data_nascimento=date(2000, 1, 1))
                   for n in ("joao", "maria", "pedro")]
        Inscricao.objects.create(aula=aula, atleta=atletas[0])
        Inscricao.objects.create(aula=aula, atleta=atletas[1])
        Inscricao.objects.create(aula=aula, atleta=atletas[2], status="CANCELADA")

        apps = self.migrar(DEPOIS)
        Agendamento = apps.get_model("agenda", "Agendamento")
        alunos = Agendamento.objects.filter(aula_id=aula.pk, status="AGENDADO")
        self.assertEqual(sorted(a.atleta.usuario.username for a in alunos), ["joao", "maria"])  # a cancelada não
        primeiro = alunos.first()
        self.assertEqual((primeiro.espaco_id, primeiro.profissional_id, primeiro.servico_id), (sala.pk, prof.pk, pilates.pk))
        self.assertEqual(primeiro.fim - primeiro.inicio, timedelta(minutes=50))
        self.assertEqual(len({a.protocolo for a in alunos}), 2)
