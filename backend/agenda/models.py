import logging
import uuid
from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import models, transaction
from django.utils import timezone

from estrutura.models import Configuracao, Espaco, Servico,Equipamento
from pessoas.models import Profissional,Atleta

logger = logging.getLogger(__name__)


def novo_protocolo():
    return uuid.uuid4().hex[:10].upper()


def quem_avisar(atleta):
    # o atleta e, se ele tiver responsável (menor de idade), o responsável também
    usuarios = [atleta.usuario]
    if atleta.responsavel_id:
        usuarios.append(atleta.responsavel.usuario)
    return usuarios


class Aula(models.Model):
    servico = models.ForeignKey(Servico, on_delete=models.PROTECT, related_name="aulas")
    profissional = models.ForeignKey(Profissional, on_delete=models.PROTECT, related_name="aulas")
    espaco = models.ForeignKey(Espaco, on_delete=models.PROTECT, related_name="aulas")
    dia = models.DateField(help_text="Dia da aula em grupo.")
    hora_inicio = models.TimeField(help_text="Horário inicial da aula.")
    hora_fim = models.TimeField(editable=False, help_text="Horário final calculado pela duração do serviço.")
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["dia", "hora_inicio"]
        verbose_name = "aula"
        verbose_name_plural = "aulas"

    CAMPOS_DO_HORARIO = ("servico_id", "profissional_id", "espaco_id", "dia", "hora_inicio")

    def _gravada(self):
        # como a aula está no banco agora (antes desta edição); None se ainda não foi gravada
        if self.pk is None:
            return None
        return Aula.objects.filter(pk=self.pk).values(*self.CAMPOS_DO_HORARIO, "ativo").first()

    def _mudou_o_horario(self, gravada):
        return gravada is not None and any(gravada[campo] != getattr(self, campo) for campo in self.CAMPOS_DO_HORARIO)

    def aulas_no_mesmo_horario(self):
        # outras aulas ativas que encostam no horário desta (mesmo dia, horários se sobrepõem)
        fim = (datetime.combine(self.dia, self.hora_inicio) + self.servico.duracao).time()
        return Aula.objects.filter(ativo=True, dia=self.dia, hora_inicio__lt=fim,
                                   hora_fim__gt=self.hora_inicio).exclude(pk=self.pk)

    def clean(self, agora=None):
        erros = {}
        def adicionar_erro(campo, mensagem):
            erros.setdefault(campo, []).append(mensagem)

        if self.servico_id and not self.servico.em_grupo:
            adicionar_erro("servico", "Aula em grupo precisa de um serviço com mais de 1 vaga.")
        if self.servico_id and self.profissional_id and not self.profissional.atende(self.servico.especialidade):
            adicionar_erro("profissional", "Este profissional não atende a especialidade do serviço.")
        if self.espaco_id and self.servico_id and not self.servico.espacos_possiveis().filter(pk=self.espaco_id).exists():
            adicionar_erro("espaco", "Esta sala não é usada por este serviço.")
        if self.profissional_id and self.servico_id and hasattr(self.profissional, "funcionario"):
            if not self.profissional.ativo or not self.profissional.funcionario.usuario.is_active:
                adicionar_erro("profissional", "Este profissional está inativo.")
        if not (self.servico_id and self.profissional_id and self.espaco_id and self.dia and self.hora_inicio):
            if erros:
                raise ValidationError(erros)
            return  # campo faltando: quem avisa é a validação do próprio campo

        # o fim vem da duração do serviço (o hora_fim gravado pode ser de antes desta edição)
        if (datetime.combine(self.dia, self.hora_inicio) + self.servico.duracao).date() != self.dia:
            adicionar_erro("hora_inicio", "A aula precisa terminar no mesmo dia.")
            raise ValidationError(erros)

        gravada = self._gravada()
        alunos = self.agendamentos.filter(status=Agendamento.Status.AGENDADO) if self.pk else Agendamento.objects.none()
        if gravada and gravada["servico_id"] != self.servico_id and alunos.exists():
            adicionar_erro("servico", "Não dá para trocar o serviço de uma aula que já tem alunos.")

        # UC21: a agenda só é conferida quando a aula reserva um horário novo
        # (aula nova, mudou dia/hora/sala/professor, ou foi reativada). Desativar ou não mexer no horário não confere.
        reativou = gravada is not None and self.ativo and not gravada["ativo"]
        if self.ativo and (gravada is None or self._mudou_o_horario(gravada) or reativou):
            inicio, fim = self.inicio, self.fim
            if inicio <= (agora or timezone.now()):
                adicionar_erro("hora_inicio", "Esse horário já passou.")
            if not Disponibilidade.objects.filter(profissional_id=self.profissional_id,
                                                  dia_da_semana=self.dia.weekday(),
                                                  hora_inicio__lte=self.hora_inicio,
                                                  hora_fim__gte=timezone.localtime(fim).time()).exists():
                adicionar_erro("profissional", "O horário está fora da disponibilidade do profissional.")
            if Bloqueio.objects.filter(profissional_id=self.profissional_id, inicio__lt=fim, fim__gt=inicio).exists():
                adicionar_erro("profissional", "O profissional está bloqueado nesse horário.")
            if Bloqueio.objects.filter(espaco_id=self.espaco_id, inicio__lt=fim, fim__gt=inicio).exists():
                adicionar_erro("espaco", "A sala está bloqueada nesse horário.")

            outras_aulas = self.aulas_no_mesmo_horario()
            individuais = Agendamento.objects.filter(status=Agendamento.Status.AGENDADO, aula__isnull=True,
                                                     inicio__lt=fim, fim__gt=inicio)
            # UC21 passo 4: o professor não dá outra aula nem tem atendimento no mesmo horário
            if outras_aulas.filter(profissional_id=self.profissional_id).exists():
                adicionar_erro("profissional", "O professor já dá outra aula nesse horário.")
            if individuais.filter(profissional_id=self.profissional_id).exists():
                adicionar_erro("profissional", "O profissional já tem um agendamento nesse horário.")
            # UC21 passo 3: a sala está livre, respeitando a capacidade (cada aula ou atendimento ocupa 1)
            ocupacao = (outras_aulas.filter(espaco_id=self.espaco_id).count()
                        + individuais.filter(espaco_id=self.espaco_id).count())
            if ocupacao >= self.espaco.capacidade:
                adicionar_erro("espaco", "A sala já está ocupada nesse horário.")
            # mudar o horário leva os alunos junto: nenhum deles pode ter outro compromisso no horário novo
            for agendamento in alunos.select_related("atleta__usuario"):
                ocupado = Agendamento.objects.filter(atleta_id=agendamento.atleta_id,
                                                     status=Agendamento.Status.AGENDADO,
                                                     inicio__lt=fim, fim__gt=inicio).exclude(aula_id=self.pk)
                if ocupado.exists():
                    adicionar_erro("hora_inicio", f"{agendamento.atleta} já tem outro agendamento no horário novo.")
        if erros:
            raise ValidationError(erros)

    @property
    def inicio(self):
        if self.dia and self.hora_inicio:
            return timezone.make_aware(datetime.combine(self.dia, self.hora_inicio), timezone.get_current_timezone())
        return None

    @property
    def fim(self):
        if self.inicio and self.servico_id:
            return self.inicio + self.servico.duracao
        return None

    @property
    def vagas_restantes(self):
        total = self.servico.vagas if self.servico_id else 0
        usados = self.agendamentos.filter(status=Agendamento.Status.AGENDADO).count()
        # UC19: vaga oferecida a quem estava na lista de espera fica guardada até ele responder
        usados += ListaEspera.objects.filter(status=ListaEspera.Status.OFERECIDA, aula_id=self.pk).count()
        return max(total - usados, 0)

    @property
    def lotada(self):
        return self.vagas_restantes <= 0 if self.servico_id else True

    @transaction.atomic
    def save(self, *args, **kwargs):
        gravada = self._gravada()
        # recalcula sempre: mudar o início ou o serviço numa edição muda o fim também
        if self.servico_id and self.dia and self.hora_inicio:
            self.hora_fim = (datetime.combine(self.dia, self.hora_inicio) + self.servico.duracao).time()
        super().save(*args, **kwargs)
        if self._mudou_o_horario(gravada):
            self._levar_os_alunos()

    def _levar_os_alunos(self):
        # a aula mudou de dia, hora, sala ou professor: os agendamentos dos alunos vão junto e eles são avisados
        alunos = list(self.agendamentos.filter(status=Agendamento.Status.AGENDADO).select_related(
            "atleta__usuario", "atleta__responsavel__usuario"))
        for agendamento in alunos:
            agendamento.inicio, agendamento.fim = self.inicio, self.fim
            agendamento.espaco_id, agendamento.profissional_id = self.espaco_id, self.profissional_id
            agendamento.lembrete_enviado_em = None  # horário novo, lembrete novo (UC20)
        Agendamento.objects.bulk_update(alunos, ["inicio", "fim", "espaco", "profissional", "lembrete_enviado_em"])
        ListaEspera.objects.filter(aula=self, status__in=ListaEspera.ATIVOS).update(
            inicio=self.inicio, profissional_id=self.profissional_id)
        texto = (f"A aula de {self.servico} mudou: agora é dia {self.dia:%d/%m} às {self.hora_inicio:%H:%M}, "
                 f"na sala {self.espaco}.")
        for agendamento in alunos:
            for usuario in quem_avisar(agendamento.atleta):
                Aviso.avisar(usuario, texto)

    def __str__(self):
        if self.dia:
            return f"{self.servico} - {self.dia:%d/%m} {self.hora_inicio:%H:%M}"
        return str(self.servico)


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
    aula = models.ForeignKey("Aula", null=True, blank=True, on_delete=models.PROTECT, related_name="agendamentos")
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
    lembrete_enviado_em = models.DateTimeField(
        null=True, blank=True, editable=False,
        help_text="Quando o lembrete de 24 horas foi enviado (UC20). Vazio = ainda não enviado.")

    ANTECEDENCIA_DO_LEMBRETE = timedelta(hours=24)

    class Meta:
        ordering = ["inicio"]

    def clean(self, agora=None):
        erros = {}
        def adicionar_erro(campo, mensagem):
            erros.setdefault(campo, []).append(mensagem)

        # UC06 e UC08: só se marca (ou remarca) para um horário que ainda não começou
        if self.pk is None and self.inicio and self.inicio <= (agora or timezone.now()):
            adicionar_erro("inicio", "Esse horário já passou.")

        if self.servico_id and self.servico.em_grupo and not self.aula_id:
            adicionar_erro("aula", "Este serviço é em grupo: escolha uma aula da grade.")

        if self.aula_id:
            aula = self.aula
            if not aula.ativo and self.pk is None:
                adicionar_erro("aula", "Esta aula foi desativada.")
            if self.servico_id and self.servico_id != aula.servico_id:
                adicionar_erro("servico", "O agendamento da aula precisa usar o mesmo serviço da aula.")
            if self.profissional_id and self.profissional_id != aula.profissional_id:
                adicionar_erro("profissional", "O profissional do agendamento precisa ser o mesmo da aula.")
            if self.espaco_id and self.espaco_id != aula.espaco_id:
                adicionar_erro("espaco", "O espaço do agendamento precisa ser o mesmo da aula.")
            if self.inicio and aula.inicio and self.inicio != aula.inicio:
                adicionar_erro("inicio", "A data/hora do agendamento precisa bater com a aula.")
            if self.aula.lotada and self.status == self.Status.AGENDADO and self.pk is None:
                adicionar_erro("aula", "A turma está lotada.")
            if self.atleta_id and self.aula.agendamentos.filter(atleta_id=self.atleta_id, status=self.Status.AGENDADO).exclude(pk=self.pk).exists():
                adicionar_erro("atleta", "Este atleta já está inscrito nesta aula.")

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
            # UC19: horário individual oferecido a quem estava na lista de espera fica guardado para ele
            guardadas = ListaEspera.objects.filter(status=ListaEspera.Status.OFERECIDA, vaga__aula__isnull=True,
                                                   vaga__inicio__lt=fim, vaga__fim__gt=self.inicio)
            if self.atleta_id:
                guardadas = guardadas.exclude(atleta_id=self.atleta_id)
            # atendimentos individuais e aulas em grupo ocupam o profissional e a sala. Os alunos de uma aula não
            # contam um por um: quem ocupa é a aula (a turma cabe na sala e o limite dela são as vagas).
            individuais = conflitos.filter(aula__isnull=True)
            aulas = Aula.objects.filter(ativo=True, dia=inicio_local.date(), hora_inicio__lt=fim_local.time(),
                                        hora_fim__gt=inicio_local.time())
            if self.aula_id:
                aulas = aulas.exclude(pk=self.aula_id)

            if self.profissional_id:
                if not self.profissional.ativo or not self.profissional.funcionario.usuario.is_active:
                    adicionar_erro("profissional", "Este profissional está inativo.")
                turno = (inicio_local.date() == fim_local.date() and Disponibilidade.objects.filter(
                    profissional_id=self.profissional_id, dia_da_semana=inicio_local.weekday(),
                    hora_inicio__lte=inicio_local.time(), hora_fim__gte=fim_local.time()).exists())
                if not turno:
                    adicionar_erro("profissional", "O horário está fora da disponibilidade do profissional.")
                if individuais.filter(profissional_id=self.profissional_id).exists():
                    adicionar_erro("profissional", "O profissional já tem um agendamento nesse horário.")
                if aulas.filter(profissional_id=self.profissional_id).exists():
                    adicionar_erro("profissional", "O profissional dá uma aula em grupo nesse horário.")
                if guardadas.filter(vaga__profissional_id=self.profissional_id).exists():
                    adicionar_erro("profissional", "Este horário está guardado para quem estava na lista de espera.")
                if Bloqueio.objects.filter(profissional_id=self.profissional_id,
                                           inicio__lt=fim, fim__gt=self.inicio).exists():
                    adicionar_erro("profissional", "O profissional está bloqueado nesse horário.")

            if self.atleta_id and conflitos.filter(atleta_id=self.atleta_id).exists():
                adicionar_erro("atleta", "O atleta já tem um agendamento nesse horário.")

            if self.espaco_id and not self.aula_id:  # numa aula, a sala já foi reservada no cadastro dela (UC21)
                ocupacao = (individuais.filter(espaco_id=self.espaco_id).count()
                            + aulas.filter(espaco_id=self.espaco_id).count()
                            + guardadas.filter(vaga__espaco_id=self.espaco_id).count())
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
                     f"Atendimento {self.protocolo} de {timezone.localtime(self.inicio):%d/%m às %H:%M} "
                     f"foi cancelado: {justificativa}")
        ListaEspera.oferecer_vaga(self)  # UC19: a vaga liberada vai para o primeiro da fila

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

    # ---------------------------------------------------------------- UC20: lembrete 24 horas antes

    def quem_recebe_avisos(self):
        return quem_avisar(self.atleta)

    def enviar_lembrete(self):
        quando = timezone.localtime(self.inicio)
        texto = (f"Lembrete: {self.servico} com {self.profissional.nome} em {quando:%d/%m às %H:%M}, "
                 f"{self.espaco}. Protocolo {self.protocolo}.")
        for usuario in self.quem_recebe_avisos():
            Aviso.avisar(usuario, texto)
        self.lembrete_enviado_em = timezone.now()
        self.save(update_fields=["lembrete_enviado_em"])

    @classmethod
    def precisam_de_lembrete(cls, agora=None):
        # marcados, sem lembrete ainda, e que começam nas próximas 24 horas
        agora = agora or timezone.now()
        return cls.objects.filter(status=cls.Status.AGENDADO, lembrete_enviado_em__isnull=True,
                                  inicio__gt=agora, inicio__lte=agora + cls.ANTECEDENCIA_DO_LEMBRETE)

    @classmethod
    def enviar_lembretes(cls, agora=None):
        pendentes = cls.precisam_de_lembrete(agora).select_related(
            "atleta__usuario", "atleta__responsavel__usuario", "servico", "espaco",
            "profissional__funcionario__usuario")
        enviados = 0
        for agendamento in pendentes:
            agendamento.enviar_lembrete()
            enviados += 1
        return enviados

    def __str__(self):
            return f"{self.protocolo} - {self.atleta} com {self.profissional} em {self.inicio:%d/%m %H:%M}"


