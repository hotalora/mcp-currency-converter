from infrastructure.entry_points.api.dto.chat_request import (
    ChatRequest,
    ChatResponse,
)


def test_minimal():
    r = ChatRequest(message="hola")
    assert r.message == "hola"
    assert r.conversation_id == "default"


def test_custom_conversation_id():
    r = ChatRequest(message="hi", conversation_id="abc-123")
    assert r.conversation_id == "abc-123"


def test_none_conversation_id():
    r = ChatRequest(message="hi", conversation_id=None)
    assert r.conversation_id is None


def test_chat_response_uses_plain_text_messages():
    response = ChatResponse.model_validate({
        "conversation_id": "demo",
        "messages": [
            {
                "type": "text",
                "content": "¡Listo! 25 USD equivalen a 22.31 EUR.",
            }
        ],
    })

    assert response.messages[0].type == "text"
    assert response.messages[0].content == "¡Listo! 25 USD equivalen a 22.31 EUR."
