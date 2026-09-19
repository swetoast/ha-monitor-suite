"""Home Assistant behavior tests for privacy-conscious diagnostics."""

from types import SimpleNamespace

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.monitor_suite.const import CONF_API_KEY, CONF_DEVICE_ID, DOMAIN
from custom_components.monitor_suite.diagnostics import (
    async_get_config_entry_diagnostics,
)

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


async def test_diagnostics_redact_connection_and_device_paths(
    hass: HomeAssistant,
) -> None:
    host = "private-monitor.local"
    token = "private-token"
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=host,
        unique_id="stable-endpoint",
        version=2,
        data={
            CONF_HOST: host,
            CONF_PORT: 5000,
            CONF_API_KEY: token,
            CONF_DEVICE_ID: "stable-device-id",
        },
    )
    entry.runtime_data = SimpleNamespace(
        data={
            "updated_at": "2026-09-19T10:00:00+00:00",
            "device": {},
            "raid": {"arrays": [{"name": "/dev/md0"}]},
            "smart": {"devices": [{"device": "/dev/sda", "temperature_c": 35}]},
            "health": {"status": "ok"},
        },
        last_update_success=True,
    )

    result = await async_get_config_entry_diagnostics(hass, entry)
    serialized = repr(result)
    assert host not in serialized
    assert token not in serialized
    assert "/dev/md0" not in serialized
    assert "/dev/sda" not in serialized
    assert result["discovery"]["raid_array_count"] == 1
    assert result["discovery"]["smart_device_count"] == 1