class ListaEspera(models.Model):
    # UC19: fila de quem quer um horário ocupado (atendimento individual) ou uma vaga numa turma lotada (aula).
    # Quando alguém cancela, a vaga é oferecida ao primeiro da fila, que tem um prazo para confirmar.
    class Status(models.TextChoices):
        AGUARDANDO = "AGUARDANDO", "Aguardando vaga"
        OFERECIDA = "OFERECIDA", "Vaga oferecida, aguardando confirmação"
        CONFIRMADA = "CONFIRMADA", "Confirmada"
        RECUSADA = "RECUSADA", "Recusada"
        VENCIDA = "VENCIDA", "Prazo vencido"
        SAIU = "SAIU", "Saiu da lista"

    atleta = models.ForeignKey(Atleta, on_delete=models.PROTECT, related_name="esperas")
    servico = models.ForeignKey(Servico, on_delete=models.PROTECT, related_name="esperas")
    profissional = models.ForeignKey(Profissional, on_delete=models.PROTECT, related_name="esperas")
    aula = models.ForeignKey(Aula, null=True, blank=True, on_delete=models.PROTECT, related_name="esperas",
                             help_text="Preenchido quando a espera é por uma vaga numa aula em grupo.")
    inicio = models.DateTimeField(help_text="O horário que o atleta quer.")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.AGUARDANDO)
    vaga = models.ForeignKey(Agendamento, null=True, blank=True, editable=False, on_delete=models.PROTECT,
                             related_name="ofertas_da_lista",
                             help_text="O agendamento cancelado cuja vaga foi oferecida.")
    prazo = models.DateTimeField(null=True, blank=True, editable=False,
                                 help_text="Até quando dá para confirmar a vaga oferecida.")
    agendamento = models.OneToOneField(Agendamento, null=True, blank=True, editable=False,
                                       on_delete=models.PROTECT, related_name="veio_da_lista",
                                       help_text="O agendamento criado quando o atleta confirmou a vaga.")
    criado_em = models.DateTimeField(auto_now_add=True)

    ATIVOS = (Status.AGUARDANDO, Status.OFERECIDA)

    class Meta:
        ordering = ["criado_em", "pk"]  # ordem de chegada
        verbose_name = "lista de espera"
        verbose_name_plural = "lista de espera"

    def mesma_fila(self):
        # quem espera pela mesma coisa: a mesma aula, ou o mesmo serviço, profissional e horário
        if self.aula_id:
            return ListaEspera.objects.filter(aula_id=self.aula_id)
        return ListaEspera.objects.filter(aula__isnull=True, servico_id=self.servico_id,
                                          profissional_id=self.profissional_id, inicio=self.inicio)

    @property
    def posicao(self):
        # 1 = o próximo a receber a vaga; só faz sentido para quem ainda está aguardando
        if self.status != self.Status.AGUARDANDO:
            return None
        na_frente = self.mesma_fila().filter(status=self.Status.AGUARDANDO).filter(
            models.Q(criado_em__lt=self.criado_em) | models.Q(criado_em=self.criado_em, pk__lt=self.pk))
        return na_frente.count() + 1

    def clean(self, agora=None):
        agora = agora or timezone.now()
        if self.aula_id:  # numa aula, serviço, profissional e horário são os dela
            self.servico, self.profissional, self.inicio = self.aula.servico, self.aula.profissional, self.aula.inicio
        if self.pk or not (self.servico_id and self.profissional_id and self.inicio):
            return  # só valida a entrada na fila; o resto quem muda é o sistema
        erros = {}
        fim = self.inicio + self.servico.duracao
        if self.inicio <= agora:
            erros.setdefault("inicio", []).append("Esse horário já passou.")
        if not self.profissional.atende(self.servico.especialidade):
            erros.setdefault("profissional", []).append("Este profissional não atende a especialidade do serviço.")
        if self.atleta_id:
            if self.mesma_fila().filter(atleta_id=self.atleta_id, status__in=self.ATIVOS).exists():
                erros.setdefault("atleta", []).append("Este atleta já está na lista de espera desse horário.")
            if Agendamento.objects.filter(atleta_id=self.atleta_id, status=Agendamento.Status.AGENDADO,
                                          inicio__lt=fim, fim__gt=self.inicio).exists():
                erros.setdefault("atleta", []).append("Este atleta já tem um agendamento nesse horário.")
        # pré-condição do UC19: só entra na fila quem quer algo que está ocupado
        if self.aula_id:
            ocupado = self.aula.lotada
        else:
            ocupado = (Agendamento.objects.filter(status=Agendamento.Status.AGENDADO, aula__isnull=True,
                                                  profissional_id=self.profissional_id,
                                                  inicio__lt=fim, fim__gt=self.inicio).exists()
                       or ListaEspera.objects.filter(status=self.Status.OFERECIDA, vaga__aula__isnull=True,
                                                     vaga__profissional_id=self.profissional_id,
                                                     vaga__inicio__lt=fim, vaga__fim__gt=self.inicio).exists())
        if not ocupado:
            erros.setdefault("inicio", []).append("Esse horário está livre: dá para agendar direto.")
        if erros:
            raise ValidationError(erros)

    def atleta_ocupado(self):
        # A1: se ele já marcou outro atendimento nesse horário, não adianta oferecer
        fim = self.inicio + self.servico.duracao
        return Agendamento.objects.filter(atleta_id=self.atleta_id, status=Agendamento.Status.AGENDADO,
                                          inicio__lt=fim, fim__gt=self.inicio).exists()

    @classmethod
    def oferecer_vaga(cls, vaga=None, agora=None, aula=None):
        # vaga = o agendamento que liberou o horário (numa aula em grupo, o agendamento do aluno que saiu).
        # Devolve a espera que recebeu a oferta, ou None.
        agora = agora or timezone.now()
        aula = aula or (vaga.aula if vaga and vaga.aula_id else None)
        prazo = Configuracao.atual().prazo_para_confirmar(aula.inicio if aula else vaga.inicio, agora)
        if prazo <= agora:
            return None  # A3: em cima da hora, a vaga fica livre para qualquer um
        if aula:
            fila = cls.objects.filter(aula=aula)
        else:
            fila = cls.objects.filter(aula__isnull=True, servico_id=vaga.servico_id,
                                      profissional_id=vaga.profissional_id, inicio=vaga.inicio)
        fila = fila.filter(status=cls.Status.AGUARDANDO).select_related(
            "atleta__usuario", "atleta__responsavel__usuario", "servico", "profissional__funcionario__usuario")
        for espera in fila:
            if espera.atleta_ocupado():
                continue
            espera.status, espera.vaga, espera.prazo = cls.Status.OFERECIDA, vaga, prazo
            espera.save(update_fields=["status", "vaga", "prazo"])
            espera.avisar(f"Abriu uma vaga para você: {espera.descricao()}. "
                          f"Confirme até {timezone.localtime(prazo):%d/%m às %H:%M}.")
            return espera
        return None

    def descricao(self):
        return f"{self.servico} com {self.profissional.nome} em {timezone.localtime(self.inicio):%d/%m às %H:%M}"

    def avisar(self, texto):
        for usuario in quem_avisar(self.atleta):
            Aviso.avisar(usuario, texto)

    def _repassar_vaga(self, agora=None):
        # a vaga que estava com este atleta passa para o próximo da mesma fila
        ListaEspera.oferecer_vaga(self.vaga, agora, aula=self.aula)

    @transaction.atomic
    def confirmar(self, agora=None):
        # a vaga vira um agendamento normal (passo 5 do UC19)
        agora = agora or timezone.now()
        if self.status != self.Status.OFERECIDA:
            raise ValidationError("Não há vaga oferecida para confirmar.")
        if agora >= self.prazo:
            raise ValidationError("O prazo para confirmar essa vaga já acabou.")
        self.status = self.Status.CONFIRMADA  # primeiro sai da reserva, senão a própria oferta bloquearia a vaga
        self.save(update_fields=["status"])
        # numa aula, o horário e a sala são os da turma
        espaco = self.aula.espaco if self.aula_id else self.vaga.espaco
        novo = Agendamento(atleta=self.atleta, servico=self.servico, profissional=self.profissional,
                           espaco=espaco, aula=self.aula, inicio=self.inicio)
        try:
            novo.clean()
        except ValidationError:
            self.status = self.Status.OFERECIDA  # o banco volta sozinho (atomic); o objeto em memória, não
            raise
        novo.save()
        self.agendamento = novo
        self.save(update_fields=["agendamento"])
        return novo

    @transaction.atomic
    def recusar(self, agora=None):
        if self.status != self.Status.OFERECIDA:
            raise ValidationError("Não há vaga oferecida para recusar.")
        self.status = self.Status.RECUSADA
        self.save(update_fields=["status"])
        self._repassar_vaga(agora)  # passa para o próximo da fila

    @transaction.atomic
    def sair(self, agora=None):
        # A4: o atleta desiste de esperar
        if self.status not in self.ATIVOS:
            raise ValidationError("Este atleta não está mais na lista de espera.")
        tinha_vaga = self.status == self.Status.OFERECIDA
        self.status = self.Status.SAIU
        self.save(update_fields=["status"])
        if tinha_vaga:
            self._repassar_vaga(agora)

    @classmethod
    def vencer_ofertas(cls, agora=None):
        # A2: quem não confirmou no prazo perde a vez, e a vaga vai para o próximo. Roda no rotinas_da_agenda.
        agora = agora or timezone.now()
        vencidas = cls.objects.filter(status=cls.Status.OFERECIDA, prazo__lte=agora).select_related(
            "atleta__usuario", "atleta__responsavel__usuario", "servico", "profissional__funcionario__usuario",
            "vaga", "aula")
        total = 0
        for espera in vencidas:
            with transaction.atomic():
                espera.status = cls.Status.VENCIDA
                espera.save(update_fields=["status"])
                espera.avisar(f"O prazo para confirmar a vaga de {espera.descricao()} acabou.")
                espera._repassar_vaga(agora)
            total += 1
        return total

    def __str__(self):
        return f"{self.atleta} espera {self.descricao()} ({self.get_status_display()})"


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
        aviso = cls.objects.create(usuario=usuario, texto=texto[:300], link=link)
        if usuario.email:
            # o aviso na tela é o principal; se o e-mail falhar (servidor fora, senha errada...), só registra no log.
            # Sem isso, a falha derrubava quem chamou: o cancelamento dava erro 500 sem oferecer a vaga à
            # lista de espera, e o lembrete era criado de novo a cada 5 minutos.
            try:
                send_mail("PKZ LAB: novo aviso", aviso.texto, settings.DEFAULT_FROM_EMAIL, [usuario.email])
            except Exception:
                logger.exception("Não foi possível enviar o e-mail do aviso %s para %s", aviso.pk, usuario.email)
        return aviso

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
        return (f"{self.alvo} bloqueado de {timezone.localtime(self.inicio):%d/%m %H:%M} "
                f"a {timezone.localtime(self.fim):%d/%m %H:%M}")

