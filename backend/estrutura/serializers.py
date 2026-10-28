from rest_framework import serializers

from .models import Espaco, Especialidade, Servico


class EspecialidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Especialidade
        fields = ["id", "nome", "ativo"]


class EspacoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Espaco
        fields = ["id", "nome", "especialidades", "capacidade", "ativo"]


class ServicoSerializer(serializers.ModelSerializer):
    em_grupo = serializers.BooleanField(read_only=True)

    class Meta:
        model = Servico
        fields = ["id", "nome", "especialidade", "duracao_minutos", "vagas", "em_grupo", "espacos", "ativo"]
