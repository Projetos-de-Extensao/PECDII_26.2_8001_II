"""Pessoas do CT: quem é quem.

Funcionario    um login e uma matrícula por pessoa da equipe. Só o administrador cadastra (UC04).
Papel          abstrata: o que todo papel tem em comum. Não vira tabela.
Profissional   atende as especialidades marcadas (Personal Trainer, Fisioterapeuta...).
Recepcao       agenda em nome de atletas e profissionais.
Administrador  cadastra a equipe e configura o CT.

Os papéis se acumulam: a coordenadora que também atende como fisioterapeuta tem os dois,
com a mesma matrícula. O Usuário do diagrama é o login do próprio Django (auth.User).
"""
from django.conf import settings
from django.db import models

from estrutura.models import Especialidade


class Funcionario(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="funcionario")
    matricula = models.CharField(max_length=20, unique=True)
    data_admissao = models.DateField()

    class Meta:
        verbose_name = "funcionário"
        ordering = ["usuario__first_name"]

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
