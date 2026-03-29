"""Metadata field constants and helpers for Quick Task."""

# Re-export from models to avoid duplication
from quick_task.models import (
    METADATA_ASSIGNEE as FIELD_ASSIGNEE,
    METADATA_PRIORITY as FIELD_PRIORITY,
    METADATA_CREATED  as FIELD_CREATED,
    METADATA_UPDATED  as FIELD_UPDATED,
    PRIORITY_LEVELS   as VALID_PRIORITIES,
)


def validate_priority(value: str) -> str:
    """Lowercase and validate a priority string.

    Returns the lowercased value on success.
    Raises ValueError if the value is not a known priority level.
    """
    lowered = value.lower()
    if lowered not in VALID_PRIORITIES:
        raise ValueError(
            f"Invalid priority {value!r}. Must be one of: {', '.join(VALID_PRIORITIES)}"
        )
    return lowered


def now_iso() -> str:
    """Return current UTC time as an ISO-8601 string (no microseconds)."""
    import datetime
    return datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
