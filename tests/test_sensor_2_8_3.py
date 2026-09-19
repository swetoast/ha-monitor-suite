"""Regression tests for the Monitor Suite Agent 2.8.3 sensor contract."""
from __future__ import annotations
from types import SimpleNamespace
from custom_components.monitor_suite.sensor import CORE_SENSORS, MonitorSuiteSmartStatusSensor, _find_named_row

STATUS = {
    "cooling": {"state": "idle", "fan_speed_rpm": 0},
    "network": {"interface": "eth0", "status": "up", "link_speed_mbps": 1000, "download_bytes_per_second": 5531, "upload_bytes_per_second": 8072},
    "raid": {"arrays": [{"name": "md0", "status": "healthy", "raid_level": "RAID0", "active_members": 2, "expected_members": 2, "redundancy": "none"}]},
    "smart": {"devices": [
        {"device": "sda", "status": "healthy", "temperature_c": 29.0},
        {"device": "sdb", "status": "healthy", "temperature_c": 28.0},
        {"device": "nvme0n1", "status": "healthy", "temperature_c": 19.85, "remaining_life_percent": 98.0},
        {"device": "nvme1n1", "status": "healthy", "temperature_c": 30.85, "remaining_life_percent": 75.0},
    ]},
}

def test_agent_2_8_3_fixed_sensor_values() -> None:
    descriptions = {description.key: description for description in CORE_SENSORS}
    assert descriptions["cpu_usage"].attributes_fn(STATUS) is None
    cpu_payload = {"cpu": {"usage_percent": 14.8, "temperature_c": 35.3, "frequency_mhz": 1500}}
    assert descriptions["cpu_usage"].attributes_fn(cpu_payload) == {"temperature_c": 35.3, "frequency_mhz": 1500}
    assert "cpu_temperature" not in descriptions
    assert "cpu_frequency" not in descriptions
    assert descriptions["fan_speed"].value_fn(STATUS) == 0
    assert descriptions["fan_speed"].attributes_fn(STATUS) == {"cooling_state": "idle"}
    assert "cooling_state" not in descriptions
    assert descriptions["network_status"].value_fn(STATUS) == "up"
    assert descriptions["network_status"].attributes_fn(STATUS) == {"interface": "eth0", "link_speed_mbps": 1000}
    assert "network_link_speed" not in descriptions
    assert descriptions["network_download"].value_fn(STATUS) == 5531
    assert descriptions["network_upload"].value_fn(STATUS) == 8072

def test_agent_2_8_3_dynamic_storage_rows() -> None:
    raid = _find_named_row(STATUS["raid"]["arrays"], "name", "md0")
    assert raid is not None and raid["status"] == "healthy"
    nvme0 = _find_named_row(STATUS["smart"]["devices"], "device", "nvme0n1")
    assert nvme0 is not None and nvme0["remaining_life_percent"] == 98.0

def test_reserved_enum_states_map_to_unavailable() -> None:
    descriptions = {description.key: description for description in CORE_SENSORS}
    assert descriptions["status"].value_fn({"health": {"status": "unavailable"}}) is None
    assert descriptions["network_status"].value_fn({"network": {"status": "unknown"}}) is None

def _smart_entity(row: dict[str, object]) -> MonitorSuiteSmartStatusSensor:
    entity = object.__new__(MonitorSuiteSmartStatusSensor)
    entity.coordinator = SimpleNamespace(last_update_success=True, data={"smart": {"devices": [row]}})
    entity._device = str(row["device"])
    return entity

def test_nvme_smart_status_compounds_temperature_and_life() -> None:
    entity = _smart_entity({"device": "nvme0n1", "status": "healthy", "temperature_c": 19.85, "remaining_life_percent": 98.0})
    assert entity.native_value == "healthy"
    assert entity.extra_state_attributes == {"temperature_c": 19.85, "remaining_life_percent": 98.0}

def test_sata_smart_status_omits_missing_remaining_life() -> None:
    entity = _smart_entity({"device": "sda", "status": "healthy", "temperature_c": 29.0})
    assert entity.extra_state_attributes == {"temperature_c": 29.0}

def test_smart_attributes_reject_boolean_measurements() -> None:
    entity = _smart_entity({"device": "nvme0n1", "status": "healthy", "temperature_c": True, "remaining_life_percent": False})
    assert entity.extra_state_attributes is None


