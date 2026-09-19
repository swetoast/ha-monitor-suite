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
    assert manifest["version"] == "0.3.15"
    assert manifest["domain"] == "monitor_suite"
    assert manifest["requirements"] == []
    assert manifest["codeowners"] == ["@swetoast"]


def test_options_are_isolated_and_meaningful() -> None:
    options = (COMPONENT / "options.py").read_text()
    flow = (COMPONENT / "config_flow.py").read_text()
    coordinator = (COMPONENT / "coordinator.py").read_text()
    assert "class MonitorSuiteOptionsFlow(OptionsFlow)" in options
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
        "memory_usage",
        "storage_usage",
        "power",
        "input_voltage",
        "fan_speed",
        "network_status",
        "disk_read",
        "disk_write",
        "last_boot",
    ):
        assert f'key="{key}"' in sensor
    for forbidden in (
        "available_bytes",
        "total_bytes",
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
    assert (COMPONENT / "brand" / "icon.png").is_file()


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


def test_sensor_presentation_and_raid_attribute_contract() -> None:
    sensor = (COMPONENT / "sensor.py").read_text()
    strings = json.loads((COMPONENT / "strings.json").read_text())
    translations = json.loads((COMPONENT / "translations" / "en.json").read_text())

    assert sensor.count("suggested_display_precision=1") >= 2
    assert "suggested_display_precision=2" in sensor
    assert "suggested_display_precision=3" in sensor
    assert '"smart_status",' not in sensor
    assert strings["entity"]["sensor"]["power"]["name"] == "Estimated power"
    assert translations["entity"]["sensor"]["power"]["name"] == "Estimated power"


def test_reserved_states_and_compound_entities_are_handled() -> None:
    sensor = (COMPONENT / "sensor.py").read_text()
    assert 'options=["ok", "warning", "critical"]' in sensor
    assert 'options=["up", "down"]' in sensor
    assert 'attributes["link_speed"] = link_speed' in sensor
    assert 'attributes["temperature"] = temperature' in sensor
    assert 'attributes["remaining_life"] = remaining_life' in sensor
    assert "MonitorSuiteSmartTemperatureSensor" not in sensor
    assert "MonitorSuiteSmartLifeSensor" not in sensor
    assert "registry.async_remove(entity_entry.entity_id)" in sensor


def test_icons_are_complete_and_dynamic() -> None:
    icons = json.loads((COMPONENT / "icons.json").read_text())["entity"]["sensor"]

    assert icons["status"]["state"] == {
        "ok": "mdi:check-circle",
        "warning": "mdi:alert-circle",
        "critical": "mdi:alert-octagon",
    }
    assert icons["network_status"]["state"] == {
        "up": "mdi:lan-connect",
        "down": "mdi:lan-disconnect",
    }
    assert icons["raid_status"]["state"] == {
        "healthy": "mdi:harddisk",
        "degraded": "mdi:alert-circle",
        "failed": "mdi:harddisk-remove",
        "recovering": "mdi:progress-wrench",
        "resyncing": "mdi:sync",
        "checking": "mdi:magnify-scan",
        "reshaping": "mdi:swap-horizontal",
    }
    assert icons["smart_status"]["state"] == {
        "healthy": "mdi:harddisk",
        "warning": "mdi:alert-circle",
        "failed": "mdi:harddisk-remove",
        "testing": "mdi:magnify-scan",
    }
    assert icons["fan_speed"]["range"] == {"1": "mdi:fan"}
    assert icons["storage_usage"]["range"] == {"90": "mdi:alert-circle"}

    obsolete = {
        "network_link_speed",
        "network_download",
        "network_upload",
        "smart_temperature",
        "smart_remaining_life",
        "cpu_frequency",
        "cpu_temperature",
        "cooling_state",
    }
    assert obsolete.isdisjoint(icons)


def test_cpu_and_fan_compound_sensor_contract() -> None:
    sensor = (COMPONENT / "sensor.py").read_text()
    assert 'attributes["temperature"] = temperature' in sensor
    assert 'attributes["frequency"] = frequency' in sensor
    assert 'return {"cooling_state": state}' in sensor
    assert 'key="cpu_frequency"' not in sensor
    assert 'key="cpu_temperature"' not in sensor
    assert 'key="cooling_state"' not in sensor
    assert '"_cpu_frequency"' in sensor
    assert '"_cpu_temperature"' in sensor
    assert '"_cooling_state"' in sensor


def test_attribute_names_follow_the_approved_standard() -> None:
    """Reject units, source-field names, and redundant context in attributes."""
    sensor = (COMPONENT / "sensor.py").read_text()
    forbidden = {
        "temperature_c",
        "frequency_mhz",
        "remaining_life_percent",
        "link_speed_mbps",
        "download_bytes_per_second",
        "upload_bytes_per_second",
        "cpu_temperature",
        "cpu_frequency",
        "drive_temperature",
    }
    exposed_attribute_names = {
        match.split('["', 1)[1].split('"]', 1)[0]
        for match in sensor.splitlines()
        if 'attributes["' in match
    }
    assert forbidden.isdisjoint(exposed_attribute_names)
    forbidden_suffixes = (
        "_c",
        "_mhz",
        "_percent",
        "_mbps",
        "_bytes_per_second",
    )
    assert not {
        name for name in exposed_attribute_names if name.endswith(forbidden_suffixes)
    }
    redundant_prefixes = ("cpu_", "drive_", "network_", "smart_")
    assert not {
        name for name in exposed_attribute_names if name.startswith(redundant_prefixes)
    }
    assert {
        "temperature",
        "frequency",
        "remaining_life",
        "link_speed",
        "download",
        "upload",
    } <= exposed_attribute_names


def test_network_is_one_compound_entity() -> None:
    sensor = (COMPONENT / "sensor.py").read_text()
    assert 'attributes["link_speed"] = link_speed' in sensor
    assert 'attributes["download"] = download' in sensor
    assert 'attributes["upload"] = upload' in sensor
    assert 'key="network_download"' not in sensor
    assert 'key="network_upload"' not in sensor
    assert '"_network_download"' in sensor
    assert '"_network_upload"' in sensor


def test_manifest_key_order_matches_hassfest() -> None:
    manifest = json.loads((COMPONENT / "manifest.json").read_text())
    keys = list(manifest)
    assert keys[:2] == ["domain", "name"]
    assert keys[2:] == sorted(keys[2:])


def test_hacs_brand_asset_is_inside_integration() -> None:
    assert (COMPONENT / "brand" / "icon.png").is_file()
    assert not (ROOT / "brand").exists()


def test_hacs_repository_metadata_checks_are_explicitly_handled() -> None:
    workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text()
    assert "ignore: topics description" in workflow


def test_github_test_dependencies_pin_compatible_pycares() -> None:
    workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text()
    assert "homeassistant==2025.12.2" in workflow
    assert "pycares==4.11.0" in workflow
