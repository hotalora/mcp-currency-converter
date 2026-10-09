from domain.model.agent_message import AgentRequest, AgentResponse, TextMessage, MessageType


class TestTextMessage:
    def test_defaults(self):
        m = TextMessage(content="hello")
        assert m.type == "text"
        assert m.content == "hello"

    def test_custom_type(self):
        m = TextMessage(content="x", type="image")
        assert m.type == "image"


class TestAgentRequest:
    def test_creation(self):
        r = AgentRequest(conversation_id="c1", user_message="hi", metadata={"k": "v"})
        assert r.conversation_id == "c1"
        assert r.user_message == "hi"
        assert r.user_id is None

    def test_with_user_id(self):
        r = AgentRequest(conversation_id="c1", user_message="hi", metadata={}, user_id="u1")
        assert r.user_id == "u1"

    def test_metadata_preserved(self):
        meta = {"UserIdentifier": "u1", "ApplicationIdentifier": "app1"}
        r = AgentRequest(conversation_id="c1", user_message="hi", metadata=meta)
        assert r.metadata["UserIdentifier"] == "u1"


class TestAgentResponse:
    def test_success(self):
        r = AgentResponse(
            conversation_id="c1",
            agent_response=[TextMessage(content="ok")],
            status="success", metadata={},
        )
        assert r.status == "success"
        assert r.error_message is None
        assert len(r.agent_response) == 1

    def test_error(self):
        r = AgentResponse(
            conversation_id="c1", agent_response=[], status="error",
            metadata={}, error_message="boom",
        )
        assert r.error_message == "boom"
        assert r.agent_response == []

    def test_empty_response(self):
        r = AgentResponse(
            conversation_id="c1", agent_response=[], status="success", metadata={},
        )
        assert len(r.agent_response) == 0
