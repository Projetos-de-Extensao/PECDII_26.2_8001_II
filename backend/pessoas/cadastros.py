"""Cadastros que criam o login e o perfil juntos (ou nenhum dos dois)."""
from datetime import date

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Atleta, ConsentimentoLGPD, Funcionario, Responsavel

VERSAO_TERMOS_ATUAL = "1.0"


def _calcular_idade(data_nascimento):
    hoje = date.today()
    return (
        hoje.year
        - data_nascimento.year
        - ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))
    )


@transaction.atomic
def cadastrar_funcionario(*, email, nome, sobrenome, senha_provisoria, matricula, data_admissao):
    # UC04: o e-mail é o login, então não pode repetir (A1)
    if User.objects.filter(username__iexact=email).exists():
        raise ValidationError({"email": "E-mail já cadastrado."})
    usuario = User.objects.create_user(
        username=email,
        email=email,
        password=senha_provisoria,
        first_name=nome,
        last_name=sobrenome,
    )
    return Funcionario.objects.create(usuario=usuario, matricula=matricula, data_admissao=data_admissao)


@transaction.atomic
def cadastrar_atleta(
    *,
    email,
    nome,
    sobrenome="",
    senha,
    data_nascimento,
    aceitou_termos=False,
    responsavel=None,
    versao_termos=VERSAO_TERMOS_ATUAL,
):
    # UC02: exige aceite do consentimento LGPD
    if not aceitou_termos:
        raise ValidationError({"aceitou_termos": "É obrigatório aceitar os termos de consentimento LGPD."})

    # UC02: o e-mail é o login, então não pode repetir
    if User.objects.filter(username__iexact=email).exists():
        raise ValidationError({"email": "E-mail já cadastrado."})

    # UC02: atleta menor de 18 anos exige responsável
    if _calcular_idade(data_nascimento) < 18 and not responsavel:
        raise ValidationError({"responsavel": "Atleta menor de idade exige um responsável."})

    if isinstance(responsavel, dict):
        responsavel = Responsavel.objects.create(**responsavel)

    usuario = User.objects.create_user(
        username=email,
        email=email,
        password=senha,
        first_name=nome,
        last_name=sobrenome,
    )

    ConsentimentoLGPD.objects.create(
        usuario=usuario,
        versao_termos=versao_termos,
    )

    return Atleta.objects.create(
        usuario=usuario,
        data_nascimento=data_nascimento,
        responsavel=responsavel,
    )