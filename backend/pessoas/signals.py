from django.apps import apps
from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .permissoes import sincronizar_grupos


@receiver(post_save, sender=get_user_model())
def sincronizar_papeis_ao_salvar_usuario(sender, instance, **kwargs):
    sincronizar_grupos(instance)


def sincronizar_papeis_do_funcionario(sender, instance, **kwargs):
    sincronizar_grupos(instance.funcionario.usuario)


def conectar_sinais_papeis():
    for nome in ("Profissional", "Recepcao", "Administrador"):
        modelo = apps.get_model("pessoas", nome)
        post_save.connect(sincronizar_papeis_do_funcionario, sender=modelo,
                          dispatch_uid=f"pessoas.sincronizar_{nome.lower()}_save")
        post_delete.connect(sincronizar_papeis_do_funcionario, sender=modelo,
                           dispatch_uid=f"pessoas.sincronizar_{nome.lower()}_delete")
