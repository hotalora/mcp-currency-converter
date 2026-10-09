import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.langchain import LangchainInstrumentor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter
)


def activate_open_telemetry():
    """Activate OpenTelemetry instrumentation for the application."""
    if os.getenv("OTEL_ENABLED", "false").lower() != "true":
        return
    provider = TracerProvider()
    trace.set_tracer_provider(provider)
    span_processor = BatchSpanProcessor(OTLPSpanExporter())
    provider.add_span_processor(span_processor)
    LangchainInstrumentor().instrument()