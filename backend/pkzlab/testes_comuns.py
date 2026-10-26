"""Funções de apoio para os testes dos três apps (não é usado pelo sistema em si)."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User

SP = ZoneInfo("America/Sao_Paulo")


def _proxima_segunda():
    hoje = date.today()
    return hoje + timedelta(days=(7 - hoje.weekday()) or 7)


SEGUNDA = _proxima_segunda()  # sempre no futuro: os testes não "vencem" com o tempo


def hora(dia, h, m=0):
    # dia 2 = SEGUNDA, dia 3 = terça, dia 1 = domingo antes
    d = SEGUNDA + timedelta(days=dia - 2)
    return datetime(d.year, d.month, d.day, h, m, tzinfo=SP)


def funcionario(login, nome, matricula):
    from pessoas.cadastros import cadastrar_funcionario
    return cadastrar_funcionario(email=f"{login}@ct.com", nome=nome, sobrenome="", senha_provisoria="senha12345",
                                 matricula=matricula, data_admissao=date(2025, 1, 10))


def profissional(login, nome, matricula, *especialidades):
    from pessoas.models import Profissional
    p = Profissional.objects.create(funcionario=funcionario(login, nome, matricula))
    p.especialidades.set(especialidades)
    return p


def atleta(login, nome, nascimento=date(2000, 1, 1), responsavel=None):
    from pessoas.cadastros import cadastrar_atleta
    return cadastrar_atleta(email=f"{login}@x.com", nome=nome, sobrenome="", senha="senha12345",
                            data_nascimento=nascimento, aceitou_termos=True, responsavel=responsavel)


def recarregar(usuario):
    return User.objects.get(pk=usuario.pk)  # limpa o cache de permissões
