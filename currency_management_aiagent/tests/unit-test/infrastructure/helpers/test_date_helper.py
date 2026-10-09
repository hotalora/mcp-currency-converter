import re
from infrastructure.driven_adapters.langgraph_agent.helpers.date_helper import (
    format_current_date,
    resolve_current_date_placeholder,
    CURRENT_DATE_PLACEHOLDER,
    DEFAULT_TIMEZONE,
)

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class TestFormatCurrentDate:
    def test_valid_timezone(self):
        result = format_current_date("UTC")
        assert DATE_PATTERN.match(result)

    def test_bogota_timezone(self):
        result = format_current_date("America/Bogota")
        assert DATE_PATTERN.match(result)

    def test_invalid_timezone_uses_fallback(self):
        result = format_current_date("Invalid/Zone")
        assert DATE_PATTERN.match(result)

    def test_empty_string_uses_default(self):
        result = format_current_date("")
        assert DATE_PATTERN.match(result)

    def test_none_uses_default(self):
        result = format_current_date(None)
        assert DATE_PATTERN.match(result)

    def test_default_timezone_constant(self):
        assert DEFAULT_TIMEZONE == "America/Bogota"


class TestResolvePlaceholder:
    def test_replaces_placeholder(self):
        prompt = f"Today is {CURRENT_DATE_PLACEHOLDER}. Be helpful."
        result = resolve_current_date_placeholder(prompt, "UTC")
        assert CURRENT_DATE_PLACEHOLDER not in result
        assert "202" in result

    def test_no_placeholder_returns_unchanged(self):
        prompt = "No placeholder here."
        assert resolve_current_date_placeholder(prompt, "UTC") == prompt

    def test_multiple_placeholders(self):
        prompt = f"Start: {CURRENT_DATE_PLACEHOLDER}, End: {CURRENT_DATE_PLACEHOLDER}"
        result = resolve_current_date_placeholder(prompt, "UTC")
        assert result.count("202") == 2
        assert CURRENT_DATE_PLACEHOLDER not in result

    def test_placeholder_constant(self):
        assert "CURRENT_DATE" in CURRENT_DATE_PLACEHOLDER
