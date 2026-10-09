from infrastructure.driven_adapters.langgraph_agent.models import ContextSchema, ResponseFormat
from domain.model.agent_message import TextMessage


class TestContextSchema:
    def test_creation(self):
        c = ContextSchema(userIdentifier="user1", applicationIdentifier="app1")
        assert c.userIdentifier == "user1"
        assert c.applicationIdentifier == "app1"

    def test_model_dump(self):
        c = ContextSchema(userIdentifier="u", applicationIdentifier="a")
        d = c.model_dump()
        assert "userIdentifier" in d
        assert "applicationIdentifier" in d

    def test_model_fields(self):
        fields = set(ContextSchema.model_fields.keys())
        assert "userIdentifier" in fields
        assert "applicationIdentifier" in fields


class TestResponseFormat:
    def test_single_text_message(self):
        response = ResponseFormat(messages=[TextMessage(content="Hola")])
        assert response.messages[0].content == "Hola"

    def test_multiple_text_messages(self):
        response = ResponseFormat(
            messages=[TextMessage(content="Hola"), TextMessage(content="Adios")]
        )
        assert len(response.messages) == 2

    def test_empty(self):
        response = ResponseFormat(messages=[])
        assert response.messages == []
