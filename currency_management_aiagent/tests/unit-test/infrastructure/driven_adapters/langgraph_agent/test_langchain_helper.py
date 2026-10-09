from unittest.mock import MagicMock
from infrastructure.driven_adapters.langgraph_agent.helpers.langchain_helper import (
    json_schema_to_fields,
    create_injected_tool,
)


class TestJsonSchemaToFields:
    def test_string_field(self):
        schema = {"properties": {"name": {"type": "string", "description": "A name"}}, "required": ["name"]}
        fields = json_schema_to_fields(schema)
        assert fields["name"][0] is str
        assert fields["name"][1] is ...

    def test_integer_field(self):
        schema = {"properties": {"age": {"type": "integer"}}, "required": []}
        assert json_schema_to_fields(schema)["age"][0] is int

    def test_number_field(self):
        schema = {"properties": {"score": {"type": "number"}}, "required": []}
        assert json_schema_to_fields(schema)["score"][0] is float

    def test_boolean_field(self):
        schema = {"properties": {"active": {"type": "boolean"}}, "required": ["active"]}
        assert json_schema_to_fields(schema)["active"][0] is bool

    def test_unknown_type(self):
        from typing import Any
        schema = {"properties": {"data": {"type": "object"}}, "required": []}
        assert json_schema_to_fields(schema)["data"][0] is Any

    def test_empty_properties(self):
        assert json_schema_to_fields({"properties": {}, "required": []}) == {}

    def test_multiple_fields(self):
        schema = {"properties": {"a": {"type": "string"}, "b": {"type": "integer"}}, "required": ["a"]}
        f = json_schema_to_fields(schema)
        assert len(f) == 2
        assert f["a"][1] is ...
        assert f["b"][1] is None


class TestCreateInjectedTool:
    def test_non_structured_tool_returns_same(self):
        tool = MagicMock()
        tool.__class__.__name__ = "NotStructuredTool"
        from langchain_core.tools import BaseTool
        result = create_injected_tool(tool, {"userIdentifier"})
        assert result is tool

    def test_no_args_schema_returns_same(self):
        from langchain_core.tools import StructuredTool
        tool = MagicMock(spec=StructuredTool)
        tool.args_schema = None
        result = create_injected_tool(tool, {"userIdentifier"})
        assert result is tool

    def test_dict_schema_creates_injected(self):
        from langchain_core.tools import StructuredTool
        tool = MagicMock(spec=StructuredTool)
        tool.name = "test_tool"
        tool.description = "A test tool"
        tool.coroutine = AsyncMock() if False else MagicMock()
        tool.args_schema = {
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "userIdentifier": {"type": "string", "description": "User ID"},
            },
            "required": ["query"],
        }
        result = create_injected_tool(tool, {"userIdentifier"})
        assert result.name == "test_tool"

    def test_non_dict_schema_returns_same(self):
        from langchain_core.tools import StructuredTool
        tool = MagicMock(spec=StructuredTool)
        tool.args_schema = MagicMock()  # Not a dict
        type(tool.args_schema).__name__ = "SomeSchema"
        result = create_injected_tool(tool, {"userIdentifier"})
        assert result is tool
