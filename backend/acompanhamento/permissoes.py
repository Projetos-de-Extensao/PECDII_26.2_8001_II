from rest_framework.permissions import SAFE_METHODS, BasePermission

from agenda.perfis import profissional_de


def da_equipe_tecnica(usuario):
    # quem registra avaliação e prescreve treino: profissional ou administração
    return usuario.is_staff or profissional_de(usuario) is not None


class EquipeTecnicaRegistra(BasePermission):
    # UC12 e UC13: todo logado consulta (o que pode ver é filtrado na view); só a equipe técnica grava
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or da_equipe_tecnica(request.user)
