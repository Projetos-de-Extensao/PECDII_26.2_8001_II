from datetime import datetime, timedelta

from django.db import migrations
from django.utils import timezone


def inscricoes_viram_agendamentos(apps, schema_editor):
    # Entrar numa aula passou a ser um agendamento da aula (UC06 A2). Antes de apagar a tabela,
    # cada inscrição confirmada que ainda não tinha agendamento ganha um, para ninguém sair da turma.
    Inscricao = apps.get_model("agenda", "Inscricao")
    Agendamento = apps.get_model("agenda", "Agendamento")
    for inscricao in Inscricao.objects.filter(status="CONFIRMADA").select_related("aula__servico"):
        aula = inscricao.aula
        ja_tem = (inscricao.agendamento_id is not None
                  or Agendamento.objects.filter(aula=aula, atleta_id=inscricao.atleta_id, status="AGENDADO").exists())
        if ja_tem:
            continue
        inicio = timezone.make_aware(datetime.combine(aula.dia, aula.hora_inicio), timezone.get_current_timezone())
        Agendamento.objects.create(atleta_id=inscricao.atleta_id, servico_id=aula.servico_id,
                                   profissional_id=aula.profissional_id, espaco_id=aula.espaco_id, aula=aula,
                                   inicio=inicio, fim=inicio + timedelta(minutes=aula.servico.duracao_minutos))


class Migration(migrations.Migration):

    dependencies = [
        ("agenda", "0009_lista_de_espera"),
    ]

    operations = [
        migrations.RunPython(inscricoes_viram_agendamentos, migrations.RunPython.noop),
        migrations.DeleteModel(
            name="Inscricao",
        ),
    ]
