from rest_framework.permissions import SAFE_METHODS, BasePermission

from pessoas.permissoes import tem_permissao


class SoAdminAltera(BasePermission):
    # Todo usuário logado consulta; só a administração cadastra e altera.
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or tem_permissao(request.user, "gerenciar_estrutura")
