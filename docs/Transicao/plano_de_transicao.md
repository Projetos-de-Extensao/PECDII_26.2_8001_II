---
id: plano_de_transicao
title: Plano de Transição
---

## Introdução

<p align="justify">
A fase de Transição entrega o sistema ao ambiente de produção e aos usuários finais. Este documento registra o estado atual do ambiente, o plano de implantação e os testes de aceitação do PKZ LAB. Por ser um back-end (API REST), o aceite é feito pela API (Swagger em <code>/api/docs/</code>) e pelo painel do administrador (<code>/admin/</code>).
</p>

## 1. Ambiente: situação atual e o que falta para produção

| Item | Hoje (desenvolvimento/demonstração) | Para produção |
| -- | -- | -- |
| Banco de dados | SQLite (`backend/db.sqlite3`) | PostgreSQL, com backup periódico |
| `DEBUG` | `True` (padrão sem `DJANGO_DEBUG`) | `DJANGO_DEBUG=0` |
| `SECRET_KEY` | Chave de desenvolvimento quando falta `DJANGO_SECRET_KEY` | `DJANGO_SECRET_KEY` longa e aleatória (com `DJANGO_DEBUG=0` o sistema não sobe sem ela) |
| `ALLOWED_HOSTS` | IP do servidor, `localhost` e `127.0.0.1` | `DJANGO_ALLOWED_HOSTS` com o domínio do CT |
| HTTPS | Não | Sim (RNF02), por proxy reverso |
| Arquivos estáticos | Sem `STATIC_ROOT` | Definir `STATIC_ROOT` e rodar `collectstatic` (o painel do admin precisa deles com `DEBUG=False`) |
| Servidor de aplicação | `runserver` | Servidor WSGI (ex.: gunicorn) |
| Senhas | Hash padrão do Django | Mantido (o hash rápido vale só nos testes) |
| Rotinas automáticas (UC19 e UC20) | Rodadas à mão (`python manage.py rotinas_da_agenda`) | Cron a cada 5 minutos (passo 6 do plano) |

## 2. Plano de implantação

