# PKZ LAB — Back-end

[![Testes](https://github.com/Projetos-de-Extensao/PECDII_26.2_8001_II/actions/workflows/testes.yml/badge.svg)](https://github.com/Projetos-de-Extensao/PECDII_26.2_8001_II/actions/workflows/testes.yml)

**Disciplina:** IBM8936 (Projeto de Extensão) · **Grupo II:** Gabriel de Souza, Vitor Luiz Zanconato, Vitor Magalhães e Filipe Andrade

## Sobre

Back-end (API REST) do **PKZ LAB**, um centro de treinamento de performance na Barra da Tijuca (Rio de Janeiro). Hoje o acompanhamento dos atletas e a agenda do CT ficam espalhados em planilhas e mensagens. O sistema centraliza o cadastro de atletas e da equipe e o agendamento de atendimentos, respeitando a LGPD e o ECA.

Documentação completa (requisitos, casos de uso, diagramas, iterações e transição): https://projetos-de-extensao.github.io/PECDII_26.2_8001_II/

### O que já funciona

- **Login e cadastro (UC01 a UC03):** login por e-mail com token JWT, autocadastro de atleta e responsável legal (menor de 18 anos exige responsável) com registro do consentimento LGPD e recuperação de senha por link com validade de 1 hora. A equipe do CT (funcionário com matrícula e papéis Profissional, Recepção e Administrador) é cadastrada pelo painel do administrador.
- **Estrutura do CT (UC17 e UC18):** especialidades, espaços (ligados às especialidades), serviços (duração e vagas) e equipamentos (com quantidade).
- **Disponibilidade (UC05 e UC07):** turnos de atendimento de cada profissional, bloqueios de profissional, sala ou equipamento e consulta dos horários livres de um serviço num dia.
- **Agendamento (UC06, UC08 a UC10):** o profissional precisa atender a especialidade do serviço, estar no turno e livre, e a sala precisa ser usada pelo serviço. Cancelar exige justificativa. Reagendar guarda o original como "Substituído". Equipamentos são reservados por quantidade. Agendamento não é apagado.
- **Aulas em grupo e lista de espera (UC19 e UC21):** a administração monta a grade de aulas; entrar numa aula é agendar nela. Com a turma cheia, o atleta entra na lista de espera e, quando abre vaga, recebe a oferta com prazo para confirmar.
- **Avisos (UC20):** cancelamento, vaga oferecida, mudança de aula e lembrete 24 horas antes viram aviso no sistema e e-mail. O comando `python manage.py rotinas_da_agenda` (no servidor, a cada 5 minutos) vence as ofertas da lista de espera e envia os lembretes.
- **Acompanhamento técnico (UC11 a UC15):** registro de presença ou falta, avaliações físicas com a comparação com a anterior, planos de treino versionados, evolução do atleta num período e relatório de desempenho.
- **Visibilidade:** atleta, responsável, profissional, recepção e administração veem cada um só a sua parte da agenda. Avaliações, planos e evolução são dados sensíveis (RNF03): só a equipe técnica, o próprio atleta e o responsável dele têm acesso.

### Fora do escopo desta entrega

- Integração com o sistema financeiro (BS16).
- Front-end: a entrega é a API, testada pelo Swagger.
- Envio real de e-mail: sem servidor SMTP configurado, o Django mostra os e-mails no log do servidor. Basta configurar as variáveis `EMAIL_*` para enviar de verdade.

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

Para chamar a API, faça login em `POST /api/token/` com `email` e `password` e envie o token recebido no cabeçalho `Authorization: Bearer <token>`. No Swagger, use o botão **Authorize**. O login por sessão do Django (pelo `/admin/` ou por `/api/auth/login/`) também funciona.

### Dados de exemplo

Para apresentar o sistema sem cadastrar tudo à mão:

```bash
cd backend
python manage.py popular_demo
```

O comando cria salas, serviços, equipamentos, a equipe com os turnos de atendimento, atletas, agendamentos passados (com presença ou falta) e futuros, uma aula de pilates com alunos, avaliações físicas e planos de treino. Se os dados já existirem, ele não faz nada.

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
| Login, cadastro e senha | `/api/token/` (+ `/refresh/`), `/api/cadastro/`, `/api/senha/recuperar/`, `/api/senha/redefinir/` |
| Especialidades, espaços, serviços, equipamentos | `/api/especialidades/`, `/api/espacos/`, `/api/servicos/`, `/api/equipamentos/` |
| Profissionais (só consulta) | `/api/profissionais/` |
| Atletas e responsáveis | `/api/atletas/`, `/api/responsaveis/` |
| Disponibilidade | `/api/disponibilidades/`, `/api/bloqueios/`, `/api/horarios-livres/` |
| Agendamentos | `/api/agendamentos/` (+ `/{id}/cancelar/`, `/{id}/reagendar/` e `/{id}/atendimento/`) |
| Aulas em grupo e lista de espera | `/api/aulas/`, `/api/lista-espera/` |
| Atendimentos | `/api/atendimentos/` |
| Avaliações, exercícios e planos | `/api/avaliacoes/`, `/api/exercicios/`, `/api/planos/` |
| Evolução e relatório | `/api/atletas/{id}/evolucao/`, `/api/relatorios/desempenho/` |
| Avisos | `/api/avisos/` (+ `/{id}/lido/`) |

Exemplos de chamadas e a lista completa estão na [página da API](https://projetos-de-extensao.github.io/PECDII_26.2_8001_II/API/).


## Organização do código

| App | O que tem |
| -- | -- |
| `estrutura` | Especialidade, Espaço, Serviço, Equipamento, Configuração |
| `pessoas` | Funcionário, Papel (abstrata), Profissional, Recepção, Administrador, Atleta, Responsável, Consentimento LGPD, login e cadastro pela API |
| `agenda` | Aula, Agendamento, Lista de espera, Aviso, Disponibilidade, Bloqueio, Atendimento |
| `acompanhamento` | Avaliação física, Exercício, Plano de treino (com os itens), evolução e relatório |

A dependência vai num sentido só: `acompanhamento` usa `agenda`, que usa `pessoas`, que usa `estrutura`.

## Licença

MIT (veja o arquivo `LICENSE`).