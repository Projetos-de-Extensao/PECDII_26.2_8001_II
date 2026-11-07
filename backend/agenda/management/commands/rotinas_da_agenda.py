from django.core.management.base import BaseCommand

from agenda.models import Agendamento


class Command(BaseCommand):
    help = ("Rotinas automáticas da agenda. Hoje: envia o lembrete de 24 horas (UC20). "
            "No servidor, rodar a cada 5 minutos (cron).")

    def handle(self, *args, **options):
        enviados = Agendamento.enviar_lembretes()
        self.stdout.write(self.style.SUCCESS(f"Lembretes enviados: {enviados}"))
