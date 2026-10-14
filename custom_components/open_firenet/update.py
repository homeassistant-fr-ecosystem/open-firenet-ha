"""Firmware update notification: tells when a newer firmware of the bridge is published on GitHub.

The entity only informs. It does not install anything: the update is done with the installer (USB or wireless)."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

import aiohttp
from homeassistant.components.update import UpdateDeviceClass, UpdateEntity, UpdateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, get_model_name
from .coordinator import OpenFirenetCoordinator

_LOGGER = logging.getLogger(__name__)

FIRMWARE_REPO = "openfirenet/open-firenet"
LATEST_RELEASE_URL = f"https://api.github.com/repos/{FIRMWARE_REPO}/releases/latest"

# GitHub allows 60 anonymous requests an hour per address: a check every few hours is plenty.
SCAN_INTERVAL = timedelta(hours=6)


async def async_fetch_latest_release(hass: HomeAssistant) -> dict | None:
    """The latest published release (never a draft or a pre-release), or None when GitHub cannot be reached."""
    session = async_get_clientsession(hass)
    try:
        async with asyncio.timeout(15):
            async with session.get(LATEST_RELEASE_URL, headers={"Accept": "application/vnd.github+json"}) as resp:
                if resp.status != 200:
                    _LOGGER.debug("GitHub answered %s to the firmware release check", resp.status)
                    return None
                data = await resp.json()
    except (asyncio.TimeoutError, aiohttp.ClientError, ValueError) as err:
        _LOGGER.debug("Firmware release check failed: %s", err)
        return None
    tag = str(data.get("tag_name") or "").strip()
    if not tag:
        return None
    return {
        "version": tag.removeprefix("v"),
        "url": data.get("html_url") or f"https://github.com/{FIRMWARE_REPO}/releases/tag/{tag}",
        "notes": data.get("body") or "",
    }


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: OpenFirenetCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([OpenFirenetFirmwareUpdate(coordinator, entry)], update_before_add=True)


class OpenFirenetFirmwareUpdate(CoordinatorEntity[OpenFirenetCoordinator], UpdateEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "firmware"
    _attr_device_class = UpdateDeviceClass.FIRMWARE
    _attr_supported_features = UpdateEntityFeature.RELEASE_NOTES
    # The coordinator polls the bridge; the release check has its own, slower, rhythm (SCAN_INTERVAL).
    _attr_should_poll = True

    def __init__(self, coordinator: OpenFirenetCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_update_firmware"
        self._release: dict | None = None

    @property
    def device_info(self) -> dict:
        device = self.coordinator.data.get("device", {})
        stove = self.coordinator.data.get("stove", {})
        model_name = stove.get("model_name") or get_model_name(stove.get("model"))
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": device.get("name", "Open Firenet"),
            "manufacturer": "Open Firenet",
            "model": f"RIKA {model_name}",
            "sw_version": f"Firmware v{device.get('version', '2.0.0')} (MB {stove.get('mainboard_version') or '?'})",
            "configuration_url": f"http://{self.coordinator.host}",
        }

    @property
    def installed_version(self) -> str | None:
        return (self.coordinator.data or {}).get("device", {}).get("version") or None

    @property
    def latest_version(self) -> str | None:
        # Without an answer from GitHub, nothing is claimed: the entity then shows no newer version.
        if self._release is None:
            return self.installed_version
        return self._release["version"]

    @property
    def release_url(self) -> str | None:
        return self._release["url"] if self._release else None

    async def async_release_notes(self) -> str | None:
        return (self._release or {}).get("notes") or None

    async def async_update(self) -> None:
        release = await async_fetch_latest_release(self.hass)
        if release is not None:
            self._release = release
