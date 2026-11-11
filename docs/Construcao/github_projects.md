---
id: gestao_de_tarefas
title: Gestão de tarefas
---

## Introdução

<p align="justify">
As tarefas do projeto são controladas pelas issues do GitHub. Cada documento e cada funcionalidade do back-end virou uma issue, com o caso de uso que ela atende. Ao fechar a issue, o pull request ou o commit fica ligado a ela, e o que foi feito em cada período aparece nas páginas de Iterações.
</p>

## Etiquetas

| Etiqueta | Uso |
| -- | -- |
| `documentation` | Documentos da Iniciação e da Elaboração (pesquisa, 5W2H, requisitos, casos de uso, diagramas) |
| `enhancement` | Funcionalidades do back-end e infraestrutura |

## Issues da Construção

| Issue | Tarefa | Entregue em |
| -- | -- | -- |
| #23 a #28 | Projeto Django e API, estrutura do CT, equipe, ciclo de agendamentos, painel administrativo e testes | PRs #19 e #20 e commits na `main` (14/10 a 28/10) |
| #29 | Cadastro de atleta, responsável e consentimento LGPD (UC02) | PR #48 |
| #30 | Atleta no agendamento e agenda filtrada por perfil (UC10) | Commit na `main` (03/11) |
| #31 | Login por token JWT, cadastro e recuperação de senha (UC01 a UC03) | PR #51 |
| #32 | Disponibilidade e bloqueios (UC05) | PR #50 |
| #33 | Verificação de conflitos e horários livres ao agendar (UC07) | Commit na `main` (07/11) |
| #34 | Equipamentos com reserva por quantidade (UC17) | Commit na `main` (03/11) |
| #35 | Grade de aulas em grupo (UC21) | PR #54 |
| #36 | Lista de espera (UC19) | PR #58 |
| #37 | Avisos, lembretes e rotina automática (UC20) | PR #53 |
| #38 | Registro de atendimento (UC11) | PR #52 |
| #39 | Avaliação física, exercícios e planos de treino (UC12 e UC13) | PR #55 |
| #40 | Evolução do atleta e relatórios (UC14 e UC15) | PR #56 |
| #41 | Permissões por papel (UC16): grupos do Django sincronizados com os papéis do funcionário | Commit na `main` (07/11) |
| #42 | Dados de exemplo (`popular_demo`) | PR #61 |
| #43 | Servidor de demonstração na EC2 | Servidor no ar (veja [Ambiente e servidor](codespace.md)) |
| #44 | Testes no GitHub Actions | PR #62 |

## Autor(es)

| Data | Versão | Descrição | Autor(es) |
| -- | -- | -- | -- |
| 11/11/2026 | 1.0 | Registro das issues da Construção e do que entregou cada uma | Vitor Magalhães |
