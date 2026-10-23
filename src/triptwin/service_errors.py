"""Recognize upstream billing failures without exposing provider payloads."""

from __future__ import annotations

import json
from typing import Any

import httpx


BILLING_UNAVAILABLE_MESSAGE = (
    "该站后台大模型 API 余额不足或已欠费，暂时无法使用 AI 服务。"
    "请等待站点维护者充值后再试；已生成结果、示例和本地风险检查仍可使用。"
)


def is_billing_failure(value: Any) -> bool:
    """Check explicit payment codes/messages, never generic 403/429 statuses."""
    if isinstance(value, httpx.HTTPStatusError):
        return is_billing_failure(value.response)
    if isinstance(value, httpx.Response):
        if value.status_code == 402:
            return True
        try:
            value = value.json()
        except ValueError:
            value = value.text[:4000]
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, default=str)
    else:
        text = str(value)
    normalized = "".join(c for c in text.casefold() if c.isalnum())
    return any(marker in normalized for marker in (
        "arrearage", "insufficientbalance", "insufficientfunds",
        "accountoverdue", "paymentrequired", "overduebalance",
        "balanceinsufficient", "balanceisnotenough", "accountinbadstanding",
        "余额不足", "账户欠费", "账号欠费", "已欠费", "后付费账单欠费",
    )) or BILLING_UNAVAILABLE_MESSAGE in text
