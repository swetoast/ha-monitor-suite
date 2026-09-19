"""Sensors for Monitor Suite."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from numbers import Real
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfDataRate,
    UnitOfElectricPotential,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, CONF_DEVICE_ID, DOMAIN
from .coordinator import MonitorSuiteCoordinator

ValueFn = Callable[[dict[str, Any]], Any]
AttributesFn = Callable[[dict[str, Any]], dict[str, Any] | None]


def _nested_value(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = data
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _number(data: dict[str, Any], path: tuple[str, ...]) -> int | float | None:
    value = _nested_value(data, path)
    if isinstance(value, bool) or not isinstance(value, Real):
        return None
    return value


def _enum_value(
    data: dict[str, Any], path: tuple[str, ...], options: tuple[str, ...]
) -> str | None:
    """Return only normal enum values, excluding Home Assistant special states."""
    value = _nested_value(data, path)
    return value if isinstance(value, str) and value in options else None


def _timestamp(data: dict[str, Any], path: tuple[str, ...]) -> datetime | None:
    value = _nested_value(data, path)
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _cpu_attributes(data: dict[str, Any]) -> dict[str, Any] | None:
    cpu = data.get("cpu")
    if not isinstance(cpu, dict):
        return None
    attributes: dict[str, Any] = {}
    temperature = cpu.get("temperature_c")
    if isinstance(temperature, Real) and not isinstance(temperature, bool):
        attributes["temperature_c"] = temperature
    frequency = cpu.get("frequency_mhz")
    if isinstance(frequency, Real) and not isinstance(frequency, bool):
        attributes["frequency_mhz"] = frequency
    return attributes or None


def _fan_attributes(data: dict[str, Any]) -> dict[str, Any] | None:
    cooling = data.get("cooling")
    if not isinstance(cooling, dict):
        return None
    state = cooling.get("state")
    return {"cooling_state": state} if state in ("idle", "active") else None


def _status_attributes(data: dict[str, Any]) -> dict[str, Any] | None:
    health = data.get("health")
    if not isinstance(health, dict):
        return None
    return {
        key: health[key]
        for key in ("power_supply", "thermal_state", "performance_state")
        if isinstance(health.get(key), str)
    } or None


def _power_attributes(data: dict[str, Any]) -> dict[str, Any] | None:
    source = data.get("power", {}).get("source")
    return {"source": source} if isinstance(source, str) else None


def _network_attributes(data: dict[str, Any]) -> dict[str, Any] | None:
    network = data.get("network")
    if not isinstance(network, dict):
        return None
    attributes: dict[str, Any] = {}
    if isinstance(network.get("interface"), str):
        attributes["interface"] = network["interface"]
    link_speed = network.get("link_speed_mbps")
    if isinstance(link_speed, Real) and not isinstance(link_speed, bool):
        attributes["link_speed_mbps"] = link_speed
    return attributes or None


@dataclass(frozen=True, kw_only=True)
class MonitorSuiteSensorDescription(SensorEntityDescription):
    """Describe a fixed Monitor Suite sensor."""

    value_fn: ValueFn
    attributes_fn: AttributesFn | None = None


CORE_SENSORS: tuple[MonitorSuiteSensorDescription, ...] = (
    MonitorSuiteSensorDescription(
        key="status",
        translation_key="status",
        device_class=SensorDeviceClass.ENUM,
        options=["ok", "warning", "critical"],
        value_fn=lambda data: _enum_value(
            data, ("health", "status"), ("ok", "warning", "critical")
        ),
        attributes_fn=_status_attributes,
    ),
    MonitorSuiteSensorDescription(
        key="cpu_usage",
        translation_key="cpu_usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: _number(data, ("cpu", "usage_percent")),
        attributes_fn=_cpu_attributes,
    ),
    MonitorSuiteSensorDescription(
        key="memory_usage",
        translation_key="memory_usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: _number(data, ("memory", "used_percent")),
    ),
    MonitorSuiteSensorDescription(
        key="storage_usage",
        translation_key="storage_usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: _number(data, ("root_filesystem", "used_percent")),
    ),
    MonitorSuiteSensorDescription(
        key="power",
        translation_key="power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda data: _number(data, ("power", "value_w")),
        attributes_fn=_power_attributes,
    ),
    MonitorSuiteSensorDescription(
        key="input_voltage",
        translation_key="input_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        value_fn=lambda data: _number(data, ("power", "input_voltage_v")),
    ),
    MonitorSuiteSensorDescription(
        key="fan_speed",
        translation_key="fan_speed",
        native_unit_of_measurement="rpm",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _number(data, ("cooling", "fan_speed_rpm")),
        attributes_fn=_fan_attributes,
    ),
    MonitorSuiteSensorDescription(
        key="network_status",
        translation_key="network_status",
        device_class=SensorDeviceClass.ENUM,
        options=["up", "down"],
        value_fn=lambda data: _enum_value(
            data, ("network", "status"), ("up", "down")
        ),
        attributes_fn=_network_attributes,
    ),
    MonitorSuiteSensorDescription(
        key="network_download",
        translation_key="network_download",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _number(data, ("network", "download_bytes_per_second")),
    ),
    MonitorSuiteSensorDescription(
        key="network_upload",
        translation_key="network_upload",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _number(data, ("network", "upload_bytes_per_second")),
    ),
    MonitorSuiteSensorDescription(
        key="disk_read",
        translation_key="disk_read",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _number(data, ("disk_activity", "read_bytes_per_second")),
    ),
    MonitorSuiteSensorDescription(
        key="disk_write",
        translation_key="disk_write",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _number(
            data, ("disk_activity", "write_bytes_per_second")
        ),
    ),
    MonitorSuiteSensorDescription(
        key="last_boot",
        translation_key="last_boot",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: _timestamp(data, ("system", "booted_at")),
    ),
)


def _find_named_row(rows: Any, key: str, expected: str) -> dict[str, Any] | None:
    if not isinstance(rows, list):
        return None
    return next(
        (row for row in rows if isinstance(row, dict) and row.get(key) == expected),
        None,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[MonitorSuiteCoordinator],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensors from one coordinator snapshot."""
    registry = er.async_get(hass)
    for entity_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        unique_id = entity_entry.unique_id
        if unique_id.endswith(
            ("_network_link_speed", "_cpu_frequency", "_cpu_temperature", "_cooling_state")
        ) or (
            "_smart_" in unique_id
            and unique_id.endswith(("_temperature", "_remaining_life"))
        ):
            registry.async_remove(entity_entry.entity_id)

    coordinator = entry.runtime_data
    async_add_entities(
        MonitorSuiteSensor(coordinator, entry, description)
        for description in CORE_SENSORS
    )

    discovered: set[str] = set()

    def discover_entities() -> None:
        new_entities: list[SensorEntity] = []

        arrays = coordinator.data.get("raid", {}).get("arrays", [])
        if isinstance(arrays, list):
            for row in arrays:
                if not isinstance(row, dict) or not isinstance(row.get("name"), str):
                    continue
                name = row["name"]
                identity = f"raid:{name}"
                if identity not in discovered:
                    discovered.add(identity)
                    new_entities.append(
                        MonitorSuiteRaidSensor(coordinator, entry, name)
                    )

        devices = coordinator.data.get("smart", {}).get("devices", [])
        if isinstance(devices, list):
            for row in devices:
                if not isinstance(row, dict) or not isinstance(row.get("device"), str):
                    continue
                device = row["device"]
                status_identity = f"smart:{device}:status"
                if status_identity not in discovered:
                    discovered.add(status_identity)
                    new_entities.append(
                        MonitorSuiteSmartStatusSensor(coordinator, entry, device)
                    )

        if new_entities:
            async_add_entities(new_entities)

    discover_entities()
    entry.async_on_unload(coordinator.async_add_listener(discover_entities))


