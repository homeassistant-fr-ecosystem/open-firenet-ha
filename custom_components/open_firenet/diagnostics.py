from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import OpenFirenetCoordinator

_REDACT = {"mac", "ip", "ssid"}


def _sanitize(data: Any) -> Any:
    if isinstance(data, dict):
        return {
            k: "**REDACTED**" if k in _REDACT else _sanitize(v)
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [_sanitize(v) for v in data]
    return data


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    coordinator: OpenFirenetCoordinator = hass.data[DOMAIN][entry.entry_id]
    return {
        "entry": {
            "host": entry.data.get("host"),
            "scan_interval": entry.data.get("scan_interval"),
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "data": _sanitize(coordinator.data),
        },
    }
