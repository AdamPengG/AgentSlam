from __future__ import annotations


def choose_active_source(
    *,
    primary_age_s: float | None,
    fallback_available: bool,
    primary_timeout_s: float,
) -> str | None:
    if primary_age_s is not None and primary_age_s <= primary_timeout_s:
        return "primary"
    if fallback_available:
        return "fallback"
    return None


def build_status_payload(
    *,
    active_source: str | None,
    primary_topic: str,
    fallback_topic: str,
    output_topic: str,
    primary_messages: int,
    fallback_messages: int,
    primary_age_s: float | None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "active_source": active_source or "none",
        "primary_topic": primary_topic,
        "fallback_topic": fallback_topic,
        "output_topic": output_topic,
        "primary_messages": primary_messages,
        "fallback_messages": fallback_messages,
    }
    if primary_age_s is not None:
        payload["primary_age_s"] = round(primary_age_s, 4)
    return payload
