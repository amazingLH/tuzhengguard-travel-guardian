"""Current-session evidence, earlier plans and conversation for model questions."""

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from triptwin.demo_service import chat_context
from triptwin.service_errors import is_model_failure_reply
from triptwin.session_history import workspace_snapshot


def conversation_messages(history: Any) -> list[dict[str, str]]:
    messages = []
    for message in history if isinstance(history, list) else []:
        if not isinstance(message, dict) or message.get("role") not in {"user", "assistant"}:
            continue
        content = message.get("content")
        if isinstance(content, list):
            content = "\n".join(block["text"] for block in content if isinstance(block, dict) and isinstance(block.get("text"), str))
        if isinstance(content, str) and content and not is_model_failure_reply(content):
            messages.append({"role": message["role"], "content": content})
    return messages


def remember_applied_plan(state: dict, option: dict, options: list) -> list[dict]:
    records = deepcopy(state.get("plan_revisions") or [])
    records.append({
        "action": "apply_plan_b", "applied_at": datetime.now(UTC).isoformat(),
        "original_trip": deepcopy(state["trip"]), "applied_trip": deepcopy(option["trip"]),
        "available_options": deepcopy(options), "selected_option_id": option["id"],
        "selected_option_label": option["label"],
        "before_risks": option["before_risks"], "after_risks": option["after_risks"],
        "known_ticket_cost_after": option["known_cost"],
        "boundary": "仅调整页面计划；未实际退改订单，退款及手续费未知。",
    })
    return records


def build_session_context(state: dict | None, history: Any, snapshot: dict | None = None) -> dict:
    state = state if isinstance(state, dict) else {}
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    trip = state.get("trip")
    context: dict[str, Any] = {}
    if state.get("legacy_image_coverage_missing"):
        context["data_quality_warnings"] = ["旧多图导入尚未逐张核齐，旧风险与 Plan B 结果不能作为可靠结论；不能据此认定没有冲突。"]
    elif isinstance(trip, dict):
        try:
            context = chat_context(
                trip, include_cached_amap=state.get("trip_source") == "synthetic_example",
                candidate_artifact=state.get("live_candidate_artifact"),
                amap_inspection=state.get("live_inspection"),
            )
        except (ValueError, KeyError, TypeError):
            context["data_quality_warnings"] = ["当前行程结构尚不完整，不据此宣称零风险或核验成功。"]
    else:
        context["data_quality_warnings"] = ["当前尚未确认并构建完整行程；草稿和用户陈述仍可讨论，但不是已核验事实。"]
    current = dict(snapshot)
    current["trip_state"] = state
    context.update({
        "context_version": 2,
        "current_workspace": workspace_snapshot(current),
        "earlier_workspaces": deepcopy(snapshot.get("workspace_history") or []),
        "earlier_conversations": [conversation_messages(segment) for segment in snapshot.get("conversation_archive") or []],
        "conversation_history": conversation_messages(history),
        "plan_revisions": deepcopy(state.get("plan_revisions") or []),
        "local_plan_b": {
            "available_options": deepcopy(state.get("local_plan_options") or []),
            "selected_option_id": state.get("local_plan_choice"),
            "validation_source": "本地结构、依赖、预算与风险规则回放；没有新增实时交通、天气或余票核验。",
        },
        "scope": "仅当前会话。历史页面与旧方案明确属于过去版本，不能冒充当前状态；未提供的事实如实说明未知。",
    })
    coverage = state.get("image_coverage") or {}
    if state.get("trip_source") in {"uploaded_image", "user_corrected"} and not coverage:
        context.setdefault("data_quality_warnings", []).append("旧导入记录没有逐图覆盖证明，不能保证全部截图均已识别，相关结论需用户核对。")
    return context


def cache_conversation(question: str, history: Any) -> list[dict[str, str]]:
    messages = conversation_messages(history)
    normalized = " ".join(question.casefold().split())
    # Exact repeat questions may reuse an answer; other follow-ups include history.
    while len(messages) >= 2 and messages[-1]["role"] == "assistant" and messages[-2]["role"] == "user" and " ".join(messages[-2]["content"].casefold().split()) == normalized:
        messages = messages[:-2]
    return messages
