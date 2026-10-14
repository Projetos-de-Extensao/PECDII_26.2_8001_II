from django.db import models

class Profissional(models.Model):
    nome = models.CharField(max_length=100)
    especialidade = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.nome
    
class Agendamento(models.Model):
    class Status(models.TextChoices):
        AGENDADO = "AGENDADO", "Agendado"
        REALIZADO = "REALIZADO", "Realizado"
        CANCELADO = "CANCELADO", "Cancelado"

    profissional = models.ForeignKey(Profissional, on_delete=models.PROTECT, related_name="agendamentos")
    data_hora = models.DateTimeField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.AGENDADO)

    def __str__(self):
        return f"{self.profissional} - {self.data_hora:%d/%m %H:%M}"