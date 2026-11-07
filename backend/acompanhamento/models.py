"""Acompanhamento técnico do atleta.

AvaliacaoFisica  os testes de um dia (velocidade, força, resistência, agilidade), comparados com a anterior (UC12).
Exercicio        o catálogo de exercícios que os profissionais usam nos planos.
PlanoTreino      o treino prescrito para o atleta (UC13). Atualizar um plano cria uma nova versão:
                 a anterior fica inativa e guardada no histórico (UC13 A1).
ItemDoPlano      um exercício dentro do plano, com séries, repetições e carga.

Este app usa pessoas (Atleta, Profissional); nenhum outro app depende dele.
"""
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from pessoas.models import Atleta, Profissional

TESTES = ("velocidade", "forca", "resistencia", "agilidade")


def _resultado(help_text):
    return models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True, help_text=help_text)


class AvaliacaoFisica(models.Model):
    atleta = models.ForeignKey(Atleta, on_delete=models.PROTECT, related_name="avaliacoes")
    profissional = models.ForeignKey(Profissional, on_delete=models.PROTECT, related_name="avaliacoes")
    data = models.DateField(default=timezone.localdate)
    velocidade = _resultado("Ex.: tempo em segundos no sprint.")
    forca = _resultado("Ex.: carga em kg no teste de força.")
    resistencia = _resultado("Ex.: distância em metros ou VO2.")
    agilidade = _resultado("Ex.: tempo em segundos no teste de agilidade.")
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "avaliação física"
        verbose_name_plural = "avaliações físicas"
        ordering = ["-data", "-criado_em"]

    def clean(self):
        if all(getattr(self, teste) is None for teste in TESTES):
            raise ValidationError("Informe o resultado de pelo menos um teste.")

    def anterior(self):
        # a última avaliação do mesmo atleta antes desta
        qs = AvaliacaoFisica.objects.filter(atleta_id=self.atleta_id, data__lte=self.data).exclude(pk=self.pk)
        if self.pk:
            qs = qs.exclude(data=self.data, criado_em__gt=self.criado_em)
        return qs.order_by("-data", "-criado_em").first()

    def comparacao(self):
        # UC12: diferença de cada teste em relação à avaliação anterior; None na primeira (A1)
        anterior = self.anterior()
        if anterior is None:
            return None
        return {teste: (getattr(self, teste) - getattr(anterior, teste)
                        if getattr(self, teste) is not None and getattr(anterior, teste) is not None else None)
                for teste in TESTES}

    def __str__(self):
        return f"{self.atleta} - {self.data:%d/%m/%Y}"


class Exercicio(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "exercício"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class PlanoTreino(models.Model):
    atleta = models.ForeignKey(Atleta, on_delete=models.PROTECT, related_name="planos")
    profissional = models.ForeignKey(Profissional, on_delete=models.PROTECT, related_name="planos")
    objetivo = models.CharField(max_length=200)
    frequencia_semanal = models.PositiveSmallIntegerField(help_text="Quantas vezes por semana.")
    inicio = models.DateField(default=timezone.localdate, help_text="Início do ciclo.")
    fim = models.DateField(null=True, blank=True, help_text="Fim do ciclo (periodização).")
    observacoes = models.TextField(blank=True)
    exercicios = models.ManyToManyField(Exercicio, through="ItemDoPlano", related_name="planos")
    versao = models.PositiveIntegerField(default=1, editable=False)
    substitui = models.OneToOneField("self", null=True, blank=True, on_delete=models.PROTECT,
                                     related_name="substituido_por", editable=False)
    ativo = models.BooleanField(default=True, editable=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "plano de treino"
        verbose_name_plural = "planos de treino"
        ordering = ["-criado_em"]

    def clean(self):
        if self.inicio and self.fim and self.fim < self.inicio:
            raise ValidationError({"fim": "O fim do ciclo precisa ser depois do início."})
        if self.frequencia_semanal is not None and not 1 <= self.frequencia_semanal <= 7:
            raise ValidationError({"frequencia_semanal": "Informe de 1 a 7 vezes por semana."})

    @classmethod
    @transaction.atomic
    def prescrever(cls, *, atleta, profissional, itens, **dados):
        # UC13: itens = [{"exercicio": ..., "series": ..., "repeticoes": ..., "carga": ...}, ...]
        if not itens:
            raise ValidationError({"itens": "O plano precisa de pelo menos um exercício."})
        atual = cls.objects.select_for_update().filter(atleta=atleta, ativo=True).first()
        plano = cls(atleta=atleta, profissional=profissional, substitui=atual,
                    versao=atual.versao + 1 if atual else 1, **dados)
        plano.full_clean(exclude=["substitui"])
        if atual:
            # A1: o plano anterior sai de cena, mas continua no histórico
            atual.ativo = False
            atual.save(update_fields=["ativo"])
        plano.save()
        for ordem, item in enumerate(itens, start=1):
            ItemDoPlano.objects.create(plano=plano, ordem=ordem, **item)
        return plano

    def __str__(self):
        return f"{self.atleta} - {self.objetivo} (v{self.versao})"


class ItemDoPlano(models.Model):
    plano = models.ForeignKey(PlanoTreino, on_delete=models.CASCADE, related_name="itens")
    exercicio = models.ForeignKey(Exercicio, on_delete=models.PROTECT, related_name="itens")
    ordem = models.PositiveSmallIntegerField(default=1)
    series = models.PositiveSmallIntegerField()
    repeticoes = models.PositiveSmallIntegerField()
    carga = models.CharField(max_length=50, blank=True, help_text="Ex.: 20 kg, peso do corpo, elástico médio.")

    class Meta:
        verbose_name = "exercício do plano"
        verbose_name_plural = "exercícios do plano"
        ordering = ["ordem"]

    def __str__(self):
        return f"{self.exercicio} {self.series}x{self.repeticoes}"
