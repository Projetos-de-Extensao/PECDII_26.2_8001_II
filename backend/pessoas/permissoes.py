from django.contrib.auth.models import Group


GRUPOS_POR_PAPEL = {
    "profissional": ("Profissional", {
        "ver_todas_as_pessoas",
        "agendar_para_qualquer_atleta",
        "registrar_dados_tecnicos",
    }),
    "recepcao": ("Recepção", {
        "ver_todas_as_pessoas",
        "agendar_para_qualquer_atleta",
        "gerenciar_agenda",
        "gerenciar_cadastros",
    }),
    "administrador": ("Administrador", {
        "ver_todas_as_pessoas",
        "agendar_para_qualquer_atleta",
        "registrar_dados_tecnicos",
        "gerenciar_agenda",
        "gerenciar_cadastros",
        "gerenciar_estrutura",
        "administrar_sistema",
    }),
}


def tem_permissao(usuario, codename):
    return bool(usuario.is_authenticated and usuario.has_perm(f"pessoas.{codename}"))


def sincronizar_grupos(usuario):
    grupos = {
        nome: Group.objects.get_or_create(name=nome)[0]
        for nome, _ in GRUPOS_POR_PAPEL.values()
    }
    usuario.groups.remove(*grupos.values())
    if usuario.is_active:
        for papel, (nome, _) in GRUPOS_POR_PAPEL.items():
            funcionario = getattr(usuario, "funcionario", None)
            perfil = getattr(funcionario, papel, None) if funcionario else None
            if perfil and perfil.ativo:
                usuario.groups.add(grupos[nome])
    for atributo in ("_perm_cache", "_user_perm_cache", "_group_perm_cache"):
        if hasattr(usuario, atributo):
            delattr(usuario, atributo)
