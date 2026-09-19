"""Home Assistant behavior tests for config-entry migration."""

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.monitor_suite import async_migrate_entry
from custom_components.monitor_suite.api import endpoint_id
from custom_components.monitor_suite.const import CONF_API_KEY, CONF_DEVICE_ID, DOMAIN

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


async def test_migrate_legacy_entry_preserves_entity_identity(
    hass: HomeAssistant,
) -> None:
    host = "monitor.local"
    port = 5000
    legacy_unique_id = endpoint_id(host, port)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=host,
        unique_id=legacy_unique_id,
        version=1,
        data={CONF_HOST: host, CONF_PORT: port, CONF_API_KEY: "token"},
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry)
    assert entry.version == 2
    assert entry.unique_id == legacy_unique_id
    assert entry.data[CONF_DEVICE_ID] == legacy_unique_id
