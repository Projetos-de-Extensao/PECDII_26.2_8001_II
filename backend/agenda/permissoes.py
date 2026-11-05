from rest_framework.permissions import SAFE_METHODS, BasePermission

from .perfis import profissional_de


class ProfissionalMantemAPropria(BasePermission):
    # UC05: todo usuário logado consulta a disponibilidade (precisa dela para agendar, UC07);
    # só o próprio profissional (ou a equipe administrativa) cadastra, altera e apaga.
    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS or request.user.is_staff
                or profissional_de(request.user) is not None)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS or request.user.is_staff:
            return True
        proprio = profissional_de(request.user)
        return proprio is not None and obj.profissional_id == proprio.pk