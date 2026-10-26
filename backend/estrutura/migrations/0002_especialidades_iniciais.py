# Especialidades com que o CT começa. O admin pode cadastrar outras pelo painel (ex.: Psicólogo).
from django.db import migrations

INICIAIS = ["Personal Trainer", "Preparador Físico", "Fisioterapeuta", "Nutricionista"]


def criar(apps, schema_editor):
    Especialidade = apps.get_model("estrutura", "Especialidade")
    for nome in INICIAIS:
        Especialidade.objects.get_or_create(nome=nome)


class Migration(migrations.Migration):

    dependencies = [("estrutura", "0001_initial")]

    operations = [migrations.RunPython(criar, migrations.RunPython.noop)]
