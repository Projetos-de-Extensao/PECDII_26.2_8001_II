from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from pkzlab.testes_comuns import hora

from .models import Configuracao, Espaco, Especialidade, Servico


class SalasPorEspecialidade(TestCase):
    def setUp(self):
        self.nutri = Especialidade.objects.get(nome="Nutricionista")
        self.pilates = Especialidade.objects.create(nome="Instrutor de Pilates")
        self.c1 = Espaco.objects.create(nome="Consultório 1")
        self.c2 = Espaco.objects.create(nome="Consultório 2")
        self.studio = Espaco.objects.create(nome="Studio 1")
        for c in (self.c1, self.c2):
            c.especialidades.add(self.nutri)
        self.studio.especialidades.add(self.pilates)

    def test_servico_usa_as_salas_da_especialidade(self):
        consulta = Servico.objects.create(nome="Consulta", especialidade=self.nutri)
        self.assertEqual(set(consulta.espacos_possiveis()), {self.c1, self.c2})

    def test_servico_pode_restringir_a_sala_como_excecao(self):
        consulta = Servico.objects.create(nome="Bioimpedância", especialidade=self.nutri)
        consulta.espacos.set([self.c2])
        self.assertEqual(list(consulta.espacos_possiveis()), [self.c2])

    def test_sala_desativada_sai_da_lista(self):
        self.c2.ativo = False
        self.c2.save()
        consulta = Servico.objects.create(nome="Consulta", especialidade=self.nutri)
        self.assertEqual(list(consulta.espacos_possiveis()), [self.c1])

    def test_vagas_definem_se_e_em_grupo(self):
        self.assertFalse(Servico(vagas=1).em_grupo)
        self.assertTrue(Servico(vagas=10).em_grupo)


class PrazoDeConfirmacao(TestCase):
    def test_padrao_e_duas_horas(self):
        agora = hora(2, 8)
        aula = hora(3, 10)  # bem longe
        self.assertEqual(Configuracao.atual().prazo_para_confirmar(aula, agora), agora + timedelta(hours=2))

    def test_aula_perto_o_prazo_acaba_30_min_antes(self):
        agora = hora(2, 8)
        aula = hora(2, 9)  # daqui a 1 hora
        self.assertEqual(Configuracao.atual().prazo_para_confirmar(aula, agora), hora(2, 8, 30))

    def test_admin_muda_o_prazo(self):
        c = Configuracao.atual()
        c.prazo_confirmacao_horas = 4
        c.save()
        agora = timezone.now()
        self.assertEqual(Configuracao.atual().prazo_para_confirmar(agora + timedelta(days=2), agora),
                         agora + timedelta(hours=4))
