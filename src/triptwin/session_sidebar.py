"""Accessible session cards and per-session actions for the sidebar."""

from html import escape
from typing import Any

from triptwin.session_history import history_choices


def session_card_html(session: dict[str, Any], metadata: str, *, current: bool = False) -> str:
    title = escape(str(session.get("title") or "新旅行会话"), quote=True)
    identifier = escape(session["id"], quote=True)
    current_attr = ' aria-current="true"' if current else ""
    return f"""<article class="session-card{' is-current' if current else ''}" data-session-id="{identifier}">
      <div class="session-row">
        <button type="button" class="session-open" data-action="open"{current_attr} aria-label="打开会话：{title}">
          <span class="session-title">{title}</span><span class="session-meta">{escape(metadata)}</span>
        </button>
        <details class="session-menu" name="session-options">
          <summary aria-label="会话「{title}」的更多操作" title="更多操作"><span aria-hidden="true">⋯</span></summary>
          <div class="session-popup" role="menu" aria-label="会话操作">
            <button type="button" role="menuitem" data-action="rename">重命名</button>
            <button type="button" role="menuitem" data-action="delete" class="session-delete">删除</button>
          </div>
        </details>
      </div>
      <form class="session-rename" hidden>
        <label>会话名称<input name="title" value="{title}" maxlength="60" required autocomplete="off"></label>
        <div class="session-rename-actions"><button type="submit">保存名称</button><button type="button" data-action="cancel">取消</button></div>
      </form>
    </article>"""


def current_session_html(session: dict[str, Any]) -> str:
    labels = history_choices({"version": 1, "active_id": session["id"], "sessions": [session]})
    metadata = labels[0][0].rsplit("\n", 1)[-1]
    return session_card_html(session, metadata, current=True)


def history_sidebar_html(store: dict[str, Any]) -> str:
    by_id = {session["id"]: session for session in store["sessions"]}
    cards = [
        session_card_html(by_id[identifier], label.rsplit("\n", 1)[-1])
        for label, identifier in history_choices(store) if identifier != store["active_id"]
    ]
    body = "".join(cards) or '<p class="session-empty">暂无历史会话</p>'
    return f'<div class="session-history-heading">历史会话 <span>{len(cards)}</span></div><div class="session-history-list">{body}</div>'


SESSION_ACTION_JS = """
// Event delegation survives autosave replacing card markup.
element.addEventListener('click', (event) => {
  const button = event.target.closest('button[data-action]');
  if (!button || !element.contains(button)) return;
  const card = button.closest('[data-session-id]');
  if (!card) return;
  const id = card.dataset.sessionId;
  const action = button.dataset.action;
  const menu = card.querySelector('details');
  const form = card.querySelector('form');
  if (menu) menu.open = false;
  if (action === 'open' && button.getAttribute('aria-current') !== 'true') trigger('open_session', {id});
  if (action === 'delete') trigger('manage_session', {id, action: 'delete'});
  if (action === 'rename') {
    form.hidden = false;
    const input = form.querySelector('input');
    input.focus(); input.select();
  }
  if (action === 'cancel') form.hidden = true;
});
element.addEventListener('submit', (event) => {
  if (!event.target.matches('.session-rename')) return;
  event.preventDefault();
  const form = event.target;
  const title = form.querySelector('input').value.trim();
  if (!title) { form.querySelector('input').reportValidity(); return; }
  trigger('manage_session', {id: form.closest('[data-session-id]').dataset.sessionId, action: 'rename', title});
});
element.addEventListener('keydown', (event) => {
  if (event.key !== 'Escape') return;
  const card = event.target.closest('[data-session-id]');
  if (!card) return;
  card.querySelector('details').open = false;
  card.querySelector('form').hidden = true;
  card.querySelector('summary').focus();
});
element.addEventListener('focusout', (event) => {
  const menu = event.target.closest('details');
  if (menu && !menu.contains(event.relatedTarget)) menu.open = false;
});
"""
