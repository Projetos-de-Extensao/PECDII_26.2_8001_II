"""Agenda do CT: o dia a dia.

Agendamento  um horário marcado de um serviço, com um profissional, numa sala.
             O fim vem da duração do serviço. Nunca é apagado: cancelar e reagendar só mudam o status,
             e o reagendamento aponta para o agendamento que ele substitui (UC08).

Ainda faltam, quando existirem as classes: atletas, aula (grade) e equipamentos.
"""
import uuid

from django.core.exceptions import ValidationError
from django.db import models, transaction

from estrutura.models import Espaco, Servico
from pessoas.models import Profissional


def novo_protocolo():
    return uuid.uuid4().hex[:10].upper()


class Agendamento(models.Model):
    class Status(models.TextChoices):
        AGENDADO = "AGENDADO", "Agendado"
        CANCELADO = "CANCELADO", "Cancelado"
        SUBSTITUIDO = "SUBSTITUIDO", "Substituído"

    protocolo = models.CharField(max_length=10, unique=True, default=novo_protocolo, editable=False)
    servico = models.ForeignKey(Servico, on_delete=models.PROTECT, related_name="agendamentos")
    profissional = models.ForeignKey(Profissional, on_delete=models.PROTECT, related_name="agendamentos")
    espaco = models.ForeignKey(Espaco, on_delete=models.PROTECT, related_name="agendamentos")
    inicio = models.DateTimeField()
    fim = models.DateTimeField(editable=False)
    status = models.CharField(max_length=11, choices=Status.choices, default=Status.AGENDADO)
    justificativa = models.TextField(blank=True, help_text="Obrigatória para cancelar (UC09).")
    substitui = models.OneToOneField(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="substituido_por",
        help_text="O agendamento anterior, quando este veio de um reagendamento.")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["inicio"]

    def clean(self):
        erros = {}
        if self.profissional_id and self.servico_id and not self.profissional.atende(self.servico.especialidade):
            erros["profissional"] = "Este profissional não atende a especialidade do serviço."
        if self.espaco_id and self.servico_id and not self.servico.espacos_possiveis().filter(pk=self.espaco_id).exists():
            erros["espaco"] = "Esta sala não é usada por este serviço."
        if erros:
            raise ValidationError(erros)

    def save(self, *args, **kwargs):
        self.fim = self.inicio + self.servico.duracao
        super().save(*args, **kwargs)

    def cancelar(self, justificativa):
        if self.status != self.Status.AGENDADO:
            raise ValidationError("Só dá para cancelar um agendamento com status Agendado.")
        if not justificativa.strip():
            raise ValidationError({"justificativa": "Informe o motivo do cancelamento."})
        self.status = self.Status.CANCELADO
        self.justificativa = justificativa
        self.save(update_fields=["status", "justificativa"])

    @transaction.atomic
    def reagendar(self, novo_inicio):
        # UC08: o original fica como substituído (não é apagado) e o novo aponta para ele
        if self.status != self.Status.AGENDADO:
            raise ValidationError("Só dá para reagendar um agendamento com status Agendado.")
        self.status = self.Status.SUBSTITUIDO
        self.save(update_fields=["status"])
        return Agendamento.objects.create(servico=self.servico, profissional=self.profissional,
                                          espaco=self.espaco, inicio=novo_inicio, substitui=self)

    def __str__(self):
        return f"{self.protocolo} - {self.servico} com {self.profissional} em {self.inicio:%d/%m %H:%M}"
