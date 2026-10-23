"""Per-session editing preserves the selected trip and browser history."""

import pytest

from triptwin.session_history import (
    create_session, delete_session, ensure_active_session, rename_session,
    save_active_session,
)
from triptwin.session_sidebar import current_session_html, history_sidebar_html


def test_custom_name_survives_autosave_and_switch_snapshot():
    store, session = ensure_active_session(None)
    store = rename_session(store, session["id"], "我的周末行程")
    store = save_active_session(store, {"trip_state": {"trip": {"title": "模型自动标题"}}})
    store, _ = create_session(store, current_snapshot={"status": "saved"})
    old = store["sessions"][0]
    assert old["title"] == "我的周末行程"
    assert old["title_is_custom"] is True
    assert old["snapshot"]["status"] == "saved"


@pytest.mark.parametrize("name", ["", "  ", "长" * 61, None])
def test_rename_rejects_invalid_names(name):
    store, session = ensure_active_session(None)
    with pytest.raises(ValueError):
        rename_session(store, session["id"], name)
    assert session["title"] == "新旅行会话"


def test_deleting_another_history_never_switches_current_session():
    store, first = ensure_active_session(None)
    store, second = create_session(store)
    store, active = delete_session(store, first["id"])
    assert active["id"] == second["id"] == store["active_id"]
    store, fresh = delete_session(store, second["id"])
    assert len(store["sessions"]) == 1
    assert fresh["id"] != second["id"]


def test_cards_separate_current_from_history_and_escape_names():
    store, first = ensure_active_session(None)
    store = rename_session(store, first["id"], '<img src=x onerror="attack">')
    store, current = create_session(store)
    html = history_sidebar_html(store)
    assert html.count('data-session-id=') == 1
    assert current["id"] not in html
    assert 'data-action="rename"' in html and 'data-action="delete"' in html
    assert '<img src=x' not in html
    assert '&lt;img' in html
    current_html = current_session_html(current)
    assert 'aria-current="true"' in current_html
    assert 'data-action="rename"' in current_html and 'data-action="delete"' in current_html


def test_rename_and_delete_other_session_preserve_unsaved_current_view():
    import app
    store, first = ensure_active_session(None)
    store, second = create_session(store)
    def action(data):
        return app.manage_history_session(
            store, {}, "未提交草稿", False, "risks", "plans", "trace", [], "", "",
            question_text="还未发送的问题", event=app.gr.EventData(None, data),
        )
    renamed = action({"id": first["id"], "action": "rename", "title": "新的历史名称"})
    assert renamed[0]["active_id"] == second["id"]
    assert renamed[0]["sessions"][0]["title"] == "新的历史名称"
    assert renamed[0]["sessions"][1]["snapshot"]["question_text"] == "还未发送的问题"
    assert all(value == app.gr.skip() for value in renamed[3:])
    deleted = action({"id": first["id"], "action": "delete"})
    assert deleted[0]["active_id"] == second["id"]
    assert len(deleted[0]["sessions"]) == 1
    assert all(value == app.gr.skip() for value in deleted[3:])


def test_deleting_current_session_restores_remaining_snapshot():
    import app
    store, first = ensure_active_session(None)
    store = save_active_session(store, {"status": "先前会话已保存"})
    store, second = create_session(store)
    result = app.manage_history_session(
        store, {}, "新会话", False, "", "", "", [], "", "",
        event=app.gr.EventData(None, {"id": second["id"], "action": "delete"}),
    )
    assert result[0]["active_id"] == first["id"]
    assert result[4] == "先前会话已保存"