class MonitorSuiteBaseSensor(CoordinatorEntity[MonitorSuiteCoordinator], SensorEntity):
    """Base Monitor Suite sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(
        self, coordinator: MonitorSuiteCoordinator, entry: ConfigEntry, key: str
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._stable_device_id = str(
            entry.data.get(CONF_DEVICE_ID) or entry.unique_id or entry.entry_id
        )
        self._attr_unique_id = f"{self._stable_device_id}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the single monitored Raspberry Pi device."""
        device = self.coordinator.data.get("device", {})
        operating_system = device.get("operating_system")
        kernel_version = device.get("kernel_version")
        if operating_system and kernel_version:
            software_version = f"{operating_system}; kernel {kernel_version}"
        else:
            software_version = operating_system or kernel_version
        return DeviceInfo(
            identifiers={(DOMAIN, self._stable_device_id)},
            name=f"Monitor Suite {self._entry.title}",
            model=device.get("model"),
            sw_version=software_version,
            hw_version=device.get("architecture"),
        )


class MonitorSuiteSensor(MonitorSuiteBaseSensor):
    """One fixed high-value sensor."""

    entity_description: MonitorSuiteSensorDescription

    def __init__(
        self,
        coordinator: MonitorSuiteCoordinator,
        entry: ConfigEntry,
        description: MonitorSuiteSensorDescription,
    ) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the cached native value."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        """Return availability without performing I/O."""
        if not super().available:
            return False
        return self.entity_description.value_fn(self.coordinator.data) is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return only approved explanatory attributes."""
        if self.entity_description.attributes_fn is None:
            return None
        return self.entity_description.attributes_fn(self.coordinator.data)


