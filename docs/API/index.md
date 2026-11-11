---
id: api
title: API
---

## Introdução

<p align="justify">
O back-end do PKZ LAB é uma API REST em Django (Django REST Framework). A documentação interativa é gerada automaticamente pelo drf-spectacular a partir do código, então ela está sempre igual ao que o servidor faz: nela é possível ver todos os campos de cada recurso e testar as chamadas.
</p>

## Documentação interativa (Swagger)

| O que | Servidor de demonstração | Local |
| -- | -- | -- |
| Swagger (testar as chamadas) | [http://3.148.241.152:8000/api/docs/](http://3.148.241.152:8000/api/docs/) | http://127.0.0.1:8000/api/docs/ |
| ReDoc (leitura) | [http://3.148.241.152:8000/api/redoc/](http://3.148.241.152:8000/api/redoc/) | http://127.0.0.1:8000/api/redoc/ |
| Esquema OpenAPI | [http://3.148.241.152:8000/api/schema/](http://3.148.241.152:8000/api/schema/) | http://127.0.0.1:8000/api/schema/ |

A documentação abre sem login, mas os dados exigem login (veja abaixo). O servidor de demonstração pode estar desligado fora do período de avaliação.

## Autenticação

A API usa o **login por sessão do Django**, o mesmo do painel do administrador. Para testar no Swagger, entre antes em `/admin/` ou em `/api/auth/login/` e volte para `/api/docs/`: o navegador já envia o cookie de sessão.

Sem login, qualquer endpoint responde `403`, com duas exceções que são abertas para o autocadastro (UC02): `POST /api/atletas/` e `POST /api/responsaveis/`.

## Recursos

| Recurso | Rota | Quem altera | Caso de uso |
| -- | -- | -- | -- |
| Especialidades | `/api/especialidades/` | Equipe administrativa | UC18 |
| Espaços | `/api/espacos/` | Equipe administrativa | UC17 |
| Serviços | `/api/servicos/` (inativar com agenda futura pede `confirmar=true`) | Equipe administrativa | UC18 |
| Equipamentos | `/api/equipamentos/` | Equipe administrativa | UC17 |
| Profissionais | `/api/profissionais/` | Só consulta (cadastro pelo painel) | UC04 |
| Atletas | `/api/atletas/` | Qualquer visitante cria; cada um vê o que lhe cabe | UC02 |
| Responsáveis | `/api/responsaveis/` | Qualquer visitante cria | UC02 |
| Agendamentos | `/api/agendamentos/` (+ `/{id}/cancelar/`, `/{id}/reagendar/`, `/{id}/atendimento/`; filtros `status`, `de`, `ate`, `profissional`, `espaco`) | Atleta, responsável, equipe | UC06, UC08, UC09, UC10, UC11 |
| Horários livres | `/api/horarios-livres/?servico=&dia=` | Só consulta | UC06, UC07 |
| Grade de aulas | `/api/aulas/` (`suspensa` = professor ou sala bloqueados naquele dia) | Equipe administrativa | UC21 |
| Lista de espera | `/api/lista-espera/` (+ `/{id}/confirmar/`, `/{id}/recusar/`, `/{id}/sair/`) | Atleta, responsável, equipe | UC19 |
| Atendimentos | `/api/atendimentos/` | Só consulta (registro pelo agendamento) | UC11 |
| Disponibilidade | `/api/disponibilidades/` | O próprio profissional e a administração | UC05 |
| Bloqueios | `/api/bloqueios/` | Equipe administrativa | UC05, UC17 |
| Avaliações físicas | `/api/avaliacoes/` | Equipe técnica | UC12 |
| Exercícios e planos de treino | `/api/exercicios/`, `/api/planos/` | Equipe técnica | UC13 |
| Evolução e relatório | `/api/atletas/{id}/evolucao/`, `/api/relatorios/desempenho/` | Só consulta | UC14, UC15 |
| Avisos | `/api/avisos/` | Só leitura e marcar como lido | UC20 |

As permissões da API vêm dos grupos Django correspondentes aos papéis ativos do funcionário:

| Grupo | Permissões |
| -- | -- |
| Profissional | Consultar cadastros, agendar para atletas e registrar dados técnicos |
| Recepção | Consultar cadastros, agendar para atletas, gerenciar a agenda e cadastros |
| Administrador | Todas as permissões, incluindo estrutura e administração do sistema |

A inativação da conta remove o usuário dos grupos de papel e, no painel, alerta sobre os agendamentos futuros que exigem revisão. Nos recursos de estrutura, todo usuário logado consulta e só a administração cadastra, altera e apaga. As listas são paginadas (20 por página) e respondem `count`, `next`, `previous` e `results`.

## Exemplos

Os exemplos usam `curl`, mas as mesmas chamadas podem ser feitas direto pelo Swagger. As datas têm fuso (`-03:00`, horário de Brasília).

### Cadastrar um atleta (UC02) — sem login

```bash
curl -X POST http://127.0.0.1:8000/api/atletas/ \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Beatriz", "sobrenome": "Costa", "email": "bia@x.com",
    "senha": "senha12345", "data_nascimento": "2001-08-15", "aceitou_termos": true
  }'
```

Resposta `201`: dados do atleta (a senha nunca volta). O consentimento LGPD é gravado junto.

Atleta menor de 18 anos sem responsável é recusado:

```json
{ "responsavel": ["Atleta menor de idade exige um responsável."] }
```

Nesse caso nada é gravado: nem o atleta, nem o login.

### Cadastrar um responsável (UC02)

```bash
curl -X POST http://127.0.0.1:8000/api/responsaveis/ \
  -H "Content-Type: application/json" \
  -d '{"nome": "Maria", "sobrenome": "Souza", "email": "maria@x.com",
       "senha": "senha12345", "aceitou_termos": true}'
```

Depois de logada, a responsável cadastra o dependente com `POST /api/atletas/`, e o menor fica ligado a ela automaticamente.

### Fazer login para as chamadas seguintes

A sessão exige o token CSRF nas chamadas que alteram dados. Com `curl`:

```bash
# 1) pega o cookie e o token do formulário de login
curl -c cookies.txt http://127.0.0.1:8000/api/auth/login/ -o /dev/null
TOKEN=$(grep csrftoken cookies.txt | awk '{print $7}')

# 2) entra
curl -b cookies.txt -c cookies.txt -X POST http://127.0.0.1:8000/api/auth/login/ \
  -d "username=bia@x.com&password=senha12345&csrfmiddlewaretoken=$TOKEN"

# 3) a partir daqui, envie o cookie e o cabeçalho X-CSRFToken
TOKEN=$(grep csrftoken cookies.txt | awk '{print $7}')
```

### Criar um agendamento (UC06)

```bash
curl -b cookies.txt -X POST http://127.0.0.1:8000/api/agendamentos/ \
  -H "Content-Type: application/json" -H "X-CSRFToken: $TOKEN" \
  -d '{
    "atleta": 1, "servico": 1, "profissional": 1, "espaco": 1,
    "inicio": "2026-11-16T09:00:00-03:00",
    "equipamentos": [1]
  }'
```

Resposta `201`:

```json
{
  "id": 1, "protocolo": "A1B2C3D4E5", "atleta": 1, "servico": 1,
  "profissional": 1, "espaco": 1,
  "inicio": "2026-11-16T09:00:00-03:00", "fim": "2026-11-16T09:50:00-03:00",
  "status": "AGENDADO", "justificativa": "", "substitui": null,
  "criado_em": "2026-11-07T14:30:00-03:00", "equipamentos": [1]
}
```

- O `fim` é calculado pela duração do serviço, e o `protocolo` e o `status` são gerados pelo sistema.
- O atleta marca para si, o responsável marca para o dependente e a equipe marca para qualquer um. Fora disso, `400` no campo `atleta`.

Erros de regra de negócio voltam como `400`, com o nome do campo:

```json
{ "profissional": ["Este profissional não atende a especialidade do serviço."] }
{ "espaco": ["Esta sala não é usada por este serviço."] }
{ "equipamentos": ["Todas as unidades de Bioimpedância já estão reservadas nesse horário."] }
```

Se a reserva do equipamento falhar, o agendamento também não é gravado.

### Entrar numa aula em grupo (UC06 A2)

Entrar numa aula é criar um agendamento ligado a ela. Basta mandar a aula: serviço, profissional, sala e horário vêm da própria aula.

```bash
curl -b cookies.txt -X POST http://127.0.0.1:8000/api/agendamentos/ \
  -H "Content-Type: application/json" -H "X-CSRFToken: $TOKEN" \
  -d '{ "atleta": 1, "aula": 3 }'
```

- Turma cheia, aula desativada ou horário que já passou: `400` no campo `aula` ou `inicio`. Com a turma cheia, o atleta pode entrar na lista de espera (`/api/lista-espera/` com a `aula`).
- O mesmo atleta não ocupa duas vagas na mesma aula.
- Serviço em grupo (mais de 1 vaga) só se marca pela aula.
- Para sair da aula, cancele o agendamento (`/{id}/cancelar/`): a vaga vai para o primeiro da lista de espera.
- Se a administração mudar o dia, a hora, a sala ou o professor da aula, os agendamentos dos alunos vão junto e eles recebem um aviso.

### Consultar a agenda (UC10)

```bash
curl -b cookies.txt "http://127.0.0.1:8000/api/agendamentos/?status=AGENDADO"
```

Cada perfil recebe só a sua parte: o atleta vê os próprios agendamentos, o responsável os dos dependentes, o profissional os seus atendimentos, e a recepção e a administração veem tudo. O filtro `status` aceita `AGENDADO`, `CANCELADO` e `SUBSTITUIDO`.

### Cancelar (UC09) e reagendar (UC08)

```bash
# cancelar: a justificativa é obrigatória
curl -b cookies.txt -X POST http://127.0.0.1:8000/api/agendamentos/1/cancelar/ \
  -H "Content-Type: application/json" -H "X-CSRFToken: $TOKEN" \
  -d '{"justificativa": "Atleta doente"}'

# reagendar: o original vira SUBSTITUIDO e é criado um novo (201)
curl -b cookies.txt -X POST http://127.0.0.1:8000/api/agendamentos/1/reagendar/ \
  -H "Content-Type: application/json" -H "X-CSRFToken: $TOKEN" \
  -d '{"inicio": "2026-11-17T09:00:00-03:00"}'
```

- O cancelamento muda o status para `CANCELADO` e avisa o profissional. Cancelar duas vezes ou sem justificativa dá `400`.
- No reagendamento, o novo agendamento aponta para o original em `substitui` e leva os mesmos equipamentos.
- `DELETE` em agendamento responde `405`: o histórico é preservado (RN-06).

### Ler os avisos (UC20)

```bash
curl -b cookies.txt "http://127.0.0.1:8000/api/avisos/?lido=false"
curl -b cookies.txt -X POST http://127.0.0.1:8000/api/avisos/1/lido/ -H "X-CSRFToken: $TOKEN"
```

A API não cria nem apaga avisos: quem cria é o sistema (hoje, ao cancelar um atendimento).

## Códigos de resposta

| Código | Significado |
| -- | -- |
| `200` / `201` | Sucesso / criado |
| `400` | Regra de negócio ou dado inválido (o corpo diz o campo). Também ao apagar algo que ainda está em uso (ex.: sala com agendamentos): desative em vez de apagar |
| `403` | Sem login ou sem permissão para a operação |
| `404` | Não existe ou não pertence ao usuário (para não revelar dados de terceiros) |
| `405` | Operação não existe para o recurso (ex.: apagar agendamento) |

## Autor(es)

| Data | Versão | Descrição | Autor(es) |
| -- | -- | -- | -- |
| 07/11/2026 | 1.0 | Criação da página da API (links do Swagger, autenticação, recursos e exemplos) | Gabriel de Souza, Vitor Luiz Zanconato, Vitor Magalhães e Filipe Andrade |
| 11/11/2026 | 1.1 | Todos os recursos da API na tabela, exemplo de entrada em aula em grupo e erro ao apagar registro em uso | Filipe Andrade |
| 11/11/2026 | 1.2 | Filtros da agenda (UC10), aula suspensa (UC21 A2) e confirmação ao inativar serviço (UC18 A1) | Filipe Andrade |