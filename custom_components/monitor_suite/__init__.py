"""Monitor Suite integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MonitorSuiteClient, endpoint_id
from .const import CONF_API_KEY, CONF_DEVICE_ID
from .coordinator import MonitorSuiteCoordinator

_LOGGER = logging.getLogger(__name__)


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload Monitor Suite after config entry options change."""
    await hass.config_entries.async_reload(entry.entry_id)

type MonitorSuiteConfigEntry = ConfigEntry[MonitorSuiteCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: MonitorSuiteConfigEntry
) -> bool:
    """Set up Monitor Suite from a config entry."""
    client = MonitorSuiteClient(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_API_KEY],
    )
    coordinator = MonitorSuiteCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, [Platform.SENSOR])
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: MonitorSuiteConfigEntry
) -> bool:
    """Unload Monitor Suite."""
    return await hass.config_entries.async_unload_platforms(entry, [Platform.SENSOR])


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate legacy entries while preserving existing entity identities."""
    if entry.version > 2:
        _LOGGER.error(
            "Cannot migrate Monitor Suite entry from version %s", entry.version
        )
        return False

    if entry.version < 2:
        current_endpoint = endpoint_id(entry.data[CONF_HOST], entry.data[CONF_PORT])
        stable_device_id = (
            entry.data.get(CONF_DEVICE_ID) or entry.unique_id or current_endpoint
        )
        hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, CONF_DEVICE_ID: stable_device_id},
            unique_id=current_endpoint,
            version=2,
        )
        _LOGGER.debug("Migrated Monitor Suite config entry to version 2")

    return True
