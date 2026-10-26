---
id: diagrama_de_classes
title: Diagrama de Classes
---

## Diagrama de Classes

### Objetivo

Este diagrama representa os principais conceitos do domínio do PKZ LAB, sistema back-end para apoiar as rotinas de um centro de treinamento. O modelo conceitual organiza os perfis de usuário, os agendamentos e recursos, e o acompanhamento técnico dos atletas, evidenciando seus relacionamentos com base nos requisitos, casos de uso e protótipo. Nesta versão, as classes são intencionalmente apresentadas sem atributos e métodos.

### Componentes do Diagrama de Classes

Este documento define um modelo para:

1. #### Diagrama conceitual

As classes são apresentadas sem atributos e sem métodos. O diagrama contempla os conceitos de pessoas, agendamentos, recursos e acompanhamento técnico identificados nos casos de uso.

```plantuml
@startuml
left to right direction
skinparam packageStyle rectangle
skinparam monochrome true
skinparam shadowing false

package "Pessoas" {
	abstract class "Usuário" as Usuario
	class "Atleta" as Atleta
	class "Responsável" as Responsavel
	class "Funcionário" as Funcionario
	abstract class "Papel" as Papel
	class "Profissional" as Profissional
	class "Recepção" as Recepcao
	class "Administrador" as Administrador
}

package "Acesso" {
	class "Permissão" as Permissao
	class "Consentimento LGPD" as Consentimento
}

package "Agendamento e recursos" {
	class "Agendamento" as Agendamento
	class "Disponibilidade" as Disponibilidade
	class "Bloqueio de disponibilidade" as Bloqueio
	class "Espaço" as Espaco
	class "Serviço" as Servico
	class "Especialidade" as Especialidade
	class "Lista de espera" as ListaEspera
	class "Aviso" as Aviso
	class "Aula (grade)" as Aula
	class "Configuração" as Configuracao
	class "Equipamento" as Equipamento
	class "Atendimento" as Atendimento
}

package "Acompanhamento técnico" {
	class "Avaliação física" as AvaliacaoFisica
	class "Plano de treino" as PlanoTreino
	class "Exercício" as Exercicio
}

Usuario <|-- Atleta
Usuario <|-- Responsavel
Usuario <|-- Funcionario
Funcionario "1" -- "1..3" Papel : exerce
Papel <|-- Profissional
Papel <|-- Recepcao
Papel <|-- Administrador
Usuario "1" -- "0..*" Permissao : possui
Usuario "1" -- "0..*" Consentimento : registra
Responsavel "0..*" -- "0..1" Atleta : responsável legal

Atleta "1..*" -- "0..*" Agendamento : participa
Profissional "1" -- "0..*" Agendamento : atende
Espaco "1" -- "0..*" Agendamento : reservado em
Servico "1" -- "0..*" Agendamento : define o tipo
Profissional "0..*" -- "1..*" Especialidade : atende
Servico "0..*" -- "1" Especialidade : pertence a
Atleta "1" -- "0..*" ListaEspera : aguarda vaga
ListaEspera "0..*" -- "1" Servico : para
ListaEspera "0..*" -- "1" Profissional : com
Usuario "1" -- "0..*" Aviso : recebe
Espaco "0..*" -- "1..*" Especialidade : atende
Aula "0..*" -- "1" Servico : de
Aula "0..*" -- "1" Profissional : ministrada por
Aula "0..*" -- "1" Espaco : reserva
Agendamento "0..*" -- "0..1" Aula : inscrição em
ListaEspera "0..*" -- "0..1" Aula : espera vaga em
Agendamento "0..*" -- "0..*" Equipamento : reserva
Administrador "1" -- "0..*" Funcionario : cadastra
Profissional "1" -- "0..*" Disponibilidade : define
Profissional "0..1" -- "0..*" Bloqueio : bloqueia horário
Espaco "0..1" -- "0..*" Bloqueio : pode sofrer
Equipamento "0..1" -- "0..*" Bloqueio : pode sofrer
Agendamento "1" -- "0..1" Atendimento : possui registro
Profissional "1" -- "0..*" Atendimento : registra
Atleta "1" -- "0..*" AvaliacaoFisica : possui histórico
Profissional "1" -- "0..*" AvaliacaoFisica : realiza
Atleta "1" -- "0..*" PlanoTreino : acompanha
Profissional "1" -- "0..*" PlanoTreino : prescreve
PlanoTreino "0..*" -- "1..*" Exercicio : contém
Agendamento "0..1" --> "0..1" Agendamento : substitui
@enduml
```
(visão de domínio)

