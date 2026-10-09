import os
from typing import Optional, List, Dict, Any
from pydantic import AliasChoices, Field, field_validator, model_validator

from application.settings.base_settings import GeneralBaseSettings


class OpenTelemetryConfig(GeneralBaseSettings):
    """OpenTelemetry configuration."""
    OTEL_ENABLED: bool = Field(default=False, env="OTEL_ENABLED")
    OTEL_SERVICE_NAME: str = Field(
        default="currency_management_aiagent",
        env="OTEL_SERVICE_NAME"
    )
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field(
        default="http://localhost:4317",
        env="OTEL_EXPORTER_OTLP_ENDPOINT"
    )


class AwsConfig(GeneralBaseSettings):
    """AWS configuration - supports both real AWS and LocalStack."""
    aws_access_key_id: Optional[str] = Field(
        default=None,
        alias="AWS_ACCESS_KEY_ID",
        validation_alias=AliasChoices("AWS_ACCESS_KEY_ID", "aws_access_key_id"),
    )
    aws_secret_access_key: Optional[str] = Field(
        default=None,
        alias="AWS_SECRET_ACCESS_KEY",
        validation_alias=AliasChoices("AWS_SECRET_ACCESS_KEY",
                                      "aws_secret_access_key"),
    )
    aws_session_token: Optional[str] = Field(
        default=None,
        alias="AWS_SESSION_TOKEN",
        validation_alias=AliasChoices("AWS_SESSION_TOKEN", "aws_session_token"),
    )
    endpoint_url: Optional[str] = Field(
        default=None,
        alias="AWS_ENDPOINT_URL",
        validation_alias=AliasChoices("AWS_ENDPOINT_URL", "aws_endpoint_url",
                                      "endpoint_url"),
    )
    region_name: Optional[str] = Field(
        default="us-east-1",
        alias="AWS_REGION",
        validation_alias=AliasChoices("AWS_REGION", "aws_region",
                                      "region_name"),
    )


class RedisConfig(GeneralBaseSettings):
    """Redis/Valkey configuration - credentials come from Secrets Manager."""
    secret_name: str = Field(
        default="redis-secret",
        alias="REDIS_SECRET_NAME",
        validation_alias=AliasChoices("REDIS_SECRET_NAME", "redis_secret_name"),
    )
    host: Optional[str] = Field(
        default=None,
        alias="REDIS_HOST",
        validation_alias=AliasChoices("REDIS_HOST", "redis_host"),
    )
    port: Optional[int] = Field(
        default=6379,
        alias="REDIS_PORT",
        validation_alias=AliasChoices("REDIS_PORT", "redis_port"),
    )
    db: Optional[int] = Field(
        default=0,
        alias="REDIS_DB",
        validation_alias=AliasChoices("REDIS_DB", "redis_db"),
    )
    ssl: Optional[bool] = Field(
        default=False,
        alias="REDIS_SSL",
        validation_alias=AliasChoices("REDIS_SSL", "redis_ssl"),
    )
    credentials_from_secrets: bool = Field(
        default=True,
        alias="REDIS_CREDENTIALS_FROM_SECRETS",
        validation_alias=AliasChoices(
            "REDIS_CREDENTIALS_FROM_SECRETS",
            "credentials_from_secrets",
        ),
    )


class LlmConfig(GeneralBaseSettings):
    """LLM configuration - API key comes from Secrets Manager."""
    secret_name: str = Field(
        default="llm-secret",
        alias="LLM_SECRET_NAME",
        validation_alias=AliasChoices("LLM_SECRET_NAME", "llm_secret_name"),
    )
    secret_field: str = Field(
        default="api_key",
        alias="LLM_SECRET_FIELD",
        validation_alias=AliasChoices("LLM_SECRET_FIELD", "llm_secret_field"),
    )
    api_key: str = Field(
        default="",
        alias="OPENAI_API_KEY",
        validation_alias=AliasChoices("OPENAI_API_KEY", "api_key"),
    )
    use_secrets: bool = Field(
        default=True,
        alias="LLM_USE_SECRETS",
        validation_alias=AliasChoices("LLM_USE_SECRETS", "use_secrets"),
    )
    base_url: str = Field(
        default="https://api.openai.com/v1",
        alias="LLM_BASE_URL",
        validation_alias=AliasChoices("LLM_BASE_URL", "llm_base_url"),
    )
    model_name: str = Field(
        default="gpt-4o-mini",
        alias="MODEL_NAME",
        validation_alias=AliasChoices("MODEL_NAME", "model_name"),
    )
    temperature: float = Field(
        default=0.7,
        alias="TEMPERATURE",
        validation_alias=AliasChoices("TEMPERATURE", "temperature"),
    )
    timeout: int = Field(
        default=30,
        alias="LLM_TIMEOUT",
        validation_alias=AliasChoices("LLM_TIMEOUT", "llm_timeout"),
    )
    max_messages_to_keep: int = Field(
        default=20,
        alias="MAX_MESSAGES_TO_KEEP",
        validation_alias=AliasChoices("MAX_MESSAGES_TO_KEEP",
                                      "max_messages_to_keep"),
    )
    message_retention_minutes: int = Field(
        default=600,
        alias="MESSAGE_RETENTION_MINUTES",
        validation_alias=AliasChoices("MESSAGE_RETENTION_MINUTES",
                                      "message_retention_minutes"),
    )
    early_exit_tools: list[str] = Field(
        default=[],
        alias="LLM_EARLY_EXIT_TOOLS",
        validation_alias=AliasChoices("LLM_EARLY_EXIT_TOOLS",
                                      "llm_early_exit_tools"),
    )
    success_keywords: list[str] = Field(
        default=[],
        alias="LLM_SUCCESS_KEYWORDS",
        validation_alias=AliasChoices("LLM_SUCCESS_KEYWORDS",
                                      "llm_success_keywords"),
    )
    memory_excluded_tools: list[str] = Field(
        default=[],
        alias="LLM_MEMORY_EXCLUDED_TOOLS",
        validation_alias=AliasChoices("LLM_MEMORY_EXCLUDED_TOOLS",
                                      "llm_memory_excluded_tools"),
    )
    timezone: str = Field(
        default="America/Bogota",
        alias="TIMEZONE",
        validation_alias=AliasChoices("TIMEZONE", "timezone"),
    )


