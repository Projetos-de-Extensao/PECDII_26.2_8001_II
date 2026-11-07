"""Quem pode ver e marcar o quê na agenda (UC10). Usado pela API e por qualquer outra porta."""

from pessoas.permissoes import tem_permissao


def profissional_de(usuario):
    # o Profissional ligado a esse login, ou None
    if not usuario.is_authenticated or not usuario.is_active:
        return None
    funcionario = getattr(usuario, "funcionario", None)
    profissional = getattr(funcionario, "profissional", None) if funcionario else None
    return profissional if profissional and profissional.ativo else None


def ve_a_agenda_toda(usuario):
    # recepção e administração veem e marcam a agenda de todo mundo
    return tem_permissao(usuario, "gerenciar_agenda")


def pode_agendar_para(usuario, atleta):
    if tem_permissao(usuario, "agendar_para_qualquer_atleta"):
        return True                                              # equipe marca para qualquer atleta
    if atleta.usuario_id == usuario.pk:
        return True                                              # o atleta marca para ele mesmo
    responsavel = getattr(usuario, "responsavel", None)
    return responsavel is not None and atleta.responsavel_id == responsavel.pk   # o responsável, para o dependente

def e_administracao(usuario):
    return tem_permissao(usuario, "administrar_sistema")


def pode_registrar_atendimento(usuario, agendamento):
    # UC11: o profissional que atendeu ou a administração (a recepção não registra)
    proprio = profissional_de(usuario)
    return e_administracao(usuario) or (
        tem_permissao(usuario, "registrar_dados_tecnicos")
        and proprio is not None
        and agendamento.profissional_id == proprio.pk
    )
