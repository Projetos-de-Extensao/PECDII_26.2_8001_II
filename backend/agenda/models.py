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


class Disponibilidade(models.Model):
    # UC05: os turnos em que o profissional atende, por dia da semana (ex.: segunda, 08:00 às 12:00).
    # O 0 é segunda, igual ao date.weekday() do Python.
    class Dia(models.IntegerChoices):
        SEGUNDA = 0, "Segunda-feira"
        TERCA = 1, "Terça-feira"
        QUARTA = 2, "Quarta-feira"
        QUINTA = 3, "Quinta-feira"
        SEXTA = 4, "Sexta-feira"
        SABADO = 5, "Sábado"
        DOMINGO = 6, "Domingo"

    profissional = models.ForeignKey(Profissional, on_delete=models.PROTECT, related_name="disponibilidades")
    dia_da_semana = models.PositiveSmallIntegerField(choices=Dia.choices)
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()

    class Meta:
        verbose_name_plural = "disponibilidades"
        ordering = ["dia_da_semana", "hora_inicio"]

    def clean(self):
        if not (self.hora_inicio and self.hora_fim):
            return  # campo faltando: quem avisa é a validação do próprio campo
        if self.hora_fim <= self.hora_inicio:
            raise ValidationError({"hora_fim": "O fim precisa ser depois do início."})
        if self.profissional_id is not None and self.dia_da_semana is not None:
            sobrepostos = Disponibilidade.objects.filter(
                profissional_id=self.profissional_id, dia_da_semana=self.dia_da_semana,
                hora_inicio__lt=self.hora_fim, hora_fim__gt=self.hora_inicio)
            if self.pk:
                sobrepostos = sobrepostos.exclude(pk=self.pk)
            if sobrepostos.exists():
                raise ValidationError("Este turno se sobrepõe a outro do mesmo dia.")

    def __str__(self):
        return f"{self.profissional} - {self.get_dia_da_semana_display()} {self.hora_inicio:%H:%M}-{self.hora_fim:%H:%M}"


class Bloqueio(models.Model):
    # UC05 e UC17: período em que um profissional (folga), uma sala (manutenção) ou um equipamento
    # não pode ser usado. Cada bloqueio é de um só alvo.
    profissional = models.ForeignKey(Profissional, null=True, blank=True, on_delete=models.PROTECT,
                                     related_name="bloqueios")
    espaco = models.ForeignKey(Espaco, null=True, blank=True, on_delete=models.PROTECT, related_name="bloqueios")
    equipamento = models.ForeignKey(Equipamento, null=True, blank=True, on_delete=models.PROTECT,
                                    related_name="bloqueios")
    inicio = models.DateTimeField()
    fim = models.DateTimeField()
    motivo = models.CharField(max_length=200)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-inicio"]

    @property
    def alvo(self):
        return self.profissional or self.espaco or self.equipamento

    def clean(self):
        alvos = [a for a in (self.profissional_id, self.espaco_id, self.equipamento_id) if a]
        if len(alvos) != 1:
            raise ValidationError("Informe um só alvo: profissional, espaço ou equipamento.")
        if self.inicio and self.fim and self.fim <= self.inicio:
            raise ValidationError({"fim": "O fim precisa ser depois do início."})

    def agendamentos_afetados(self):
        # UC05 A1 e UC17 A1: os agendamentos ainda marcados que caem dentro do bloqueio
        afetados = Agendamento.objects.filter(status=Agendamento.Status.AGENDADO,
                                              inicio__lt=self.fim, fim__gt=self.inicio)
        if self.profissional_id:
            afetados = afetados.filter(profissional_id=self.profissional_id)
        elif self.espaco_id:
            afetados = afetados.filter(espaco_id=self.espaco_id)
        elif self.equipamento_id:
            afetados = afetados.filter(equipamentos=self.equipamento_id)
        else:
            return Agendamento.objects.none()
        return afetados.distinct()

    def __str__(self):
        return f"{self.alvo} bloqueado de {self.inicio:%d/%m %H:%M} a {self.fim:%d/%m %H:%M}"