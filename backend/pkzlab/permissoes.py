from rest_framework.permissions import SAFE_METHODS, BasePermission


class SoAdminAltera(BasePermission):
    # Todo usuário logado consulta; só a equipe administrativa (is_staff) cadastra e altera.
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or request.user.is_staff
