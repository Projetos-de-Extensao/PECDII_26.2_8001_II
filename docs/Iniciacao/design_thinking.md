---
id: dt
title: Design Thinking
---

## 1. Capa

- **Título do Projeto**: PKZ LAB — Plataforma de Performance Integrada (Back-end / API REST)
- **Equipe**: Gabriel de Souza, Vitor Luiz Zanconato, Vitor Magalhães e Filipe Andrade
- **Data**: 2026.2
- **Organização/Stakeholder**: PKZ LAB — CT de Performance Integrado (Barra da Tijuca, Rio de Janeiro/RJ)

---

## Introdução

<p align = "justify">
Design Thinking é uma abordagem de resolução de problemas centrada no usuário, estruturada em cinco fases não necessariamente lineares — Empatia, Definição, Ideação, Prototipagem e Teste — que se retroalimentam ao longo do processo. Este documento reorganiza, sob a ótica dessas cinco fases, o trabalho de elicitação e especificação já realizado para o PKZ LAB, articulando os artefatos produzidos em documentos anteriores (Pesquisa, Brainstorm, 5W2H, Mapa Mental, Protótipo de Baixa Fidelidade, Casos de Uso e Diagrama de Classes) em uma narrativa única de descoberta e definição do problema.
</p>

<p align = "justify">
O projeto encontra-se na fase inicial de documentação, que antecede a implementação do back-end em <b>Django</b>. A equipe adota uma postura híbrida: uma etapa inicial de determinação forte de escopo e requisitos — típica de uma fase de elaboração — seguida pela execução do desenvolvimento em ciclos ágeis (sprints), nos quais o Design Thinking continua a ser aplicado de forma iterativa para validar hipóteses com usuários reais do CT à medida que protótipos funcionais forem entregues. A seção <a href="#relacao-com-o-processo-agil">Relação com o processo ágil</a> detalha essa articulação.
</p>

### Contexto do Projeto

<p align = "justify">
O PKZ LAB é um centro de treinamento (CT) de performance integrado, com foco em futebol e desenvolvimento atlético. Atualmente, o acompanhamento de atletas — avaliações físicas, planos de treino e evolução ao longo do tempo — é feito de forma dispersa, em planilhas, anotações e mensagens, o que dificulta consolidar o histórico de cada atleta, mensurar objetivamente sua evolução e organizar a agenda do CT sem conflitos de horário.
</p>

### Objetivo

<p align = "justify">
Compreender profundamente as necessidades dos diferentes perfis de usuário do CT para orientar o desenvolvimento de um back-end (API REST) que centralize o cadastro de atletas e profissionais, o registro de avaliações e planos de treino, o agendamento de atendimentos com verificação automática de disponibilidade e o acompanhamento da evolução por indicadores.
</p>

### Público-Alvo

- **Atletas** do centro (do amador ao alto rendimento), que acompanham sua própria evolução e, quando menores de idade, dependem de um **Responsável** legal (ECA).
- **Equipe técnica (Profissionais)** — Personal Trainer, Preparador Físico, Fisioterapeuta e Nutricionista — que planeja e registra treinos e avaliações.
- **Recepção**, que realiza agendamentos e consultas em nome de atletas e profissionais.
- **Administrador/Gestão do CT**, que precisa de visão geral de agenda, ocupação, usuários e resultados.

### Escopo

<p align = "justify">
O projeto abrange o back-end da plataforma — modelagem de dados, regras de negócio e API para atletas, avaliações, planos de treino, sessões e indicadores de evolução — com controle de acesso por perfil e conformidade com a LGPD (Lei nº 13.709/2018) e o ECA (Lei nº 8.069/1990). Não fazem parte desta versão a construção de aparelhos/sensores físicos, a operação comercial (cobrança/financeiro) do CT, telemedicina, prescrição por IA e aplicativo mobile nativo.
</p>

---

## 3. Fases do Design Thinking

### 3.1. Empatia

#### Pesquisa

