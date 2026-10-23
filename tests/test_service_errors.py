"""Billing failures remain distinct, safe to display, and retryable after top-up."""

import httpx
import pytest

from triptwin.service_errors import BILLING_UNAVAILABLE_MESSAGE, is_billing_failure
from triptwin.functional_examples import example_trip


@pytest.mark.parametrize("status,body,expected", [
    (402, {}, True),
    (403, {"code": "Arrearage", "message": "Access denied, account is in arrearage."}, True),
    (400, {"error": {"code": "InsufficientBalance"}}, True),
    (403, {"code": "AccessDenied"}, False),
    (429, {"code": "Throttling.RateQuota"}, False),
    (500, {"message": "Internal server error"}, False),
])
def test_billing_status_is_not_confused_with_other_failures(status, body, expected):
    response = httpx.Response(status, json=body, request=httpx.Request("POST", "https://example.test"))
    assert is_billing_failure(response) is expected
    with pytest.raises(httpx.HTTPStatusError) as error:
        response.raise_for_status()
    assert is_billing_failure(error.value) is expected


def test_question_billing_toast_is_not_cached_and_recovers(monkeypatch):
    import app
    warnings = []
    monkeypatch.setattr(app.gr, "Warning", lambda message, **kwargs: warnings.append(message))
    monkeypatch.setattr(app, "reserve_global", lambda *_: (True, 1, 0))
    response = httpx.Response(403, json={"code": "Arrearage"}, request=httpx.Request("POST", "https://example.test"))
    def failed(*_):
        response.raise_for_status()
    monkeypatch.setattr(app, "answer_with_trip_context", failed)
    state = {"trip": example_trip("multi"), "trip_source": "uploaded_image"}
    _, history, store = app.answer_question_guarded("帮我解释行程", [], state, None)
    assert warnings == [BILLING_UNAVAILABLE_MESSAGE]
    assert history[-1]["content"] == BILLING_UNAVAILABLE_MESSAGE
    assert not store.get("answer_cache")
    monkeypatch.setattr(app, "answer_with_trip_context", lambda *_: "服务已恢复。")
    _, history, store = app.answer_question_guarded("帮我解释行程", history, state, store)
    assert history[-1]["content"] == "服务已恢复。"
    assert len(store["answer_cache"]) == 1


def test_image_billing_failure_shows_safe_popup(monkeypatch, tmp_path):
    import app
    from PIL import Image
    path = tmp_path / "upload.png"
    Image.new("RGB", (24, 24), "white").save(path)
    monkeypatch.setattr(app, "reserve_global", lambda *_: (True, 1, 0))
    def failed(*_):
        response = httpx.Response(403, json={"code": "Arrearage", "private": "never display"}, request=httpx.Request("POST", "https://example.test"))
        response.raise_for_status()
    monkeypatch.setattr(app, "build_twin", failed)
    with pytest.raises(app.gr.Error, match="余额不足或已欠费") as error:
        app.build_twin_guarded([path], True, None)
    assert "never display" not in str(error.value)


def test_managed_agent_billing_error_is_safe_and_not_retried():
    from triptwin.bailian_client import BailianApiError, BailianManagedAgentClient
    from triptwin.config import Settings
    settings = Settings(dashscope_api_key="test-key", flyai_api_key="test-flyai", bailian_workspace_id="ws", bailian_agent_id="agent", bailian_environment_id="env")
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(403, json={"code": "Arrearage", "message": "test-key"})
    with httpx.Client(base_url="https://example.test", transport=httpx.MockTransport(handler)) as http:
        agent = BailianManagedAgentClient(settings, client=http)
        with pytest.raises(BailianApiError, match="余额不足或已欠费") as error:
            agent.list_sessions()
    assert len(calls) == 1
    assert "test-key" not in str(error.value)
