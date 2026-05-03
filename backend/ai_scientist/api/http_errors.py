"""Map vendor LLM failures to HTTP status codes for the FastAPI layer."""

from __future__ import annotations


def runtime_error_status_and_headers(msg: str) -> tuple[int, dict[str, str]]:
    """Return (status_code, headers) for a ``RuntimeError`` ``str()`` body."""
    msg_lower = msg.lower()
    headers: dict[str, str] = {}
    if "API_KEY" in msg or "not configured" in msg_lower:
        return 503, headers
    if (
        "429" in msg
        or "rate_limit_exceeded" in msg_lower
        or "rate limit reached" in msg_lower
        or "requests per min" in msg_lower
        or "too many requests" in msg_lower
        or ("openai" in msg_lower and "rate limit" in msg_lower)
    ):
        headers["Retry-After"] = "60"
        return 503, headers
    return 500, headers
