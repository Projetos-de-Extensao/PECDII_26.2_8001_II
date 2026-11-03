# O Responsável passa a ter login (UC02, UC06, UC08, UC09, UC10, UC14).
# Responsáveis que já existiam ganham um login com o nome e o e-mail que tinham, sem senha:
# a pessoa define a senha depois (ou a recepção redefine pelo painel).
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def criar_logins(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Responsavel = apps.get_model("pessoas", "Responsavel")
    for r in Responsavel.objects.all():
        login = (r.email or f"responsavel{r.pk}@sem-email.pkzlab").lower()
        if User.objects.filter(username__iexact=login).exists():
            login = f"responsavel{r.pk}@sem-email.pkzlab"
        partes = r.nome.split(" ", 1)
        u = User.objects.create(username=login, email=r.email, first_name=partes[0][:150],
                                last_name=(partes[1] if len(partes) > 1 else "")[:150], password="!")  # "!" = sem senha
        r.usuario = u
        r.save(update_fields=["usuario"])


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("pessoas", "0002_responsavel_consentimentolgpd_atleta"),
    ]

    operations = [
        migrations.AddField(
            model_name="responsavel",
            name="usuario",
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT,
                                       related_name="responsavel", to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(criar_logins, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="responsavel",
            name="usuario",
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT,
                                       related_name="responsavel", to=settings.AUTH_USER_MODEL),
        ),
        migrations.RemoveField(model_name="responsavel", name="nome"),
        migrations.RemoveField(model_name="responsavel", name="email"),
        migrations.AlterModelOptions(
            name="responsavel",
            options={"ordering": ["usuario__first_name"], "verbose_name": "responsável",
                     "verbose_name_plural": "responsáveis"},
        ),
    ]