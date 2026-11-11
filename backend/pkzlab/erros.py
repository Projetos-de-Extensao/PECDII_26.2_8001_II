from django.db.models import ProtectedError, RestrictedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def tratar_erros(exc, context):
    # Apagar algo que ainda está em uso (on_delete=PROTECT) estourava 500. Vira 400 dizendo o que está usando.
    if isinstance(exc, (ProtectedError, RestrictedError)):
        em_uso = {}
        for objeto in exc.protected_objects if isinstance(exc, ProtectedError) else exc.restricted_objects:
            nome = objeto._meta.verbose_name_plural
            em_uso[nome] = em_uso.get(nome, 0) + 1
        lista = ", ".join(f"{quantidade} {nome}" for nome, quantidade in sorted(em_uso.items()))
        return Response({"detail": f"Não dá para apagar: ainda está em uso ({lista}). Desative em vez de apagar."},
                        status=status.HTTP_400_BAD_REQUEST)
    return exception_handler(exc, context)
