"""Se o e-mail falhar, o aviso na tela continua e o resto do sistema segue (UC19 e UC20)."""
import smtplib
from datetime import timedelta
from unittest import mock

from pkzlab.testes_comuns import hora

from .models import Agendamento, Aviso, ListaEspera
from .tests_lista_espera import ComFila

SERVIDOR_FORA = mock.patch("agenda.models.send_mail", side_effect=smtplib.SMTPException("servidor fora do ar"))


class EmailForaDoAr(ComFila):
    def test_aviso_na_tela_e_criado_mesmo_sem_email(self):
        with SERVIDOR_FORA, self.assertLogs("agenda.models", level="ERROR"):
            aviso = Aviso.avisar(self.maria.usuario, "Teste")
        self.assertTrue(Aviso.objects.filter(pk=aviso.pk).exists())

    def test_cancelamento_continua_e_oferece_a_vaga(self):
        maria = self.entrar(self.maria)
        with SERVIDOR_FORA, self.assertLogs("agenda.models", level="ERROR"):
            self.consulta_seg.cancelar("viagem")
        maria.refresh_from_db()
        self.assertEqual(maria.status, ListaEspera.Status.OFERECIDA)

    def test_lembrete_e_marcado_e_nao_repete(self):
        agora = hora(2, 9) - timedelta(hours=20)
        with SERVIDOR_FORA, self.assertLogs("agenda.models", level="ERROR"):
            self.assertEqual(Agendamento.enviar_lembretes(agora), 1)
            self.assertEqual(Agendamento.enviar_lembretes(agora), 0)
        self.assertEqual(Aviso.objects.filter(usuario=self.joao.usuario).count(), 1)
