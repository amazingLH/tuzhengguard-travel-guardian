"""Question answering retains original plans and stays within one session."""

from copy import deepcopy

import httpx

from triptwin.functional_examples import example_trip
from triptwin.qa_context import build_session_context
from triptwin.session_history import create_session, ensure_active_session, save_active_session, switch_session
from triptwin.service_errors import FREE_QUOTA_UNAVAILABLE_MESSAGE, model_failure_message


def test_pending_local_options_and_conversation_are_in_model_context():
    import app
    state = {"trip": example_trip("conflict"), "trip_source": "ticket_example"}
    planned = app.generate_plan_b(state, True)[2]
    messages = [{"role": "user", "content": "我更想去葫芦岛"}, {"role": "assistant", "content": "可以比较两个候选。"}]
    context = build_session_context(planned, messages)
    assert len(context["local_plan_b"]["available_options"]) == 2
    assert context["conversation_history"][0]["content"] == "我更想去葫芦岛"
    assert len(context["trip"]["events"]) == 3


def test_applied_plan_retains_original_and_all_candidates_after_restore(monkeypatch):
    import app
    state = {"trip": example_trip("conflict"), "trip_source": "ticket_example"}
    plan_text, _, planned, _, _ = app.generate_plan_b(state, True)
    store = save_active_session(None, {"trip_state": planned, "plan_b": plan_text, "risks": "原方案存在重叠"})
    selected = planned["local_plan_options"][0]
    applied = app.apply_local_option(selected["id"], planned)[3]
    assert len(planned["trip"]["events"]) == 3  # Original state is not mutated.
    store = save_active_session(store, {"trip_state": applied, "plan_b": "已应用替代方案"})
    store, first = ensure_active_session(store)
    store, _ = create_session(store)
    store, restored = switch_session(store, first["id"])
    observed = {}
    def model(question, context):
        observed.update(context)
        return "原方案有重叠，Plan B 保留一个目的地并消除已知冲突。"
    monkeypatch.setattr(app, "answer_with_trip_context", model)
    monkeypatch.setattr(app, "reserve_global", lambda *_: (True, 1, 0))
    _, messages, _ = app.answer_question_guarded("Plan B 比第一个计划好在哪里？", [], restored["snapshot"]["trip_state"], store)
    revision = observed["plan_revisions"][0]
    assert len(revision["original_trip"]["events"]) == 3
    assert len(revision["applied_trip"]["events"]) == 2
    assert len(revision["available_options"]) == 2
    assert revision["before_risks"] == 1 and revision["after_risks"] == 0
    assert observed["earlier_workspaces"][0]["workspace"]["plan_b"] == plan_text
    assert "重叠" in messages[-1]["content"]


def test_old_workspace_and_messages_survive_reimport_without_media_bytes():
    store = save_active_session(None, {
        "trip_state": {"trip": example_trip("conflict")}, "plan_b": "先前生成的两个方案",
        "chat_history": [{"role": "user", "content": "记住我想去秦皇岛"}],
    })
    store = save_active_session(store, {"trip_state": {}, "chat_history": []})
    _, session = ensure_active_session(store)
    context = build_session_context({}, [], session["snapshot"])
    assert context["earlier_conversations"][0][0]["content"] == "记住我想去秦皇岛"
    assert len(context["earlier_workspaces"][0]["workspace"]["trip_state"]["trip"]["events"]) == 3
    assert "image_previews" not in context["earlier_workspaces"][0]["workspace"]


def test_full_conversation_is_not_silently_cut_to_last_hundred_messages():
    messages = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"第 {i} 条消息"} for i in range(120)]
    store = save_active_session(None, {"chat_history": messages})
    _, session = ensure_active_session(store)
    assert session["snapshot"]["chat_history"] == messages
    assert len(build_session_context({}, messages)["conversation_history"]) == 120


def test_followup_and_other_session_do_not_reuse_wrong_cached_answers(monkeypatch):
    import app
    calls = []
    def model(question, context):
        calls.append(deepcopy(context))
        return f"第 {len(calls)} 次上下文回答。"
    monkeypatch.setattr(app, "answer_with_trip_context", model)
    monkeypatch.setattr(app, "reserve_global", lambda *_: (True, 1, 0))
    state = {"trip": example_trip("multi"), "trip_source": "ticket_example"}
    _, _, store = app.answer_question_guarded("怎么看？", [], state, None)
    history = [{"role": "user", "content": "我刚才说的是酒店预算"}]
    _, _, store = app.answer_question_guarded("怎么看？", history, state, store)
    store, new = create_session(store)
    _, _, store = app.answer_question_guarded("怎么看？", [], {}, store)
    assert len(calls) == 3
    assert calls[1]["conversation_history"] == history
    assert not calls[2]["current_workspace"]["trip_state"]
    assert not calls[2]["earlier_workspaces"]
    assert not calls[2]["conversation_history"]
    assert store["active_id"] == new["id"]


def test_dialogue_only_autosaves_do_not_duplicate_workspace_archive():
    state = {"trip": example_trip("multi")}
    store = save_active_session(None, {"trip_state": state, "chat_history": []})
    for i in range(3):
        store = save_active_session(store, {"trip_state": state, "chat_history": [{"role": "user", "content": str(i)}]})
    _, session = ensure_active_session(store)
    assert session["snapshot"]["workspace_history"] == []


def test_free_quota_error_is_actionable_not_cached_and_not_marked_success(monkeypatch):
    import app
    response = httpx.Response(403, json={"error": {"code": "insufficient_quota", "message": "Free quota exhausted; disable use free tier only."}}, request=httpx.Request("POST", "https://example.test"))
    error = httpx.HTTPStatusError("provider refused", request=response.request, response=response)
    assert model_failure_message(error) == FREE_QUOTA_UNAVAILABLE_MESSAGE
    def model(*_):
        raise error
    monkeypatch.setattr(app, "answer_with_trip_context", model)
    monkeypatch.setattr(app, "reserve_global", lambda *_: (True, 1, 0))
    monkeypatch.setattr(app.gr, "Warning", lambda *args, **kwargs: None)
    result = app.timed_operation(app.answer_question_guarded, "行程问答")("请比较方案", [], {}, None)
    assert result[1][-1]["content"] == FREE_QUOTA_UNAVAILABLE_MESSAGE
    assert result[2]["answer_cache"] == {}
    assert result[-1].startswith("⚠️") and "未完成" in result[-1]
