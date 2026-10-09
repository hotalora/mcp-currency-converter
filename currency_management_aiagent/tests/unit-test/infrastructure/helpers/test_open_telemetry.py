# --- BEGIN OTEL_TEST ---
from unittest.mock import patch, MagicMock
import os


def test_disabled_when_false():
    with patch.dict(os.environ, {"OTEL_ENABLED": "false"}):
        from infrastructure.helpers.open_telemetry import activate_open_telemetry
        activate_open_telemetry()


def test_disabled_when_missing():
    env = {k: v for k, v in os.environ.items() if k != "OTEL_ENABLED"}
    with patch.dict(os.environ, env, clear=True):
        from infrastructure.helpers.open_telemetry import activate_open_telemetry
        activate_open_telemetry()


def test_enabled_instruments():
    import infrastructure.helpers.open_telemetry as otel_mod

    with patch.dict(os.environ, {"OTEL_ENABLED": "true"}), \
         patch.object(otel_mod, "TracerProvider", return_value=MagicMock()) as mock_tp, \
         patch.object(otel_mod, "BatchSpanProcessor"), \
         patch.object(otel_mod, "OTLPSpanExporter"), \
         patch.object(otel_mod, "LangchainInstrumentor"), \
         patch.object(otel_mod, "trace") as mock_trace:
        if hasattr(otel_mod, "AIOKafkaInstrumentor"):
            with patch.object(otel_mod, "AIOKafkaInstrumentor"):
                otel_mod.activate_open_telemetry()
        else:
            otel_mod.activate_open_telemetry()
        mock_trace.set_tracer_provider.assert_called_once()
# --- END OTEL_TEST ---