class LoggerConfig(GeneralBaseSettings):
    """Logger configuration."""
    logger_level: str = Field(
        default="INFO",
        alias="LOGGER_LEVEL",
        validation_alias=AliasChoices("LOGGER_LEVEL", "logger_level"),
    )
    logger_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        alias="LOGGER_FORMAT",
        validation_alias=AliasChoices("LOGGER_FORMAT", "logger_format"),
    )


class Config(GeneralBaseSettings):
    """Main application configuration."""
    agent_instructions: str = Field(
        default=(
            "Eres un asistente amable y conversacional. Responde siempre en "
            "espanol natural, de forma clara y breve. Usa las herramientas "
            "disponibles cuando sean necesarias. Para conversiones, utiliza "
            "los valores exactos devueltos por convert_currency y presenta "
            "el resultado en un mensaje breve, amable y natural, incluyendo "
            "tasa y fecha si estan disponibles. La respuesta de la herramienta "
            "es interna: no devuelvas JSON, esquemas, tablas, listas, "
            "encabezados ni formato Markdown (como negritas); responde solo "
            "con texto plano. No inventes tasas ni resultados."
        ),
        alias="AGENT_INSTRUCTIONS",
    )
    agent_name: str = Field(default="My Agent", alias="AGENT_NAME")
    agent_description: str = Field(
        default="An AI agent",
        alias="AGENT_DESCRIPTION",
    )
    agent_base_url: str = Field(
        default="http://localhost:8003",
        alias="AGENT_BASE_URL",
    )
    agent_error_message: str = Field(
        default="Tuvimos un inconveniente. Intenta más tarde, por favor.",
        alias="AGENT_ERROR_MESSAGE",
        validation_alias=AliasChoices("AGENT_ERROR_MESSAGE",
                                      "agent_error_message"),
    )
    check_connectivity_on_startup: bool = Field(
        default=False,
        alias="CHECK_CONNECTIVITY_ON_STARTUP",
        validation_alias=AliasChoices("CHECK_CONNECTIVITY_ON_STARTUP",
                                      "check_connectivity_on_startup"),
    )
    auth_provider_url: str = Field(
        default="http://auth-service:8000/auth/validate",
        alias="AUTH_PROVIDER_URL",
        validation_alias=AliasChoices("AUTH_PROVIDER_URL", "auth_provider_url"),
    )

    # Sub-configurations
    otel_config: OpenTelemetryConfig = Field(
        default_factory=OpenTelemetryConfig
    )
    logger: LoggerConfig = Field(default_factory=LoggerConfig)
    aws: AwsConfig = Field(default_factory=AwsConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    llm: LlmConfig = Field(default_factory=LlmConfig)


    # MCP Connections
    mcp_connections: List[Dict[str, str]] = Field(default_factory=list)

    @model_validator(mode='before')
    @classmethod
    def load_mcp_connections(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        connections = []
        i = 1
        while True:
            name_var = f"MCP_CONNECTION_{i}_NAME"
            endpoint_var = f"MCP_CONNECTION_{i}_ENDPOINT"
            name = data.get(name_var, os.getenv(name_var))
            endpoint = data.get(endpoint_var, os.getenv(endpoint_var))
            if name and endpoint:
                connections.append({"name": name, "endpoint": endpoint})
                i += 1
            else:
                break
        if connections:
            data['mcp_connections'] = connections
        i = 1
        while f"MCP_CONNECTION_{i}_NAME" in data:
            del data[f"MCP_CONNECTION_{i}_NAME"]
            del data[f"MCP_CONNECTION_{i}_ENDPOINT"]
            i += 1
        return data