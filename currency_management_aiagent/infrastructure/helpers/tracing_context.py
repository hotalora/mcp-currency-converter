import functools
from typing import Any, Callable
from opentelemetry.trace.propagation.tracecontext import (
    TraceContextTextMapPropagator
)
from opentelemetry import context


def with_trace_context(func: Callable):
    """Decorator to extract and set OpenTelemetry context from Kafka headers."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        message_headers = kwargs.get('message_headers')
        if not message_headers and len(args) >= 3:
            message_headers = args[2]
        if not message_headers and not isinstance(message_headers, dict):
            return await func(*args, **kwargs)

        propagator = TraceContextTextMapPropagator()
        ctx = propagator.extract(carrier=message_headers)

        token = context.attach(ctx)
        try:
            return await func(*args, **kwargs)
        finally:
            context.detach(token)

    return wrapper
