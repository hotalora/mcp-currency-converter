# 🤖 Agent Template — Clean Architecture

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.121+-green.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.0+-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![LangChain](https://img.shields.io/badge/LangChain-1.0+-brown.svg)](https://docs.langchain.com/)

Conversational AI agent built with **Clean Architecture**, **LangGraph**, and **LangChain**. Connects to external LLMs and tools via Model Context Protocol (MCP).

---

## Quick Start

```bash
# Install dependencies
uv sync

# Configure environment variables
cp application/settings/.env.example application/settings/.env
# Edit .env with your credentials (LLM API key, AWS, etc.)

# Run
uv run python main.py
```

The agent starts at `http://localhost:8003` (configurable via `APP_PORT`).

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/chat` | Send a message to the agent |
| `GET` | `/health` | Health check |

### Usage Example

```bash
curl -X POST http://localhost:8003/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, what day is today?", "conversation_id": "my-conv-1"}'
```

**Response:**
```json
{
  "conversation_id": "my-conv-1",
  "messages": [
    {"type": "text", "content": "Hello! Today is March 28, 2026..."}
  ]
}
```

The `conversation_id` identifies the conversation. Messages with the same ID share context and history (if Valkey is enabled).

---

## Architecture

The project follows **Clean Architecture** with layered separation:

```
┌──────────────────────────────────────────────────────────┐
│                     ENTRY POINTS                         │
│  • FastAPI REST (/chat, /health)                         │
│  • Kafka Consumer (if Kafka enabled)                     │
├──────────────────────────────────────────────────────────┤
│                   APPLICATION LAYER                      │
│  • Config (pydantic-settings + .env)                     │
│  • Container (dependency injection)                      │
├──────────────────────────────────────────────────────────┤
│                     DOMAIN LAYER                         │
│  • AgentRequest / AgentResponse / TextMessage            │
│  • AgentGateway (abstract interface)                     │
│  • ProcessAgentMessageUseCase                            │
├──────────────────────────────────────────────────────────┤
│                  INFRASTRUCTURE LAYER                    │
│  • LangGraph Agent (AgentFactory + 6 middlewares)        │
│  • LLM Auth (API key from AWS Secrets Manager)           │
│  • MCP Client (external tools)                           │
│  • Valkey/Redis — short-term memory (optional)           │
│  • Kafka Producer — async responses (optional)           │
│  • OpenTelemetry — distributed tracing (optional)        │
└──────────────────────────────────────────────────────────┘
```

### Message Flow

```
POST /chat {"message": "Hello", "conversation_id": "abc"}
     │
     ▼
 ChatRequest (DTO) → ProcessAgentMessageUseCase (Domain)
     │
     ▼
 LangGraphAgentAdapter.process_message()
     │
     ▼
 AgentFactory creates the agent with:
 ├── ChatOpenAI (configured LLM)
 ├── Tools from connected MCP Servers
 ├── System Prompt (with {{CURRENT_DATE}} resolved)
 ├── Valkey Checkpointer (memory, if enabled)
 └── 6 Middlewares (see section below)
     │
     ▼
 LLM processes → may use tools → generates response
     │
     ▼
 AgentResponse → JSON to user
```

---

## Configuration (.env)

### Main Variables (always present)

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_PORT` | FastAPI server port | `8003` |
| `MODEL_NAME` | LLM model to use | `gpt-4o-mini` |
| `LLM_BASE_URL` | LLM provider base URL | `https://api.openai.com/v1` |
| `LLM_SECRET_NAME` | Secret name in AWS Secrets Manager | `llm-secret` |
| `LLM_SECRET_FIELD` | Field in the secret containing the API key | `api_key` |
| `AGENT_INSTRUCTIONS` | Agent system prompt. Supports `{{CURRENT_DATE}}` | `You are a helpful AI assistant.` |
| `AGENT_NAME` | Agent name (used in Kafka metadata) | `My Agent` |
| `TEMPERATURE` | LLM temperature (0.0 - 1.0) | `0.7` |
| `TIMEZONE` | IANA timezone for `{{CURRENT_DATE}}` | `America/Bogota` |
| `MAX_MESSAGES_TO_KEEP` | Max messages in history (DeleteOldMessages middleware) | `20` |
| `MESSAGE_RETENTION_MINUTES` | TTL for Valkey checkpoints (minutes) | `600` |
| `AWS_ACCESS_KEY_ID` | AWS credential (or `test` for LocalStack) | — |
| `AWS_SECRET_ACCESS_KEY` | AWS credential | — |
| `AWS_REGION` | AWS region | `us-east-1` |
| `AWS_ENDPOINT_URL` | LocalStack URL (local dev only) | — |
| `LOGGER_LEVEL` | Log level | `INFO` |

### MCP Connection Variables

MCP connections are configured numerically in `.env`:

```dotenv
MCP_CONNECTION_1_NAME=my_mcp_server
MCP_CONNECTION_1_ENDPOINT=http://localhost:3001/api/mcp
MCP_CONNECTION_2_NAME=another_mcp
MCP_CONNECTION_2_ENDPOINT=http://localhost:3002/api/mcp
```

Can be added post-generation with:
```bash
scaffold-py add -mcp "new_mcp|http://localhost:4000/api/mcp"
```

### 🔶 Valkey/Redis Variables (only if `--enable-valkey` was used)

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_SECRET_NAME` | AWS SM secret with Redis credentials | `redis-secret` |
| `REDIS_HOST` | Redis/Valkey host | `localhost` |
| `REDIS_PORT` | Port | `6379` |

**What it does:** Enables short-term memory. The agent remembers conversation context (identified by `conversation_id`). Without Valkey, each request is independent.

### 🔶 OpenTelemetry Variables (only if `--enable-otel` was used)

| Variable | Description | Default |
|----------|-------------|---------|
| `OTEL_ENABLED` | Enable/disable instrumentation | `false` |
| `OTEL_SERVICE_NAME` | Service name in traces | project name |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Collector endpoint (Jaeger, etc.) | `http://localhost:4317` |

**What it does:** Instruments the agent with OpenTelemetry. Traces include LLM calls, tool execution, and Kafka consumption. Visualized in Jaeger or any compatible collector.

### 🔶 Kafka Variables (only if `--enable-kafka` was used)

| Variable | Description | Default |
|----------|-------------|---------|
| `MOUNT_KAFKA` | Enable/disable Kafka consumer | `false` |

Full Kafka configuration (bootstrap servers, topics, SASL, etc.) is defined in `kafka_settings.py` and credentials come from AWS Secrets Manager.

**What it does:** Adds an additional Kafka entry point. The agent receives messages from an input topic, processes them with the same use case as REST, and sends the response to an output topic. Supports concurrency, automatic retries, and self-restart by message limit.

---

## Middlewares

The agent includes **6 middlewares** that intercept the flow at different points:

### 1. DynamicDatePromptMiddleware

**Hook:** `awrap_model_call` (before each LLM call)

Replaces the `{{CURRENT_DATE}}` placeholder in the system prompt with the actual date formatted according to the configured `TIMEZONE`.

```
Before:  "You are an assistant. Today is {{CURRENT_DATE}}."
After:   "You are an assistant. Today is 2026-03-28."
```

### 2. ToolModifyArgsMiddleware

**Hook:** `awrap_tool_call` (before each tool execution)

Automatically injects conversation context fields (`userIdentifier`, `applicationIdentifier`) into MCP tool arguments that require them. The LLM doesn't need to know these values.

### 3. ToolEarlyExitMiddleware

**Hook:** `awrap_tool_call` + `abefore_model`

If a tool returns a response containing success keywords (configurable via `LLM_EARLY_EXIT_TOOLS` and `LLM_SUCCESS_KEYWORDS`), the agent jumps directly to the end without calling the LLM again. Useful for tools like "create_payment" where the tool response is already the final answer.

### 4. ApiKeyRefreshMiddleware

**Hook:** `awrap_model_call` (wraps LLM call)

If the LLM responds with `401 AuthenticationError`, refreshes the API key from AWS Secrets Manager and retries the call automatically.

### 5. DeleteOldMessagesMiddleware

**Hook:** `aafter_agent` (after each complete turn)

Removes old messages from history to control token usage. Respects message group integrity (user + assistant + tools are never separated). Limit configured via `MAX_MESSAGES_TO_KEEP`.

### 6. ToolResultMemoryFilterMiddleware

**Hook:** `aafter_agent` (after each complete turn)

Removes intermediate tool call messages from memory history. After the agent uses a tool and generates the final response, `AIMessage(tool_calls=[...])` and `ToolMessage(content="...")` are removed, keeping only useful context. Configurable via `LLM_MEMORY_EXCLUDED_TOOLS`.

---

## Directory Structure

```
├── application/
│   └── settings/
│       ├── .env.example            # Environment variables template
│       ├── base_settings.py        # BaseSettings with pydantic-settings
│       ├── container.py            # Dependency injection container
│       ├── settings.py             # Main config (Pydantic models)
│       └── kafka_settings.py       # 🔶 Kafka config (if enabled)
├── domain/
│   ├── model/
│   │   ├── agent_message/          # AgentRequest, AgentResponse, TextMessage
│   │   │   ├── agent_message_model.py
│   │   │   └── gateways/           # AgentGateway (abstract interface)
│   │   └── error/                  # AgentInitializationError
│   └── usecase/
│       └── process_agent_message_use_case.py
├── infrastructure/
│   ├── driven_adapters/
│   │   ├── langgraph_agent/
│   │   │   ├── adapter/            # LangGraphAgentAdapter
│   │   │   ├── helpers/            # date_helper, langchain_helper
│   │   │   ├── middlewares/        # 6 middlewares
│   │   │   ├── models/             # ContextSchema, ResponseFormat
│   │   │   └── operations/         # AgentFactory
│   │   ├── llm_auth/               # LlmAuthAdapter
│   │   ├── secrets_manager/        # SecretsManagerAdapter
│   │   ├── cache_repository/       # 🔶 CacheRepository (if Valkey)
│   │   ├── checkpointer/           # 🔶 CheckpointerRepository (if Valkey)
│   │   └── kafka_producer_adapter/ # 🔶 KafkaProducerAdapter (if Kafka)
│   ├── entry_points/
│   │   ├── api/                    # FastAPI: /chat, /health
│   │   │   └── dto/                # ChatRequest
│   │   └── kafka/                  # 🔶 Consumer + Handler (if Kafka)
│   └── helpers/
│       ├── check_connectivity.py   # Network check on startup
│       ├── logger_helper.py        # Logging setup
│       ├── open_telemetry.py       # 🔶 OTel instrumentation (if OTel)
│       ├── tracing_context.py      # 🔶 Kafka trace propagation (if OTel)
│       └── kafka_helper.py         # 🔶 OTel hook for Kafka (if Kafka+OTel)
├── tests/
│   └── unit-test/                  # Unit tests (adapt to features)
├── main.py                         # Application entry point
├── pyproject.toml
└── README.md
```

> Files marked with 🔶 are only present if the corresponding feature was enabled during generation.

---

## 🔶 Kafka — Async Communication (optional)

If the project was generated with `--enable-kafka`, it includes an additional Kafka entry point running in parallel with the REST server.

### Kafka Flow

```
Input Topic → KafkaConsumerAdapter → AgentMessageHandler
                                          │
                                ProcessAgentMessageUseCase
                                    (same as REST)
                                          │
                                KafkaProducerAdapter → Output Topic
```

### Input Message Format

```json
{
  "data": {
    "MessageContent": "Hello, what day is today?"
  },
  "metadata": {
    "MessageIdentifier": "conv-123",
    "UserIdentifier": "user-456",
    "ReplyTo": "agent-output-topic"
  }
}
```

### Consumer Features

- **Controlled concurrency** with semaphore (`max_concurrent_messages`)
- **Automatic retries** with exponential backoff
- **Self-restart** by processed message limit (prevents memory leaks)
- **At-most-once semantics** — no duplicate processing
- **SASL credentials** from AWS Secrets Manager

---

## 🔶 Valkey/Redis — Short-Term Memory (optional)

If the project was generated with `--enable-valkey`, the agent has persistent per-conversation memory.

### How It Works

- Each conversation is identified by `conversation_id` (REST) or `UserIdentifier` (Kafka)
- History is stored as checkpoints in Valkey with configurable TTL
- Internal `thread_id` is `{ApplicationIdentifier}#{UserIdentifier}`
- `DeleteOldMessagesMiddleware` controls history size

### Example

```bash
# Message 1: save context
curl -X POST http://localhost:8003/chat \
  -d '{"message": "My name is Carlos and I live in Medellin", "conversation_id": "demo"}'

# Message 2: ask (same conversation_id → remembers)
curl -X POST http://localhost:8003/chat \
  -d '{"message": "What is my name and where do I live?", "conversation_id": "demo"}'
# → "Your name is Carlos and you live in Medellin"

# Message 3: different conversation_id → doesn't remember
curl -X POST http://localhost:8003/chat \
  -d '{"message": "What is my name?", "conversation_id": "other"}'
# → "I don't have that information"
```

---

## 🔶 OpenTelemetry — Tracing (optional)

If the project was generated with `--enable-otel`, it includes OpenTelemetry instrumentation.

### What It Instruments

- LLM calls (via LangChain instrumentor)
- FastAPI endpoint execution
- Kafka consumption/production (if enabled)
- Trace context propagation between Kafka and REST

### Visualization

With `OTEL_ENABLED=true` and a configured collector (e.g., Jaeger), traces are visible at `http://localhost:16686`.

---

## Tests

The project includes unit tests that adapt to enabled features:

```bash
# Run tests
uv run python -m pytest tests/unit-test/ -v

# With coverage
uv run python -m pytest tests/unit-test/ \
  --cov=domain --cov=infrastructure --cov-report=term-missing
```

| Combination | Tests | Coverage |
|-------------|-------|----------|
| Everything enabled | ~169 | ~86% |
| Valkey + OTel (no Kafka) | ~136 | ~85% |
| Nothing optional | ~121 | ~85% |

---

## Local Development with Infrastructure

For local development with all features:

| Service | Port | Purpose |
|---------|------|---------|
| LocalStack | 4566 | Local AWS Secrets Manager |
| Valkey | 6379 | Short-term memory |
| Kafka (broker) | 9092 / 29092 | Async messaging |
| Jaeger | 16686 / 4317 | Trace visualization |

### Create Secrets in LocalStack

```bash
# LLM API key
docker exec localstack-main awslocal secretsmanager create-secret \
  --name llm-secret --secret-string '{"api_key":"sk-..."}'

# Valkey credentials (empty for local)
docker exec localstack-main awslocal secretsmanager create-secret \
  --name redis-secret --secret-string '{"password":"","username":""}'

# Kafka credentials (empty for local)
docker exec localstack-main awslocal secretsmanager create-secret \
  --name kafka-credentials \
  --secret-string '{"bootstrapServer":"localhost:29092","username":"","password":""}'
```