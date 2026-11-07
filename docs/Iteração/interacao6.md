---
id: iteração6
title: Iteração 6
---
# Iteração 6 (24/10/2026 à 06/11/2026)

**Foco:** corrigir a documentação após o feedback do professor e começar o back-end em Django.

## Planejamento de Iteração

#### Presentes na reunião: Gabriel de Souza, Vitor Luiz Zanconato, Vitor Magalhães e Filipe Andrade

### Lista de Tarefas da Iteração

| Tarefa | Responsabilidade | Situação |
| -- | -- | -- |
| Corrigir os documentos após o feedback (profissional vira equipe do CT, cadastrada pelo administrador; serviços; grade de aulas; lista de espera) | Todos | Concluída em 26/10 |
| Modelar os três apps Django (`estrutura`, `pessoas`, `agenda`) e as migrações iniciais | Todos | Concluída em 26/10 e 28/10 |
| Cadastro de atleta e responsável com login e consentimento LGPD | Todos | Concluída |
| Agendamento com cancelamento (com justificativa) e reagendamento (guarda o original) | Todos | Concluída |
| Equipamentos com reserva por quantidade e avisos ao profissional | Todos | Concluída em 03/11 |
| Atleta no agendamento e visibilidade da agenda por perfil | Todos | Concluída |
| [Diagramas de sequência](../Elaboracao/diagrama_de_sequencia.md) (seis, de UC01 a UC21) | Todos | Concluída em 03/11 |
| Testes automáticos dos três apps | Todos | Concluída |

## Sprint Retrospective/Review Meeting

### Dívidas da Iteração

- Disponibilidade e bloqueios, grade de aulas, lista de espera, avaliações e planos de treino ainda não implementados.
- Iterações, transição e README ainda a preencher (issue #47).

### Riscos Encontrados

- Requisito mal entendido: o feedback do professor obrigou a revisar sete documentos (autocadastro de profissionais).
- Documentação descrevendo funcionalidades que o código ainda não tem.

### Pontos Positivos

- Regras de negócio concentradas nos models, valendo para API e painel do administrador.
- Cobertura de testes automáticos desde o início do código.

### Pontos Negativos

- Retrabalho de documentação por pressuposto não validado.

### O que podemos melhorar?

- Marcar nos documentos o que já está implementado e o que é planejado.
- Validar pressupostos com o professor e o stakeholder antes de replicá-los em vários documentos.

### Ferramentas utilizadas

- GitHub (repositório e issues), Django e Django REST Framework, drf-spectacular (Swagger), MkDocs Material e PlantUML.