class MonitorSuiteRaidSensor(MonitorSuiteBaseSensor):
    """Status for one Linux MD array."""

    _attr_translation_key = "raid_status"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [
        "healthy",
        "degraded",
        "failed",
        "recovering",
        "resyncing",
        "checking",
        "reshaping",
    ]

    def __init__(
        self, coordinator: MonitorSuiteCoordinator, entry: ConfigEntry, array_name: str
    ) -> None:
        super().__init__(coordinator, entry, f"raid_{array_name}_status")
        self._array_name = array_name
        self._attr_translation_placeholders = {"name": array_name}

    def _row(self) -> dict[str, Any] | None:
        return _find_named_row(
            self.coordinator.data.get("raid", {}).get("arrays", []),
            "name",
            self._array_name,
        )

    @property
    def native_value(self) -> str | None:
        """Return the cached RAID state."""
        row = self._row()
        value = row.get("status") if row else None
        return value if value in self._attr_options else None

    @property
    def available(self) -> bool:
        """Return whether this array has a supported current state."""
        return super().available and self.native_value is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return approved RAID details that explain the status."""
        row = self._row()
        if row is None:
            return None
        attributes = {
            key: row[key]
            for key in (
                "raid_level",
                "active_members",
                "expected_members",
                "failed_members",
                "redundancy",
            )
            if row.get(key) is not None
        }
        if isinstance(row.get("progress_percent"), Real):
            attributes["progress"] = row["progress_percent"]
        return attributes or None


class MonitorSuiteSmartSensor(MonitorSuiteBaseSensor):
    """Base sensor for one physical SMART device."""

    def __init__(
        self,
        coordinator: MonitorSuiteCoordinator,
        entry: ConfigEntry,
        device: str,
        suffix: str,
    ) -> None:
        super().__init__(coordinator, entry, f"smart_{device}_{suffix}")
        self._device = device
        self._attr_translation_placeholders = {"name": device}

    def _row(self) -> dict[str, Any] | None:
        return _find_named_row(
            self.coordinator.data.get("smart", {}).get("devices", []),
            "device",
            self._device,
        )

    @property
    def available(self) -> bool:
        """Return whether the physical device currently provides SMART data."""
        row = self._row()
        return (
            super().available and row is not None and row.get("status") != "unavailable"
        )


class MonitorSuiteSmartStatusSensor(MonitorSuiteSmartSensor):
    """SMART health and supporting measurements for one physical disk."""

    _attr_translation_key = "smart_status"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["healthy", "warning", "failed", "testing"]

    def __init__(
        self, coordinator: MonitorSuiteCoordinator, entry: ConfigEntry, device: str
    ) -> None:
        super().__init__(coordinator, entry, device, "status")

    @property
    def native_value(self) -> str | None:
        """Return the cached SMART state."""
        row = self._row()
        value = row.get("status") if row else None
        return value if value in self._attr_options else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return temperature and remaining life when supplied by the agent."""
        row = self._row()
        if row is None:
            return None
        attributes: dict[str, Any] = {}
        temperature = row.get("temperature_c")
        if isinstance(temperature, Real) and not isinstance(temperature, bool):
            attributes["temperature_c"] = temperature
        remaining_life = row.get("remaining_life_percent")
        if isinstance(remaining_life, Real) and not isinstance(remaining_life, bool):
            attributes["remaining_life_percent"] = remaining_life
        return attributes or None

