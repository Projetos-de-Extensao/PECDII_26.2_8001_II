---
id: mapa_mental
title: Mapas Mentais
---
 
## Introdução
 
<p align = "justify">
Mapa mental consiste em criar resumos cheios de símbolos, cores, setas e frases de efeito com o objetivo de organizar o conteúdo e facilitar associações entre as informações destacadas. Esse material é muito indicado para pessoas que têm facilidade de aprender de forma visual.
</p>
 
## Metodologia
 
<p align = "justify">
A partir do escopo definido na pesquisa e no brainstorm do projeto, a equipe organizou os principais conceitos da plataforma do PKZ LAB em um mapa mental. O diagrama foi produzido em PlantUML e é renderizado diretamente nesta página.
</p>
 
## Mapa mental - Geral
 
## Versão 1.0
 
### Mapa mental — PKZ LAB
 
```plantuml
@startmindmap
title Mapa Mental - PKZ LAB (Plataforma de Performance Integrada)

* PKZ LAB
** Usuários
*** Atleta / Cliente
**** Criar conta
**** Buscar profissionais
**** Agendar sessão
**** Reagendar
**** Cancelar
**** Acompanhar evolução
*** Profissional (equipe técnica)
**** Configurar disponibilidade
**** Bloquear horários
**** Registrar avaliações
**** Prescrever planos de treino
**** Visualizar agenda
*** Recepção
**** Consultar disponibilidade
**** Criar agendamentos
**** Reagendar / cancelar
*** Administrador
**** Gerenciar usuários
**** Gerenciar profissionais
**** Gerenciar serviços
**** Gerenciar espaços e recursos
**** Gerenciar permissões

** Profissionais
*** Personal Trainer
*** Preparador Físico
*** Nutricionista
*** Fisioterapeuta

** Avaliações e Testes
*** Velocidade
*** Força
*** Resistência
*** Agilidade
*** Registro por data
*** Comparação de resultados

** Planos de Treino
*** Prescrição por atleta
*** Exercícios
*** Ciclos / periodização

** Evolução
*** Indicadores de performance
*** Acompanhamento no tempo
*** Relatórios

left side

** Agendamento
*** Escolher serviço
*** Escolher profissional
*** Escolher local
*** Escolher data e horário
*** Confirmar / reagendar / cancelar
*** Recorrência (semanal)

** Agenda
*** Agenda do atleta
*** Agenda do profissional
*** Disponibilidade e bloqueios
*** Prevenção de conflitos
**** Conflito do atleta
**** Conflito do profissional
**** Conflito de sala / recurso

** Espaços e Recursos
*** Salas / estúdios
*** Campo / quadra
*** Equipamentos
*** Controle de disponibilidade

** Segurança e Acesso
*** Login / recuperação de senha
*** Perfis e privilégios
*** Proteção de dados sensíveis
*** LGPD

** Automação
*** Lembretes e confirmações
*** Aviso de cancelamento
*** Lista de espera / nova vaga
*** Integração futura com calendário

** Gestão
*** Serviços / profissionais / atletas
*** Agenda / espaços / recursos
*** Permissões
*** Relatórios

** MVP
*** Cadastro e autenticação
*** Perfis e papéis
*** Profissionais e serviços
*** Disponibilidade
*** Agendamento / reagendamento / cancelamento
*** Avaliações e planos de treino
*** Validação de conflitos

** Fora do MVP
*** Prontuário clínico completo
*** Telemedicina
*** Prescrição por IA
*** Convênios / pagamentos avançados
*** Aplicativo mobile nativo
@endmindmap
```
 
## Conclusão
 
<p align = "justify">
O mapa mental é uma ficha de estudos que ajuda a dar uma visão geral do tema, e ajuda a fixar os pontos mais importantes sobre a plataforma do PKZ LAB.
</p>
 
## Referências
> BUZAN, Tony. Mapas Mentais e sua Elaboração. Cultrix, 2005.
 
> PlantUML. Mindmap diagram. Disponível em: https://plantuml.com/mindmap-diagram
 
## Versionamento
| Data | Versão | Descrição | Autor(es) |
| -- | -- | -- | -- |
| 08/09/2026 | 1.0 | Criação do mapa mental do PKZ LAB | _(preencher com a equipe)_ |
