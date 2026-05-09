# AI-Assisted Incident Resolution Platform

## Especificação Técnica Completa da POC

---

# 1. Visão Geral

Este projeto tem como objetivo construir uma plataforma de resolução de incidentes assistida por Inteligência Artificial utilizando observabilidade, workflows automatizados e agentes de IA especializados.

A proposta inicial será desenvolvida como uma POC (Proof of Concept) local utilizando Docker Compose.

O foco principal desta primeira versão é validar tecnicamente o fluxo:

```text
Erro na aplicação
→ Observabilidade detecta problema
→ Plataforma recebe evento
→ Agentes de IA analisam incidente
→ Sistema gera hipótese de causa raiz
→ Sistema gera sugestão de correção
```

Nesta fase inicial NÃO haverá:

* alteração automática de código
* deploy automático
* merge automático
* automação sem aprovação humana

O objetivo é validar:

* observabilidade
* integração entre sistemas
* workflows orientados a eventos
* análise automatizada utilizando IA
* arquitetura multi-agente

---

# 2. Objetivos do Projeto

## 2.1 Objetivos Técnicos

* Construir uma plataforma orientada a eventos
* Integrar observabilidade com workflows automatizados
* Validar utilização de agentes especializados
* Estruturar arquitetura extensível
* Simular fluxo de incident management assistido por IA
* Reduzir esforço operacional manual

---

## 2.2 Objetivos de Negócio

* Reduzir MTTR (Mean Time To Recovery)
* Automatizar investigação inicial de incidentes
* Padronizar análise de falhas
* Criar fundação para futuras automações
* Melhorar produtividade operacional

---

# 3. Escopo da POC

---

# 3.1 Escopo Incluído

A primeira versão DEVE incluir:

* Aplicação backend Spring Boot
* Observabilidade utilizando OpenTelemetry
* Plataforma SigNoz
* Workflow baseado em webhook
* API orquestradora com FastAPI
* Framework multi-agente CrewAI
* Persistência PostgreSQL
* Infraestrutura Docker Compose
* Agentes especializados em análise de incidente
* Geração automatizada de hipótese de causa raiz
* Sugestão textual de correção

---

# 3.2 Escopo NÃO Incluído

NÃO faz parte desta primeira fase:

* GitHub Pull Request automation
* alteração automática de código
* deploy automatizado
* aprovação humana via UI
* Slack integration
* Teams integration
* ServiceNow integration
* Datadog integration
* autenticação/autorização
* filas distribuídas
* kubernetes
* microsserviços complexos
* memória vetorial
* AI reviewer
* análise de regressão
* análise arquitetural

---

# 4. Arquitetura da Solução

## Arquitetura de Alto Nível

```text
┌────────────────────┐
│ Spring Boot App    │
│ Aplicação Exemplo  │
└─────────┬──────────┘
          │
          │ OpenTelemetry
          ▼
┌────────────────────┐
│ SigNoz             │
│ Logs/Metrics/Trace │
└─────────┬──────────┘
          │
          │ Webhook
          ▼
┌────────────────────┐
│ FastAPI            │
│ AI Orchestrator    │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ CrewAI Agents      │
│ Incident Analysis  │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ PostgreSQL         │
│ Persistência       │
└────────────────────┘
```

---

# 5. Stack Tecnológica

| Camada                     | Tecnologia     |
| -------------------------- | -------------- |
| Linguagem Backend          | Java 21        |
| Framework Backend          | Spring Boot    |
| Observabilidade            | OpenTelemetry  |
| Plataforma Observabilidade | SigNoz         |
| Linguagem Orquestrador     | Python 3.12    |
| Framework API              | FastAPI        |
| Multi-Agent Framework      | CrewAI         |
| Banco de Dados             | PostgreSQL     |
| Infraestrutura             | Docker Compose |
| Versionamento              | GitHub         |
| Containers                 | Docker         |

---

# 6. Estrutura Esperada do Projeto

```text
project-root/
│
├── app/
│   ├── src/
│   ├── Dockerfile
│   ├── pom.xml
│   └── README.md
│
├── orchestrator/
│   ├── agents/
│   ├── workflows/
│   ├── services/
│   ├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
│
├── infrastructure/
│   ├── docker-compose.yml
│   ├── .env
│   └── signoz/
│
├── docs/
│
└── README.md
```

---

# 7. Requisitos Funcionais

---

# RF-001 — Aplicação Backend

A aplicação backend DEVE:

* ser construída em Spring Boot
* utilizar Java 21
* expor endpoints REST
* possuir healthcheck
* gerar logs estruturados
* gerar traces OpenTelemetry
* possuir endpoints de erro simulado

---

## Endpoints obrigatórios

```http
GET /health
GET /error
GET /timeout
GET /payment/{id}
```

---

## Comportamento esperado

### `/health`

Retorna:

```json
{
  "status": "UP"
}
```

---

### `/error`

Deve lançar exception proposital:

```java
throw new NullPointerException("Fake exception");
```

Objetivo:

* validar captura de exception
* validar traces
* validar alertas

---

### `/timeout`

Deve simular timeout:

```java
Thread.sleep(15000);
```

Objetivo:

* validar lentidão
* validar traces longos
* validar métricas

---

### `/payment/{id}`

Endpoint simples para simular serviço de negócio.

Quando:

```text
id = 999
```

Deve lançar erro proposital.

---

# RF-002 — Observabilidade

A aplicação DEVE:

* exportar traces
* exportar métricas
* exportar logs
* utilizar OpenTelemetry
* integrar com SigNoz

---

# RF-003 — Alertas

