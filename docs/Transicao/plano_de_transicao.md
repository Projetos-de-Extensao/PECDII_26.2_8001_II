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
| Arquivos estáticos | `STATIC_ROOT` em `backend/staticfiles/` | Rodar `collectstatic` e servir a pasta pelo proxy (o painel do admin precisa deles com `DEBUG=False`) |
| Servidor de aplicação | `runserver` | Servidor WSGI (ex.: gunicorn) |
| Senhas | Hash padrão do Django | Mantido (o hash rápido vale só nos testes) |
| Rotinas automáticas (UC19 e UC20) | Rodadas à mão (`python manage.py rotinas_da_agenda`) | Cron a cada 5 minutos (passo 6 do plano) |
| E-mail (avisos e recuperação de senha) | Mostrado no log do servidor (backend `console`) | Servidor SMTP nas variáveis `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER` e `EMAIL_HOST_PASSWORD` |

## 2. Plano de implantação

<<<<<<< HEAD
1. **Congelar a versão:** rodar `python manage.py test` (todos os apps) e criar uma tag no Git.
=======
1. **Congelar a versão:** rodar `python manage.py test` (todos os apps; o GitHub Actions roda o mesmo a cada push) e criar uma tag no Git.
>>>>>>> 0fedf5d7016483fa5ac71c6a425074532639f88a
2. **Preparar o servidor:** Python 3.12, ambiente virtual e `pip install -r backend/requirements.txt`.
3. **Configurar o ambiente:** `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` e banco; depois `python manage.py collectstatic`.
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
| Administrador | Cadastrar espaços, serviços, equipamentos e equipe; montar a grade de aulas; bloquear profissional, sala ou equipamento; inativar contas; gerar relatórios | Painel `/admin/` e API (Swagger) |
| Recepção | Cadastrar atletas e responsáveis; agendar, reagendar e cancelar; colocar atletas na lista de espera | API (Swagger) e painel |
| Profissional | Informar os turnos de atendimento; consultar a própria agenda e os avisos; registrar presença ou falta, avaliações físicas e planos de treino; acompanhar a evolução e o relatório de desempenho | API (Swagger) |
| Atleta e responsável | Cadastrar-se e recuperar a senha; agendar, entrar em aulas e na lista de espera, cancelar e consultar a agenda; acompanhar avaliações, plano de treino e evolução | API (Swagger) |

## 4. Testes de aceitação

<p align="justify">
Os testes automáticos já cobrem estas regras (<code>python manage.py test</code>, também rodado pelo GitHub Actions a cada push). Nos testes de aceitação, o PKZ LAB executa os cenários abaixo no ambiente de produção e registra o resultado.
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
| AC14 | UC01 | Login em `/api/token/` com a senha certa e com a senha errada | `200` com `access` e `refresh`; depois `401`, sem dizer qual dado falhou | Pendente |
| AC15 | UC03 | Pedir a recuperação de senha com e-mail cadastrado e com e-mail inexistente; redefinir com o link | Mesma resposta nos dois casos; a senha nova funciona e o link não serve uma segunda vez | Pendente |
| AC16 | UC05/UC07 | Agendar fora do turno do profissional e consultar `/api/horarios-livres/` | `400` no campo `profissional`; a consulta mostra só os horários livres | Pendente |
| AC17 | UC21/UC06 | Entrar numa aula com a turma cheia | `400`; o atleta pode entrar na lista de espera da aula | Pendente |
| AC18 | UC19/UC20 | Um aluno da aula cancela com alguém na lista de espera | O primeiro da fila recebe aviso da vaga com prazo; ao confirmar, vira agendamento da aula | Pendente |
| AC19 | UC11/UC12 | Profissional registra presença e duas avaliações físicas do mesmo atleta | `201`; a segunda avaliação mostra a diferença para a anterior | Pendente |
| AC20 | UC13 | Prescrever um segundo plano de treino para o atleta | O novo plano é a versão 2 e o anterior fica no histórico | Pendente |
| AC21 | RNF03/UC14 | Recepção consulta `/api/avaliacoes/`, `/api/planos/` e a evolução de um atleta | Listas vazias e `404`: dado técnico é só da equipe técnica, do atleta e do responsável | Pendente |
| AC22 | UC15 | Profissional e atleta pedem o relatório de desempenho | O profissional vê só o que ele avaliou e atendeu; o atleta recebe `403` | Pendente |

## 5. Fora do aceite desta versão

<<<<<<< HEAD
Previstos nos documentos, mas ainda não implementados no back-end: agendamento recorrente (UC06 A3 e UC09 A1), aula que se repete toda semana dentro de uma vigência (UC21, hoje cada aula é de um dia), bloqueio registrado pelo próprio profissional (UC05 passo 3, hoje só a administração registra) e integração financeira (BS16).
=======
- **Integração com o sistema financeiro (BS16):** prevista nos documentos, fora do escopo desta versão.
- **Front-end:** a entrega é a API REST; o aceite é feito pelo Swagger e pelo painel do administrador.
- **Envio real de e-mail:** depende de um servidor SMTP do CT (seção 1). Até lá, os e-mails aparecem no log do servidor.
>>>>>>> 0fedf5d7016483fa5ac71c6a425074532639f88a

## 6. Critérios de aceite e pós-entrega

- **Aceite:** todos os cenários da seção 4 com resultado "Aprovado" e validação da coordenação do PKZ LAB.
- **Defeitos:** registrados como issues no GitHub, com prioridade definida com o PKZ LAB; correções entram nas iterações seguintes.

## Autor(es)

| Data | Versão | Descrição | Autor(es) |
| -- | -- | -- | -- |
| 07/11/2026 | 1.0 | Criação do plano de implantação e dos testes de aceitação | Gabriel de Souza, Vitor Luiz Zanconato, Vitor Magalhães e Filipe Andrade |
<<<<<<< HEAD
| 11/11/2026 | 1.1 | Variáveis de ambiente do servidor, cron das rotinas (UC19 e UC20), migração das inscrições, `STATIC_ROOT` e seção 5 atualizada com o que de fato falta | Filipe Andrade |
=======
| 11/11/2026 | 1.1 | Cenários de aceite das funcionalidades novas (AC14 a AC22), treinamento por perfil, e-mail e escopo atualizados | Vitor Magalhães |
>>>>>>> 0fedf5d7016483fa5ac71c6a425074532639f88a
