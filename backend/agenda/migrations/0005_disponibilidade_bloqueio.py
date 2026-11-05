# Disponibilidade do profissional (UC05) e Bloqueio de profissional, espaço ou equipamento (UC05, UC17).
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('estrutura', '0003_equipamento'),
        ('pessoas', '0003_responsavel_com_login'),
        ('agenda', '0004_atleta_no_agendamento'),
    ]

    operations = [
        migrations.CreateModel(
            name='Disponibilidade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dia_da_semana', models.PositiveSmallIntegerField(choices=[(0, 'Segunda-feira'), (1, 'Terça-feira'), (2, 'Quarta-feira'), (3, 'Quinta-feira'), (4, 'Sexta-feira'), (5, 'Sábado'), (6, 'Domingo')])),
                ('hora_inicio', models.TimeField()),
                ('hora_fim', models.TimeField()),
                ('profissional', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='disponibilidades', to='pessoas.profissional')),
            ],
            options={
                'verbose_name_plural': 'disponibilidades',
                'ordering': ['dia_da_semana', 'hora_inicio'],
            },
        ),
        migrations.CreateModel(
            name='Bloqueio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inicio', models.DateTimeField()),
                ('fim', models.DateTimeField()),
                ('motivo', models.CharField(max_length=200)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('equipamento', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='bloqueios', to='estrutura.equipamento')),
                ('espaco', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='bloqueios', to='estrutura.espaco')),
                ('profissional', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='bloqueios', to='pessoas.profissional')),
            ],
            options={
                'ordering': ['-inicio'],
            },
        ),
    ]