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

A API usa **token JWT** (UC01). O login é `POST /api/token/` com `email` e `password`. A resposta traz um `access`, que vale 30 minutos e vai no cabeçalho `Authorization: Bearer <access>`, e um `refresh`, que vale 7 dias e gera um novo `access` em `POST /api/token/refresh/`. Senha errada e conta inativa dão a mesma resposta (`401`), sem dizer qual falhou.

Para testar no Swagger, faça o login em `/api/token/`, copie o `access` e cole no botão **Authorize**. O login por sessão do Django (pelo `/admin/` ou por `/api/auth/login/`) também funciona no navegador.

Sem login, os endpoints respondem `401`. São abertos só o login e os fluxos de quem ainda não tem conta: `POST /api/cadastro/` (UC02), `POST /api/atletas/` e `POST /api/responsaveis/` (autocadastro) e a recuperação de senha (UC03).

### Recuperação de senha (UC03)

1. `POST /api/senha/recuperar/` com o `email`. A resposta é sempre a mesma, exista o e-mail ou não, para não revelar quem tem cadastro.
2. Se o e-mail existir, o sistema envia um link com `uid` e `token`, que vale 1 hora e serve uma vez só.
3. `POST /api/senha/redefinir/` com `uid`, `token` e a nova `senha`, que passa pelas mesmas regras do cadastro.

Cada IP pode fazer no máximo 5 chamadas por hora a esses dois endpoints. No servidor de demonstração não há servidor de e-mail configurado, então o e-mail com o link aparece no log do servidor.

## Recursos

| Recurso | Rota | Quem altera | Caso de uso |
| -- | -- | -- | -- |
| Login | `/api/token/`, `/api/token/refresh/` | Qualquer um com conta | UC01 |
| Cadastro | `/api/cadastro/` (`tipo`: `atleta` ou `responsavel`) | Qualquer visitante | UC02 |
| Recuperação de senha | `/api/senha/recuperar/`, `/api/senha/redefinir/` | Qualquer visitante | UC03 |
| Especialidades | `/api/especialidades/` | Equipe administrativa | UC18 |
| Espaços | `/api/espacos/` | Equipe administrativa | UC17 |
| Serviços | `/api/servicos/` | Equipe administrativa | UC18 |
| Equipamentos | `/api/equipamentos/` | Equipe administrativa | UC17 |
| Profissionais | `/api/profissionais/` | Só consulta (cadastro pelo painel) | UC04 |
| Atletas | `/api/atletas/` | Qualquer visitante cria; cada um vê o que lhe cabe | UC02 |
| Responsáveis | `/api/responsaveis/` | Qualquer visitante cria | UC02 |
| Agendamentos | `/api/agendamentos/` (+ `/{id}/cancelar/`, `/{id}/reagendar/`, `/{id}/atendimento/`) | Atleta, responsável, equipe | UC06, UC08, UC09, UC10, UC11 |
| Horários livres | `/api/horarios-livres/?servico=&dia=` | Só consulta | UC06, UC07 |
| Grade de aulas | `/api/aulas/` | Equipe administrativa | UC21 |
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
| Profissional | Consultar cadastros, agendar para atletas e registrar e consultar dados técnicos |
| Recepção | Consultar cadastros, agendar para atletas, gerenciar a agenda e cadastros. Não vê dados técnicos |
| Administrador | Todas as permissões, incluindo estrutura e administração do sistema |

Avaliações físicas, planos de treino e evolução são dados sensíveis (RNF03). Quem vê esses dados é a equipe técnica (profissionais e administração), o próprio atleta e o responsável pelos dependentes dele. A recepção recebe lista vazia e `404`.

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

```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "bia@x.com", "password": "senha12345"}'
```

Resposta `200`: `{"refresh": "...", "access": "..."}`. Guarde o `access` e envie em todas as chamadas seguintes:

```bash
ACCESS="cole aqui o access"
```

### Criar um agendamento (UC06)

```bash
curl -H "Authorization: Bearer $ACCESS" -X POST http://127.0.0.1:8000/api/agendamentos/ \
  -H "Content-Type: application/json" \
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
curl -H "Authorization: Bearer $ACCESS" -X POST http://127.0.0.1:8000/api/agendamentos/ \
  -H "Content-Type: application/json" \
  -d '{ "atleta": 1, "aula": 3 }'
```

