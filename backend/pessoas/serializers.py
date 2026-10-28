from rest_framework import serializers

from .models import Profissional


class ProfissionalSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(read_only=True)

    class Meta:
        model = Profissional
        fields = ["id", "nome", "especialidades"]
