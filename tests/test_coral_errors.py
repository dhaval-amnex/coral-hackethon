from incident_captain.coral import classify_coral_error


def test_classify_coral_error_auth() -> None:
    assert classify_coral_error("Unauthorized: invalid token") == "auth"


def test_classify_coral_error_rate_limit() -> None:
    assert classify_coral_error("429 too many requests") == "rate_limit"


def test_classify_coral_error_network() -> None:
    assert classify_coral_error("connection timed out") == "network"