<p align = "justify">
A etapa de empatia combinou três frentes de investigação, já registradas no documento de Pesquisa e na sessão de Brainstorm:
</p>

| Método | Descrição | Documento de origem |
| -- | -- | -- |
| Discussão em equipe orientada por perguntas-chave | Sessão colaborativa com perguntas sobre objetivo, cadastro, agendamento e informações relevantes para o cliente | Brainstorm |
| Levantamento de contexto do stakeholder | Entendimento da rotina do CT (Barra da Tijuca/RJ), da forma dispersa de registro de dados e da necessidade de mensurar evolução | Pesquisa |
| Análise de mercado (benchmark) | Levantamento de soluções de referência no acompanhamento esportivo — *TrainingPeaks*, *Playmaker AI*, *Wyscout* e apps de gestão de academia/CT | Pesquisa |
| Levantamento de legislação | Identificação de exigências da LGPD (dados de saúde/desempenho como dados sensíveis) e do ECA (consentimento de responsáveis para atletas menores de idade) | Pesquisa |

#### Insights

<p align = "justify">
Da pesquisa e do brainstorm emergiram os seguintes insights, que orientaram diretamente a definição do problema:
</p>

- A gestão de dados de evolução, treinos e avaliações é **dispersa** em planilhas, anotações e mensagens, dificultando consolidar históricos e mensurar objetivamente a evolução dos atletas.
- **Conflitos de agenda** entre atletas, profissionais, espaços e equipamentos são constantes e hoje não têm verificação automática.
- Cada perfil de usuário precisa de **acesso e visibilidade diferentes** (atleta só vê os próprios dados; recepção vê a agenda geral; administrador tem visão irrestrita), o que exige controle de acesso desde a concepção.
- **Dados de saúde e desempenho** são sensíveis (LGPD) e, no caso de atletas menores de idade, exigem vínculo e consentimento de um responsável (ECA) — isso precisa estar embutido no fluxo de cadastro, e não ser um ajuste posterior.
- O **agendamento com verificação automática de disponibilidade** é percebido pela equipe como a funcionalidade núcleo, à qual as demais (cadastros, avaliações, planos de treino) se conectam.

#### Personas

<p align = "justify">
As personas foram construídas a partir dos perfis de usuário já identificados no Mapa Mental e utilizados como exemplos ilustrativos no Protótipo de Baixa Fidelidade e nos Casos de Uso.
</p>

**Persona 1 — João Souza (Atleta)**

| Campo | Descrição |
| -- | -- |
| Perfil | Atleta do PKZ LAB, atualmente menor de idade |
| Objetivos | Acompanhar sua evolução física, consultar sua própria agenda e histórico de avaliações |
| Frustrações | Não tem visão organizada do próprio progresso; depende de perguntar diretamente ao profissional sobre resultados de avaliações anteriores |
| Necessidades | Consultar agenda e avaliações filtradas por perfil; ter seu cadastro vinculado a um responsável, conforme o ECA |

**Persona 2 — Marcos Souza (Responsável)**

| Campo | Descrição |
| -- | -- |
| Perfil | Pai de João Souza, responsável legal pelo atleta menor de idade |
| Objetivos | Acompanhar os agendamentos e a evolução do filho; garantir que os dados sensíveis de saúde do dependente sejam tratados com segurança |
| Frustrações | Falta de transparência sobre o que é registrado a respeito do filho; preocupação com privacidade de dados de saúde |
| Necessidades | Visualizar agendamentos e evolução do dependente; registrar consentimento LGPD no cadastro |

**Persona 3 — Ana Martins (Profissional / Personal Trainer)**

| Campo | Descrição |
| -- | -- |
| Perfil | Personal Trainer da equipe técnica do CT |
| Objetivos | Registrar avaliações físicas e planos de treino em um único lugar; visualizar sua própria agenda de atendimentos |
| Frustrações | Hoje usa múltiplas planilhas e anotações dispersas; dificuldade de comparar avaliações antigas com as atuais |
| Necessidades | Definir a própria disponibilidade e bloqueios; prescrever e atualizar planos de treino com histórico de versões |

