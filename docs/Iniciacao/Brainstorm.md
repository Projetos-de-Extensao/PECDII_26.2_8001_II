---
id: brainstorm
title: Brainstorm
---

## Introdução

<p align="justify">
O brainstorm é uma técnica de elicitação de requisitos que estimula a geração livre de ideias em grupo, sem críticas imediatas, com o objetivo de ampliar a visão sobre o problema e identificar oportunidades de solução. No contexto do projeto, a técnica foi aplicada para discutir os principais objetivos, usuários, funcionalidades e processos que a plataforma deve apoiar, contribuindo para a definição inicial dos requisitos do sistema.
</p>

## Metodologia

<p align="justify">
A equipe realizou uma sessão colaborativa de discussão, com foco na identificação das necessidades do sistema e na exploração de ideias relacionadas ao domínio do projeto. A dinâmica foi orientada por perguntas-chave sobre o propósito da aplicação, os usuários envolvidos, as principais funcionalidades e os fluxos críticos de uso. As ideias geradas foram registradas, agrupadas e transformadas em requisitos preliminares.
</p>

## Brainstorm

### Versão 1.0

### 1. Qual o objetivo principal da aplicação?

<p align="justify">
<strong>Gabriel</strong> - A plataforma deve centralizar o acompanhamento de atletas, treinos e avaliações em um único ambiente para facilitar a gestão da performance esportiva.
</p>

<p align="justify">
<strong>Vitor Luiz</strong> - O objetivo principal é permitir que a equipe técnica tenha uma visão clara do histórico de evolução dos atletas e dos planejamentos de treinamento.
</p>

<p align="justify">
<strong>Vitor Magalhães</strong> - A aplicação deve apoiar a organização das atividades do centro de treinamento, reduzindo a dispersão de informações em planilhas e mensagens.
</p>

<p align="justify">
<strong>Filipe</strong> - A solução deve facilitar o controle de agenda, avaliações, metas e acompanhamento de desempenho, proporcionando uma base mais objetiva para tomadas de decisão.
</p>

---

### 2. Como será o processo para cadastrar um novo cliente?

<p align="justify">
<strong>Gabriel</strong> - O sistema deve permitir o cadastro de atletas e profissionais com dados básicos, além de informações relevantes para acompanhamento da evolução e das atividades.
</p>

<p align="justify">
<strong>Vitor Luiz</strong> - Cada perfil deve ter acesso de acordo com sua função, como atletas, treinadores, fisioterapeutas e administradores.
</p>

<p align="justify">
<strong>Vitor Magalhães</strong> - O cadastro de treinos deve permitir a definição de exercícios, objetivos, frequência, carga e observações, além de registrar evolução ao longo do tempo.
</p>

<p align="justify">
<strong>Filipe</strong> - A plataforma deve manter um histórico do processo de treinamento para permitir análise de desempenho e retorno sobre as intervenções realizadas.
</p>

---

### 3. Como será a forma de adicionar produtos?

<p align="justify">
<strong>Gabriel</strong> - O sistema deve permitir agendar atendimentos, treinos e avaliações, considerando a disponibilidade de atletas, profissionais e espaços físicos.
</p>

<p align="justify">
<strong>Vitor Luiz</strong> - O agendamento deve evitar conflitos de horários e apoiar a organização da rotina do centro de treinamento.
</p>

<p align="justify">
<strong>Vitor Magalhães</strong> - A agenda deve mostrar disponibilidade, compromissos e pendências para facilitar o controle diário da operação.
</p>

<p align="justify">
<strong>Filipe</strong> - O sistema deve manter registro de presença, observações e ajuste de agenda quando houver alterações no planejamento.
</p>

---

### 4. Outras perguntas pertinentes ao contexto

<p align="justify">
<strong>Gabriel</strong> - Informações como histórico de treinamento, avaliações físicas, metas, cronograma de treinos e disponibilidade devem estar acessíveis com clareza.
</p>

<p align="justify">
<strong>Vitor Luiz</strong> - O usuário precisa visualizar indicadores de evolução, dados dos atendimentos e informações sobre eventos e programas esportivos.
</p>

<p align="justify">
<strong>Vitor Magalhães</strong> - O sistema deve apresentar relatórios simples e úteis para acompanhamento do desempenho, como progresso, frequência e evolução de indicadores.
</p>

