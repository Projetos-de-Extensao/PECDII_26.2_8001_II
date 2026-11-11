from django.utils import timezone
from rest_framework import serializers

from .models import Espaco, Especialidade, Servico, Equipamento


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
    confirmar = serializers.BooleanField(write_only=True, required=False, default=False,
                                         help_text="Envie true para inativar mesmo com agendamentos futuros (UC18 A1).")

    class Meta:
        model = Servico
        fields = ["id", "nome", "especialidade", "duracao_minutos", "vagas", "em_grupo", "espacos", "ativo",
                  "confirmar"]

    def validate(self, attrs):
        confirmar = attrs.pop("confirmar", False)  # não é campo do model
        inativando = self.instance is not None and self.instance.ativo and attrs.get("ativo") is False
        if inativando and not confirmar:
            # UC18 A1: alerta o administrador; os agendamentos já marcados continuam valendo
            from agenda.models import Agendamento, Aula
            futuros = Agendamento.objects.filter(servico=self.instance, status=Agendamento.Status.AGENDADO,
                                                 inicio__gt=timezone.now())
            aulas = Aula.objects.filter(servico=self.instance, ativo=True, dia__gte=timezone.localdate())
            partes = []
            total = futuros.count()
            if total:
                protocolos = list(futuros.values_list("protocolo", flat=True)[:5])
                if total > len(protocolos):
                    protocolos.append(f"e mais {total - len(protocolos)}")
                partes.append(f"{total} agendamento(s) futuro(s) ({', '.join(protocolos)})")
            if aulas.exists():
                partes.append(f"{aulas.count()} aula(s) na grade")
            if partes:
                raise serializers.ValidationError({"confirmar": (
                    f"Este serviço tem {' e '.join(partes)}. O que já está marcado continua valendo, mas o serviço "
                    "deixa de aceitar agendamentos novos. Envie confirmar=true para inativar mesmo assim.")})
        return attrs


class EquipamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipamento
        fields = ["id", "nome", "quantidade", "ativo"]  
