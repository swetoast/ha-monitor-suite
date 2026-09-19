"""Home Assistant behavior tests for Monitor Suite config flows."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
import voluptuous_serialize
from homeassistant.config_entries import SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.monitor_suite.api import (
    MonitorSuiteConnectionInfo,
    MonitorSuiteHealth,
    endpoint_id,
)
from custom_components.monitor_suite.const import (
    CONF_API_KEY,
    CONF_DEVICE_ID,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
)

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")

HOST = "monitor.local"
PORT = 5000
TOKEN = "secret-token"


def _connection(host: str = HOST, port: int = PORT) -> MonitorSuiteConnectionInfo:
    return MonitorSuiteConnectionInfo(
        host=host,
        port=port,
        health=MonitorSuiteHealth("ok", "3.0.0", True),
        status={},
    )


async def test_user_flow_form_loads(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {}
    voluptuous_serialize.convert(
        result["data_schema"], custom_serializer=cv.custom_serializer
    )


async def test_user_flow_stores_stable_device_id(hass: HomeAssistant) -> None:
    with patch(
        "custom_components.monitor_suite.config_flow.async_validate_connection",
        AsyncMock(return_value=_connection()),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_HOST: HOST, CONF_PORT: PORT, CONF_API_KEY: TOKEN},
        )

    expected_id = endpoint_id(HOST, PORT)
    assert result["type"] == "create_entry"
    assert result["data"][CONF_DEVICE_ID] == expected_id
    assert result["data"][CONF_HOST] == HOST


async def test_reconfigure_updates_endpoint_not_device_id(
    hass: HomeAssistant,
) -> None:
    old_id = endpoint_id(HOST, PORT)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=HOST,
        unique_id=old_id,
        version=2,
        data={
            CONF_HOST: HOST,
            CONF_PORT: PORT,
            CONF_API_KEY: TOKEN,
            CONF_DEVICE_ID: old_id,
        },
    )
    entry.add_to_hass(hass)
    new_host = "monitor-new.local"

    with (
        patch(
            "custom_components.monitor_suite.config_flow.async_validate_connection",
            AsyncMock(return_value=_connection(new_host, PORT)),
        ),
        patch.object(hass.config_entries, "async_reload", AsyncMock(return_value=True)),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
            data={CONF_HOST: new_host, CONF_PORT: PORT, CONF_API_KEY: ""},
        )

    assert result["type"] == "abort"
    assert result["reason"] == "reconfigure_successful"
    assert entry.unique_id == endpoint_id(new_host, PORT)
    assert entry.data[CONF_DEVICE_ID] == old_id
    assert entry.data[CONF_API_KEY] == TOKEN


async def test_options_flow_form_loads(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=HOST,
        unique_id=endpoint_id(HOST, PORT),
        version=2,
        data={
            CONF_HOST: HOST,
            CONF_PORT: PORT,
            CONF_API_KEY: TOKEN,
            CONF_DEVICE_ID: endpoint_id(HOST, PORT),
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == "form"
    assert result["step_id"] == "init"
    assert result["errors"] == {}


async def test_options_update_interval(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=HOST,
        unique_id=endpoint_id(HOST, PORT),
        version=2,
        data={
            CONF_HOST: HOST,
            CONF_PORT: PORT,
            CONF_API_KEY: TOKEN,
            CONF_DEVICE_ID: endpoint_id(HOST, PORT),
        },
    )
    entry.add_to_hass(hass)

    with patch.object(
        hass.config_entries, "async_reload", AsyncMock(return_value=True)
    ):
        result = await hass.config_entries.options.async_init(
            entry.entry_id,
            data={CONF_UPDATE_INTERVAL: 30},
        )

    assert result["type"] == "create_entry"
    assert entry.options[CONF_UPDATE_INTERVAL] == 30
