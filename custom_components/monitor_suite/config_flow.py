"""Config flow for Monitor Suite."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import (
    MonitorSuiteAuthenticationError,
    MonitorSuiteConnectionError,
    MonitorSuiteInvalidResponseError,
    MonitorSuiteNotReadyError,
    async_validate_connection,
    endpoint_id,
    normalize_host,
)
from .const import CONF_API_KEY, CONF_DEVICE_ID, DEFAULT_PORT, DOMAIN
from .options import MonitorSuiteOptionsFlow

_LOGGER = logging.getLogger(__name__)


def _connection_schema(
    defaults: dict[str, Any] | None = None, *, api_key_required: bool = True
) -> vol.Schema:
    values = defaults or {}
    api_key_marker = vol.Required if api_key_required else vol.Optional
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=values.get(CONF_HOST, "")): vol.All(
                str, vol.Length(min=1)
            ),
            vol.Required(
                CONF_PORT, default=values.get(CONF_PORT, DEFAULT_PORT)
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
            api_key_marker(CONF_API_KEY, default=""): TextSelector(
                TextSelectorConfig(type=TextSelectorType.PASSWORD)
            ),
        }
    )


def _reauth_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_API_KEY): TextSelector(
                TextSelectorConfig(type=TextSelectorType.PASSWORD)
            )
        }
    )


def _error_key(err: Exception) -> str:
    if isinstance(err, MonitorSuiteAuthenticationError):
        return "invalid_auth"
    if isinstance(err, MonitorSuiteNotReadyError):
        return "not_ready"
    if isinstance(err, (MonitorSuiteConnectionError, ValueError)):
        return "cannot_connect"
    if isinstance(err, MonitorSuiteInvalidResponseError):
        return "invalid_response"
    return "unknown"


class MonitorSuiteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure a Monitor Suite Agent."""

    VERSION = 2

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> MonitorSuiteOptionsFlow:
        """Create the options flow."""
        return MonitorSuiteOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create a new Monitor Suite entry."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await async_validate_connection(
                    async_get_clientsession(self.hass),
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input[CONF_API_KEY],
                )
            except (
                MonitorSuiteAuthenticationError,
                MonitorSuiteConnectionError,
                MonitorSuiteInvalidResponseError,
                MonitorSuiteNotReadyError,
                ValueError,
            ) as err:
                errors["base"] = _error_key(err)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error while validating Monitor Suite")
                errors["base"] = "unknown"
            else:
                unique_id = endpoint_id(info.host, info.port)
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=info.host,
                    data={
                        CONF_HOST: info.host,
                        CONF_PORT: info.port,
                        CONF_API_KEY: user_input[CONF_API_KEY],
                        CONF_DEVICE_ID: unique_id,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_connection_schema(user_input),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Start reauthentication for an existing entry."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Validate and save a replacement API token."""
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            try:
                await async_validate_connection(
                    async_get_clientsession(self.hass),
                    entry.data[CONF_HOST],
                    entry.data[CONF_PORT],
                    user_input[CONF_API_KEY],
                )
            except (
                MonitorSuiteAuthenticationError,
                MonitorSuiteConnectionError,
                MonitorSuiteInvalidResponseError,
                MonitorSuiteNotReadyError,
                ValueError,
            ) as err:
                errors["base"] = _error_key(err)
            except Exception:  # noqa: BLE001
                _LOGGER.exception(
                    "Unexpected error while reauthenticating Monitor Suite"
                )
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={CONF_API_KEY: user_input[CONF_API_KEY]},
                    reason="reauth_successful",
                )

        return self.async_show_form(
            step_id="reauth_confirm", data_schema=_reauth_schema(), errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Validate and save new connection settings."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            api_key = user_input.get(CONF_API_KEY) or entry.data[CONF_API_KEY]
            try:
                info = await async_validate_connection(
                    async_get_clientsession(self.hass),
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    api_key,
                )
                requested_endpoint = endpoint_id(info.host, info.port)
                for existing in self._async_current_entries():
                    if existing.entry_id == entry.entry_id:
                        continue
                    if (
                        endpoint_id(existing.data[CONF_HOST], existing.data[CONF_PORT])
                        == requested_endpoint
                    ):
                        return self.async_abort(reason="already_configured")
            except (
                MonitorSuiteAuthenticationError,
                MonitorSuiteConnectionError,
                MonitorSuiteInvalidResponseError,
                MonitorSuiteNotReadyError,
                ValueError,
            ) as err:
                errors["base"] = _error_key(err)
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error while reconfiguring Monitor Suite")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    unique_id=requested_endpoint,
                    data_updates={
                        CONF_HOST: normalize_host(info.host),
                        CONF_PORT: info.port,
                        CONF_API_KEY: api_key,
                    },
                    title=info.host,
                    reason="reconfigure_successful",
                )

        defaults = {
            CONF_HOST: entry.data[CONF_HOST],
            CONF_PORT: entry.data[CONF_PORT],
        }
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_connection_schema(defaults, api_key_required=False),
            errors=errors,
        )
