"""Indicadores do atleta: evolução (UC14) e relatório de desempenho (UC15).

Só lê o que já está gravado: avaliações físicas, planos de treino e atendimentos (presença/falta).
Os períodos são datas (de/ate), inclusive nas duas pontas; vazio = sem limite.
"""
from django.db.models import Count, Q

from agenda.models import Atendimento

from .models import TESTES, AvaliacaoFisica, PlanoTreino


def _no_periodo(qs, campo, de, ate):
    if de:
        qs = qs.filter(**{f"{campo}__gte": de})
    if ate:
        qs = qs.filter(**{f"{campo}__lte": ate})
    return qs


def variacao(avaliacoes):
    # diferença entre o primeiro e o último resultado de cada teste no conjunto (avaliações em ordem de data)
    resultado = {}
    for teste in TESTES:
        valores = [getattr(a, teste) for a in avaliacoes if getattr(a, teste) is not None]
        resultado[teste] = valores[-1] - valores[0] if len(valores) >= 2 else None
    return resultado


def frequencia(atendimentos):
    # presença, falta e cancelamento; a taxa de presença ignora cancelamentos
    contagem = atendimentos.aggregate(
        presencas=Count("pk", filter=Q(status=Atendimento.Status.PRESENCA)),
        faltas=Count("pk", filter=Q(status=Atendimento.Status.FALTA)),
        cancelamentos=Count("pk", filter=Q(status=Atendimento.Status.CANCELAMENTO)),
    )
    realizados = contagem["presencas"] + contagem["faltas"]
    contagem["taxa_presenca"] = round(contagem["presencas"] / realizados, 2) if realizados else None
    return contagem


def evolucao(atleta, de=None, ate=None):
    # UC14: avaliações ao longo do tempo, frequência e planos de treino
    avaliacoes = list(_no_periodo(atleta.avaliacoes.order_by("data", "criado_em"), "data", de, ate))
    atendimentos = _no_periodo(Atendimento.objects.filter(agendamento__atleta=atleta),
                               "agendamento__inicio__date", de, ate)
    planos = _no_periodo(atleta.planos.order_by("versao"), "inicio", de, ate)
    suficiente = len(avaliacoes) >= 2
    return {
        "atleta": atleta.pk,
        "periodo": {"de": de, "ate": ate},
        "historico_suficiente": suficiente,
        "mensagem": "" if suficiente else "Não há avaliações suficientes para comparar (são necessárias pelo menos duas).",
        "avaliacoes": [{"id": a.pk, "data": a.data, **{t: getattr(a, t) for t in TESTES}} for a in avaliacoes],
        "variacao": variacao(avaliacoes),
        "frequencia": frequencia(atendimentos),
        "planos": [{"id": p.pk, "versao": p.versao, "objetivo": p.objetivo, "inicio": p.inicio, "fim": p.fim,
                    "ativo": p.ativo} for p in planos],
    }


def relatorio_de_desempenho(de, ate, atletas=None, profissional=None):
    # UC15: um resumo por atleta com dados no período; profissional restringe ao que ele avaliou e atendeu
    avaliacoes = _no_periodo(AvaliacaoFisica.objects.select_related("atleta__usuario"), "data", de, ate)
    atendimentos = _no_periodo(Atendimento.objects.all(), "agendamento__inicio__date", de, ate)
    if profissional is not None:
        avaliacoes = avaliacoes.filter(profissional=profissional)
        atendimentos = atendimentos.filter(agendamento__profissional=profissional)
    if atletas:
        avaliacoes = avaliacoes.filter(atleta__in=atletas)
        atendimentos = atendimentos.filter(agendamento__atleta__in=atletas)

    por_atleta = {}
    for a in avaliacoes.order_by("data", "criado_em"):
        por_atleta.setdefault(a.atleta, []).append(a)
    for atleta in {at.agendamento.atleta for at in atendimentos.select_related("agendamento__atleta__usuario")}:
        por_atleta.setdefault(atleta, [])

    linhas = [{
        "atleta": atleta.pk,
        "nome": atleta.nome,
        "avaliacoes": len(lista),
        "variacao": variacao(lista),
        "frequencia": frequencia(atendimentos.filter(agendamento__atleta=atleta)),
        "plano_ativo": PlanoTreino.objects.filter(atleta=atleta, ativo=True).values_list("objetivo", flat=True).first(),
    } for atleta, lista in sorted(por_atleta.items(), key=lambda item: item[0].nome)]

    return {
        "periodo": {"de": de, "ate": ate},
        "mensagem": "" if linhas else "Sem dados no período selecionado.",  # A1
        "atletas": linhas,
        "totais": {"atletas": len(linhas), "avaliacoes": avaliacoes.count(), **frequencia(atendimentos)},
    }
