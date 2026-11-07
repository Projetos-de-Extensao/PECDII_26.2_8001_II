from django.apps import AppConfig


class PessoasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pessoas"
    verbose_name = "Pessoas"

    def ready(self):
        from .signals import conectar_sinais_papeis

        conectar_sinais_papeis()