2. **Evolução para o Diagrama de Classes de Especificação** (visão de projeto).  

Ambos devem ser derivados de:

- Casos de uso;
- Diagrama de casos de uso;
- Documento de levantamento de requisitos;
- Protótipo de baixa fidelidade.

### Fontes de entrada obrigatórias

- **Levantamento de requisitos**: requisitos funcionais e não funcionais.
- **Casos de uso**: atores, fluxos principal e alternativos.
- **Diagrama de casos de uso**: escopo e fronteiras do sistema.
- **Protótipo de baixa fidelidade**: entidades percebidas na interface e regras de navegação.

### 1) Diagrama de Classes Conceitual

#### 1.1 Finalidade

Identificar e organizar os conceitos do domínio necessários para compreender as funcionalidades descritas nos casos de uso, sem detalhar implementação. O diagrama dá ênfase às associações, às multiplicidades e às generalizações entre perfis.

#### 1.2 Escopo

- Perfis de usuário do centro de treinamento: atleta, responsável, profissional, recepção e administrador;
- Acesso e consentimento relacionados à autenticação, às permissões e ao cadastro;
- Agendamento, disponibilidade, bloqueios, espaços, equipamentos e registro de atendimento;
- Acompanhamento técnico do atleta por avaliações físicas, planos de treino e exercícios;
- Associações, multiplicidades e generalizações necessárias para expressar os vínculos do domínio.

O escopo não inclui componentes técnicos da API, como telas, endpoints, controladores ou repositórios.

#### 1.3 Notação mínima

O diagrama utiliza notação UML e segue estas regras:

- Cada classe contém somente seu nome; não são incluídos atributos nem métodos;
- Associações representam vínculos identificados nos casos de uso e no domínio do projeto;
- Multiplicidades indicam quantas instâncias podem participar de cada associação;
- Generalizações são usadas para representar especializações de perfis quando aplicável;
- Não são incluídos detalhes de implementação nem classes técnicas.

#### 1.4 Rastreabilidade

A tabela relaciona cada classe aos requisitos do Brainstorm (`BS`), aos casos de uso (`UC`) e às telas do Protótipo de Baixa Fidelidade que fornecem evidência para o conceito. Quando o protótipo não apresenta uma tela para determinada classe, isso é indicado explicitamente.

