import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from infrastructure.driven_adapters.langgraph_agent.middlewares.tool_result_memory_filter_middleware import (
    ToolResultMemoryFilterMiddleware,
)


@pytest.fixture
def mw():
    return ToolResultMemoryFilterMiddleware([])


@pytest.fixture
def mw_specific():
    return ToolResultMemoryFilterMiddleware(["sumar"])


class TestShouldFilter:
    def test_empty_filters_all(self, mw):
        assert mw._should_filter_tool("anything") is True

    def test_specific_listed(self, mw_specific):
        assert mw_specific._should_filter_tool("sumar") is True

    def test_specific_unlisted(self, mw_specific):
        assert mw_specific._should_filter_tool("restar") is False


class TestFindLastGroup:
    def test_basic(self, mw):
        msgs = [
            HumanMessage(content="1", id="h1"), AIMessage(content="a", id="a1"),
            HumanMessage(content="2", id="h2"), AIMessage(content="b", id="a2"),
        ]
        assert mw._find_last_group(msgs)[0].content == "2"

    def test_no_human(self, mw):
        assert len(mw._find_last_group([AIMessage(content="a", id="a1")])) == 1

    def test_single_human(self, mw):
        assert len(mw._find_last_group([HumanMessage(content="s", id="h")])) == 1


class TestShouldRemove:
    def test_tool_with_id(self, mw):
        assert mw._should_remove_tool_message(
            ToolMessage(content="r", tool_call_id="tc", id="t1", name="s")
        ) is True

    def test_tool_no_id(self, mw):
        assert mw._should_remove_tool_message(
            ToolMessage(content="r", tool_call_id="tc", id=None, name="s")
        ) is False

    def test_ai_with_calls(self, mw):
        assert mw._should_remove_ai_message(
            AIMessage(content="", id="a1", tool_calls=[{"name": "s", "id": "tc", "args": {}}])
        ) is True

    def test_ai_no_id(self, mw):
        assert mw._should_remove_ai_message(
            AIMessage(content="", id=None, tool_calls=[{"name": "s", "id": "tc", "args": {}}])
        ) is False


class TestGetMessagesToRemove:
    def test_removes_both(self, mw):
        ai = AIMessage(content="", id="a1", tool_calls=[{"name": "s", "id": "tc", "args": {}}])
        tool = ToolMessage(content="15", tool_call_id="tc", id="t1", name="s")
        assert len(mw._get_messages_to_remove([ai, tool])) == 2

    def test_specific_skips(self, mw_specific):
        tool = ToolMessage(content="r", tool_call_id="tc", id="t1", name="restar")
        assert len(mw_specific._get_messages_to_remove([tool])) == 0

    def test_empty(self, mw):
        assert mw._get_messages_to_remove([]) == []


class TestAafterAgent:
    @pytest.mark.asyncio
    async def test_empty_messages(self, mw):
        result = await mw.aafter_agent({"messages": []}, MagicMock())
        assert result is None

    @pytest.mark.asyncio
    async def test_no_tools_to_remove(self, mw_specific):
        msgs = [
            HumanMessage(content="hi", id="h1"),
            AIMessage(content="hello", id="a1"),
        ]
        result = await mw_specific.aafter_agent({"messages": msgs}, MagicMock())
        assert result is None

    @pytest.mark.asyncio
    async def test_removes_tool_messages(self, mw):
        msgs = [
            HumanMessage(content="hi", id="h1"),
            AIMessage(content="", id="a1", tool_calls=[{"name": "s", "id": "tc", "args": {}}]),
            ToolMessage(content="15", tool_call_id="tc", id="t1", name="s"),
            AIMessage(content="result is 15", id="a2"),
        ]
        with patch("infrastructure.driven_adapters.langgraph_agent.middlewares.tool_result_memory_filter_middleware.get_config",
                    return_value={"configurable": {"thread_id": "test"}}):
            result = await mw.aafter_agent({"messages": msgs}, MagicMock())
        assert result is not None
        assert len(result["messages"]) == 2

    @pytest.mark.asyncio
    async def test_handles_get_config_error(self, mw):
        msgs = [
            HumanMessage(content="hi", id="h1"),
            AIMessage(content="", id="a1", tool_calls=[{"name": "s", "id": "tc", "args": {}}]),
            ToolMessage(content="15", tool_call_id="tc", id="t1", name="s"),
            AIMessage(content="done", id="a2"),
        ]
        with patch("infrastructure.driven_adapters.langgraph_agent.middlewares.tool_result_memory_filter_middleware.get_config",
                    side_effect=RuntimeError("no config")):
            result = await mw.aafter_agent({"messages": msgs}, MagicMock())
        assert result is not None
