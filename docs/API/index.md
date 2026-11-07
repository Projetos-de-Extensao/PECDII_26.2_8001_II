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
| Serviços | `/api/servicos/` | Equipe administrativa | UC18 |
| Equipamentos | `/api/equipamentos/` | Equipe administrativa | UC17 |
| Profissionais | `/api/profissionais/` | Só consulta (cadastro pelo painel) | UC04 |
| Atletas | `/api/atletas/` | Qualquer visitante cria; cada um vê o que lhe cabe | UC02 |
| Responsáveis | `/api/responsaveis/` | Qualquer visitante cria | UC02 |
| Agendamentos | `/api/agendamentos/` | Atleta, responsável, equipe | UC06, UC08, UC09, UC10 |
| Avisos | `/api/avisos/` | Só leitura e marcar como lido | UC20 |

Nos recursos de estrutura, todo usuário logado consulta e só a equipe administrativa (`is_staff`) cadastra, altera e apaga. As listas são paginadas (20 por página) e respondem `count`, `next`, `previous` e `results`.

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
| `400` | Regra de negócio ou dado inválido (o corpo diz o campo) |
| `403` | Sem login ou sem permissão para a operação |
| `404` | Não existe ou não pertence ao usuário (para não revelar dados de terceiros) |
| `405` | Operação não existe para o recurso (ex.: apagar agendamento) |

## Ainda não disponível

Disponibilidade e bloqueios, grade de aulas, lista de espera, registro de atendimento, avaliações, planos de treino e relatórios estão nos documentos de casos de uso, mas ainda não têm endpoint.

## Autor(es)

| Data | Versão | Descrição | Autor(es) |
| -- | -- | -- | -- |
| 07/11/2026 | 1.0 | Criação da página da API (links do Swagger, autenticação, recursos e exemplos) | Gabriel de Souza, Vitor Luiz Zanconato, Vitor Magalhães e Filipe Andrade |