| Classe Conceitual | Requisito(s) | Caso(s) de Uso | Tela/Protótipo |
|---|---|---|---|
| Usuário | BS12, BS13 | UC01, UC02, UC03, UC04, UC16 | Tela 1 — Login; Tela 1b — Cadastro |
| Funcionário | BS02, BS12, BS14 | UC04, UC16 | Tela 1 — Login; cadastro da equipe pelo administrador (não detalhado no protótipo) |
| Papel (abstrata) | BS02, BS12 | UC04, UC16 | Define as permissões de cada função (Profissional, Recepção, Administrador) |
| Atleta | BS01, BS05, BS06, BS07, BS11 | UC02, UC06, UC07, UC08, UC09, UC10, UC12, UC14 | Tela 1b — Cadastro; Tela 2 — Informações de agendamento; Tela 5 — Minha agenda |
| Responsável | BS01, BS12, BS13 | UC02, UC06, UC08, UC09, UC10, UC14 | Tela 1b — Cadastro; Tela 2 — Informações de agendamento; Tela 5 — Minha agenda |
| Profissional | BS02, BS06, BS07, BS08, BS09, BS10, BS11, BS15 | UC04, UC05, UC06, UC07, UC08, UC09, UC10, UC11, UC12, UC13, UC14, UC15 | Tela 1 — Login; Tela 2 — Informações de agendamento; Tela 5 — Minha agenda; Tela 6 — Registro de status do atendimento |
| Recepção | BS05, BS11, BS12 | UC01, UC03, UC04, UC06, UC08, UC09, UC10 | Tela 1 — Login; Tela 2 — Informações de agendamento; Tela 5 — Minha agenda |
| Administrador | BS12, BS13, BS14 | UC01, UC03, UC04, UC06, UC08, UC09, UC10, UC11, UC15, UC16, UC17, UC18 | Tela 1 — Login; demais telas administrativas não detalhadas no protótipo |
| Permissão | BS12, BS13 | UC01, UC04, UC16 | Tela 1 — Login; Tela 1b — Cadastro |
| Consentimento LGPD | BS13 | UC02 | Tela 1b — Cadastro |
| Agendamento | BS05, BS06, BS10, BS11, BS14 | UC06, UC07, UC08, UC09, UC10, UC11 | Tela 2 — Informações de agendamento; Tela 3 — Verificação de disponibilidade; Tela 4 — Confirmação do agendamento; Tela 5 — Minha agenda; Tela 6 — Registro de status do atendimento |
| Disponibilidade | BS06 | UC05, UC07, UC17 | Tela 2 — Informações de agendamento; Tela 3 — Verificação de disponibilidade |
| Bloqueio de disponibilidade | BS06, BS14 | UC05, UC07, UC17 | Tela 3 — Verificação de disponibilidade; gestão de bloqueios não detalhada no protótipo |
| Espaço | BS06, BS14 | UC06, UC07, UC17 | Tela 2 — Informações de agendamento; Tela 3 — Verificação de disponibilidade |
| Serviço | BS05, BS14 | UC06, UC18 | Tela 2 — Informações de agendamento |
| Especialidade | BS02, BS05 | UC04, UC18 | Tela 2 — Informações de agendamento |
| Lista de espera | BS05, BS06, BS14 | UC09, UC19 | Tela 2 — Informações de agendamento (horário em cinza) |
| Aviso | BS11, BS15 | UC19, UC20 | Agenda (quadro de avisos) e e-mail |
| Aula (grade) | BS05, BS06, BS14 | UC06, UC19, UC21 | Tela 2 — Informações de agendamento (aulas do dia com vagas) |
| Configuração | BS14 | UC19 | Painel do administrador (prazo para confirmar a vaga) |
| Equipamento | BS06, BS14 | UC06, UC07, UC17 | Tela 2 — Informações de agendamento; Tela 3 — Verificação de disponibilidade |
| Atendimento | BS08, BS10, BS15 | UC11, UC14, UC15 | Tela 6 — Registro de status do atendimento |
| Avaliação física | BS03, BS07, BS09 | UC12, UC14, UC15 | Não detalhada no protótipo |
| Plano de treino | BS04, BS07, BS09 | UC13, UC14, UC15 | Não detalhada no protótipo |
| Exercício | BS04 | UC13 | Não detalhada no protótipo |

#### 1.5 Critérios de validação

- Cada classe deve corresponder a um conceito do domínio e estar ligada a pelo menos um requisito ou caso de uso;
- As classes devem conter somente seus nomes, sem atributos ou métodos;
- Os relacionamentos, multiplicidades e generalizações devem ser compatíveis com os fluxos e regras descritos nos documentos do projeto;
- Os nomes devem manter a terminologia usada nos casos de uso e no protótipo;
- Não devem ser incluídas classes técnicas nem conceitos fora do escopo do PKZ LAB;
- Cada linha de rastreabilidade deve apontar para referências existentes; a ausência de tela no protótipo deve ser identificada, não presumida.

### 2) Transição para Diagrama de Classes de Especificação

#### 2.1 Objetivo
Refinar o modelo conceitual para uma estrutura orientada à implementação.

#### 2.2 Regras de refinamento