1. **Congelar a versão:** rodar `python manage.py test estrutura pessoas agenda` e criar uma tag no Git.
2. **Preparar o servidor:** Python 3.12, ambiente virtual e `pip install -r backend/requirements.txt`.
3. **Configurar o ambiente:** `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, banco e `STATIC_ROOT`.
4. **Aplicar as migrações:** `python manage.py migrate`. A migração `estrutura/0002` já cria as quatro especialidades iniciais. A migração `agenda/0004` para e avisa se houver agendamentos antigos sem atleta; nesse caso, preencher o atleta de cada um antes de repetir. A migração `agenda/0010` transforma cada inscrição confirmada num agendamento da aula e depois apaga a tabela de inscrições (entrar numa aula passou a ser um agendamento da aula, UC06 A2); ninguém sai da turma.
5. **Criar o primeiro administrador:** `python manage.py createsuperuser`.
6. **Ligar as rotinas automáticas:** vencer as vagas da lista de espera não confirmadas no prazo (UC19) e mandar o lembrete de 24 horas (UC20) são feitos pelo comando `rotinas_da_agenda`, que precisa rodar sozinho a cada 5 minutos. No Linux (`crontab -e`, com o usuário que roda o sistema):

    ```
    */5 * * * * cd /caminho/do/projeto/backend && /caminho/do/venv/bin/python manage.py rotinas_da_agenda >> $HOME/pkzlab-rotinas.log 2>&1
    ```

    As variáveis de ambiente do passo 3 também precisam valer para o cron (ex.: um arquivo `.env` carregado antes do comando). Para conferir: `crontab -l` e o arquivo de log, que mostra "Lembretes enviados: N" a cada execução.
7. **Cadastrar a estrutura do CT pelo painel (UC17 e UC18):** espaços (ligados às especialidades), serviços e equipamentos.
8. **Cadastrar a equipe (UC04):** funcionários com matrícula e papéis (Profissional, Recepção, Administrador).
9. **Publicar:** servidor WSGI atrás do proxy HTTPS e conferir `/api/docs/`.
10. **Rollback:** restaurar o backup do banco e voltar para a tag anterior.

## 3. Treinamento dos usuários

| Perfil | O que aprende | Como |
| -- | -- | -- |
| Administrador | Cadastrar espaços, serviços, equipamentos e equipe; inativar contas | Painel `/admin/` |
| Recepção | Cadastrar atletas e responsáveis; agendar, reagendar e cancelar | API (Swagger) e painel |
| Profissional | Consultar a própria agenda e os avisos | API (Swagger) |
| Atleta e responsável | Cadastrar-se, agendar, cancelar e consultar a agenda | API (Swagger) |

## 4. Testes de aceitação

<p align="justify">
Os testes automáticos já cobrem estas regras (<code>python manage.py test estrutura pessoas agenda</code>). Nos testes de aceitação, o PKZ LAB executa os cenários abaixo no ambiente de produção e registra o resultado.
</p>

| ID | Caso de uso | Cenário | Resultado esperado | Resultado |
| -- | -- | -- | -- | -- |
| AC01 | UC02 | `POST /api/atletas/` com atleta maior de idade e aceite dos termos | `201`; atleta criado e consentimento LGPD registrado | Pendente |
| AC02 | UC02 | Cadastro de menor de 18 anos sem responsável | `400`, exigindo responsável; nenhum login fica criado | Pendente |
| AC03 | UC02 | Cadastro sem aceitar os termos ou com e-mail já usado | `400` e nada é gravado | Pendente |
| AC04 | UC06 | Agendar com profissional que não atende a especialidade do serviço | `400` no campo `profissional` | Pendente |
| AC05 | UC06 | Agendar em sala que o serviço não usa | `400` no campo `espaco` | Pendente |
| AC06 | UC06 | Agendar com sucesso | `201`, status `AGENDADO`, protocolo de 10 caracteres e fim calculado pela duração do serviço | Pendente |
| AC07 | UC09 | Cancelar sem justificativa e depois com justificativa | `400`; depois status `CANCELADO` e aviso ao profissional | Pendente |
| AC08 | UC08 | Reagendar um agendamento | Original vira `SUBSTITUIDO`; novo `AGENDADO` aponta para ele e leva os equipamentos | Pendente |
| AC09 | UC10 | Atleta, responsável, profissional e recepção consultam `/api/agendamentos/` | Cada um vê só a sua parte; a recepção vê tudo | Pendente |
| AC10 | UC06 | Atleta tenta agendar ou cancelar para outro atleta | `400` ao agendar; `404` ao cancelar | Pendente |
| AC11 | UC17 | Reservar equipamento de unidade única já reservada no mesmo horário | `400` no campo `equipamentos` e nada é gravado | Pendente |
| AC12 | UC16/UC18 | Usuário sem perfil administrativo tenta criar serviço ou especialidade | `403` | Pendente |
| AC13 | RN-06 | `DELETE` em um agendamento | `405`; o histórico é preservado | Pendente |

## 5. Fora do aceite desta versão

Previstos nos documentos, mas ainda não implementados no back-end: disponibilidade e bloqueios (UC05), grade de aulas (UC21), lista de espera (UC19), lembretes automáticos (UC20), registro de atendimento, avaliações, planos de treino e relatórios (UC11 a UC15) e integração financeira (BS16).

## 6. Critérios de aceite e pós-entrega

- **Aceite:** todos os cenários da seção 4 com resultado "Aprovado" e validação da coordenação do PKZ LAB.
- **Defeitos:** registrados como issues no GitHub, com prioridade definida com o PKZ LAB; correções entram nas iterações seguintes.

## Autor(es)

| Data | Versão | Descrição | Autor(es) |
| -- | -- | -- | -- |
| 07/11/2026 | 1.0 | Criação do plano de implantação e dos testes de aceitação | Gabriel de Souza, Vitor Luiz Zanconato, Vitor Magalhães e Filipe Andrade |