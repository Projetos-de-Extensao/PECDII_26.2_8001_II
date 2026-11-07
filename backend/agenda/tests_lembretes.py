"""Testes da issue #37: lembrete 24 horas antes e a rotina automática (UC20)."""
from datetime import date, timedelta
from io import StringIO

from django.core.management import call_command

from pessoas.cadastros import cadastrar_responsavel
from pkzlab.testes_comuns import atleta, hora

from .models import Agendamento, Aviso
from .tests import Base


class Lembretes(Base):
    def setUp(self):
        super().setUp()
        self.consulta_seg = self.agendar(hora(2, 9))          # segunda 9h
        self.agora = hora(2, 9) - timedelta(hours=20)         # domingo 13h: faltam 20 horas

    def test_pega_quem_comeca_nas_proximas_24_horas(self):
        self.assertIn(self.consulta_seg, Agendamento.precisam_de_lembrete(self.agora))

    def test_nao_pega_quem_esta_a_mais_de_24_horas(self):
        cedo_demais = hora(2, 9) - timedelta(hours=30)
        self.assertNotIn(self.consulta_seg, Agendamento.precisam_de_lembrete(cedo_demais))

    def test_nao_pega_quem_ja_passou(self):
        depois = hora(2, 10)
        self.assertNotIn(self.consulta_seg, Agendamento.precisam_de_lembrete(depois))

    def test_nao_pega_cancelado(self):
        self.consulta_seg.cancelar("viagem")
        self.assertNotIn(self.consulta_seg, Agendamento.precisam_de_lembrete(self.agora))

    def test_envia_aviso_para_o_atleta(self):
        self.assertEqual(Agendamento.enviar_lembretes(self.agora), 1)
        aviso = Aviso.objects.get(usuario=self.joao.usuario)
        self.assertIn(self.consulta_seg.protocolo, aviso.texto)
        self.consulta_seg.refresh_from_db()
        self.assertIsNotNone(self.consulta_seg.lembrete_enviado_em)

    def test_nao_envia_duas_vezes(self):
        Agendamento.enviar_lembretes(self.agora)
        self.assertEqual(Agendamento.enviar_lembretes(self.agora), 0)
        self.assertEqual(Aviso.objects.filter(usuario=self.joao.usuario).count(), 1)

    def test_menor_de_idade_avisa_o_responsavel_tambem(self):
        mae = cadastrar_responsavel(email="mae@x.com", nome="Maria", senha="senha12345", aceitou_termos=True)
        pedro = atleta("pedro", "Pedro", nascimento=date(2015, 5, 1), responsavel=mae)
        self.agendar(hora(2, 11), atleta=pedro)
        Agendamento.enviar_lembretes(self.agora)
        self.assertTrue(Aviso.objects.filter(usuario=pedro.usuario).exists())
        self.assertTrue(Aviso.objects.filter(usuario=mae.usuario).exists())

    def test_reagendado_ganha_lembrete_novo(self):
        Agendamento.enviar_lembretes(self.agora)
        novo = Agendamento.objects.create(atleta=self.joao, servico=self.consulta, profissional=self.nutricionista,
                                          espaco=self.consultorio, inicio=hora(2, 11), substitui=self.consulta_seg)
        self.assertIsNone(novo.lembrete_enviado_em)
        self.assertIn(novo, Agendamento.precisam_de_lembrete(self.agora))


class ComandoRotinas(Base):
    def test_comando_roda_e_diz_quantos_enviou(self):
        saida = StringIO()
        call_command("rotinas_da_agenda", stdout=saida)
        self.assertIn("Lembretes enviados: 0", saida.getvalue())