- Converter conceitos em classes de software quando aplicável;
- Definir tipos de atributos e visibilidade;
- Incluir operações principais;
- Aplicar estereótipos quando necessário (ex.: `<<entity>>`, `<<service>>`, `<<boundary>>`);
- Preservar rastreabilidade com requisitos e casos de uso.

#### 2.3 Itens esperados por classe

- **Nome da classe**;
- **Atributos** (`nome: tipo [visibilidade]`);
- **Métodos/operações** (`assinatura`);
- **Responsabilidade**;
- **Dependências e associações**;
- **Restrições/invariantes** (quando houver).


### 3) Diagrama de Classes de Especificação

#### 3.1 Conteúdo mínimo

- Classes de domínio e de apoio à aplicação;
- Interfaces relevantes;
- Associações, agregações/composições e heranças;
- Multiplicidades e navegabilidade;
- Operações alinhadas aos fluxos dos casos de uso.

#### 3.2 Rastreabilidade

| Classe de Especificação | Origem Conceitual | Requisito(s) | Caso(s) de Uso |
|---|---|---|---|
| `<ClasseSpec>` | `<ClasseConceitual>` | `RF-xx` | `UC-xx` |

#### 3.3 Critérios de qualidade

- Cobertura dos requisitos funcionais;
- Coesão alta e acoplamento controlado;
- Nomes consistentes com o domínio;
- Ausência de classes sem responsabilidade clara.


### 4) Estrutura de versionamento e revisão

- **Versão**: `v0.1`
- **Data**: `25/09/2026`
- **Autor(es)**: Gabriel de Souza, Vitor Luiz Zanconato, Vitor Magalhães e Filipe Andrade
- **Revisor(es)**: Gabriel de Souza, Vitor Luiz Zanconato, Vitor Magalhães e Filipe Andrade
- **Resumo da alteração**: Inclusão do Diagrama de Classes Conceitual, com classes vazias e relacionamentos derivados dos Casos de uso, Documento de Levantamento de Requisitos e Protótipo de Baixa fidelidade do PKZ LAB.

### 5) Entregáveis

- Diagrama de Classes Conceitual (imagem + fonte);
- Diagrama de Classes de Especificação (imagem + fonte);
- Tabelas de rastreabilidade preenchidas;
- Registro de validação com equipe e stakeholders.

## Organização do código em apps (Django)

<p align="justify">
As classes foram divididas em três apps do Django, um por assunto. Cada app reúne só o que tem a ver com ele (alta coesão) e a dependência entre eles vai num sentido só: <b>agenda</b> usa <b>pessoas</b> e <b>estrutura</b>, <b>pessoas</b> usa <b>estrutura</b>, e o contrário nunca acontece (baixo acoplamento). Assim cada integrante pode trabalhar num app sem mexer no código dos outros, e os testes de cada parte rodam separados.
</p>

| App | Classes | O que faz |
| -- | -- | -- |
| <b>estrutura</b> | Especialidade, Espaço, Serviço, Configuração | O que o CT oferece e onde: salas ligadas às especialidades, modalidades com duração e vagas, ajustes do administrador |
| <b>pessoas</b> | Funcionário, Papel (abstrata), Profissional, Recepção, Administrador, Atleta, Responsável, Consentimento LGPD | Quem é quem: um login e uma matrícula por pessoa, papéis que se acumulam e definem as permissões |
| <b>agenda</b> | Disponibilidade, Bloqueio, Aula (grade), Agendamento, Lista de espera, Aviso | O dia a dia: horários livres, grade de aulas, agendamentos, lista de espera com confirmação, avisos e lembretes |

<p align="justify">
A classe <b>Papel</b> é abstrata: não vira tabela, só reúne o que todo papel tem em comum. O <b>Usuário</b> do diagrama corresponde ao login do próprio Django; no código, cada perfil se liga a ele por uma associação 1 para 1, o que permite que a mesma pessoa tenha mais de um papel (por exemplo, a coordenadora que também atende como fisioterapeuta).
</p>
