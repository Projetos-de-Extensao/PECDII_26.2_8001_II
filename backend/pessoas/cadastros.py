"""Cadastros que criam o login e o perfil juntos (ou nenhum dos dois)."""
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Funcionario


@transaction.atomic
def cadastrar_funcionario(*, email, nome, sobrenome, senha_provisoria, matricula, data_admissao):
    # UC04: o e-mail é o login, então não pode repetir (A1)
    if User.objects.filter(username__iexact=email).exists():
        raise ValidationError({"email": "E-mail já cadastrado."})
    usuario = User.objects.create_user(username=email, email=email, password=senha_provisoria,
                                       first_name=nome, last_name=sobrenome)
    return Funcionario.objects.create(usuario=usuario, matricula=matricula, data_admissao=data_admissao)
