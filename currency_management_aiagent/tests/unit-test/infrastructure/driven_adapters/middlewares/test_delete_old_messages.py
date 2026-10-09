import pytest
from unittest.mock import MagicMock
from langchain.messages import HumanMessage, AIMessage
from infrastructure.driven_adapters.langgraph_agent.middlewares.delete_old_messages_middleware import (
    DeleteOldMessagesMiddleware,
)


@pytest.fixture
def mw():
    return DeleteOldMessagesMiddleware(max_messages_to_keep=4)


def test_init(mw):
    assert mw.max_messages_to_keep == 4


def test_group_single_turn(mw):
    msgs = [HumanMessage(content="hi"), AIMessage(content="hello")]
    assert len(mw._group_messages_by_conversation_turn(msgs)) == 1


def test_group_multi_turn(mw):
    msgs = [
        HumanMessage(content="1"), AIMessage(content="a"),
        HumanMessage(content="2"), AIMessage(content="b"),
        HumanMessage(content="3"), AIMessage(content="c"),
    ]
    assert len(mw._group_messages_by_conversation_turn(msgs)) == 3


def test_group_empty(mw):
    assert mw._group_messages_by_conversation_turn([]) == []


def test_select_respects_limit(mw):
    groups = [[HumanMessage(content=str(i)), AIMessage(content="a")] for i in range(5)]
    kept = mw._select_groups_to_keep(groups)
    assert sum(len(g) for g in kept) <= 4


def test_select_empty():
    assert DeleteOldMessagesMiddleware(max_messages_to_keep=10)._select_groups_to_keep([]) == []


def test_select_all_fit():
    mw = DeleteOldMessagesMiddleware(max_messages_to_keep=100)
    groups = [[HumanMessage(content="1"), AIMessage(content="a")]]
    assert len(mw._select_groups_to_keep(groups)) == 1


@pytest.mark.asyncio
async def test_aafter_agent_under_limit(mw):
    msgs = [HumanMessage(content="hi", id="h1"), AIMessage(content="ok", id="a1")]
    state = {"messages": msgs}
    runtime = MagicMock()
    result = await mw.aafter_agent(state, runtime)
    assert result is None


@pytest.mark.asyncio
async def test_aafter_agent_over_limit():
    mw = DeleteOldMessagesMiddleware(max_messages_to_keep=2)
    msgs = [
        HumanMessage(content="1", id="h1"), AIMessage(content="a", id="a1"),
        HumanMessage(content="2", id="h2"), AIMessage(content="b", id="a2"),
        HumanMessage(content="3", id="h3"), AIMessage(content="c", id="a3"),
    ]
    state = {"messages": msgs}
    runtime = MagicMock()
    result = await mw.aafter_agent(state, runtime)
    assert result is not None
    assert "messages" in result
    assert len(result["messages"]) > 0
