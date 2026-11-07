from django.contrib.auth.models import Group, Permission


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


def _grupo(nome, codenames):
    grupo, criado = Group.objects.get_or_create(name=nome)
    if criado:
        # o grupo sumiu (apagado ou renomeado no /admin/): volta com as permissões do papel, não vazio
        grupo.permissions.set(Permission.objects.filter(content_type__app_label="pessoas", codename__in=codenames))
    return grupo


def sincronizar_grupos(usuario):
    grupos = {nome: _grupo(nome, codenames) for nome, codenames in GRUPOS_POR_PAPEL.values()}
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
