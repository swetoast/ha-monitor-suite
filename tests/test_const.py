"""Tests for option validation that do not require Home Assistant."""

from custom_components.monitor_suite.const import (
    DEFAULT_UPDATE_INTERVAL,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    validated_update_interval,
)


def test_update_interval_accepts_valid_values() -> None:
    assert validated_update_interval(5) == MIN_UPDATE_INTERVAL
    assert validated_update_interval(10) == DEFAULT_UPDATE_INTERVAL
    assert validated_update_interval(300) == MAX_UPDATE_INTERVAL
    assert validated_update_interval(12.9) == 12


def test_update_interval_clamps_out_of_range_values() -> None:
    assert validated_update_interval(0) == MIN_UPDATE_INTERVAL
    assert validated_update_interval(4) == MIN_UPDATE_INTERVAL
    assert validated_update_interval(301) == MAX_UPDATE_INTERVAL
    assert validated_update_interval(3600) == MAX_UPDATE_INTERVAL


def test_update_interval_rejects_invalid_stored_values() -> None:
    assert validated_update_interval(True) == DEFAULT_UPDATE_INTERVAL
    assert validated_update_interval(False) == DEFAULT_UPDATE_INTERVAL
    assert validated_update_interval("10") == DEFAULT_UPDATE_INTERVAL
    assert validated_update_interval(None) == DEFAULT_UPDATE_INTERVAL