- Turma cheia, aula desativada ou horário que já passou: `400` no campo `aula` ou `inicio`. Com a turma cheia, o atleta pode entrar na lista de espera (`/api/lista-espera/` com a `aula`).
- O mesmo atleta não ocupa duas vagas na mesma aula.
- Serviço em grupo (mais de 1 vaga) só se marca pela aula.
- Para sair da aula, cancele o agendamento (`/{id}/cancelar/`): a vaga vai para o primeiro da lista de espera.
- Se a administração mudar o dia, a hora, a sala ou o professor da aula, os agendamentos dos alunos vão junto e eles recebem um aviso.

### Consultar a agenda (UC10)

```bash
curl -H "Authorization: Bearer $ACCESS" "http://127.0.0.1:8000/api/agendamentos/?status=AGENDADO"
```

Cada perfil recebe só a sua parte: o atleta vê os próprios agendamentos, o responsável os dos dependentes, o profissional os seus atendimentos, e a recepção e a administração veem tudo. O filtro `status` aceita `AGENDADO`, `CANCELADO` e `SUBSTITUIDO`.

### Cancelar (UC09) e reagendar (UC08)

```bash
# cancelar: a justificativa é obrigatória
curl -H "Authorization: Bearer $ACCESS" -X POST http://127.0.0.1:8000/api/agendamentos/1/cancelar/ \
  -H "Content-Type: application/json" \
  -d '{"justificativa": "Atleta doente"}'

# reagendar: o original vira SUBSTITUIDO e é criado um novo (201)
curl -H "Authorization: Bearer $ACCESS" -X POST http://127.0.0.1:8000/api/agendamentos/1/reagendar/ \
  -H "Content-Type: application/json" \
  -d '{"inicio": "2026-11-17T09:00:00-03:00"}'
```

- O cancelamento muda o status para `CANCELADO` e avisa o profissional. Cancelar duas vezes ou sem justificativa dá `400`.
- No reagendamento, o novo agendamento aponta para o original em `substitui` e leva os mesmos equipamentos.
- `DELETE` em agendamento responde `405`: o histórico é preservado (RN-06).

### Ler os avisos (UC20)

```bash
curl -H "Authorization: Bearer $ACCESS" "http://127.0.0.1:8000/api/avisos/?lido=false"
curl -H "Authorization: Bearer $ACCESS" -X POST http://127.0.0.1:8000/api/avisos/1/lido/
```

A API não cria nem apaga avisos: quem cria é o sistema, quando um atendimento é cancelado, uma vaga da lista de espera é oferecida, a aula muda de dia, hora, sala ou professor e 24 horas antes do atendimento (lembrete). Cada aviso também vai por e-mail.

## Códigos de resposta

| Código | Significado |
| -- | -- |
| `200` / `201` | Sucesso / criado |
| `400` | Regra de negócio ou dado inválido (o corpo diz o campo). Também ao apagar algo que ainda está em uso (ex.: sala com agendamentos): desative em vez de apagar |
| `401` | Sem login, token vencido ou login recusado |
| `403` | Sem permissão para a operação |
| `429` | Muitas chamadas seguidas (recuperação de senha: 5 por hora) |
| `404` | Não existe ou não pertence ao usuário (para não revelar dados de terceiros) |
| `405` | Operação não existe para o recurso (ex.: apagar agendamento) |

## Autor(es)

| Data | Versão | Descrição | Autor(es) |
| -- | -- | -- | -- |
| 07/11/2026 | 1.0 | Criação da página da API (links do Swagger, autenticação, recursos e exemplos) | Gabriel de Souza, Vitor Luiz Zanconato, Vitor Magalhães e Filipe Andrade |
| 11/11/2026 | 1.1 | Todos os recursos da API na tabela, exemplo de entrada em aula em grupo e erro ao apagar registro em uso | Filipe Andrade |
| 11/11/2026 | 1.2 | Login por token JWT, cadastro e recuperação de senha, acesso aos dados técnicos (RNF03) e novos códigos de resposta | Vitor Magalhães |