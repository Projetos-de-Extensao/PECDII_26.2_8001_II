"""Dados de exemplo para apresentar o sistema: python manage.py popular_demo"""

from datetime import date, datetime, time, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.test.utils import override_settings
from django.utils import timezone

from acompanhamento.models import AvaliacaoFisica, Exercicio, PlanoTreino
from agenda.models import Agendamento, Atendimento, Aula, Aviso, Bloqueio, Disponibilidade
from estrutura.models import Equipamento, Espaco, Especialidade, Servico
from pessoas.cadastros import cadastrar_atleta, cadastrar_funcionario, cadastrar_responsavel
from pessoas.models import Administrador, Profissional, Recepcao

SENHA = "senha12345"
DOMINIO = "pkzlab.demo"


def email(login):
    return f"{login}@{DOMINIO}"


def dias_uteis(a_partir_de, quantos, passo):
    # os próximos (passo=1) ou os últimos (passo=-1) dias de segunda a sexta
    dias, dia = [], a_partir_de
    while len(dias) < quantos:
        dia += timedelta(days=passo)
        if dia.weekday() < 5:
            dias.append(dia)
    return dias


def as_(dia, hora, minuto=0):
    return timezone.make_aware(datetime.combine(dia, time(hora, minuto)))


class Command(BaseCommand):
    help = (f"Cria dados de exemplo (estrutura, equipe, atletas, agenda e acompanhamento) para apresentar "
            f"o sistema. Todos os logins usam a senha '{SENHA}'. Não faz nada se os dados já existirem.")

    def handle(self, *args, **options):
        if User.objects.filter(username=email("carla")).exists():
            self.stdout.write(self.style.WARNING("Os dados de exemplo já existem; nada foi criado."))
            return
        # os avisos mandam e-mail; os endereços de exemplo não existem, então nada sai daqui
        with override_settings(EMAIL_BACKEND="django.core.mail.backends.dummy.EmailBackend"), transaction.atomic():
            self.popular()
        self.resumo()

    # ---------------------------------------------------------------- estrutura
    def estrutura(self):
        esp = {e.nome: e for e in Especialidade.objects.all()}
        esp["Instrutor de Pilates"], _ = Especialidade.objects.get_or_create(nome="Instrutor de Pilates")

        def espaco(nome, capacidade, *especialidades):
            e, _ = Espaco.objects.get_or_create(nome=nome, defaults={"capacidade": capacidade})
            e.especialidades.add(*[esp[n] for n in especialidades])
            return e

        self.consultorio1 = espaco("Consultório 1", 1, "Nutricionista", "Fisioterapeuta")
        self.consultorio2 = espaco("Consultório 2", 1, "Nutricionista")
        self.musculacao = espaco("Sala de Musculação", 4, "Personal Trainer", "Preparador Físico")
        self.studio = espaco("Studio de Pilates", 1, "Instrutor de Pilates")

        def servico(nome, especialidade, minutos, vagas=1, *espacos):
            s, _ = Servico.objects.get_or_create(nome=nome, defaults={
                "especialidade": esp[especialidade], "duracao_minutos": minutos, "vagas": vagas})
            s.espacos.add(*espacos)
            return s

        self.consulta = servico("Consulta nutricional", "Nutricionista", 50)
        self.fisio = servico("Sessão de fisioterapia", "Fisioterapeuta", 50)
        self.treino = servico("Treino com personal", "Personal Trainer", 60)
        self.avaliacao = servico("Avaliação física", "Preparador Físico", 60)
        self.pilates = servico("Pilates em grupo", "Instrutor de Pilates", 50, 8, self.studio)

        for nome, quantidade in (("Esteira", 2), ("Bicicleta ergométrica", 1), ("Kit de elásticos", 5)):
            Equipamento.objects.get_or_create(nome=nome, defaults={"quantidade": quantidade})
        self.esp = esp

    # ---------------------------------------------------------------- pessoas
    def funcionario(self, login, nome, sobrenome, matricula):
        return cadastrar_funcionario(email=email(login), nome=nome, sobrenome=sobrenome, senha_provisoria=SENHA,
                                     matricula=matricula, data_admissao=date(2026, 2, 2))

    def profissional(self, funcionario, *especialidades):
        p = Profissional.objects.create(funcionario=funcionario)
        p.especialidades.set([self.esp[n] for n in especialidades])
        for dia in range(5):  # segunda a sexta, manhã e tarde
            Disponibilidade.objects.create(profissional=p, dia_da_semana=dia, hora_inicio=time(8), hora_fim=time(12))
            Disponibilidade.objects.create(profissional=p, dia_da_semana=dia, hora_inicio=time(14), hora_fim=time(18))
        return p

    def equipe(self):
        carla = self.funcionario("carla", "Carla", "Mendes", "D001")
        carla.usuario.is_staff = True  # entra no /admin/
        carla.usuario.save()
        Administrador.objects.create(funcionario=carla)
        # a mesma pessoa pode acumular papéis: a Carla também atende como fisioterapeuta
        self.carla = self.profissional(carla, "Fisioterapeuta")
        Recepcao.objects.create(funcionario=self.funcionario("rita", "Rita", "Souza", "D002"))
        self.nina = self.profissional(self.funcionario("nina", "Nina", "Costa", "D003"), "Nutricionista")
        self.teo = self.profissional(self.funcionario("teo", "Teo", "Almeida", "D004"), "Personal Trainer")
        self.paulo = self.profissional(self.funcionario("paulo", "Paulo", "Lima", "D005"), "Preparador Físico")
        self.lia = self.profissional(self.funcionario("lia", "Lia", "Rocha", "D006"), "Instrutor de Pilates")

    def atletas(self):
        def atleta(login, nome, sobrenome, nascimento, responsavel=None):
            return cadastrar_atleta(email=email(login), nome=nome, sobrenome=sobrenome, senha=SENHA,
                                    data_nascimento=nascimento, aceitou_termos=True, responsavel=responsavel)

        self.joao = atleta("joao", "João", "Pereira", date(1998, 4, 12))
        self.maria = atleta("maria", "Maria", "Oliveira", date(2001, 9, 3))
        self.pedro = atleta("pedro", "Pedro", "Santos", date(1995, 1, 20))
        self.ana = cadastrar_responsavel(email=email("ana"), nome="Ana", sobrenome="Ferreira", senha=SENHA,
                                         telefone="(21) 99999-0000", aceitou_termos=True)
        # menor de idade: precisa do responsável (a Ana entra e vê a agenda dele)
        self.lucas = atleta("lucas", "Lucas", "Ferreira", date(2012, 6, 15), responsavel=self.ana)

    # ---------------------------------------------------------------- agenda
    def agendar(self, atleta, servico, profissional, espaco, inicio, agora=None):
        a = Agendamento(atleta=atleta, servico=servico, profissional=profissional, espaco=espaco, inicio=inicio)
        a.clean(agora)  # as mesmas regras da API
        a.save()
        return a

    def agenda(self):
        hoje = timezone.localdate()
        ontem, anteontem, semana_passada, antes = dias_uteis(hoje, 4, -1)
        amanha, depois, mais_um = dias_uteis(hoje, 3, 1)
        registra = self.carla.funcionario.usuario

        # o que já aconteceu, com presença ou falta registrada
        passados = [
            (self.joao, self.avaliacao, self.paulo, self.musculacao, as_(antes, 9), None),
            (self.joao, self.consulta, self.nina, self.consultorio1, as_(semana_passada, 10), None),
            (self.maria, self.treino, self.teo, self.musculacao, as_(semana_passada, 9), None),
            (self.pedro, self.fisio, self.carla, self.consultorio1, as_(anteontem, 14), "Não avisou."),
            (self.lucas, self.treino, self.teo, self.musculacao, as_(anteontem, 15), None),
            (self.joao, self.treino, self.teo, self.musculacao, as_(ontem, 9), None),
            (self.maria, self.avaliacao, self.paulo, self.musculacao, as_(ontem, 10), None),
        ]
        for atleta, servico, profissional, espaco, inicio, falta in passados:
            # validado como se tivesse sido marcado na semana anterior (não se marca no passado)
            ag = self.agendar(atleta, servico, profissional, espaco, inicio, agora=inicio - timedelta(days=7))
            status = Atendimento.Status.FALTA if falta else Atendimento.Status.PRESENCA
            Atendimento.registrar(ag, status, registra, falta or "")

        # o que ainda vai acontecer
        self.agendar(self.joao, self.treino, self.teo, self.musculacao, as_(amanha, 9))
        self.agendar(self.maria, self.consulta, self.nina, self.consultorio1, as_(amanha, 10))
        self.agendar(self.pedro, self.fisio, self.carla, self.consultorio1, as_(depois, 9))
        self.agendar(self.lucas, self.avaliacao, self.paulo, self.musculacao, as_(depois, 14))
        cancelado = self.agendar(self.pedro, self.treino, self.teo, self.musculacao, as_(mais_um, 9))
        cancelado.cancelar("Viagem a trabalho.")

        # aula em grupo de pilates com dois alunos (UC06 A2: o atleta escolhe a aula e vira um agendamento)
        aula = Aula(servico=self.pilates, profissional=self.lia, espaco=self.studio, dia=mais_um,
                    hora_inicio=time(15))
        aula.clean()
        aula.save()
        for atleta in (self.maria, self.joao):
            no_grupo = Agendamento(atleta=atleta, servico=aula.servico, profissional=aula.profissional,
                                   espaco=aula.espaco, aula=aula, inicio=aula.inicio)
            no_grupo.clean()
            no_grupo.save()

        Bloqueio.objects.create(espaco=self.consultorio2, inicio=as_(amanha, 14), fim=as_(amanha, 18),
                                motivo="Manutenção do ar-condicionado.")

    # ---------------------------------------------------------------- acompanhamento
    def acompanhamento(self):
        hoje = timezone.localdate()
        ex = {nome: Exercicio.objects.get_or_create(nome=nome)[0] for nome in (
            "Agachamento", "Supino", "Prancha", "Corrida intervalada", "Levantamento terra")}

        # três avaliações do João para a evolução ter o que mostrar
        for dias, velocidade, forca, resistencia, agilidade in ((60, 7.4, 80, 2100, 11.2),
                                                                (30, 7.1, 88, 2350, 10.8),
                                                                (3, 6.9, 95, 2500, 10.5)):
            AvaliacaoFisica.objects.create(atleta=self.joao, profissional=self.paulo, data=hoje - timedelta(dias),
                                           velocidade=velocidade, forca=forca, resistencia=resistencia,
                                           agilidade=agilidade)
        AvaliacaoFisica.objects.create(atleta=self.maria, profissional=self.paulo, data=hoje - timedelta(5),
                                       velocidade=8.2, resistencia=1900, observacoes="Primeira avaliação.")

        def item(nome, series, repeticoes, carga=""):
            return {"exercicio": ex[nome], "series": series, "repeticoes": repeticoes, "carga": carga}

        PlanoTreino.prescrever(atleta=self.joao, profissional=self.teo, objetivo="Ganho de força",
                               frequencia_semanal=3, inicio=hoje - timedelta(60),
                               itens=[item("Agachamento", 3, 12, "40 kg"), item("Supino", 3, 12, "30 kg")])
        # a nova versão substitui a anterior, que fica no histórico
        PlanoTreino.prescrever(atleta=self.joao, profissional=self.teo, objetivo="Ganho de força",
                               frequencia_semanal=4, inicio=hoje - timedelta(30),
                               itens=[item("Agachamento", 4, 10, "50 kg"), item("Supino", 4, 10, "36 kg"),
                                      item("Levantamento terra", 3, 8, "60 kg")])
        PlanoTreino.prescrever(atleta=self.lucas, profissional=self.teo, objetivo="Condicionamento",
                               frequencia_semanal=2,
                               itens=[item("Corrida intervalada", 4, 1, "4 min"),
                                      item("Prancha", 3, 1, "30 s")])

    def popular(self):
        self.estrutura()
        self.equipe()
        self.atletas()
        self.agenda()
        self.acompanhamento()
        for usuario in User.objects.filter(username__endswith=f"@{DOMINIO}"):
            Aviso.avisar(usuario, "Bem-vindo ao PKZ LAB! Estes são dados de exemplo para conhecer o sistema.")

    def resumo(self):
        self.stdout.write(self.style.SUCCESS("Dados de exemplo criados."))
        self.stdout.write(f"Todos os logins usam a senha: {SENHA}")
        for login, papel in (("carla", "administração e fisioterapeuta (entra no /admin/)"),
                             ("rita", "recepção"), ("nina", "nutricionista"), ("teo", "personal trainer"),
                             ("paulo", "preparador físico"), ("lia", "instrutora de pilates"),
                             ("joao", "atleta"), ("maria", "atleta"), ("pedro", "atleta"),
                             ("ana", "responsável pelo Lucas"), ("lucas", "atleta menor de idade")):
            self.stdout.write(f"  {email(login):<20} {papel}")
