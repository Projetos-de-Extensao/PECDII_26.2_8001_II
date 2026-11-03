# O agendamento passa a ter atleta (UC06, #30).
# Os agendamentos criados antes não tinham atleta e não dá para adivinhar de quem eram:
# se existir algum, a migração para e diz o que fazer, em vez de apagar dado de ninguém.
from django.db import migrations, models
import django.db.models.deletion


def conferir_agendamentos_sem_atleta(apps, schema_editor):
    Agendamento = apps.get_model("agenda", "Agendamento")
    sem_atleta = Agendamento.objects.filter(atleta__isnull=True)
    if sem_atleta.exists():
        protocolos = ", ".join(sem_atleta.values_list("protocolo", flat=True)[:10])
        raise RuntimeError(
            f"Existem {sem_atleta.count()} agendamento(s) sem atleta ({protocolos}), criados antes do atleta "
            "existir no sistema. Se forem só testes, apague o db.sqlite3 e rode o migrate de novo. "
            "Se forem reais, preencha o atleta de cada um pelo python manage.py shell e rode o migrate de novo.")


class Migration(migrations.Migration):

    dependencies = [
        ("pessoas", "0003_responsavel_com_login"),
        ("agenda", "0003_aviso"),
    ]

    operations = [
        migrations.AddField(
            model_name="agendamento",
            name="atleta",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT,
                                    related_name="agendamentos", to="pessoas.atleta"),
        ),
        migrations.RunPython(conferir_agendamentos_sem_atleta, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="agendamento",
            name="atleta",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                    related_name="agendamentos", to="pessoas.atleta"),
        ),
    ]