**Persona 4 — Camila Duarte (Recepção)**

| Campo | Descrição |
| -- | -- |
| Perfil | Funcionária da recepção do CT |
| Objetivos | Criar, reagendar e cancelar agendamentos em nome de atletas e profissionais sem gerar conflitos de horário |
| Frustrações | Conflitos de agenda descobertos apenas na hora do atendimento, por falta de verificação cruzada de disponibilidade |
| Necessidades | Visão geral da agenda do CT; verificação automática de disponibilidade de atleta, profissional, espaço e equipamento antes de confirmar |

**Persona 5 — Renata Cardoso (Administradora/Coordenadora)**

| Campo | Descrição |
| -- | -- |
| Perfil | Coordenadora do CT, responsável pela gestão administrativa |
| Objetivos | Gerenciar usuários, permissões, espaços e equipamentos; acompanhar relatórios de desempenho e ocupação |
| Frustrações | Ausência de indicadores consolidados; aprovação manual e informal de novos profissionais |
| Necessidades | Aprovar cadastros de profissionais/recepção; gerenciar bloqueios de espaços/equipamentos por manutenção; visão irrestrita da agenda |

---

### 3.2. Definição

#### Problema Central

> **Como podemos** centralizar o acompanhamento de atletas, treinos, avaliações e agendamentos de um centro de treinamento — hoje disperso em planilhas e mensagens — garantindo controle de acesso por perfil e conformidade com a LGPD e o ECA?

<p align = "justify">
Desse problema central derivam perguntas mais específicas ("Como podemos...?") que orientaram a ideação:
</p>

- Como podemos evitar conflitos de agenda entre atletas, profissionais, espaços e equipamentos no momento do agendamento?
- Como podemos permitir que cada perfil de usuário veja apenas os dados relevantes à sua função?
- Como podemos garantir o consentimento e a proteção de dados sensíveis de saúde de atletas, especialmente menores de idade?
- Como podemos dar à equipe técnica uma visão histórica e comparável da evolução de cada atleta?

#### Pontos de Vista (POV)

| Persona | Necessidade | Insight (porque) |
| -- | -- | -- |
| Atleta (João) | precisa acompanhar sua evolução e consultar sua agenda | porque hoje não tem visão organizada do próprio histórico, disperso entre planilhas e anotações da equipe técnica |
| Responsável (Marcos) | precisa visualizar os agendamentos e a evolução do dependente com segurança | porque dados de saúde de menores exigem consentimento e controle de acesso, conforme o ECA e a LGPD |
| Profissional (Ana) | precisa registrar avaliações e planos de treino em um só lugar | porque hoje usa múltiplas planilhas dispersas, o que dificulta comparar resultados ao longo do tempo |
| Recepção (Camila) | precisa de verificação automática de disponibilidade ao agendar | porque conflitos de horário entre atleta, profissional, espaço e equipamento hoje só são percebidos na hora do atendimento |
| Administradora (Renata) | precisa de uma visão geral de usuários, agenda e recursos | porque a aprovação de cadastros e a gestão de bloqueios por manutenção hoje são feitas de forma manual e informal |

---

### 3.3. Ideação

#### Brainstorming

<p align = "justify">
A sessão de Brainstorm, orientada pelas perguntas-chave sobre objetivo, cadastro, agendamento e informações relevantes, gerou 15 requisitos preliminares (BS01 a BS15), posteriormente ampliados pelo 5W2H (versão 2.0 — visão produto) e organizados no Mapa Mental. Entre as ideias discutidas pela equipe, destacam-se:
</p>

