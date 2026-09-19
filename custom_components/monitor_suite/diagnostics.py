"""Diagnostics support for Monitor Suite."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import MonitorSuiteConfigEntry
from .const import (
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    validated_update_interval,
)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: MonitorSuiteConfigEntry
) -> dict[str, Any]:
    """Return diagnostics without connection details or device paths."""
    del hass
    coordinator = entry.runtime_data
    data = coordinator.data or {}
    raid_arrays = data.get("raid", {}).get("arrays", [])
    smart_devices = data.get("smart", {}).get("devices", [])
    if not isinstance(raid_arrays, list):
        raid_arrays = []
    if not isinstance(smart_devices, list):
        smart_devices = []

    return {
        "entry": {
            "host_configured": bool(entry.data.get("host")),
            "port_configured": bool(entry.data.get("port")),
            "api_key_configured": bool(entry.data.get("api_key")),
            "update_interval_seconds": validated_update_interval(
                entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
            ),
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "updated_at": data.get("updated_at"),
        },
        "device": {
            "model": data.get("device", {}).get("model"),
            "operating_system": data.get("device", {}).get("operating_system"),
            "kernel_version": data.get("device", {}).get("kernel_version"),
            "architecture": data.get("device", {}).get("architecture"),
        },
        "discovery": {
            "raid_array_count": len(raid_arrays),
            "smart_device_count": len(smart_devices),
            "smart_temperature_device_count": sum(
                1
                for row in smart_devices
                if isinstance(row, dict) and row.get("temperature_c") is not None
            ),
            "smart_remaining_life_device_count": sum(
                1
                for row in smart_devices
                if isinstance(row, dict)
                and row.get("remaining_life_percent") is not None
            ),
        },
        "health": data.get("health", {}),
    }
