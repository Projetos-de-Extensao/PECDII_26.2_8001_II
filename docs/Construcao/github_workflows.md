---
id: github_workflows
title: Fluxo de trabalho no GitHub
---

## Introdução

<p align="justify">
O código do PKZ LAB fica num único repositório no GitHub, junto com esta documentação. O grupo combinou um fluxo simples: cada funcionalidade é feita numa branch própria, entra na <code>main</code> por pull request e só é considerada pronta com os testes automáticos passando.
</p>

## Branches

A `main` é a versão que vai para o servidor de demonstração e para o GitHub Pages. O trabalho é feito em branches com o tipo da mudança no nome e, quando existe, o número da issue:

| Tipo | Exemplo real | Uso |
| -- | -- | -- |
| `feature/` | `feature/32-disponibilidade-bloqueio`, `feature/lista-espera-36` | Funcionalidade nova |
| `fix/` | `fix/main-quebrada`, `fix/email-nao-derruba-aviso` | Correção |
| `docs/` | `docs/issue-22-diagramas-sequencia` | Documentação |

## Commits

As mensagens seguem o formato `tipo(app): o que mudou`, e a issue é citada no fim:

- `feat(agenda): lista de espera com oferta, confirmação e prazo (Closes #36)`
- `feat(agenda): lembrete de 24 horas e comando rotinas_da_agenda (Refs #37)`
- `fix(agenda): falha no e-mail não derruba o aviso, o cancelamento nem os lembretes`
- `ci: roda os testes no GitHub Actions (#44)`

Com `Closes #N`, o GitHub fecha a issue sozinho quando o pull request entra na `main`.

## Pull requests

A maior parte das funcionalidades entrou na `main` por pull request. Algumas foram commits diretos na `main`, como o projeto Django, o app `estrutura`, os equipamentos e as permissões por papel (a lista completa está em [Gestão de tarefas](github_projects.md)). Os pull requests da Construção:

| PR | Autor | O que entregou |
| -- | -- | -- |
| #48 | Gabriel de Souza | Cadastro de atleta, responsável e consentimento LGPD |
| #50 | Gabriel de Souza | Disponibilidade dos profissionais e bloqueios |
| #51 | Gabriel de Souza | Login por token JWT, cadastro e recuperação de senha |
| #52 | Vitor Magalhães | Registro de atendimento (presença, falta ou cancelamento) |
| #53 | Filipe Andrade | Lembrete de 24 horas e comando `rotinas_da_agenda` |
| #54 | Vitor Luiz Zanconato | Grade de aulas em grupo |
| #55 | Vitor Magalhães | Avaliação física, exercícios e planos de treino |
| #56 | Vitor Magalhães | Evolução do atleta e relatório de desempenho |
| #57 | Filipe Andrade | Correção da `main` depois de merges simultâneos (migrações duplicadas e imports perdidos) |
| #58 | Filipe Andrade | Lista de espera com oferta, confirmação e prazo |
| #60 | Filipe Andrade | Falha no envio de e-mail não derruba mais o aviso, o cancelamento nem os lembretes |
| #61 | Vitor Magalhães | Comando `popular_demo` com dados de exemplo |
| #62 | Vitor Magalhães | Testes no GitHub Actions |
| #63 | Vitor Magalhães | Correções da revisão do back-end |
| #64 | Filipe Andrade | Correções das aulas em grupo, da grade de aulas e da exclusão de registros em uso |

<p align="justify">
No dia 07/11, vários pull requests entraram na <code>main</code> em sequência e dois deles criaram migrações com o mesmo número, o que quebrou o projeto. O PR #57 juntou as migrações e restaurou os imports perdidos. No mesmo dia, os testes passaram a rodar automaticamente a cada push e pull request (PR #62), para que um problema assim apareça antes do merge.
</p>

## GitHub Actions

| Workflow | Quando roda | O que faz |
| -- | -- | -- |
| `.github/workflows/testes.yml` | A cada push, em qualquer branch, e a cada pull request | Com Python 3.12: `manage.py check`, confere se falta alguma migração (`makemigrations --check`) e roda todos os testes (`manage.py test`) |
| `.github/workflows/deploy.yml` | A cada push na `main` | Gera esta documentação com o MkDocs e publica no GitHub Pages |

O badge "Testes" no topo do README mostra o resultado da última execução.

## Autor(es)

| Data | Versão | Descrição | Autor(es) |
| -- | -- | -- | -- |
| 11/11/2026 | 1.0 | Fluxo de trabalho real do grupo: branches, commits, pull requests e GitHub Actions | Vitor Magalhães |