O SigNoz DEVE:

* detectar exceptions
* detectar HTTP 500
* detectar timeout
* disparar webhook automaticamente

---

# RF-004 — Orquestrador

O orquestrador DEVE:

* receber webhooks do SigNoz
* persistir incidentes
* iniciar workflows
* executar agentes CrewAI

---

## Endpoint obrigatório

```http
POST /incidents
```

---

# RF-005 — Persistência

O sistema DEVE persistir:

* incidentes
* stacktraces
* hipóteses de causa raiz
* propostas de correção

---

# RF-006 — Agentes de IA

O sistema DEVE possuir agentes especializados.

---

## Incident Analyst Agent

Responsabilidades:

* interpretar stacktrace
* identificar erro principal
* resumir incidente
* classificar severidade

---

## Root Cause Agent

Responsabilidades:

* gerar hipótese de causa raiz
* identificar arquivos impactados
* sugerir estratégia de correção
* gerar análise textual

---

# RF-007 — Resultado da Análise

O sistema DEVE gerar resposta estruturada:

```json
{
  "incident_id": "INC-001",
  "root_cause": "NullPointerException em PaymentService",
  "impacted_files": [
    "PaymentService.java"
  ],
  "suggested_fix": "Adicionar validação nula antes do processamento",
  "risk_level": "LOW"
}
```

---

# 8. Requisitos Não Funcionais

---

# RNF-001 — Infraestrutura Local

Toda infraestrutura DEVE subir utilizando:

```bash
docker compose up
```

---

# RNF-002 — Containers

Devem existir containers separados para:

* spring-app
* orchestrator
* postgres
* signoz
* otel-collector

---

# RNF-003 — Configuração

Toda configuração DEVE utilizar:

* variáveis de ambiente
* arquivos `.env`

---

# RNF-004 — Logs Estruturados

Todos os serviços DEVEM gerar:

* logs JSON
* trace_id
* correlation_id

---

# RNF-005 — Simplicidade

A solução DEVE priorizar:

* simplicidade
* modularidade
* facilidade de manutenção
* execução local simples

---

# RNF-006 — Baixo Acoplamento

Os componentes DEVEM ser desacoplados.

O orquestrador NÃO deve depender diretamente da implementação interna da aplicação.

---

# 9. Estrutura do Orquestrador

```text
orchestrator/
│
├── agents/
│   ├── incident_analyst.py
│   ├── root_cause_agent.py
│   └── __init__.py
│
├── workflows/
│   ├── incident_workflow.py
│   └── __init__.py
│
├── api/
│   ├── main.py
│   └── routes.py
│
├── services/
│   ├── signoz_parser.py
│   ├── database.py
│   └── incident_service.py
│
├── models/
│   └── incident.py
│
└── requirements.txt
```

---

# 10. Banco de Dados

## Banco

PostgreSQL

---

## Tabela: incidents

Campos sugeridos:

| Campo         | Tipo      |
| ------------- | --------- |
| id            | UUID      |
| timestamp     | TIMESTAMP |
| severity      | VARCHAR   |
| service_name  | VARCHAR   |
| stacktrace    | TEXT      |
| root_cause    | TEXT      |
| suggested_fix | TEXT      |
| status        | VARCHAR   |

---

# 11. Docker Compose

O Docker Compose DEVE subir:

* Spring Boot App
* PostgreSQL
* SigNoz
* OpenTelemetry Collector
* FastAPI Orchestrator

---

# 12. Fluxo End-to-End Esperado

---

# Cenário Completo

## Etapa 1

Usuário chama:

```http
GET /error
```

---

## Etapa 2

Aplicação lança exception proposital.

---

## Etapa 3

OpenTelemetry exporta trace/log.

---

## Etapa 4

SigNoz detecta erro.

---

## Etapa 5

SigNoz dispara webhook.

---

## Etapa 6

FastAPI recebe evento.

---

## Etapa 7

Workflow CrewAI inicia.

---

## Etapa 8

Agentes analisam:

* logs
* stacktrace
* tipo do erro

---

## Etapa 9

Sistema gera:

* hipótese de causa raiz
* sugestão de correção

---

## Etapa 10

Resultado é salvo no PostgreSQL.

---

# 13. Critérios de Aceite

A POC será considerada funcional quando:

* todos os containers subirem corretamente
* traces aparecerem no SigNoz
* erros simulados dispararem alertas
* webhooks chegarem ao orquestrador
* agentes gerarem análise textual
* incidentes forem persistidos no PostgreSQL

---

# 14. Diretrizes de Desenvolvimento

---

# Priorizar

* simplicidade
* observabilidade
* modularidade
* clareza
* facilidade de execução

---

# Evitar

* kubernetes
* arquitetura excessivamente complexa
* microsserviços prematuros
* autenticação avançada
* filas distribuídas
* event sourcing
* otimização prematura

---

# 15. Roadmap Futuro

Funcionalidades futuras:

* integração GitHub
* criação automática de PR
* AI PR Reviewer
* aprovação humana
* integração Slack
* integração Teams
* integração ServiceNow
* integração Datadog
* memória vetorial
* análise arquitetural
* análise de regressão
* deploy assistido por IA

---

# 16. Objetivo Final

Esta POC tem como objetivo validar tecnicamente a viabilidade de uma plataforma de:

```text
AI-Assisted Incident Resolution
```

como fundação para futura evolução para:

```text
Erro
→ Observabilidade
→ Investigação automatizada
→ Sugestão de correção
→ Aprovação humana
→ Geração de PR
→ Review automatizado
→ Deploy assistido
```
