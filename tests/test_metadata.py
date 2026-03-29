"""Tests for the metadata constants and helpers module."""

import pytest

from quick_task.metadata import (
    FIELD_ASSIGNEE,
    FIELD_PRIORITY,
    FIELD_CREATED,
    FIELD_UPDATED,
    VALID_PRIORITIES,
    validate_priority,
    now_iso,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

def test_field_constants_have_correct_string_values():
    assert FIELD_ASSIGNEE == "assignee"
    assert FIELD_PRIORITY == "priority"
    assert FIELD_CREATED == "created"
    assert FIELD_UPDATED == "updated"


def test_valid_priorities_contains_expected_levels():
    assert "low" in VALID_PRIORITIES
    assert "medium" in VALID_PRIORITIES
    assert "high" in VALID_PRIORITIES
    assert "critical" in VALID_PRIORITIES


def test_valid_priorities_length():
    assert len(VALID_PRIORITIES) == 4


# ---------------------------------------------------------------------------
# validate_priority
# ---------------------------------------------------------------------------

def test_validate_priority_accepts_low():
    assert validate_priority("low") == "low"


def test_validate_priority_accepts_medium():
    assert validate_priority("medium") == "medium"


def test_validate_priority_accepts_high():
    assert validate_priority("high") == "high"


def test_validate_priority_accepts_critical():
    assert validate_priority("critical") == "critical"


def test_validate_priority_lowercases_input():
    assert validate_priority("HIGH") == "high"
    assert validate_priority("Critical") == "critical"


def test_validate_priority_rejects_invalid():
    with pytest.raises(ValueError, match="Invalid priority"):
        validate_priority("urgent")


def test_validate_priority_error_message_includes_value():
    with pytest.raises(ValueError, match="'bogus'"):
        validate_priority("bogus")


def test_validate_priority_error_message_lists_valid():
    with pytest.raises(ValueError, match="low"):
        validate_priority("nope")


# ---------------------------------------------------------------------------
# now_iso
# ---------------------------------------------------------------------------

def test_now_iso_returns_string():
    result = now_iso()
    assert isinstance(result, str)


def test_now_iso_format():
    import re
    result = now_iso()
    # Should match YYYY-MM-DDTHH:MM:SSZ
    pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
    assert re.match(pattern, result), f"Unexpected format: {result}"


def test_now_iso_is_utc(monkeypatch):
    """Monkeypatching datetime lets us verify the function honours timezone=UTC."""
    import datetime
    fixed = datetime.datetime(2024, 6, 15, 12, 30, 45, tzinfo=datetime.timezone.utc)

    class FakeDatetime:
        @staticmethod
        def now(tz=None):
            return fixed

    import quick_task.metadata as meta_module
    monkeypatch.setattr(meta_module, "now_iso", lambda: fixed.strftime("%Y-%m-%dT%H:%M:%SZ"))
    assert meta_module.now_iso() == "2024-06-15T12:30:45Z"


# ---------------------------------------------------------------------------
# Re-export consistency: metadata.py mirrors models.py
# ---------------------------------------------------------------------------

def test_field_constants_match_models():
    from quick_task.models import (
        METADATA_ASSIGNEE,
        METADATA_PRIORITY,
        METADATA_CREATED,
        METADATA_UPDATED,
        PRIORITY_LEVELS,
    )
    assert FIELD_ASSIGNEE == METADATA_ASSIGNEE
    assert FIELD_PRIORITY == METADATA_PRIORITY
    assert FIELD_CREATED == METADATA_CREATED
    assert FIELD_UPDATED == METADATA_UPDATED
    assert VALID_PRIORITIES is PRIORITY_LEVELS
