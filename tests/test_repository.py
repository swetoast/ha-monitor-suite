"""Repository contract tests for ha-monitor-suite."""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
COMPONENT = ROOT / "custom_components" / "monitor_suite"


def test_python_files_parse() -> None:
    for path in COMPONENT.glob("*.py"):
        ast.parse(path.read_text(), filename=str(path))


def test_json_files_parse() -> None:
    paths = [
        ROOT / "hacs.json",
        COMPONENT / "manifest.json",
        COMPONENT / "strings.json",
        COMPONENT / "icons.json",
        COMPONENT / "translations" / "en.json",
    ]
    for path in paths:
        assert isinstance(json.loads(path.read_text()), dict)


def test_versions_and_repository_metadata() -> None:
    hacs = json.loads((ROOT / "hacs.json").read_text())
    manifest = json.loads((COMPONENT / "manifest.json").read_text())
    assert hacs == {
        "name": "Monitor Suite",
        "homeassistant": "2025.12.2",
        "hacs": "2.0.0",
    }
    assert manifest["version"] == "0.3.1"
    assert manifest["domain"] == "monitor_suite"
    assert manifest["requirements"] == []
    assert manifest["codeowners"] == ["@swetoast"]


def test_options_are_isolated_and_meaningful() -> None:
    options = (COMPONENT / "options.py").read_text()
    flow = (COMPONENT / "config_flow.py").read_text()
    coordinator = (COMPONENT / "coordinator.py").read_text()
    assert "class MonitorSuiteOptionsFlow(OptionsFlowWithReload)" in options
    assert "CONF_UPDATE_INTERVAL" in options
    assert "MIN_UPDATE_INTERVAL" in options
    assert "MAX_UPDATE_INTERVAL" in options
    assert "return MonitorSuiteOptionsFlow()" in flow
    assert "entry.options.get(CONF_UPDATE_INTERVAL" in coordinator
    assert "show_sensor" not in options


def test_setup_flows_and_secret_handling() -> None:
    flow = (COMPONENT / "config_flow.py").read_text()
    assert "async_step_user" in flow
    assert "async_step_reauth_confirm" in flow
    assert "async_step_reconfigure" in flow
    assert "async_validate_connection" in flow
    assert "TextSelectorType.PASSWORD" in flow
    assert "user_input.get(CONF_API_KEY) or entry.data[CONF_API_KEY]" in flow
    assert "data_updates=" in flow
    assert "_async_current_entries" in flow


def test_coordinator_uses_one_status_request() -> None:
    setup = (COMPONENT / "__init__.py").read_text()
    coordinator = (COMPONENT / "coordinator.py").read_text()
    assert "async_health" not in setup
    assert "async_config_entry_first_refresh" in setup
    assert "return await self.client.async_status()" in coordinator
    assert "ConfigEntryAuthFailed" in coordinator


def test_sensor_surface_stays_focused() -> None:
    sensor = (COMPONENT / "sensor.py").read_text()
    for key in (
        "status",
        "cpu_usage",
        "cpu_frequency",
        "cpu_temperature",
        "memory_usage",
        "storage_usage",
        "power",
        "input_voltage",
        "fan_speed",
        "network_download",
        "network_upload",
        "disk_read",
        "disk_write",
        "last_boot",
    ):
        assert f'key="{key}"' in sensor
    for forbidden in (
        "available_bytes",
        "total_bytes",
        "link_speed_mbps",
        "serial_number",
        "power_on_hours",
    ):
        assert forbidden not in sensor
    assert '"power_supply"' in sensor
    assert '"thermal_state"' in sensor
    assert '"performance_state"' in sensor
    assert '"source"' in sensor


def test_dynamic_discovery_and_numeric_validation() -> None:
    sensor = (COMPONENT / "sensor.py").read_text()
    assert "def discover_entities()" in sensor
    assert "coordinator.async_add_listener(discover_entities)" in sensor
    assert "isinstance(value, Real)" in sensor
    assert "datetime.fromisoformat" in sensor
    assert "parsed.tzinfo is not None" in sensor


def test_diagnostics_do_not_expose_connection_values() -> None:
    diagnostics = (COMPONENT / "diagnostics.py").read_text()
    assert '"host_configured"' in diagnostics
    assert '"api_key_configured"' in diagnostics
    assert '"host":' not in diagnostics
    assert '"api_key":' not in diagnostics
    assert '"update_interval_seconds"' in diagnostics
    assert "entry.title" not in diagnostics
    assert '"smart_devices"' not in diagnostics


def test_translations_include_options_and_states() -> None:
    strings = json.loads((COMPONENT / "strings.json").read_text())
    assert "init" in strings["options"]["step"]
    assert "update_interval" in strings["options"]["step"]["init"]["data"]
    assert "state" in strings["entity"]["sensor"]["status"]
    assert "state" in strings["entity"]["sensor"]["raid_status"]
    assert "state" in strings["entity"]["sensor"]["smart_status"]


def test_mit_license_and_single_integration() -> None:
    license_text = (ROOT / "LICENSE").read_text()
    assert license_text.startswith("MIT License")
    assert "Copyright (c) 2026 Toast" in license_text
    integrations = [
        path.name for path in (ROOT / "custom_components").iterdir() if path.is_dir()
    ]
    assert integrations == ["monitor_suite"]


def test_release_infrastructure_and_branding() -> None:
    assert (ROOT / "pyproject.toml").is_file()
    assert (ROOT / ".github" / "workflows" / "validate.yml").is_file()
    assert (ROOT / "brand" / "icon.png").is_file()


def test_identity_migration_and_reconfigure_contract() -> None:
    init_source = (COMPONENT / "__init__.py").read_text()
    flow = (COMPONENT / "config_flow.py").read_text()
    sensor = (COMPONENT / "sensor.py").read_text()
    assert "async_migrate_entry" in init_source
    assert "CONF_DEVICE_ID" in init_source
    assert "unique_id=requested_endpoint" in flow
    assert "CONF_DEVICE_ID: unique_id" in flow
    assert "entry.data.get(CONF_DEVICE_ID)" in sensor
    assert 'manufacturer="Toast"' not in sensor


def test_behavior_test_modules_present() -> None:
    for filename in (
        "test_config_flow.py",
        "test_migration.py",
        "test_diagnostics.py",
        "test_const.py",
    ):
        assert (ROOT / "tests" / filename).is_file()
