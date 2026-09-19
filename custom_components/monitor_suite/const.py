"""Constants for Monitor Suite."""

from datetime import timedelta
from numbers import Real

DOMAIN = "monitor_suite"
CONF_API_KEY = "api_key"
CONF_DEVICE_ID = "device_id"
CONF_UPDATE_INTERVAL = "update_interval"
DEFAULT_PORT = 5000
DEFAULT_UPDATE_INTERVAL = 10
MIN_UPDATE_INTERVAL = 5
MAX_UPDATE_INTERVAL = 300
REQUEST_TIMEOUT_SECONDS = 10
PLATFORMS = ["sensor"]
ATTRIBUTION = "Data provided by Monitor Suite Agent"


def validated_update_interval(value: object) -> int:
    """Return a safe polling interval from stored config-entry options."""
    if isinstance(value, bool) or not isinstance(value, Real):
        return DEFAULT_UPDATE_INTERVAL
    seconds = int(value)
    return min(MAX_UPDATE_INTERVAL, max(MIN_UPDATE_INTERVAL, seconds))


def update_interval(seconds: int) -> timedelta:
    """Convert a validated update interval to a timedelta."""
    return timedelta(seconds=validated_update_interval(seconds))
