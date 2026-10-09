# --- BEGIN OTEL_TEST ---
import pytest
from infrastructure.helpers.tracing_context import with_trace_context


@pytest.mark.asyncio
async def test_decorator_without_headers():
    @with_trace_context
    async def handler(msg_value, message_headers=None):
        return "processed"

    result = await handler(b"data", message_headers=None)
    assert result == "processed"


@pytest.mark.asyncio
async def test_decorator_with_empty_headers():
    @with_trace_context
    async def handler(msg_value, message_headers=None):
        return "done"

    result = await handler(b"data", message_headers={})
    assert result == "done"
# --- END OTEL_TEST ---
