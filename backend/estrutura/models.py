"""Estrutura do CT: o que ele oferece e onde.

Especialidade  a área do profissional (Nutricionista, Personal Trainer, Instrutor de Pilates...).
Espaco         a sala diz quais especialidades atende (Consultórios 1 e 2 -> Nutricionista).
               Cadastrou uma nutricionista: ela já pode usar essas salas, sem ligar uma por uma.
Servico        a modalidade: duração e vagas. Pode restringir salas como exceção.
Configuracao   ajustes que o admin muda pelo painel (prazo para confirmar vaga da lista de espera).

Este app não depende de nenhum outro: pessoas e agenda é que dependem dele.
"""
from datetime import timedelta

from django.db import models
from django.utils import timezone


class Especialidade(models.Model):
    # Tabela (e não lista fixa no código): o CT cadastra novas especialidades pelo painel, ex.: Psicólogo.
    nome = models.CharField(max_length=60, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Espaco(models.Model):
    # Salas, consultórios, studios, piscinas, tatames...
    nome = models.CharField(max_length=100)
    especialidades = models.ManyToManyField(
        Especialidade, blank=True, related_name="espacos",
        help_text="Quais especialidades usam esta sala. Ex.: Consultório 1 atende Nutricionista.")
    capacidade = models.PositiveIntegerField(
        default=1, help_text="Quantos atendimentos ou turmas cabem ao mesmo tempo nesta sala.")
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "espaço"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Servico(models.Model):
    # A modalidade: "Treino funcional" (individual, 60 min), "Pilates" (grupo de 10, 50 min)...
    nome = models.CharField(max_length=100)
    especialidade = models.ForeignKey(Especialidade, on_delete=models.PROTECT, related_name="servicos")
    duracao_minutos = models.PositiveIntegerField(default=60, help_text="O fim do atendimento é calculado por aqui.")
    vagas = models.PositiveIntegerField(
        default=1, help_text="Atletas por horário. 1 = individual (ex.: personal). "
                             "Mais de 1 = aula em grupo, marcada pela grade de aulas (ex.: Pilates com 10).")
    espacos = models.ManyToManyField(
        Espaco, blank=True, related_name="servicos",
        help_text="Exceção opcional: só nestas salas. Em branco: as salas da especialidade.")
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "serviço"
        ordering = ["nome"]

    @property
    def em_grupo(self):
        return self.vagas > 1

    @property
    def duracao(self):
        return timedelta(minutes=self.duracao_minutos)

    def espacos_possiveis(self):
        if self.pk and self.espacos.exists():
            return self.espacos.filter(ativo=True)
        return Espaco.objects.filter(ativo=True, especialidades=self.especialidade)

    def __str__(self):
        return self.nome


class Configuracao(models.Model):
    # Uma linha só. Use Configuracao.atual() para ler.
    prazo_confirmacao_horas = models.PositiveIntegerField(
        default=2, help_text="Quanto tempo quem foi chamado da lista de espera tem para confirmar a vaga.")
    confirmar_ate_minutos_antes = models.PositiveIntegerField(
        default=30, help_text="Se o atendimento estiver perto, o prazo acaba este tanto de minutos antes de ele começar.")

    class Meta:
        verbose_name = "configuração"
        verbose_name_plural = "configuração"

    @classmethod
    def atual(cls):
        return cls.objects.get_or_create(pk=1)[0]

    def prazo_para_confirmar(self, inicio_do_atendimento, agora=None):
        # o menor entre "agora + prazo" e "X minutos antes do início"
        agora = agora or timezone.now()
        return min(agora + timedelta(hours=self.prazo_confirmacao_horas),
                   inicio_do_atendimento - timedelta(minutes=self.confirmar_ate_minutos_antes))

    def __str__(self):
        return "Configuração do CT"