- Centralizar cadastro de atletas e profissionais com níveis de acesso distintos.
- Registrar avaliações físicas (velocidade, força, resistência, agilidade) com comparação histórica.
- Permitir criação e atualização de planos de treino com exercícios, ciclos e periodização.
- Agendar atendimentos cruzando a disponibilidade de atletas, profissionais, espaços e equipamentos em uma única reserva.
- Controlar disponibilidade e bloqueios (folgas, manutenção) de profissionais, espaços e equipamentos.
- Manter histórico de presença, falta e cancelamento para fins de auditoria.
- Gerar relatórios simples de progresso, frequência e evolução.
- Diferenciar níveis de acesso por perfil e proteger dados sensíveis de saúde.
- (Ideia levantada, ainda sem fluxo detalhado) Integração futura com sistema financeiro externo — registrada como BS16 no documento de Casos de Uso, pendente da definição do sistema de destino.

#### Seleção de Ideias

<p align = "justify">
A seleção de ideias seguiu os critérios definidos no 5W2H e consolidados no Mapa Mental:
</p>

- **Alinhamento com o núcleo do produto**: prioridade para ideias relacionadas ao agendamento com verificação automática de disponibilidade, identificado como a funcionalidade central.
- **Aderência ao escopo declarado**: exclusão de módulo financeiro e de integração direta com sensores físicos (restrições explícitas do 5W2H).
- **Conformidade legal**: toda ideia que envolvesse dados pessoais ou de saúde precisava prever controle de acesso e consentimento (LGPD/ECA).
- **Viabilidade dentro do escopo de back-end**: ideias que dependessem de app mobile nativo, telemedicina ou prescrição por IA foram adiadas para iterações futuras.

#### Ideias Selecionadas (MVP)

<p align = "justify">
O resultado da priorização, registrado no Mapa Mental como MVP e refletido no Protótipo de Baixa Fidelidade e nos Casos de Uso, foi:
</p>

| Incluído no MVP | Fora do MVP (iterações futuras) |
| -- | -- |
| Cadastro e autenticação por perfil | Prontuário clínico completo |
| Perfis e papéis (Atleta, Responsável, Profissional, Recepção, Administrador) | Telemedicina |
| Cadastro de profissionais e serviços | Prescrição de treino por IA |
| Gestão de disponibilidade e bloqueios | Convênios / pagamentos avançados |
| Agendamento, reagendamento e cancelamento com verificação de conflitos | Aplicativo mobile nativo |
| Avaliações físicas e planos de treino | Integração com sistema financeiro externo (BS16, sem fluxo detalhado) |
| Validação de conflitos de recursos (UC07) | Automação avançada (lembretes automáticos, lista de espera) |

---

### 3.4. Prototipagem

#### Descrição do Protótipo

<p align = "justify">
A ideia selecionada foi transformada em um <b>protótipo de baixa fidelidade</b>, anterior a qualquer definição de identidade visual, cobrindo os dois fluxos essenciais da primeira iteração: <b>autenticação/cadastro</b> e <b>agendamento com verificação automática de disponibilidade</b>. O protótipo é composto por seis telas (Login, Cadastro, Informações de agendamento, Verificação de disponibilidade, Confirmação e Minha agenda/Registro de status), cada uma detalhada com wireframe, tabela de elementos e regras de negócio associadas.
</p>

<p align = "justify">
Como o escopo do PKZ LAB é o desenvolvimento de um back-end (API REST), o protótipo cumpriu um papel adicional: cada campo e botão desenhado antecipou um atributo de entidade, um endpoint ou uma regra de validação — funcionando como ponte entre a elicitação de requisitos e a modelagem de dados (Diagrama de Classes).
</p>

#### Materiais Utilizados

- **PlantUML (Salt)** para os wireframes das telas, versionados junto ao repositório do projeto.
- **PlantUML (Activity Diagram)** para os fluxos de navegação (login/cadastro e verificação de disponibilidade).
- Ferramentas reservadas para a etapa de alta fidelidade: **Figma** (componentes visuais) e **Material Design Color Tool** (paleta de cores).

#### Testes Realizados

