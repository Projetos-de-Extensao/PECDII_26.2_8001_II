from django.core.management.base import BaseCommand

from agenda.models import Agendamento, ListaEspera


class Command(BaseCommand):
    help = ("Rotinas automáticas da agenda: vence as vagas da lista de espera não confirmadas no prazo (UC19) "
            "e envia o lembrete de 24 horas (UC20). No servidor, rodar a cada 5 minutos (cron).")

    def handle(self, *args, **options):
        vencidas = ListaEspera.vencer_ofertas()
        self.stdout.write(self.style.SUCCESS(f"Vagas da lista de espera vencidas: {vencidas}"))
        enviados = Agendamento.enviar_lembretes()
        self.stdout.write(self.style.SUCCESS(f"Lembretes enviados: {enviados}"))
