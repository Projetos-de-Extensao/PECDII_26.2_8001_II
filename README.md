# PKZ LAB — Back-end

[![Testes](https://github.com/Projetos-de-Extensao/PECDII_26.2_8001_II/actions/workflows/testes.yml/badge.svg)](https://github.com/Projetos-de-Extensao/PECDII_26.2_8001_II/actions/workflows/testes.yml)

**Disciplina:** IBM8936 (Projeto de Extensão) · **Grupo II:** Gabriel de Souza, Vitor Luiz Zanconato, Vitor Magalhães e Filipe Andrade

## Sobre

Back-end (API REST) do **PKZ LAB**, um centro de treinamento de performance na Barra da Tijuca (Rio de Janeiro). Hoje o acompanhamento dos atletas e a agenda do CT ficam espalhados em planilhas e mensagens. O sistema centraliza o cadastro de atletas e da equipe e o agendamento de atendimentos, respeitando a LGPD e o ECA.

Documentação completa (requisitos, casos de uso, diagramas, iterações e transição): https://projetos-de-extensao.github.io/PECDII_26.2_8001_II/

### O que já funciona

- **Cadastros:** atleta e responsável legal (menor de 18 anos exige responsável), com login por e-mail e registro do consentimento LGPD. A equipe do CT (funcionário com matrícula e papéis Profissional, Recepção e Administrador) é cadastrada pelo painel do administrador.
- **Estrutura do CT:** especialidades, espaços (ligados às especialidades), serviços (duração e vagas) e equipamentos (com quantidade).
- **Agendamento:** o profissional precisa atender a especialidade do serviço e a sala precisa ser usada pelo serviço. Cancelar exige justificativa. Reagendar guarda o original como "Substituído". Equipamentos são reservados por quantidade. Agendamento não é apagado.
- **Visibilidade:** atleta, responsável, profissional e recepção/administração veem cada um só a sua parte da agenda.
- **Avisos:** o profissional é avisado quando um atendimento é cancelado, e cada pessoa lê só os próprios avisos.

### Ainda não implementado (previsto na documentação)

Disponibilidade e bloqueios, grade de aulas em grupo, lista de espera, lembretes automáticos, registro de atendimento, avaliações físicas, planos de treino, relatórios e integração com o sistema financeiro.

## Instalação

**Linguagem e frameworks:** Python 3.12, Django 4.2, Django REST Framework e drf-spectacular.
**Banco:** SQLite (arquivo `backend/db.sqlite3`, criado pelo `migrate`).

```bash
python3 -m venv venv
source venv/bin/activate            # no Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
cd backend
python manage.py migrate
python manage.py createsuperuser    # primeiro administrador
python manage.py runserver
```

- Painel do administrador: http://127.0.0.1:8000/admin/
- Documentação interativa da API (Swagger): http://127.0.0.1:8000/api/docs/ (também `/api/redoc/` e `/api/schema/`)

A API usa o login por sessão do Django: entre pelo `/admin/` ou por `/api/auth/login/` antes de chamar os endpoints.

### Dados de exemplo

Para apresentar o sistema sem cadastrar tudo à mão:

```bash
cd backend
python manage.py popular_demo
```

O comando cria salas, serviços, equipamentos, a equipe com os turnos de atendimento, atletas, agendamentos passados (com presença ou falta) e futuros, uma aula de pilates com inscritos, avaliações físicas e planos de treino. Se os dados já existirem, ele não faz nada.

**Todos os logins de exemplo usam a senha `senha12345`** (só para demonstração, não use em produção):

| Login | Papel |
|---|---|
| `carla@pkzlab.demo` | administração e fisioterapeuta (entra no `/admin/`) |
| `rita@pkzlab.demo` | recepção |
| `nina@pkzlab.demo` | nutricionista |
| `teo@pkzlab.demo` | personal trainer |
| `paulo@pkzlab.demo` | preparador físico |
| `lia@pkzlab.demo` | instrutora de pilates |
| `joao@pkzlab.demo`, `maria@pkzlab.demo`, `pedro@pkzlab.demo` | atletas |
| `ana@pkzlab.demo` | responsável pelo atleta menor `lucas@pkzlab.demo` |

### Testes

```bash
cd backend
python manage.py test
```

O GitHub Actions roda os mesmos testes a cada push e pull request (`.github/workflows/testes.yml`). O badge no topo deste README mostra se a última execução passou.

### Rodar a documentação localmente

```bash
pip install -r requirements.txt     # na raiz do repositório
mkdocs serve
```

A documentação é publicada automaticamente no GitHub Pages a cada push na `main` (`.github/workflows/deploy.yml`).

## Endpoints

| Recurso | Rota |
| -- | -- |
| Especialidades, espaços, serviços, equipamentos | `/api/especialidades/`, `/api/espacos/`, `/api/servicos/`, `/api/equipamentos/` |
| Profissionais (só consulta) | `/api/profissionais/` |
| Atletas e responsáveis | `/api/atletas/`, `/api/responsaveis/` |
| Agendamentos | `/api/agendamentos/` (+ `/{id}/cancelar/` e `/{id}/reagendar/`) |
| Avisos | `/api/avisos/` (+ `/{id}/lido/`) |
Exemplos de chamadas e a lista completa estão na [página da API](https://projetos-de-extensao.github.io/PECDII_26.2_8001_II/API/).


## Organização do código

| App | O que tem |
| -- | -- |
| `estrutura` | Especialidade, Espaço, Serviço, Equipamento, Configuração |
| `pessoas` | Funcionário, Papel (abstrata), Profissional, Recepção, Administrador, Atleta, Responsável, Consentimento LGPD |
| `agenda` | Agendamento e Aviso |

A dependência vai num sentido só: `agenda` usa `pessoas` e `estrutura`; `pessoas` usa `estrutura`.

## Licença

MIT (veja o arquivo `LICENSE`).