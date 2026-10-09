from infrastructure.entry_points.api.dto.chat_request import ChatRequest


def test_chat_request_defaults():
    r = ChatRequest(message="hola")
    assert r.conversation_id == "default"
