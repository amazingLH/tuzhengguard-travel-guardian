"""Recognize upstream billing failures without exposing provider payloads."""

from __future__ import annotations

import json
from typing import Any

import httpx


BILLING_UNAVAILABLE_MESSAGE = (
    "该站后台大模型 API 余额不足或已欠费，暂时无法使用 AI 服务。"
    "请等待站点维护者充值后再试；已生成结果、示例和本地风险检查仍可使用。"
)
FREE_QUOTA_UNAVAILABLE_MESSAGE = (
    "当前问答模型的免费额度已耗尽，且模型开启了“仅使用免费额度”。"
    "请站点维护者在百炼控制台检查该模型的用量设置，或配置有可用额度的模型后重试。"
)
FALLBACK_QUOTA_UNAVAILABLE_MESSAGE = (
    "免费优先模型额度已耗尽，付费备用模型仍被“仅使用免费额度”限制。"
    "请站点维护者在百炼控制台关闭备用模型的“免费额度用完即停”后重试。"
)
MODEL_UNAVAILABLE_MESSAGE = "当前模型服务暂时不可用，请稍后重试；TripGraph 和已生成的 Plan B 不受影响。"
MODEL_PERMISSION_MESSAGE = "当前问答模型的凭据或调用权限不可用，请站点维护者检查模型配置与授权后重试。"
MODEL_TIMEOUT_MESSAGE = "本次大模型问答超时，请稍后重试；当前会话和已有方案仍保留。"
MODEL_RATE_LIMIT_MESSAGE = "大模型服务当前请求较多，请稍后重试；当前会话和已有方案仍保留。"


class FallbackQuotaBlockedError(httpx.HTTPStatusError):
    """The primary quota was exhausted and the paid fallback is also free-only."""


def is_free_quota_failure(response: httpx.Response) -> bool:
    if response.status_code not in (403, 429) or is_billing_failure(response):
        return False
    body = response.text.casefold()
    return any(marker in body for marker in (
        "insufficient_quota", "freetieronly", "free quota", "free tier only",
    ))


def model_failure_message(error: Exception) -> str:
    if is_billing_failure(error):
        return BILLING_UNAVAILABLE_MESSAGE
    if isinstance(error, httpx.TimeoutException):
        return MODEL_TIMEOUT_MESSAGE
    if isinstance(error, FallbackQuotaBlockedError):
        return FALLBACK_QUOTA_UNAVAILABLE_MESSAGE
    if isinstance(error, httpx.HTTPStatusError):
        response = error.response
        if is_free_quota_failure(response):
            return FREE_QUOTA_UNAVAILABLE_MESSAGE
        if response.status_code in (401, 403):
            return MODEL_PERMISSION_MESSAGE
        if response.status_code == 429:
            return MODEL_RATE_LIMIT_MESSAGE
    return MODEL_UNAVAILABLE_MESSAGE


def is_model_failure_reply(value: object) -> bool:
    return isinstance(value, str) and value in {
        BILLING_UNAVAILABLE_MESSAGE, FREE_QUOTA_UNAVAILABLE_MESSAGE,
        MODEL_UNAVAILABLE_MESSAGE, MODEL_PERMISSION_MESSAGE, MODEL_TIMEOUT_MESSAGE,
        MODEL_RATE_LIMIT_MESSAGE, FALLBACK_QUOTA_UNAVAILABLE_MESSAGE,
    }


def vision_failure_message(error: httpx.HTTPStatusError) -> str:
    """Explain known provider failures without displaying its private payload."""
    message = model_failure_message(error)
    if message != MODEL_UNAVAILABLE_MESSAGE:
        return message.replace("问答模型", "图片解析模型").replace("大模型问答", "图片解析")
    if error.response.status_code == 404:
        return "当前图片解析模型在此业务空间不可用，请站点维护者核对视觉模型配置与地域。"
    return f"图片解析服务拒绝了请求（HTTP {error.response.status_code}），请稍后重试或由站点维护者检查模型配置。"


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
