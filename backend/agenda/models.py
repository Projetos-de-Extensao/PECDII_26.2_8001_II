import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

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
        def adicionar_erro(campo, mensagem):
            erros.setdefault(campo, []).append(mensagem)

        if self.profissional_id and self.servico_id and not self.profissional.atende(self.servico.especialidade):
            adicionar_erro("profissional", "Este profissional não atende a especialidade do serviço.")
        if self.espaco_id and self.servico_id and not self.servico.espacos_possiveis().filter(pk=self.espaco_id).exists():
            adicionar_erro("espaco", "Esta sala não é usada por este serviço.")

        if self.inicio and self.servico_id:
            fim = self.inicio + self.servico.duracao
            inicio_local = (timezone.localtime(self.inicio) if timezone.is_aware(self.inicio)
                            else timezone.make_aware(self.inicio))
            fim_local = (timezone.localtime(fim) if timezone.is_aware(fim)
                         else timezone.make_aware(fim))
            conflitos = Agendamento.objects.filter(status=self.Status.AGENDADO,
                                                   inicio__lt=fim, fim__gt=self.inicio)
            if self.pk:
                conflitos = conflitos.exclude(pk=self.pk)

            if self.profissional_id:
                if not self.profissional.ativo or not self.profissional.funcionario.usuario.is_active:
                    adicionar_erro("profissional", "Este profissional está inativo.")
                turno = (inicio_local.date() == fim_local.date() and Disponibilidade.objects.filter(
                    profissional_id=self.profissional_id, dia_da_semana=inicio_local.weekday(),
                    hora_inicio__lte=inicio_local.time(), hora_fim__gte=fim_local.time()).exists())
                if not turno:
                    adicionar_erro("profissional", "O horário está fora da disponibilidade do profissional.")
                if conflitos.filter(profissional_id=self.profissional_id).exists():
                    adicionar_erro("profissional", "O profissional já tem um agendamento nesse horário.")
                if Bloqueio.objects.filter(profissional_id=self.profissional_id,
                                           inicio__lt=fim, fim__gt=self.inicio).exists():
                    adicionar_erro("profissional", "O profissional está bloqueado nesse horário.")

            if self.atleta_id and conflitos.filter(atleta_id=self.atleta_id).exists():
                adicionar_erro("atleta", "O atleta já tem um agendamento nesse horário.")

            if self.espaco_id:
                ocupacao = conflitos.filter(espaco_id=self.espaco_id).count()
                if ocupacao >= self.espaco.capacidade:
                    adicionar_erro("espaco", "A sala já atingiu sua capacidade nesse horário.")
                if Bloqueio.objects.filter(espaco_id=self.espaco_id,
                                           inicio__lt=fim, fim__gt=self.inicio).exists():
                    adicionar_erro("espaco", "A sala está bloqueada nesse horário.")
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
            bloqueado = Bloqueio.objects.filter(equipamento=equipamento,
                                                inicio__lt=self.fim, fim__gt=self.inicio).exists()
            if bloqueado:
                erros.append(f"{equipamento} está bloqueado nesse horário.")
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
        novo = Agendamento(atleta=self.atleta, servico=self.servico, profissional=self.profissional,
                           espaco=self.espaco, inicio=novo_inicio, substitui=self)
        novo.clean()
        novo.save()
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