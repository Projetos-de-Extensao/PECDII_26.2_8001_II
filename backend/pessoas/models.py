"""Pessoas do CT: quem é quem.

Funcionario        um login e uma matrícula por pessoa da equipe. Só o administrador cadastra (UC04).
Papel              abstrata: o que todo papel tem em comum. Não vira tabela.
Profissional       atende as especialidades marcadas (Personal Trainer, Fisioterapeuta...).
Recepcao           agenda em nome de atletas e profissionais.
Administrador      cadastra a equipe e configura o CT.
Responsavel        responsável legal de um ou mais atletas menores de idade (UC02).
Atleta             cliente do CT; login 1 para 1 e data de nascimento (UC02).
ConsentimentoLGPD  registro do aceite dos termos de uso e privacidade (UC02).

Os papéis se acumulam: a coordenadora que também atende como fisioterapeuta tem os dois,
com a mesma matrícula. O Usuário do diagrama é o login do próprio Django (auth.User).
"""
from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from estrutura.models import Especialidade


class Funcionario(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="funcionario")
    matricula = models.CharField(max_length=20, unique=True)
    data_admissao = models.DateField()

    class Meta:
        verbose_name = "funcionário"
        ordering = ["usuario__first_name"]
        permissions = [
            ("ver_todas_as_pessoas", "Pode consultar todos os cadastros de pessoas"),
            ("agendar_para_qualquer_atleta", "Pode agendar para qualquer atleta"),
            ("registrar_dados_tecnicos", "Pode registrar dados da equipe técnica"),
            ("gerenciar_agenda", "Pode gerenciar a agenda de toda a equipe"),
            ("gerenciar_cadastros", "Pode gerenciar cadastros de pessoas"),
            ("gerenciar_estrutura", "Pode gerenciar a estrutura e a equipe"),
            ("administrar_sistema", "Pode administrar todas as funções do sistema"),
        ]

    @property
    def nome(self):
        return self.usuario.get_full_name() or self.usuario.username

    @property
    def ativo(self):
        # desligamento (UC04 A2) é inativar a conta: o histórico continua
        return self.usuario.is_active

    def __str__(self):
        return f"{self.nome} ({self.matricula})"


class Papel(models.Model):
    # funcionario "1" -- "1..3" Papel: cada papel no máximo uma vez por funcionário
    funcionario = models.OneToOneField(Funcionario, on_delete=models.PROTECT, related_name="%(class)s")
    ativo = models.BooleanField(default=True, help_text="Desmarque para tirar só este papel (UC04 A4).")

    class Meta:
        abstract = True

    @property
    def nome(self):
        return self.funcionario.nome

    def __str__(self):
        return self.nome


class Profissional(Papel):
    especialidades = models.ManyToManyField(Especialidade, related_name="profissionais")

    class Meta:
        verbose_name_plural = "profissionais"

    @classmethod
    def ativos(cls):
        # só quem pode aparecer em novos agendamentos (UC06 A4)
        return cls.objects.filter(ativo=True, funcionario__usuario__is_active=True)

    def atende(self, especialidade):
        return self.especialidades.filter(pk=especialidade.pk).exists()


class Recepcao(Papel):
    class Meta:
        verbose_name = "recepção"
        verbose_name_plural = "recepção"


class Administrador(Papel):
    class Meta:
        verbose_name_plural = "administradores"


class Responsavel(models.Model):
    # Responsável legal pelo atleta menor (ECA). Tem login: cadastra, agenda, cancela e
    # acompanha pelo dependente (UC02, UC06, UC08, UC09, UC10, UC14). Nome e e-mail vêm do login.
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="responsavel")
    cpf = models.CharField(max_length=14, blank=True)
    telefone = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = "responsável"
        verbose_name_plural = "responsáveis"
        ordering = ["usuario__first_name"]

    @property
    def nome(self):
        return self.usuario.get_full_name() or self.usuario.username

    @property
    def email(self):
        return self.usuario.email

    def __str__(self):
        return self.nome


class Atleta(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="atleta")
    data_nascimento = models.DateField()
    responsavel = models.ForeignKey(
        Responsavel,
        on_delete=models.PROTECT,
        related_name="atletas",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "atleta"
        verbose_name_plural = "atletas"
        ordering = ["usuario__first_name"]

    @property
    def nome(self):
        return self.usuario.get_full_name() or self.usuario.username

    @property
    def email(self):
        return self.usuario.email

    @property
    def idade(self):
        hoje = date.today()
        nasc = self.data_nascimento
        return hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))

    @property
    def menor_de_idade(self):
        return self.idade < 18
    def clean(self):
        # ECA: menor de 18 anos só com responsável. Fica na classe para valer em qualquer porta
        # (cadastro, painel do admin, API), e não só no cadastros.py.
        if self.data_nascimento and self.data_nascimento > date.today():
            raise ValidationError({"data_nascimento": "A data de nascimento não pode ser no futuro."})
        if self.data_nascimento and self.menor_de_idade and not self.responsavel_id:
            raise ValidationError({"responsavel": "Atleta menor de idade exige um responsável."})

    def save(self, *args, **kwargs):
        self.full_clean()  # roda o clean() em toda gravação
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome


class ConsentimentoLGPD(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="consentimentos_lgpd",
    )
    data = models.DateTimeField(auto_now_add=True)
    versao_termos = models.CharField(max_length=20, default="1.0")

    class Meta:
        verbose_name = "consentimento LGPD"
        verbose_name_plural = "consentimentos LGPD"
        ordering = ["-data"]

    def __str__(self):
        return f"{self.usuario.username} (v{self.versao_termos})"