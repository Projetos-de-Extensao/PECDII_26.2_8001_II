"""Quem pode ver e marcar o quê na agenda (UC10). Usado pela API e por qualquer outra porta."""


def profissional_de(usuario):
    # o Profissional ligado a esse login, ou None
    funcionario = getattr(usuario, "funcionario", None)
    return getattr(funcionario, "profissional", None) if funcionario else None


def ve_a_agenda_toda(usuario):
    # recepção e administração veem e marcam a agenda de todo mundo
    funcionario = getattr(usuario, "funcionario", None)
    return (usuario.is_superuser or usuario.is_staff
            or (funcionario is not None and (hasattr(funcionario, "recepcao") or hasattr(funcionario, "administrador"))))


def pode_agendar_para(usuario, atleta):
    if ve_a_agenda_toda(usuario) or profissional_de(usuario):
        return True                                              # equipe marca para qualquer atleta
    if atleta.usuario_id == usuario.pk:
        return True                                              # o atleta marca para ele mesmo
    responsavel = getattr(usuario, "responsavel", None)
    return responsavel is not None and atleta.responsavel_id == responsavel.pk   # o responsável, para o dependente

def e_administracao(usuario):
    funcionario = getattr(usuario, "funcionario", None)
    return usuario.is_superuser or usuario.is_staff or (funcionario is not None and hasattr(funcionario, "administrador"))


def pode_registrar_atendimento(usuario, agendamento):
    # UC11: o profissional que atendeu ou a administração (a recepção não registra)
    proprio = profissional_de(usuario)
    return e_administracao(usuario) or (proprio is not None and agendamento.profissional_id == proprio.pk)
