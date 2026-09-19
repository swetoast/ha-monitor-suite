"""Data coordinator for Monitor Suite."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MonitorSuiteAuthenticationError, MonitorSuiteClient, MonitorSuiteError
from .const import (
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    update_interval,
    validated_update_interval,
)

_LOGGER = logging.getLogger(__name__)


class MonitorSuiteCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch one shared status snapshot for every entity."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: MonitorSuiteClient,
    ) -> None:
        interval_seconds = validated_update_interval(
            entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        )
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.title}",
            update_interval=update_interval(interval_seconds),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.async_status()
        except MonitorSuiteAuthenticationError as err:
            raise ConfigEntryAuthFailed("API token was rejected") from err
        except MonitorSuiteError as err:
            raise UpdateFailed(str(err)) from err
