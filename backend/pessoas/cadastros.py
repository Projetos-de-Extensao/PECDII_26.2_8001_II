"""Cadastros que criam o login e o perfil juntos (ou nenhum dos dois)."""


from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Atleta, ConsentimentoLGPD, Funcionario, Responsavel

VERSAO_TERMOS_ATUAL = "1.0"


def _conferir_senha(senha, campo, email, nome, sobrenome):
    # RNF05: a política de senha vale em toda porta de cadastro (API, cadastro público, comando...),
    # por isso fica aqui e não em cada serializer
    try:
        password_validation.validate_password(
            senha, User(username=email, email=email, first_name=nome, last_name=sobrenome))
    except ValidationError as erro:
        raise ValidationError({campo: erro.messages})


@transaction.atomic
def cadastrar_funcionario(*, email, nome, sobrenome, senha_provisoria, matricula, data_admissao):
    # UC04: o e-mail é o login, então não pode repetir (A1)
    if User.objects.filter(username__iexact=email).exists():
        raise ValidationError({"email": "E-mail já cadastrado."})
    _conferir_senha(senha_provisoria, "senha_provisoria", email, nome, sobrenome)
    usuario = User.objects.create_user(
        username=email,
        email=email,
        password=senha_provisoria,
        first_name=nome,
        last_name=sobrenome,
    )
    return Funcionario.objects.create(usuario=usuario, matricula=matricula, data_admissao=data_admissao)


@transaction.atomic
def _criar_login(email, nome, sobrenome, senha):
    # o e-mail é o login, então não pode repetir (UC02 A1)
    if User.objects.filter(username__iexact=email).exists():
        raise ValidationError({"email": "E-mail já cadastrado."})
    _conferir_senha(senha, "senha", email, nome, sobrenome)
    return User.objects.create_user(username=email, email=email, password=senha,
                                    first_name=nome, last_name=sobrenome)


def _conferir_aceite(aceitou_termos):
    if not aceitou_termos:
        raise ValidationError({"aceitou_termos": "É obrigatório aceitar os termos de consentimento LGPD."})


@transaction.atomic
def cadastrar_responsavel(*, email, nome, sobrenome="", senha, cpf="", telefone="",
                          aceitou_termos=False, versao_termos=VERSAO_TERMOS_ATUAL):
    # UC02: o responsável cria a própria conta e aceita os termos (LGPD art. 14: dados de menor
    # precisam do consentimento do responsável)
    _conferir_aceite(aceitou_termos)
    usuario = _criar_login(email, nome, sobrenome, senha)
    ConsentimentoLGPD.objects.create(usuario=usuario, versao_termos=versao_termos)
    return Responsavel.objects.create(usuario=usuario, cpf=cpf, telefone=telefone)


@transaction.atomic
def cadastrar_atleta(*, email, nome, sobrenome="", senha, data_nascimento, aceitou_termos=False,
                     responsavel=None, versao_termos=VERSAO_TERMOS_ATUAL):
    # UC02. A regra do menor de idade fica no Atleta.clean(): se falhar, a transação desfaz o login também.
    _conferir_aceite(aceitou_termos)
    usuario = _criar_login(email, nome, sobrenome, senha)
    ConsentimentoLGPD.objects.create(usuario=usuario, versao_termos=versao_termos)
    return Atleta.objects.create(usuario=usuario, data_nascimento=data_nascimento, responsavel=responsavel)