<p align = "justify">
Nesta fase de documentação, os testes do protótipo foram internos, feitos pela própria equipe em confronto com os requisitos do Brainstorm e do 5W2H e com os fluxos de perfil/visibilidade definidos. O protótipo evoluiu em três versões (1.0 → 1.2): a versão inicial trouxe as telas de login, cadastro e agendamento com verificação de disponibilidade; a versão 1.1 adicionou o fluxo de navegação completo e os perfis de acesso; a versão 1.2 incluiu a tabela de rastreabilidade com a API REST, conectando cada tela às operações previstas no back-end.
</p>

---

### 3.5. Teste

#### Feedback dos Usuários

<p align = "justify">
Como o projeto está na fase inicial de documentação, ainda não houve testes de usabilidade com usuários finais reais (atletas, profissionais e recepção do PKZ LAB) sobre um protótipo interativo ou funcional. O "feedback" desta etapa foi obtido por meio de revisões internas da equipe, cruzando cada novo artefato com os documentos anteriores — uma forma de validação por consistência que substitui, temporariamente, o teste com o usuário final.
</p>

#### Ajustes Realizados

<p align = "justify">
Essas revisões internas já geraram ajustes visíveis no histórico de versionamento dos documentos do projeto:
</p>

- O **5W2H** evoluiu da visão geral (v1.0) para uma visão de produto (v2.0), detalhando o agendamento como núcleo funcional após discussão da equipe.
- O **Diagrama de Casos de Uso** foi reestruturado da v1.0 para a v1.1: com 17 casos de uso e 5 atores, um único diagrama gerava muitas linhas cruzadas, prejudicando a leitura; a solução foi dividir em uma visão geral por área funcional e quatro diagramas detalhados.
- O **Protótipo de Baixa Fidelidade** recebeu, entre as versões 1.0 e 1.2, o fluxo de navegação, os perfis de visibilidade e a tabela de rastreabilidade com a API — ajustes motivados pela necessidade de conectar as telas diretamente aos endpoints previstos.

#### Resultados Finais

<p align = "justify">
O resultado desta rodada de "teste por consistência" é um conjunto coerente de documentos — Pesquisa, Brainstorm, 5W2H, Mapa Mental, Protótipo de Baixa Fidelidade, Casos de Uso e Diagrama de Classes — todos rastreáveis entre si, prontos para servir de base à fase de Elaboração (modelagem de dados e definição de endpoints) e, em seguida, à implementação em Django. Testes de usabilidade com usuários reais do CT ficam previstos para o momento em que um protótipo funcional (ou uma versão navegável de alta fidelidade) estiver disponível.
</p>

---

<a id="relacao-com-o-processo-agil"></a>
## Relação com o processo ágil

<p align = "justify">
O critério de avaliação do projeto combina duas exigências aparentemente opostas: forte determinação inicial na documentação e uso de métodos ágeis. O Design Thinking resolve essa tensão ao funcionar em dois ritmos: um ciclo mais longo e completo — Empatia → Definição → Ideação → Prototipagem → Teste — conduzido agora, na fase de documentação, para reduzir incertezas antes de escrever código; e ciclos curtos e repetidos do mesmo processo, embutidos em cada sprint da implementação em Django, em que pequenas hipóteses (um endpoint, uma regra de validação, um fluxo de tela) são prototipadas e testadas com o CT rapidamente.
</p>

<p align = "justify">
Dessa forma, os documentos produzidos nesta fase — em especial o Protótipo de Baixa Fidelidade, os Casos de Uso e o Diagrama de Classes — não são engessados: funcionam como o <i>backlog inicial</i> e os critérios de aceite das primeiras sprints, e continuarão a ser revisados a cada novo ciclo de teste com usuários reais, na mesma lógica de versionamento incremental já observada no histórico dos documentos anteriores.
</p>

---

## 4. Conclusão

### Resultados Obtidos

<p align = "justify">
A aplicação do Design Thinking permitiu reorganizar, sob uma lente centrada no usuário, todo o trabalho de elicitação já realizado para o PKZ LAB: identificar as dores de cada perfil (Empatia), sintetizá-las em um problema central e em pontos de vista específicos (Definição), priorizar as funcionalidades do MVP (Ideação), materializar o fluxo núcleo de agendamento em telas (Prototipagem) e validar a consistência do conjunto de documentos (Teste).
</p>

