"""Free quota exhaustion switches models without losing session or image data."""

import copy
import json

import httpx
import pytest
from PIL import Image

from triptwin.config import ModelSettings
from triptwin.functional_examples import example_trip
from triptwin.model_routing import request_model
from triptwin.service_errors import (
    FALLBACK_QUOTA_UNAVAILABLE_MESSAGE, FallbackQuotaBlockedError,
    is_model_failure_reply, model_failure_message,
)
from triptwin.trip_assistant import answer_with_trip_context
from triptwin.vision_parser import extract_trip_from_images


def install_transport(monkeypatch, handler):
    original = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))


def settings():
    return ModelSettings(dashscope_api_key="test-key", bailian_workspace_id="ws-test")


def test_question_falls_back_once_with_entire_session_and_reply_limit(monkeypatch):
    calls = []
    def handler(request):
        calls.append(json.loads(request.content))
        if len(calls) == 1:
            return httpx.Response(403, json={"code": "AllocationQuota.FreeTierOnly"})
        return httpx.Response(200, json={"choices": [{"message": {"content": "旅" * 350}}]})
    install_transport(monkeypatch, handler)
    context = {"trip": example_trip("multi"), "plan_revisions": [{"original_trip": example_trip("conflict")}], "conversation_history": [{"role": "user", "content": "我想比较原方案"}]}
    result = answer_with_trip_context("原方案呢？", context, settings=settings())
    assert [p["model"] for p in calls] == ["deepseek-v4.1-flash-1017", "qwen3.7-flash"]
    assert calls[0]["messages"] == calls[1]["messages"]
    assert json.loads(calls[1]["messages"][1]["content"].split("：\n", 1)[1])["verified_context"] == context
    assert len(result) == 300


@pytest.mark.parametrize("status,body", [
    (401, {"code": "InvalidApiKey"}),
    (403, {"code": "AccessDenied"}),
    (403, {"code": "Arrearage"}),
    (402, {"code": "insufficient_quota"}),
    (429, {"code": "Throttling.RateQuota"}),
    (500, {"message": "Internal server error"}),
])
def test_other_errors_do_not_trigger_paid_model(monkeypatch, status, body):
    calls = []
    def handler(request):
        calls.append(json.loads(request.content))
        return httpx.Response(status, json=body)
    install_transport(monkeypatch, handler)
    with pytest.raises(httpx.HTTPStatusError):
        answer_with_trip_context("比较方案", {}, settings=settings())
    assert len(calls) == 1


def test_blocked_fallback_is_bounded_actionable_and_not_a_cacheable_reply(monkeypatch):
    calls = []
    def handler(request):
        calls.append(json.loads(request.content))
        return httpx.Response(403, json={"error": {"code": "insufficient_quota", "message": "private upstream payload"}})
    install_transport(monkeypatch, handler)
    with pytest.raises(FallbackQuotaBlockedError) as exc:
        answer_with_trip_context("比较方案", {}, settings=settings())
    assert len(calls) == 2
    message = model_failure_message(exc.value)
    assert message == FALLBACK_QUOTA_UNAVAILABLE_MESSAGE
    assert is_model_failure_reply(message)
    assert "private" not in message


def test_successful_primary_never_calls_paid_model_and_payload_is_not_mutated():
    calls = []
    def handler(request):
        calls.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": []})
    payload = {"model": "primary", "messages": [{"role": "user", "content": "hello"}]}
    original = copy.deepcopy(payload)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = request_model(client, "https://example.test", headers={}, payload=payload, fallback_model="fallback")
    assert len(calls) == 1 and result.model == "primary"
    assert payload == original and result.fallback_reason is None


def test_vision_repair_stays_on_fallback_and_preserves_all_images(monkeypatch, tmp_path):
    paths = [tmp_path / "a.png", tmp_path / "b.png"]
    for path, color in zip(paths, ("red", "blue")):
        Image.new("RGB", (40, 80), color).save(path)
    entries = []
    for index in (1, 2):
        trip = example_trip("multi")
        event = trip["events"][index - 1]
        event.update(depends_on=[], transfer_from_event_id=None)
        trip.update(events=[event], constraints={"budget_cny": None, "protected_event_ids": []})
        entries.append({"image_index": index, "trip": trip, "field_confidence": {}, "notes": []})
    calls = []
    def handler(request):
        calls.append(json.loads(request.content))
        if len(calls) == 1:
            return httpx.Response(403, json={"error": {"code": "insufficient_quota"}})
        content = {"images": []} if len(calls) == 2 else {"images": entries}
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(content)}}]})
    install_transport(monkeypatch, handler)
    extraction, meta = extract_trip_from_images(paths, settings=settings())
    assert [p["model"] for p in calls] == ["deepseek-v4.1-flash-1017", "qwen3.7-flash", "qwen3.7-flash"]
    assert calls[0]["messages"] == calls[1]["messages"]
    assert calls[1]["messages"][1] == calls[2]["messages"][1]
    assert len([b for b in calls[2]["messages"][1]["content"] if b["type"] == "image_url"]) == 2
    assert meta["model"] == "qwen3.7-flash" and meta["attempts"] == 3
    assert meta["fallback_reason"] == "free_quota_exhausted"
    assert len(meta["image_report"]) == 2
    trip = extraction.trip.model_dump() if hasattr(extraction.trip, "model_dump") else extraction.trip
    assert len(trip["events"]) == 2


def test_explicit_model_override_does_not_route_to_a_different_model(monkeypatch):
    calls = []
    def handler(request):
        calls.append(json.loads(request.content))
        return httpx.Response(403, json={"code": "AllocationQuota.FreeTierOnly"})
    install_transport(monkeypatch, handler)
    with pytest.raises(httpx.HTTPStatusError):
        answer_with_trip_context("测试指定模型", {}, settings=settings(), model="explicit-model")
    assert [p["model"] for p in calls] == ["explicit-model"]
