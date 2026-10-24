"""Use the configured paid fallback only after an explicit free-quota refusal."""

from dataclasses import dataclass
from typing import Any

import httpx

from triptwin.service_errors import FallbackQuotaBlockedError, is_free_quota_failure


@dataclass(frozen=True)
class ModelReply:
    response: httpx.Response
    model: str
    attempted_models: tuple[str, ...]
    fallback_reason: str | None = None


def request_model(
    client: httpx.Client, endpoint: str, *, headers: dict[str, str],
    payload: dict[str, Any], fallback_model: str | None = None,
) -> ModelReply:
    """Keep the complete payload; at most one quota-triggered fallback request."""
    primary = payload["model"]
    response = client.post(endpoint, headers=headers, json=payload)
    fallback = (fallback_model or "").strip()
    if not (fallback and fallback != primary and is_free_quota_failure(response)):
        response.raise_for_status()
        return ModelReply(response, primary, (primary,))
    response = client.post(endpoint, headers=headers, json={**payload, "model": fallback})
    if is_free_quota_failure(response):
        raise FallbackQuotaBlockedError(
            "Both primary and fallback models were refused by free-quota policy.",
            request=response.request, response=response,
        )
    response.raise_for_status()
    return ModelReply(response, fallback, (primary, fallback), "free_quota_exhausted")
