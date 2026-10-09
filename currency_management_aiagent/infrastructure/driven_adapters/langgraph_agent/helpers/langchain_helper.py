from typing import Any, Dict, Annotated
from pydantic import create_model, Field
from langchain_core.tools import BaseTool, InjectedToolArg, StructuredTool


def json_schema_to_fields(schema_dict: Dict[str, Any]) -> Dict[str, tuple]:
    """Convert JSON schema properties to create_model fields."""
    fields = {}
    properties = schema_dict.get("properties", {})
    required = set(schema_dict.get("required", []))

    for prop, info in properties.items():
        type_str = info.get("type")
        if type_str == "string":
            typ = str
        elif type_str == "integer":
            typ = int
        elif type_str == "number":
            typ = float
        elif type_str == "boolean":
            typ = bool
        else:
            typ = Any

        default = ... if prop in required else None
        description = info.get("description", "")
        fields[prop] = (typ, default, description)

    return fields


def create_injected_tool(original_tool: BaseTool,
                         context_fields: set) -> BaseTool:
    """Create a tool with injected args for context fields."""
    if not isinstance(original_tool, StructuredTool):
        return original_tool

    if original_tool.args_schema is None:
        return original_tool

    fields: Dict[str, Any] = {}

    if isinstance(original_tool.args_schema, dict):
        temp_fields = json_schema_to_fields(original_tool.args_schema)
        for k, (typ, default, description) in temp_fields.items():
            if k in context_fields:
                fields[k] = (Annotated[typ, InjectedToolArg])
            else:
                fields[k] = (typ, Field(default=default,
                                        description=description))
    else:
        return original_tool

    new_schema_name = f"{original_tool.name}InjectedSchema"
    new_schema = create_model(new_schema_name, **fields)

    new_tool = StructuredTool(name=original_tool.name,
                              description=original_tool.description,
                              coroutine=original_tool.coroutine,
                              args_schema=new_schema)
    return new_tool