<p align="justify">
<strong>Filipe</strong> - Também deve haver espaço para observações técnicas, informações de contexto e comunicação entre atletas e profissionais.
</p>

---

### 5. "Outras perguntas pertinentes ao contexto", Como seria a forma de adicionar do cliente adicionar os produtos ?

<p align="justify">
<strong>Gabriel</strong> - A funcionalidade central deve ser o gerenciamento de agendamentos, seguida pelo cadastro de atletas, avaliações e planos de treinamento.
</p>

<p align="justify">
<strong>Vitor Luiz</strong> - O sistema deve permitir a manutenção de históricos e relatórios para subsidiar decisões técnicas e de acompanhamento.
</p>

<p align="justify">
<strong>Vitor Magalhães</strong> - A segurança das informações sensíveis, especialmente dados de saúde e avaliação física, deve ser tratada como prioridade.
</p>

<p align="justify">
<strong>Filipe</strong> - O produto deve ser pensado para uso prático no ambiente do centro de treinamento, com foco em organização, visibilidade e acesso rápido à informação.
</p>

---

### 6. Quais informações seriam interessante para o cliente?

<p align="justify">
<strong>Gabriel</strong> - Informações como histórico de treinamento, avaliações físicas, metas, cronograma de treinos e disponibilidade devem estar acessíveis com clareza.
</p>

<p align="justify">
<strong>Vitor Luiz</strong> - O usuário precisa visualizar indicadores de evolução, dados dos atendimentos e informações sobre eventos e programas esportivos.
</p>

<p align="justify">
<strong>Vitor Magalhães</strong> - O sistema deve apresentar relatórios simples e úteis para acompanhamento do desempenho, como progresso, frequência e evolução de indicadores.
</p>

<p align="justify">
<strong>Filipe</strong> - Também deve haver espaço para observações técnicas, informações de contexto e comunicação entre atletas e profissionais.
</p>

### Requisitos elicitados

| ID | Descrição |
| -- | -- |
| BS01 | O sistema deve permitir o cadastro de atletas com informações pessoais e de contexto esportivo. |
| BS02 | O sistema deve permitir o cadastro de profissionais envolvidos no atendimento e treinamento. |
| BS03 | O sistema deve registrar avaliações físicas e indicadores de desempenho do atleta. |
| BS04 | O sistema deve possibilitar a criação e atualização de planos de treino. |
| BS05 | O sistema deve permitir o agendamento de atendimentos, treinos e demais atividades. |
| BS06 | O sistema deve controlar a disponibilidade de atletas, profissionais, espaços e equipamentos. |
| BS07 | O sistema deve manter um histórico de evolução do atleta ao longo do tempo. |
| BS08 | O sistema deve registrar observações e acompanhamento de cada treino ou avaliação. |
| BS09 | O sistema deve apresentar relatórios e indicadores de progresso para auxiliar a tomada de decisão. |
| BS10 | O sistema deve permitir o controle de presença e acompanhamento da execução das atividades. |
| BS11 | O sistema deve disponibilizar informações sobre agenda e compromissos para os usuários. |
| BS12 | O sistema deve oferecer diferentes níveis de acesso conforme o perfil do usuário. |
| BS13 | O sistema deve garantir a confidencialidade e segurança dos dados sensíveis. |
| BS14 | O sistema deve suportar a organização das rotinas e operações do centro de treinamento. |
| BS15 | O sistema deve facilitar a comunicação e o compartilhamento de informações entre equipe e atletas. |

## Conclusão

<p align="justify">
A aplicação da técnica de brainstorm permitiu identificar ideias, necessidades e requisitos iniciais relevantes para a solução proposta. A sessão evidenciou a importância de centralizar dados, organizar agendas, acompanhar evolução esportiva e garantir segurança da informação, elementos fundamentais para o sucesso do sistema.
</p>

## Referências Bibliográficas

> BARBOSA, S. D. J.; SILVA, B. S. Interação Humano-Computador. Elsevier, 2010.

> PRESSMAN, R. S.; MAXIM, B. R. Engenharia de Software: uma abordagem profissional. McGraw-Hill, 2016.

## Autor(es)
| Data | Versão | Descrição | Autor(es) |
| -- | -- | -- | -- |
| 14/09/2026 | 1.0 | Criação do documento | Gabriel de Souza, Vitor Luiz Zanconato, Vitor Magalhães e Filipe Andrade |
