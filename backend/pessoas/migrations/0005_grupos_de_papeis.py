from django.db import migrations


PERMISSOES_POR_GRUPO = {
    "Profissional": (
        "ver_todas_as_pessoas",
        "agendar_para_qualquer_atleta",
        "registrar_dados_tecnicos",
    ),
    "Recepção": (
        "ver_todas_as_pessoas",
        "agendar_para_qualquer_atleta",
        "gerenciar_agenda",
        "gerenciar_cadastros",
    ),
    "Administrador": (
        "ver_todas_as_pessoas",
        "agendar_para_qualquer_atleta",
        "registrar_dados_tecnicos",
        "gerenciar_agenda",
        "gerenciar_cadastros",
        "gerenciar_estrutura",
        "administrar_sistema",
    ),
}

PAPEIS_POR_GRUPO = {
    "Profissional": "profissional",
    "Recepção": "recepcao",
    "Administrador": "administrador",
}


def criar_grupos_e_atribuir_papeis(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    Funcionario = apps.get_model("pessoas", "Funcionario")
    nomes_permissoes = dict(Funcionario._meta.permissions)
    ct, _ = ContentType.objects.get_or_create(app_label="pessoas", model="funcionario")
    grupos = {}

    for nome, codenames in PERMISSOES_POR_GRUPO.items():
        grupo, _ = Group.objects.get_or_create(name=nome)
        permissoes = []
        for codename in codenames:
            permissao, _ = Permission.objects.get_or_create(
                content_type=ct,
                codename=codename,
                defaults={"name": nomes_permissoes[codename]},
            )
            permissoes.append(permissao)
        grupo.permissions.set(permissoes)
        grupos[nome] = grupo

    for funcionario in Funcionario.objects.select_related("usuario").iterator():
        if not funcionario.usuario.is_active:
            continue
        for grupo, papel in PAPEIS_POR_GRUPO.items():
            try:
                perfil = getattr(funcionario, papel)
            except AttributeError:
                continue
            if perfil.ativo:
                funcionario.usuario.groups.add(grupos[grupo])


def remover_grupos_de_papeis(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=PERMISSOES_POR_GRUPO).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("pessoas", "0004_alter_funcionario_options"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(criar_grupos_e_atribuir_papeis, remover_grupos_de_papeis),
    ]
