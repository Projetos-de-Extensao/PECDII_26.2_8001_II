
import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction

from estrutura.models import Espaco, Servico,Equipamento
from pessoas.models import Profissional,Atleta


def novo_protocolo():
    return uuid.uuid4().hex[:10].upper()


class Agendamento(models.Model):
    class Status(models.TextChoices):
        AGENDADO = "AGENDADO", "Agendado"
        CANCELADO = "CANCELADO", "Cancelado"
        SUBSTITUIDO = "SUBSTITUIDO", "Substituído"

    protocolo = models.CharField(max_length=10, unique=True, default=novo_protocolo, editable=False)
    atleta = models.ForeignKey(Atleta, on_delete=models.PROTECT, related_name="agendamentos")
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
    equipamentos = models.ManyToManyField(Equipamento, blank=True, related_name="agendamentos",
                                          help_text="Equipamentos reservados para este atendimento.")
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
    def reservar_equipamentos(self, equipamentos):
        erros = []
        for equipamento in equipamentos:
            if not equipamento.ativo:
                erros.append(f"{equipamento} está fora de uso.")
                continue
            em_uso = (Agendamento.objects
                      .filter(equipamentos=equipamento, status=self.Status.AGENDADO,
                              inicio__lt=self.fim, fim__gt=self.inicio)
                      .exclude(pk=self.pk).count())
            if em_uso >= equipamento.quantidade:
                erros.append(f"Todas as unidades de {equipamento} já estão reservadas nesse horário.")
        if erros:
            raise ValidationError({"equipamentos": erros})
        self.equipamentos.set(equipamentos)         

    def cancelar(self, justificativa):
        if self.status != self.Status.AGENDADO:
            raise ValidationError("Só dá para cancelar um agendamento com status Agendado.")
        if not justificativa.strip():
            raise ValidationError({"justificativa": "Informe o motivo do cancelamento."})
        self.status = self.Status.CANCELADO
        self.justificativa = justificativa
        self.save(update_fields=["status", "justificativa"])
        Aviso.avisar(self.profissional.funcionario.usuario,
                     f"Atendimento {self.protocolo} de {self.inicio:%d/%m às %H:%M} foi cancelado: {justificativa}")

    @transaction.atomic
    def reagendar(self, novo_inicio):
        # UC08: o original fica como substituído (não é apagado) e o novo aponta para ele
        if self.status != self.Status.AGENDADO:
            raise ValidationError("Só dá para reagendar um agendamento com status Agendado.")
        self.status = self.Status.SUBSTITUIDO
        self.save(update_fields=["status"])
        novo = Agendamento.objects.create(atleta=self.atleta, servico=self.servico, profissional=self.profissional,
                                          espaco=self.espaco, inicio=novo_inicio, substitui=self)
        novo.reservar_equipamentos(self.equipamentos.all())  # leva os mesmos equipamentos para o novo horário
        return novo

    def __str__(self):
            return f"{self.protocolo} - {self.atleta} com {self.profissional} em {self.inicio:%d/%m %H:%M}"
class Aviso(models.Model):
    
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="avisos")
    texto = models.CharField(max_length=300)
    link = models.CharField(max_length=200, blank=True, help_text="Para onde o aviso leva (opcional).")
    lido = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]  # o mais novo primeiro

    @classmethod
    def avisar(cls, usuario, texto, link=""):
       
        return cls.objects.create(usuario=usuario, texto=texto[:300], link=link)

    def marcar_como_lido(self):
        if not self.lido:
            self.lido = True
            self.save(update_fields=["lido"])

    def __str__(self):
        return self.texto