### Próximos Passos

- Evoluir o protótipo de baixa fidelidade para **alta fidelidade** (Figma + Material Design Color Tool), com identidade visual definida.
- Avançar da visão conceitual do Diagrama de Classes para o **Diagrama de Classes de Especificação**, com atributos, métodos e estereótipos (`<<entity>>`, `<<service>>`, `<<boundary>>`).
- Iniciar a implementação do back-end em **Django**, organizada em sprints, priorizando o núcleo de agendamento com verificação de disponibilidade (UC06/UC07).
- Planejar e conduzir **testes de usabilidade com usuários reais** do PKZ LAB (atletas, profissionais e recepção) assim que houver uma versão navegável ou funcional.
- Detalhar o requisito BS16 (integração financeira externa), hoje sem fluxo definido, quando o sistema de destino for escolhido.

### Aprendizados

<p align = "justify">
A equipe constatou que investir tempo na fase de documentação — pesquisa, brainstorm, 5W2H, mapa mental e protótipo — não é incompatível com agilidade: pelo contrário, reduz o retrabalho nas sprints seguintes, já que decisões de escopo, conformidade legal (LGPD/ECA) e regra de negócio central (verificação de disponibilidade) ficaram claras antes de qualquer linha de código. Também ficou evidente que revisar um documento em função do seguinte (por exemplo, o Diagrama de Casos de Uso em função do Protótipo) é, na prática, uma forma de teste e iteração, mesmo sem um usuário final envolvido ainda.
</p>

---

## 5. Anexos

<p align = "justify">
Este documento se apoia diretamente nos seguintes artefatos do projeto, que devem ser consultados para o detalhamento completo de cada fase:
</p>

| Documento | Conteúdo relevante para o Design Thinking |
| -- | -- |
| Pesquisa | Contexto, objetivo, público-alvo, escopo, análise de mercado e legislação (Empatia/Definição) |
| Brainstorm | Discussão em grupo e requisitos elicitados BS01–BS15 (Empatia/Ideação) |
| 5W2H | Visão geral e visão de produto do sistema (Definição/Ideação) |
| Mapa Mental | Organização dos conceitos da plataforma, MVP e fora do MVP (Ideação) |
| Protótipo de Baixa Fidelidade | Wireframes, fluxo de navegação e regras de negócio das telas (Prototipagem) |
| Casos de Uso | Atores, fluxos principais/alternativos e diagramas de caso de uso (Teste/Especificação) |
| Diagrama de Classes | Modelo conceitual de domínio e rastreabilidade com requisitos e casos de uso (Especificação) |

---

## Referências Bibliográficas

> BROWN, Tim. Design Thinking: uma metodologia poderosa para decretar o fim das velhas ideias. Rio de Janeiro: Elsevier, 2010.

> VIANNA, Maurício et al. Design Thinking: Inovação em Negócios. Rio de Janeiro: MJV Press, 2012.

> Stanford d.school. An Introduction to Design Thinking: Process Guide. Disponível em: https://dschool.stanford.edu

> BRASIL. Lei nº 13.709, de 14 de agosto de 2018. Lei Geral de Proteção de Dados Pessoais (LGPD).

> BRASIL. Lei nº 8.069, de 13 de julho de 1990. Estatuto da Criança e do Adolescente (ECA).

## Autor(es)

| Data | Versão | Descrição | Autor(es) |
| -- | -- | -- | -- |
| 27/09/2026 | 1.0 | Criação do documento de Design Thinking, consolidando Pesquisa, Brainstorm, 5W2H, Mapa Mental, Protótipo de Baixa Fidelidade, Casos de Uso e Diagrama de Classes sob as fases de Empatia, Definição, Ideação, Prototipagem e Teste | Gabriel de Souza, Vitor Luiz Zanconato, Vitor Magalhães e Filipe Andrade |