class Atendimento(models.Model):
    # UC11: o que aconteceu no horário marcado. Um registro por agendamento, gravado pelo profissional
    # que atendeu (ou pela administração) depois que o horário começou. Não se edita nem se apaga.
    class Status(models.TextChoices):
        PRESENCA = "PRESENCA", "Presença"
        FALTA = "FALTA", "Falta"
        CANCELAMENTO = "CANCELAMENTO", "Cancelamento"

    agendamento = models.OneToOneField(Agendamento, on_delete=models.PROTECT, related_name="atendimento")
    status = models.CharField(max_length=12, choices=Status.choices)
    justificativa = models.TextField(blank=True, help_text="Obrigatória para falta e cancelamento.")
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                       related_name="atendimentos_registrados")
    registrado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-registrado_em"]

    def clean(self, agora=None):
        erros = {}
        if self.status in (self.Status.FALTA, self.Status.CANCELAMENTO) and not self.justificativa.strip():
            erros["justificativa"] = "Informe a justificativa para falta ou cancelamento."
        if self.agendamento_id:
            if self.agendamento.status != Agendamento.Status.AGENDADO:
                erros["agendamento"] = "Só dá para registrar o atendimento de um agendamento com status Agendado."
            elif not self.pk and Atendimento.objects.filter(agendamento_id=self.agendamento_id).exists():
                erros["agendamento"] = "Este agendamento já tem atendimento registrado."
            elif self.agendamento.inicio > (agora or timezone.now()):
                erros["agendamento"] = "O atendimento só pode ser registrado depois que o horário começar."
        if erros:
            raise ValidationError(erros)

    @classmethod
    @transaction.atomic
    def registrar(cls, agendamento, status, autor, justificativa="", agora=None):
        atendimento = cls(agendamento=agendamento, status=status, justificativa=justificativa, registrado_por=autor)
        atendimento.clean(agora)
        atendimento.save()
        if status == cls.Status.CANCELAMENTO:
            # UC11 A1: o agendamento sai da agenda, liberando sala, profissional e equipamentos
            agendamento.status = Agendamento.Status.CANCELADO
            agendamento.justificativa = justificativa
            agendamento.save(update_fields=["status", "justificativa"])
        return atendimento

    def __str__(self):
        return f"{self.agendamento.protocolo} - {self.get_status_display()}"
