from domain.model.error import AgentInitializationError


def test_is_exception():
    e = AgentInitializationError("test error")
    assert isinstance(e, Exception)
    assert str(e) == "test error"


def test_empty_message():
    e = AgentInitializationError("")
    assert str(e) == ""


def test_can_be_raised_and_caught():
    try:
        raise AgentInitializationError("oops")
    except AgentInitializationError as exc:
        assert "oops" in str(exc)
