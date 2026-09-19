"""Regression tests for the Monitor Suite Agent 2.8.3 sensor contract."""

from __future__ import annotations

from types import SimpleNamespace

from custom_components.monitor_suite.sensor import (
    CORE_SENSORS,
    MonitorSuiteSmartTemperatureSensor,
    _find_named_row,
)

STATUS = {
    "cooling": {"state": "idle", "fan_speed_rpm": 0},
    "network": {
        "interface": "eth0",
        "status": "up",
        "link_speed_mbps": 1000,
        "download_bytes_per_second": 5531,
        "upload_bytes_per_second": 8072,
    },
    "raid": {
        "arrays": [
            {
                "name": "md0",
                "status": "healthy",
                "raid_level": "RAID0",
                "active_members": 2,
                "expected_members": 2,
                "redundancy": "none",
            }
        ]
    },
    "smart": {
        "devices": [
            {"device": "sda", "status": "healthy", "temperature_c": 29.0},
            {"device": "sdb", "status": "healthy", "temperature_c": 28.0},
            {
                "device": "nvme0n1",
                "status": "healthy",
                "temperature_c": 19.85,
                "remaining_life_percent": 98.0,
            },
            {
                "device": "nvme1n1",
                "status": "healthy",
                "temperature_c": 30.85,
                "remaining_life_percent": 75.0,
            },
        ]
    },
}


def test_agent_2_8_3_fixed_sensor_values() -> None:
    descriptions = {description.key: description for description in CORE_SENSORS}
    assert descriptions["cooling_state"].value_fn(STATUS) == "idle"
    assert descriptions["fan_speed"].value_fn(STATUS) == 0
    assert descriptions["network_status"].value_fn(STATUS) == "up"
    assert descriptions["network_status"].attributes_fn is not None
    assert descriptions["network_status"].attributes_fn(STATUS) == {"interface": "eth0"}
    assert descriptions["network_link_speed"].value_fn(STATUS) == 1000
    assert descriptions["network_download"].value_fn(STATUS) == 5531
    assert descriptions["network_upload"].value_fn(STATUS) == 8072


def test_agent_2_8_3_dynamic_storage_rows() -> None:
    raid = _find_named_row(STATUS["raid"]["arrays"], "name", "md0")
    assert raid is not None
    assert raid["status"] == "healthy"
    assert raid["raid_level"] == "RAID0"

    nvme0 = _find_named_row(STATUS["smart"]["devices"], "device", "nvme0n1")
    nvme1 = _find_named_row(STATUS["smart"]["devices"], "device", "nvme1n1")
    assert nvme0 is not None and nvme0["remaining_life_percent"] == 98.0
    assert nvme1 is not None and nvme1["remaining_life_percent"] == 75.0


def test_reserved_enum_states_map_to_unavailable() -> None:
    descriptions = {description.key: description for description in CORE_SENSORS}

    assert descriptions["status"].options == ["ok", "warning", "critical"]
    assert descriptions["status"].value_fn(
        {"health": {"status": "unavailable"}}
    ) is None

    assert descriptions["cooling_state"].options == ["idle", "active"]
    assert descriptions["cooling_state"].value_fn(
        {"cooling": {"state": "unavailable"}}
    ) is None

    assert descriptions["network_status"].options == ["up", "down"]
    assert descriptions["network_status"].value_fn(
        {"network": {"status": "unknown"}}
    ) is None
    assert descriptions["network_status"].value_fn(
        {"network": {"status": "unavailable"}}
    ) is None


def test_hwmon_temperature_sensor_survives_unavailable_smart_health() -> None:
    entity = object.__new__(MonitorSuiteSmartTemperatureSensor)
    entity.coordinator = SimpleNamespace(
        last_update_success=True,
        data={
            "smart": {
                "devices": [
                    {
                        "device": "nvme0n1",
                        "status": "unavailable",
                        "temperature_c": 41.2,
                    }
                ]
            }
        },
    )
    entity._device = "nvme0n1"

    assert entity.native_value == 41.2
    assert entity.available is True
