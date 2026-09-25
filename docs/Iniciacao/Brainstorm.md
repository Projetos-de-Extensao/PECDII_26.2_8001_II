---
id: brainstorm
title: Brainstorm
---

## Introdução

<p align="justify">
O brainstorm é uma técnica de elicitação de requisitos que estimula a geração de ideias em grupo para compreender o problema e identificar necessidades da solução. Neste projeto, foi utilizado para levantar necessidades do PKZ LAB — CT de Performance Integrado e orientar a definição dos requisitos da plataforma back-end (API REST) de gestão esportiva.
</p>

## Metodologia

<p align="justify">
A equipe organizou as ideias por temas: objetivo e escopo do produto, perfis de usuário, cadastro e acesso, agendamentos e disponibilidade, acompanhamento técnico e proteção de dados. As contribuições foram consolidadas em requisitos preliminares e posteriormente detalhadas nos casos de uso, no protótipo de baixa fidelidade e nos demais documentos de elaboração.
</p>

## Brainstorm

### Versão 1.0

### 1. Qual é o objetivo e o escopo da plataforma?

<p align="justify">
<strong>Gabriel</strong> - A plataforma deve centralizar os dados de atletas, avaliações físicas e planos de treino para apoiar o acompanhamento da performance esportiva.
</p>

<p align="justify">
<strong>Vitor Luiz</strong> - A equipe técnica precisa consultar o histórico de evolução dos atletas e os planejamentos de treinamento em um só lugar.
</p>

<p align="justify">
<strong>Vitor Magalhães</strong> - O sistema deve reduzir a dispersão de informações hoje mantidas em planilhas, anotações e mensagens, além de apoiar a organização da rotina do CT.
</p>

<p align="justify">
<strong>Filipe</strong> - O back-end deve fornecer dados consistentes sobre agenda, avaliações e desempenho para apoiar as decisões da equipe técnica.
</p>

---

### 2. Quais perfis utilizarão o sistema e como será controlado o acesso?

<p align="justify">
<strong>Gabriel</strong> - Os principais perfis são atletas, responsáveis por atletas menores, profissionais, recepção e administradores.
</p>

<p align="justify">
<strong>Vitor Luiz</strong> - Cada perfil deve acessar somente as informações e funcionalidades necessárias à sua atuação no CT.
</p>

<p align="justify">
<strong>Vitor Magalhães</strong> - O cadastro de atletas deve permitir o vínculo com um responsável quando necessário, e os cadastros de profissionais e recepção devem seguir o processo de aprovação administrativa previsto.
</p>

<p align="justify">
<strong>Filipe</strong> - O histórico do atleta deve estar disponível aos perfis autorizados, respeitando os vínculos e as permissões definidos pelo sistema.
</p>

---

### 3. Como devem funcionar os agendamentos e a disponibilidade?

<p align="justify">
<strong>Gabriel</strong> - A criação de um agendamento deve considerar a disponibilidade dos atletas, do profissional, do espaço e dos equipamentos selecionados.
</p>

<p align="justify">
<strong>Vitor Luiz</strong> - O sistema deve verificar conflitos antes da confirmação e preservar as informações preenchidas quando for necessário ajustar o horário ou os recursos.
</p>

<p align="justify">
<strong>Vitor Magalhães</strong> - A agenda deve permitir consulta por perfil e apoiar a criação, o reagendamento e o cancelamento de compromissos.
</p>

<p align="justify">
<strong>Filipe</strong> - Alterações e cancelamentos devem manter o histórico do agendamento, e os atendimentos devem permitir registrar presença, falta ou cancelamento.
</p>

---

### 4. Como será feito o acompanhamento técnico dos atletas?

<p align="justify">
<strong>Gabriel</strong> - O profissional deve registrar avaliações físicas com data e resultados para compor o histórico do atleta.
</p>

<p align="justify">
<strong>Vitor Luiz</strong> - O profissional deve prescrever planos de treino e acompanhar sua evolução ao longo do tempo.
</p>

<p align="justify">
<strong>Vitor Magalhães</strong> - Atletas e equipe técnica devem consultar indicadores de evolução e comparar resultados quando houver histórico suficiente.
</p>

<p align="justify">
<strong>Filipe</strong> - Relatórios de desempenho devem consolidar dados de avaliações, planos e atendimentos para apoiar decisões técnicas e administrativas.
</p>

---

### 5. Quais cuidados de segurança e limites de escopo devem ser considerados?

<p align="justify">
<strong>Gabriel</strong> - O sistema deve controlar o acesso por perfil e proteger os dados pessoais e sensíveis dos atletas.
</p>

<p align="justify">
<strong>Vitor Luiz</strong> - O cadastro deve registrar o consentimento aplicável e, para menores de idade, considerar o vínculo e a autorização do responsável.
</p>

<p align="justify">
<strong>Vitor Magalhães</strong> - O tratamento das informações deve observar a LGPD; os dados de saúde e desempenho exigem controle de acesso adequado.
</p>

<p align="justify">
<strong>Filipe</strong> - O escopo desta versão é o back-end da plataforma. Um módulo financeiro próprio, a integração direta com sensores e funcionalidades avançadas de comunicação não fazem parte do MVP; a integração com um sistema financeiro externo deve ser considerada sem transferir para o PKZ LAB a responsabilidade por cobranças e pagamentos.
</p>

---

### 6. Síntese do brainstorm

<p align="justify">
As ideias convergem para uma API REST que centraliza cadastros e dados de acompanhamento, com gerenciamento de agendamentos e verificação de disponibilidade como fluxo operacional prioritário. O escopo também contempla avaliações físicas, planos de treino, histórico e relatórios, com acesso condicionado ao perfil e atenção especial à proteção de dados. A plataforma não terá módulo financeiro próprio, mas deverá prever integração com um sistema financeiro externo. Mensagens automatizadas e integração com sensores não integram o escopo desta versão.
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
| BS16 | O sistema deve permitir integração com um sistema financeiro externo do centro de treinamento, sem implementar operações financeiras próprias. |

<p align="justify">
O requisito BS15 é atendido parcialmente nesta versão por meio de observações associadas a agendamentos, atendimentos e avaliações. Mensagens e notificações automatizadas não fazem parte do MVP e ficam previstas para evolução futura.
</p>

<p align="justify">
O requisito BS16 estabelece a necessidade de integração externa, mas o sistema financeiro de destino, os dados a compartilhar e as operações disponíveis ainda precisam ser definidos. A integração não inclui processamento de pagamentos nem gestão financeira dentro do PKZ LAB.
</p>

## Conclusão

<p align="justify">
A aplicação do brainstorm permitiu consolidar as necessidades iniciais do PKZ LAB: centralizar informações de atletas, apoiar a rotina de agendamentos e disponibilidade, registrar o acompanhamento técnico, proteger dados pessoais e sensíveis e prever integração com o sistema financeiro externo do CT. Os requisitos BS01 a BS16 orientam o detalhamento dos casos de uso; a integração financeira ainda depende da definição do sistema de destino e dos dados e operações envolvidos.
</p>

## Referências Bibliográficas

> BARBOSA, S. D. J.; SILVA, B. S. Interação Humano-Computador. Elsevier, 2010.

> PRESSMAN, R. S.; MAXIM, B. R. Engenharia de Software: uma abordagem profissional. McGraw-Hill, 2016.

## Autor(es)
| Data | Versão | Descrição | Autor(es) |
| -- | -- | -- | -- |
| 14/09/2026 | 1.0 | Criação do documento | Gabriel de Souza, Vitor Luiz Zanconato, Vitor Magalhães e Filipe Andrade |
