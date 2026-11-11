---
id: construcao
title: Construção
---

## Introdução

<p align="justify">
A Construção transformou os documentos da Elaboração (requisitos, casos de uso e diagramas) no back-end do PKZ LAB: uma API REST em Django, com Django REST Framework e documentação automática no Swagger. Ela aconteceu nas iterações 6 e 7 (de 24/10/2026 a 20/11/2026). Cada funcionalidade nasceu de uma issue, foi feita numa branch própria e entrou na <code>main</code> por pull request, com os testes automáticos rodando no GitHub Actions.
</p>

## Arquitetura

O back-end é dividido em quatro apps Django, e a dependência entre eles vai num sentido só:

| App | Responsabilidade | Casos de uso |
| -- | -- | -- |
| `estrutura` | Especialidades, espaços, serviços, equipamentos e configuração do CT | UC17, UC18 |
| `pessoas` | Equipe (profissional, recepção, administração), atletas, responsáveis, consentimento LGPD, login, cadastro e permissões por papel | UC01 a UC04, UC16 |
| `agenda` | Disponibilidade, bloqueios, agendamentos, aulas em grupo, lista de espera, atendimentos e avisos | UC05 a UC11, UC19 a UC21 |
| `acompanhamento` | Avaliações físicas, exercícios, planos de treino, evolução do atleta e relatórios | UC12 a UC15 |

<p align="justify">
As regras de negócio ficam nos models (no método <code>clean()</code>), e não nas telas. Assim, a mesma regra vale para a API e para o painel do administrador. Os serializers só traduzem os erros para a resposta da API, com o nome do campo que falhou.
</p>

## O que foi entregue

| Entrega | Onde ver |
| -- | -- |
| API REST e painel do administrador cobrindo os 21 casos de uso (UC01 a UC21) | [Página da API](../API/index.md) e o Swagger em `/api/docs/` |
| 266 testes automáticos, rodando a cada push e pull request | Badge "Testes" no README e aba Actions do GitHub |
| Servidor de demonstração na AWS, com dados de exemplo | [Ambiente e servidor](codespace.md) |
| Comando `popular_demo`, que cria equipe, atletas, agenda, aulas, avaliações e planos | README, seção "Dados de exemplo" |
| Comando `rotinas_da_agenda`, que vence as ofertas da lista de espera e envia os lembretes | [Plano de transição](../Transicao/plano_de_transicao.md), passo 6 |

## Como o trabalho foi organizado

- [Fluxo de trabalho no GitHub](github_workflows.md): branches, commits, pull requests e os workflows do GitHub Actions.
- [Gestão de tarefas](github_projects.md): as issues de cada funcionalidade e o pull request que entregou cada uma.
- [Ambiente e servidor](codespace.md): como rodar o projeto na máquina e como o servidor de demonstração é atualizado.

## Autor(es)

| Data | Versão | Descrição | Autor(es) |
| -- | -- | -- | -- |
| 11/11/2026 | 1.0 | Registro da construção do back-end: arquitetura, entregas e organização do trabalho | Vitor Magalhães |
